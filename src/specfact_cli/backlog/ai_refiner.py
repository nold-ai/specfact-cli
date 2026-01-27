"""
Backlog refinement prompt generator and validator.

This module generates prompts for IDE AI copilots to refine backlog items,
and validates/processes the refined content returned by the AI copilot.

SpecFact CLI Architecture:
- SpecFact CLI generates prompts/instructions for IDE AI copilots
- IDE AI copilots execute those instructions using their native LLM
- IDE AI copilots feed results back to SpecFact CLI
- SpecFact CLI validates and processes the results
"""

from __future__ import annotations

import re

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.templates.registry import BacklogTemplate


class RefinementResult:
    """Result of AI refinement with refined content and confidence."""

    def __init__(
        self,
        refined_body: str,
        confidence: float,
        has_todo_markers: bool = False,
        has_notes_section: bool = False,
        needs_splitting: bool = False,
        splitting_suggestion: str | None = None,
    ) -> None:
        """
        Initialize refinement result.

        Args:
            refined_body: AI-refined body content
            confidence: Confidence score (0.0-1.0)
            has_todo_markers: Whether refinement contains TODO markers
            has_notes_section: Whether refinement contains NOTES section
            needs_splitting: Whether story should be split (complexity detection)
            splitting_suggestion: Suggestion for how to split the story
        """
        self.refined_body = refined_body
        self.confidence = confidence
        self.has_todo_markers = has_todo_markers
        self.has_notes_section = has_notes_section
        self.needs_splitting = needs_splitting
        self.splitting_suggestion = splitting_suggestion


