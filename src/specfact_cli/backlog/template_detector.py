"""
Template detection engine for backlog items.

This module provides structural and pattern-based template matching with
confidence scoring (60% structure, 40% pattern).
"""

from __future__ import annotations

import re

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.templates.registry import BacklogTemplate, TemplateRegistry


class TemplateDetectionResult:
    """Result of template detection with confidence and missing fields."""

    def __init__(
        self,
        template_id: str | None = None,
        confidence: float = 0.0,
        missing_fields: list[str] | None = None,
    ) -> None:
        """
        Initialize template detection result.

        Args:
            template_id: Detected template ID (None if no match)
            confidence: Confidence score (0.0-1.0)
            missing_fields: List of missing required fields
        """
        self.template_id = template_id
        self.confidence = confidence
        self.missing_fields = missing_fields or []


class TemplateDetector:
    """
    Template detection engine with structural and pattern-based matching.

    The detector uses:
    - Structural fit scoring (60% weight): Checks presence of required section headings
    - Pattern fit scoring (40% weight): Matches title and body regex patterns
    - Weighted confidence calculation: 0.6 * structural_score + 0.4 * pattern_score
    """

    def __init__(self, registry: TemplateRegistry) -> None:
        """
        Initialize template detector.

        Args:
            registry: TemplateRegistry instance
        """
        self.registry = registry

    @beartype
    @require(lambda self, item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @require(lambda self, template: isinstance(template, BacklogTemplate), "Template must be BacklogTemplate")
    @ensure(lambda result: isinstance(result, float) and 0.0 <= result <= 1.0, "Must return float in [0.0, 1.0]")
    def _score_structural_fit(self, item: BacklogItem, template: BacklogTemplate) -> float:
        """
        Score structural fit by checking required section headings.

        Args:
            item: BacklogItem to check
            template: BacklogTemplate to match against

        Returns:
            Structural fit score (0.0-1.0)
        """
        if not template.required_sections:
            return 1.0  # No requirements = perfect match

        body_lower = item.body_markdown.lower()
        found_sections = 0

        for section in template.required_sections:
            # Check for exact heading match (markdown heading)
            section_lower = section.lower()
            # Match markdown headings: # Section, ## Section, ### Section, etc.
            heading_pattern = rf"^#+\s+{re.escape(section_lower)}\s*$"
            if re.search(heading_pattern, body_lower, re.MULTILINE | re.IGNORECASE):
                found_sections += 1
                continue

            # Check for fuzzy match (section appears in text)
            if section_lower in body_lower:
                found_sections += 1

        if not template.required_sections:
            return 1.0

        return found_sections / len(template.required_sections)

    @beartype
    @require(lambda self, item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @require(lambda self, template: isinstance(template, BacklogTemplate), "Template must be BacklogTemplate")
    @ensure(lambda result: isinstance(result, float) and 0.0 <= result <= 1.0, "Must return float in [0.0, 1.0]")
    def _score_pattern_fit(self, item: BacklogItem, template: BacklogTemplate) -> float:
        """
        Score pattern fit by matching regex patterns.

        Args:
            item: BacklogItem to check
            template: BacklogTemplate to match against

        Returns:
            Pattern fit score (0.0-1.0)
        """
        patterns_to_check: list[tuple[str, str]] = []

        # Add title patterns
        for pattern in template.title_patterns:
            patterns_to_check.append(("title", pattern))

        # Add body patterns
        for _pattern_name, pattern in template.body_patterns.items():
            patterns_to_check.append(("body", pattern))

        if not patterns_to_check:
            return 1.0  # No patterns = perfect match

        matched_patterns = 0
        for pattern_type, pattern in patterns_to_check:
            text = item.title if pattern_type == "title" else item.body_markdown
            try:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    matched_patterns += 1
            except re.error:
                # Invalid regex pattern, skip
                continue

        return matched_patterns / len(patterns_to_check) if patterns_to_check else 1.0

    @beartype
    @require(lambda self, item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @require(lambda self, template: isinstance(template, BacklogTemplate), "Template must be BacklogTemplate")
    @ensure(lambda result: isinstance(result, list), "Must return list of strings")
    def _find_missing_fields(self, item: BacklogItem, template: BacklogTemplate) -> list[str]:
        """
        Find missing required fields for a template.

        Args:
            item: BacklogItem to check
            template: BacklogTemplate to match against

        Returns:
            List of missing required section names
        """
        missing: list[str] = []
        body_lower = item.body_markdown.lower()

        for section in template.required_sections:
            section_lower = section.lower()
            # Check for exact heading match
            heading_pattern = rf"^#+\s+{re.escape(section_lower)}\s*$"
            found = re.search(heading_pattern, body_lower, re.MULTILINE | re.IGNORECASE)
            if not found and section_lower not in body_lower:
                missing.append(section)

        return missing

    @beartype
    @require(lambda self, item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @require(lambda self, provider: provider is None or isinstance(provider, str), "Provider must be str or None")
    @require(lambda self, framework: framework is None or isinstance(framework, str), "Framework must be str or None")
    @require(lambda self, persona: persona is None or isinstance(persona, str), "Persona must be str or None")
    @ensure(lambda result: isinstance(result, TemplateDetectionResult), "Must return TemplateDetectionResult")
    def detect_template(
        self,
        item: BacklogItem,
        provider: str | None = None,
        framework: str | None = None,
        persona: str | None = None,
    ) -> TemplateDetectionResult:
        """
        Detect which template (if any) a backlog item matches.

        Uses priority-based template resolution with persona/framework/provider filtering.

        Args:
            item: BacklogItem to analyze
            provider: Provider name for template filtering (default: from item.provider)
            framework: Framework name for template filtering
            persona: Persona name for template filtering

        Returns:
            TemplateDetectionResult with template_id, confidence, and missing_fields
        """
        # Use item.provider if provider not specified
        if provider is None:
            provider = item.provider

        # First, try to resolve template using priority-based resolution
        resolved_template = self.registry.resolve_template(provider=provider, framework=framework, persona=persona)

        # If resolved template found, check if it matches the item
        if resolved_template:
            structural_score = self._score_structural_fit(item, resolved_template)
            pattern_score = self._score_pattern_fit(item, resolved_template)
            confidence = 0.6 * structural_score + 0.4 * pattern_score

            if confidence >= 0.5:
                missing_fields = self._find_missing_fields(item, resolved_template)
                return TemplateDetectionResult(
                    template_id=resolved_template.template_id,
                    confidence=confidence,
                    missing_fields=missing_fields,
                )

        # Fallback: Check all templates and find best match
        best_match: TemplateDetectionResult | None = None
        best_confidence = 0.0

        # Get all corporate templates, filtered by provider/framework/persona if specified
        templates = self.registry.list_templates(scope="corporate")
        filtered_templates = templates

        # Apply filters
        if provider:
            filtered_templates = [t for t in filtered_templates if t.provider is None or t.provider == provider]
        if framework:
            filtered_templates = [t for t in filtered_templates if t.framework is None or t.framework == framework]
        if persona:
            filtered_templates = [t for t in filtered_templates if not t.personas or persona in t.personas]

        # If no templates match filters, use all templates
        if not filtered_templates:
            filtered_templates = templates

        for template in filtered_templates:
            # Calculate structural fit (60% weight)
            structural_score = self._score_structural_fit(item, template)

            # Calculate pattern fit (40% weight)
            pattern_score = self._score_pattern_fit(item, template)

            # Weighted confidence: 0.6 * structural_score + 0.4 * pattern_score
            confidence = 0.6 * structural_score + 0.4 * pattern_score

            # Track best match
            if confidence > best_confidence:
                best_confidence = confidence
                missing_fields = self._find_missing_fields(item, template)
                best_match = TemplateDetectionResult(
                    template_id=template.template_id,
                    confidence=confidence,
                    missing_fields=missing_fields,
                )

        # Return best match or no match result
        if best_match and best_confidence >= 0.5:
            return best_match

        # No match or low confidence
        return TemplateDetectionResult(template_id=None, confidence=best_confidence, missing_fields=[])
