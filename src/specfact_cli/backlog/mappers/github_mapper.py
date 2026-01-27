"""
GitHub field mapper for extracting fields from GitHub issue markdown body.

This mapper extracts fields from GitHub issues which use a single markdown body
with headings to structure content (e.g., ## Acceptance Criteria, ## Story Points).
"""

from __future__ import annotations

import re
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.backlog.mappers.base import FieldMapper


class GitHubFieldMapper(FieldMapper):
    """
    Field mapper for GitHub issues.

    Extracts fields from markdown body using heading patterns:
    - Description: Default body content or ## Description section
    - Acceptance Criteria: ## Acceptance Criteria heading
    - Story Points: ## Story Points or **Story Points:** patterns
    - Business Value: ## Business Value or **Business Value:** patterns
    - Priority: ## Priority or **Priority:** patterns
    - Work Item Type: Extracted from labels or issue type metadata
    """

    @beartype
    @require(lambda self, item_data: isinstance(item_data, dict), "Item data must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_fields(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract fields from GitHub issue data.

        Args:
            item_data: GitHub issue data from API

        Returns:
            Dict mapping canonical field names to extracted values
        """
        body = item_data.get("body", "") or ""
        labels = item_data.get("labels", [])
        label_names = [label.get("name", "") if isinstance(label, dict) else str(label) for label in labels if label]

        fields: dict[str, Any] = {}

        # Extract description (default body content or ## Description section)
        description = self._extract_section(body, "Description")
        if not description:
            # If no ## Description section, use body as-is (excluding other sections)
            description = self._extract_default_content(body)
        fields["description"] = description.strip() if description else ""

        # Extract acceptance criteria from ## Acceptance Criteria heading
        acceptance_criteria = self._extract_section(body, "Acceptance Criteria")
        fields["acceptance_criteria"] = acceptance_criteria.strip() if acceptance_criteria else None

        # Extract story points from ## Story Points or **Story Points:** patterns
        story_points = self._extract_numeric_field(body, "Story Points")
        fields["story_points"] = story_points if story_points is not None else None

        # Extract business value from ## Business Value or **Business Value:** patterns
        business_value = self._extract_numeric_field(body, "Business Value")
        fields["business_value"] = business_value if business_value is not None else None

        # Extract priority from ## Priority or **Priority:** patterns
        priority = self._extract_numeric_field(body, "Priority")
        fields["priority"] = priority if priority is not None else None

        # Calculate value points (SAFe-specific: business_value / story_points)
        business_value_val: int | None = fields.get("business_value")
        story_points_val: int | None = fields.get("story_points")
        if (
            business_value_val is not None
            and story_points_val is not None
            and story_points_val != 0
            and isinstance(business_value_val, int)
            and isinstance(story_points_val, int)
        ):
            try:
                value_points = int(business_value_val / story_points_val)
                fields["value_points"] = value_points
            except (ZeroDivisionError, TypeError):
                fields["value_points"] = None
        else:
            fields["value_points"] = None

        # Extract work item type from labels or issue metadata
        work_item_type = self._extract_work_item_type(label_names, item_data)
        fields["work_item_type"] = work_item_type

        return fields

    @beartype
    @require(lambda self, canonical_fields: isinstance(canonical_fields, dict), "Canonical fields must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def map_from_canonical(self, canonical_fields: dict[str, Any]) -> dict[str, Any]:
        """
        Map canonical fields back to GitHub markdown format.

        Args:
            canonical_fields: Dict of canonical field names to values

        Returns:
            Dict with markdown body structure for GitHub
        """
        body_sections: list[str] = []

        # Add description
        description = canonical_fields.get("description", "")
        if description:
            body_sections.append(description)

        # Add acceptance criteria as markdown heading
        acceptance_criteria = canonical_fields.get("acceptance_criteria")
        if acceptance_criteria:
            body_sections.append(f"## Acceptance Criteria\n\n{acceptance_criteria}")

        # Add story points as markdown heading
        story_points = canonical_fields.get("story_points")
        if story_points is not None:
            body_sections.append(f"## Story Points\n\n{story_points}")

        # Add business value as markdown heading
        business_value = canonical_fields.get("business_value")
        if business_value is not None:
            body_sections.append(f"## Business Value\n\n{business_value}")

        # Add priority as markdown heading
        priority = canonical_fields.get("priority")
        if priority is not None:
            body_sections.append(f"## Priority\n\n{priority}")

        # Combine sections
        body = "\n\n".join(body_sections)

        return {"body": body}

    @beartype
    @require(lambda self, body: isinstance(body, str), "Body must be str")
    @require(lambda self, section_name: isinstance(section_name, str), "Section name must be str")
    @ensure(lambda result: result is None or isinstance(result, str), "Must return str or None")
    def _extract_section(self, body: str, section_name: str) -> str | None:
        """
        Extract content from a markdown section heading.

        Args:
            body: Markdown body content
            section_name: Section name to extract (e.g., "Acceptance Criteria")

        Returns:
            Section content or None if not found
        """
        # Pattern: ## Section Name or ### Section Name followed by content
        pattern = rf"^##+\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##|\Z)"
        match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    @beartype
    @require(lambda self, body: isinstance(body, str), "Body must be str")
    @ensure(lambda result: isinstance(result, str), "Must return str")
    def _extract_default_content(self, body: str) -> str:
        """
        Extract default content (body without structured sections).

        Args:
            body: Markdown body content

        Returns:
            Default content (body without ## headings)
        """
        # Remove all sections starting with ##
        # Use a more efficient pattern to avoid ReDoS: match lines starting with ##
        # and everything up to the next ## or end of string, using non-backtracking approach
        lines = body.split("\n")
        result_lines: list[str] = []
        skip_section = False

        for line in lines:
            # Check if this line starts a new section (## heading)
            if re.match(r"^##+", line):
                skip_section = True
            else:
                if not skip_section:
                    result_lines.append(line)

        return "\n".join(result_lines).strip()

    @beartype
    @require(lambda self, body: isinstance(body, str), "Body must be str")
    @require(lambda self, field_name: isinstance(field_name, str), "Field name must be str")
    @ensure(lambda result: result is None or isinstance(result, int), "Must return int or None")
    def _extract_numeric_field(self, body: str, field_name: str) -> int | None:
        """
        Extract numeric field from markdown body.

        Supports patterns:
        - ## Field Name\n\n<number>
        - **Field Name:** <number>

        Args:
            body: Markdown body content
            field_name: Field name to extract

        Returns:
            Numeric value or None if not found
        """
        # Pattern 1: ## Field Name\n\n<number>
        section_pattern = rf"^##+\s+{re.escape(field_name)}\s*$\n\s*(\d+)"
        match = re.search(section_pattern, body, re.MULTILINE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass

        # Pattern 2: **Field Name:** <number>
        inline_pattern = rf"\*\*{re.escape(field_name)}:\*\*\s*(\d+)"
        match = re.search(inline_pattern, body, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass

        return None

    @beartype
    @require(lambda self, label_names: isinstance(label_names, list), "Label names must be list")
    @require(lambda self, item_data: isinstance(item_data, dict), "Item data must be dict")
    @ensure(lambda result: result is None or isinstance(result, str), "Must return str or None")
    def _extract_work_item_type(self, label_names: list[str], item_data: dict[str, Any]) -> str | None:
        """
        Extract work item type from labels or issue metadata.

        Args:
            label_names: List of label names
            item_data: GitHub issue data

        Returns:
            Work item type or None if not found
        """
        # Common work item type labels
        work_item_types = ["Epic", "Feature", "User Story", "Story", "Task", "Bug", "Bugfix"]
        for label in label_names:
            if label in work_item_types:
                return label

        # Check issue type metadata if available
        issue_type = item_data.get("issue_type") or item_data.get("type")
        if issue_type:
            return str(issue_type)

        return None
