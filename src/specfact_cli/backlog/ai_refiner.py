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
    ) -> None:
        """
        Initialize refinement result.

        Args:
            refined_body: AI-refined body content
            confidence: Confidence score (0.0-1.0)
            has_todo_markers: Whether refinement contains TODO markers
            has_notes_section: Whether refinement contains NOTES section
        """
        self.refined_body = refined_body
        self.confidence = confidence
        self.has_todo_markers = has_todo_markers
        self.has_notes_section = has_notes_section


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

        prompt = f"""Transform the following backlog item into the {template.name} template format.

Original Backlog Item:
Title: {item.title}

Body:
{item.body_markdown}

Target Template: {template.name}
Description: {template.description}

Required Sections:
{required_sections_str}

Optional Sections:
{optional_sections_str}

Instructions:
1. Preserve all original requirements, scope, and technical details
2. Do NOT add new features or change the scope
3. Transform the content to match the template structure
4. If information is missing for a required section, use a Markdown checkbox: - [ ] describe what's needed
5. If you detect conflicting or ambiguous information, add a [NOTES] section at the end explaining the ambiguity
6. Use markdown formatting for sections (## Section Name)

Return ONLY the refined backlog item body content in markdown format. Do not include any explanations or metadata."""
        return prompt.strip()

    @beartype
    @require(
        lambda self, refined_body: isinstance(refined_body, str) and len(refined_body) > 0,
        "Refined body must be non-empty",
    )
    @require(lambda self, template: isinstance(template, BacklogTemplate), "Template must be BacklogTemplate")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def _validate_required_sections(self, refined_body: str, template: BacklogTemplate) -> bool:
        """
        Validate that refined content contains all required sections.

        Args:
            refined_body: Refined body content
            template: Target BacklogTemplate

        Returns:
            True if all required sections are present, False otherwise
        """
        if not template.required_sections:
            return True  # No requirements = valid

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
    @ensure(lambda result: isinstance(result, RefinementResult), "Must return RefinementResult")
    def validate_and_score_refinement(
        self,
        refined_body: str,
        original_body: str,
        template: BacklogTemplate,
    ) -> RefinementResult:
        """
        Validate and score refined content from IDE AI copilot.

        This method validates the refined content returned by the IDE AI copilot
        and calculates a confidence score based on completeness and quality.

        Args:
            refined_body: Refined body content from IDE AI copilot
            original_body: Original body content
            template: Target BacklogTemplate

        Returns:
            RefinementResult with validated content and confidence score

        Raises:
            ValueError: If refined content is invalid or malformed
        """
        if not refined_body.strip():
            msg = "Refined body is empty"
            raise ValueError(msg)

        # Validate required sections
        if not self._validate_required_sections(refined_body, template):
            msg = f"Refined content is missing required sections: {template.required_sections}"
            raise ValueError(msg)

        # Check for TODO markers and NOTES section
        has_todo = self._has_todo_markers(refined_body)
        has_notes = self._has_notes_section(refined_body)

        # Calculate confidence
        confidence = self._calculate_confidence(refined_body, original_body, template, has_todo, has_notes)

        return RefinementResult(
            refined_body=refined_body,
            confidence=confidence,
            has_todo_markers=has_todo,
            has_notes_section=has_notes,
        )

    @beartype
    @require(lambda self, refined_body: isinstance(refined_body, str), "Refined body must be string")
    @require(lambda self, original_body: isinstance(original_body, str), "Original body must be string")
    @require(lambda self, template: isinstance(template, BacklogTemplate), "Template must be BacklogTemplate")
    @ensure(lambda result: isinstance(result, float) and 0.0 <= result <= 1.0, "Must return float in [0.0, 1.0]")
    def _calculate_confidence(
        self,
        refined_body: str,
        original_body: str,
        template: BacklogTemplate,
        has_todo: bool,
        has_notes: bool,
    ) -> float:
        """
        Calculate confidence score for refined content.

        Args:
            refined_body: Refined body content
            original_body: Original body content
            template: Target BacklogTemplate
            has_todo: Whether TODO markers are present
            has_notes: Whether NOTES section is present

        Returns:
            Confidence score (0.0-1.0)
        """
        # Base confidence: 1.0 if all required sections present, 0.8 otherwise
        base_confidence = 1.0 if self._validate_required_sections(refined_body, template) else 0.8

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