class BacklogAIRefiner:
    """
    Backlog refinement prompt generator and validator.

    This class generates prompts for IDE AI copilots to refine backlog items,
    and validates/processes the refined content returned by the AI copilot.

    SpecFact CLI does NOT directly invoke LLM APIs. Instead:
    1. Generate prompt for IDE AI copilot
    2. IDE AI copilot executes prompt using its native LLM
    3. IDE AI copilot feeds refined content back to SpecFact CLI
    4. SpecFact CLI validates and processes the refined content
    """

    # Scrum threshold: stories > 13 points should be split
    SCRUM_SPLIT_THRESHOLD = 13

    @beartype
    @require(lambda self, item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @require(lambda self, template: isinstance(template, BacklogTemplate), "Template must be BacklogTemplate")
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty prompt string")
    def generate_refinement_prompt(self, item: BacklogItem, template: BacklogTemplate) -> str:
        """
        Generate prompt for IDE AI copilot to refine backlog item.

        This prompt instructs the IDE AI copilot to:
        1. Transform the backlog item into target template format
        2. Preserve original intent and scope
        3. Return refined content for validation

        Args:
            item: BacklogItem to refine
            template: Target BacklogTemplate

        Returns:
            Prompt string for IDE AI copilot
        """
        required_sections_str = "\n".join(f"- {section}" for section in template.required_sections)
        optional_sections_str = (
            "\n".join(f"- {section}" for section in template.optional_sections)
            if template.optional_sections
            else "None"
        )

        # Provider-specific instructions
        provider_instructions = ""
        if item.provider == "github":
            provider_instructions = """
For GitHub issues: Use markdown headings (## Section Name) in the body to structure content.
Each required section should be a markdown heading with content below it."""
        elif item.provider == "ado":
            provider_instructions = """
For Azure DevOps work items: Note that fields are separate (not markdown headings in body).
However, for refinement purposes, structure the content as markdown headings in the body.
The adapter will map these back to separate ADO fields during writeback."""

        # Include story points, business value, priority if available
        metrics_info = ""
        if item.story_points is not None:
            metrics_info += f"\nStory Points: {item.story_points}"
        if item.business_value is not None:
            metrics_info += f"\nBusiness Value: {item.business_value}"
        if item.priority is not None:
            metrics_info += f"\nPriority: {item.priority} (1=highest)"
        if item.value_points is not None:
            metrics_info += f"\nValue Points (SAFe): {item.value_points}"
        if item.work_item_type:
            metrics_info += f"\nWork Item Type: {item.work_item_type}"

        prompt = f"""Transform the following backlog item into the {template.name} template format.

Original Backlog Item:
Title: {item.title}
Provider: {item.provider}
{metrics_info}

Body:
{item.body_markdown}

Target Template: {template.name}
Description: {template.description}

Required Sections:
{required_sections_str}

Optional Sections:
{optional_sections_str}
{provider_instructions}

Instructions:
1. Preserve all original requirements, scope, and technical details
2. Do NOT add new features or change the scope
3. Transform the content to match the template structure
4. If information is missing for a required section, use a Markdown checkbox: - [ ] describe what's needed
5. If you detect conflicting or ambiguous information, add a [NOTES] section at the end explaining the ambiguity
6. Use markdown formatting for sections (## Section Name)
7. Include story points, business value, priority, and work item type if available in the appropriate sections
8. For stories with high story points (>13 for Scrum, >21 for SAFe), consider suggesting story splitting
9. Provider-aware formatting:
   - **GitHub**: Use markdown headings in body (## Section Name)
   - **ADO**: Use markdown headings in body (will be mapped to separate ADO fields during writeback)

Return ONLY the refined backlog item body content in markdown format. Do not include any explanations or metadata."""
        return prompt.strip()

    @beartype
    @require(
        lambda self, refined_body: isinstance(refined_body, str) and len(refined_body) > 0,
        "Refined body must be non-empty",
    )
    @require(lambda self, template: isinstance(template, BacklogTemplate), "Template must be BacklogTemplate")
    @require(lambda self, item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def _validate_required_sections(self, refined_body: str, template: BacklogTemplate, item: BacklogItem) -> bool:
        """
        Validate that refined content contains all required sections.

        Note: Refined content is always markdown (from AI copilot), so we always check
        markdown headings regardless of provider. The provider-aware logic is used for
        extraction, but validation of refined content always uses markdown heading checks.

        Args:
            refined_body: Refined body content (always markdown)
            template: Target BacklogTemplate
            item: BacklogItem being validated (used for context, not field checking)

        Returns:
            True if all required sections are present, False otherwise
        """
        if not template.required_sections:
            return True  # No requirements = valid

        # Refined content is always markdown (from AI copilot), so check markdown headings
        body_lower = refined_body.lower()
        for section in template.required_sections:
            section_lower = section.lower()
            # Check for markdown heading
            heading_pattern = rf"^#+\s+{re.escape(section_lower)}\s*$"
            found = re.search(heading_pattern, body_lower, re.MULTILINE | re.IGNORECASE)
            if not found and section_lower not in body_lower:
                return False
        return True

    @beartype
    @require(lambda self, refined_body: isinstance(refined_body, str), "Refined body must be string")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def _has_todo_markers(self, refined_body: str) -> bool:
        """
        Check if refined content contains TODO markers.

        Args:
            refined_body: Refined body content

        Returns:
            True if TODO markers are present, False otherwise
        """
        todo_pattern = r"\[TODO[:\s][^\]]+\]"
        return bool(re.search(todo_pattern, refined_body, re.IGNORECASE))

    @beartype
    @require(lambda self, refined_body: isinstance(refined_body, str), "Refined body must be string")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def _has_notes_section(self, refined_body: str) -> bool:
        """
        Check if refined content contains NOTES section.

        Args:
            refined_body: Refined body content

        Returns:
            True if NOTES section is present, False otherwise
        """
        notes_pattern = r"^#+\s+NOTES\s*$"
        return bool(re.search(notes_pattern, refined_body, re.MULTILINE | re.IGNORECASE))

    @beartype
    @require(lambda self, refined_body: isinstance(refined_body, str), "Refined body must be string")
    @require(lambda self, original_body: isinstance(original_body, str), "Original body must be string")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def _has_significant_size_increase(self, refined_body: str, original_body: str) -> bool:
        """
        Check if refined body has significant size increase (possible hallucination).

        Args:
            refined_body: Refined body content
            original_body: Original body content

        Returns:
            True if size increased significantly (>50%), False otherwise
        """
        if not original_body:
            return False
        size_increase = (len(refined_body) - len(original_body)) / len(original_body)
        return size_increase > 0.5

    @beartype
    @require(lambda self, refined_body: isinstance(refined_body, str), "Refined body must be string")
    @require(lambda self, original_body: isinstance(original_body, str), "Original body must be string")
    @require(lambda self, template: isinstance(template, BacklogTemplate), "Template must be BacklogTemplate")
    @require(lambda self, item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @ensure(lambda result: isinstance(result, RefinementResult), "Must return RefinementResult")
    def validate_and_score_refinement(
        self,
        refined_body: str,
        original_body: str,
        template: BacklogTemplate,
        item: BacklogItem,
    ) -> RefinementResult:
        """
        Validate and score refined content from IDE AI copilot.

        This method validates the refined content returned by the IDE AI copilot
        and calculates a confidence score based on completeness and quality.

        Args:
            refined_body: Refined body content from IDE AI copilot
            original_body: Original body content
            template: Target BacklogTemplate
            item: BacklogItem being validated (for provider-aware validation)

        Returns:
            RefinementResult with validated content and confidence score

        Raises:
            ValueError: If refined content is invalid or malformed
        """
        if not refined_body.strip():
            msg = "Refined body is empty"
            raise ValueError(msg)

        # Validate required sections (provider-aware)
        if not self._validate_required_sections(refined_body, template, item):
            msg = f"Refined content is missing required sections: {template.required_sections}"
            raise ValueError(msg)

        # Validate story points, business value, priority fields if present
        validation_errors = self._validate_agile_fields(item)
        if validation_errors:
            msg = f"Field validation errors: {', '.join(validation_errors)}"
            raise ValueError(msg)

        # Check for TODO markers and NOTES section
        has_todo = self._has_todo_markers(refined_body)
        has_notes = self._has_notes_section(refined_body)

        # Detect story splitting needs
        needs_splitting, splitting_suggestion = self._detect_story_splitting(item)

        # Calculate confidence
        confidence = self._calculate_confidence(refined_body, original_body, template, item, has_todo, has_notes)

        return RefinementResult(
            refined_body=refined_body,
            confidence=confidence,
            has_todo_markers=has_todo,
            has_notes_section=has_notes,
            needs_splitting=needs_splitting,
            splitting_suggestion=splitting_suggestion,
        )

    @beartype
    @require(lambda self, refined_body: isinstance(refined_body, str), "Refined body must be string")
    @require(lambda self, original_body: isinstance(original_body, str), "Original body must be string")
    @require(lambda self, template: isinstance(template, BacklogTemplate), "Template must be BacklogTemplate")
    @require(lambda self, item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @ensure(lambda result: isinstance(result, float) and 0.0 <= result <= 1.0, "Must return float in [0.0, 1.0]")
    def _calculate_confidence(
        self,
        refined_body: str,
        original_body: str,
        template: BacklogTemplate,
        item: BacklogItem,
        has_todo: bool,
        has_notes: bool,
    ) -> float:
        """
        Calculate confidence score for refined content.

        Args:
            refined_body: Refined body content
            original_body: Original body content
            template: Target BacklogTemplate
            item: BacklogItem being validated
            has_todo: Whether TODO markers are present
            has_notes: Whether NOTES section is present

        Returns:
            Confidence score (0.0-1.0)
        """
        # Base confidence: 1.0 if all required sections present, 0.8 otherwise
        base_confidence = 1.0 if self._validate_required_sections(refined_body, template, item) else 0.8

        # Bonus for having story points, business value, priority (indicates completeness)
        if item.story_points is not None or item.business_value is not None or item.priority is not None:
            base_confidence = min(1.0, base_confidence + 0.05)

        # Deduct 0.1 per TODO marker (max 2 TODO markers checked)
        if has_todo:
            todo_count = len(re.findall(r"\[TODO[:\s][^\]]+\]", refined_body, re.IGNORECASE))
            base_confidence -= min(0.1 * todo_count, 0.2)  # Max deduction 0.2

        # Deduct 0.15 for NOTES section
        if has_notes:
            base_confidence -= 0.15

        # Deduct 0.1 for significant size increase (possible hallucination)
        if self._has_significant_size_increase(refined_body, original_body):
            base_confidence -= 0.1

        # Ensure confidence is in [0.0, 1.0]
        return max(0.0, min(1.0, base_confidence))

    @beartype
    @require(lambda self, item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @ensure(lambda result: isinstance(result, tuple) and len(result) == 2, "Must return tuple (bool, str | None)")
    def _detect_story_splitting(self, item: BacklogItem) -> tuple[bool, str | None]:
        """
        Detect if story needs splitting based on complexity (Scrum/SAFe thresholds).

        Stories > 13 points (Scrum) or multi-sprint stories should be split into
        multiple stories under the same feature.

        Args:
            item: BacklogItem to check

        Returns:
            Tuple of (needs_splitting: bool, suggestion: str | None)
        """
        if item.story_points is None:
            return (False, None)

        # Check if story exceeds Scrum threshold
        if item.story_points > self.SCRUM_SPLIT_THRESHOLD:
            suggestion = (
                f"Story has {item.story_points} story points, which exceeds the Scrum threshold of {self.SCRUM_SPLIT_THRESHOLD} points. "
                f"Consider splitting into multiple smaller stories under the same feature. "
                f"Each story should be 1-{self.SCRUM_SPLIT_THRESHOLD} points and completable within a single sprint."
            )
            return (True, suggestion)

        # Check for multi-sprint stories (stories spanning multiple iterations)
        # This is indicated by story points > typical sprint capacity (13 points)
        # or by explicit iteration/sprint tracking showing multiple sprints
        if item.sprint and item.iteration and item.story_points and item.story_points > self.SCRUM_SPLIT_THRESHOLD:
            # If story has both sprint and iteration, check if it spans multiple sprints
            # (This would require more context, but we can flag high-point stories)
            suggestion = (
                f"Story may span multiple sprints ({item.story_points} points). "
                f"Consider splitting into multiple stories to ensure each can be completed in a single sprint."
            )
            return (True, suggestion)

        # SAFe-specific: Check Feature → Story hierarchy
        if (
            item.work_item_type
            and item.work_item_type.lower() in ["user story", "story"]
            and item.story_points
            and item.story_points > 21
        ):  # Very high for a story
            # In SAFe, stories should have a Feature parent
            # If story_points is very high, it might be a Feature masquerading as a Story
            suggestion = (
                f"Story has {item.story_points} points, which is unusually high for a User Story in SAFe. "
                f"Consider if this should be a Feature instead, or split into multiple Stories under a Feature."
            )
            return (True, suggestion)

        return (False, None)

    @beartype
    @require(lambda self, item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @ensure(lambda result: isinstance(result, list), "Must return list of strings")
    def _validate_agile_fields(self, item: BacklogItem) -> list[str]:
        """
        Validate agile framework fields (story_points, business_value, priority).

        Args:
            item: BacklogItem to validate

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors: list[str] = []

        # Validate story_points (0-100 range, Scrum/SAFe)
        if item.story_points is not None:
            if not isinstance(item.story_points, int):
                errors.append(f"story_points must be int, got {type(item.story_points).__name__}")
            elif item.story_points < 0 or item.story_points > 100:
                errors.append(f"story_points must be in range 0-100, got {item.story_points}")

        # Validate business_value (0-100 range, Scrum/SAFe)
        if item.business_value is not None:
            if not isinstance(item.business_value, int):
                errors.append(f"business_value must be int, got {type(item.business_value).__name__}")
            elif item.business_value < 0 or item.business_value > 100:
                errors.append(f"business_value must be in range 0-100, got {item.business_value}")

        # Validate priority (1-4 range, 1=highest, all frameworks)
        if item.priority is not None:
            if not isinstance(item.priority, int):
                errors.append(f"priority must be int, got {type(item.priority).__name__}")
            elif item.priority < 1 or item.priority > 4:
                errors.append(f"priority must be in range 1-4 (1=highest), got {item.priority}")

        # Validate value_points (SAFe-specific, should be calculated from business_value / story_points)
        if item.value_points is not None:
            if not isinstance(item.value_points, int):
                errors.append(f"value_points must be int, got {type(item.value_points).__name__}")
            elif item.value_points < 0:
                errors.append(f"value_points must be non-negative, got {item.value_points}")

        return errors
