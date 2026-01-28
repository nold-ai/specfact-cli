"""
OpenSpec parser for adapter-specific OpenSpec format parsing.

This module provides parsing functionality for OpenSpec artifacts:
- project.md (project context, legacy)
- config.yaml (OPSX project context)
- spec.md (feature specifications)
- proposal.md (change proposals)
- spec.md with ADDED/MODIFIED/REMOVED markers (delta specs)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from beartype import beartype
from icontract import ensure, require


class OpenSpecParser:
    """
    Parser for OpenSpec format artifacts.

    This parser handles adapter-specific OpenSpec format parsing,
    converting markdown files into structured data for SpecFact integration.
    """

    @beartype
    @require(lambda path: isinstance(path, Path), "Path must be Path")
    @ensure(lambda result: result is None or isinstance(result, dict), "Must return dict or None")
    def parse_project_md(self, path: Path) -> dict[str, Any] | None:
        """
        Parse OpenSpec project.md file.

        Args:
            path: Path to openspec/project.md file

        Returns:
            Dictionary with parsed project context or None if file doesn't exist:
            - "purpose": Project purpose section (list)
            - "context": Project context section (list)
            - "tech_stack": Tech stack section
            - "conventions": Conventions section
            - "raw_content": Full markdown content
        """
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            parsed = self._parse_markdown_sections(content)
            parsed["raw_content"] = content
            return parsed
        except Exception:
            # Return None on parse error (consistent with missing file)
            return None

    @beartype
    @require(lambda path: isinstance(path, Path), "Path must be Path")
    @ensure(lambda result: result is None or isinstance(result, dict), "Must return dict or None")
    def parse_config_yaml(self, path: Path) -> dict[str, Any] | None:
        """
        Parse OpenSpec OPSX config.yaml (project context).

        Args:
            path: Path to openspec/config.yaml file

        Returns:
            Dictionary compatible with project context import:
            - "context": List of context string(s) from context: block
            - "purpose": Optional (empty list if not in YAML)
            - "raw_content": Full file content
        """
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            data = yaml.safe_load(content) or {}
            result: dict[str, Any] = {"purpose": [], "context": [], "raw_content": content}
            if isinstance(data.get("context"), str):
                result["context"] = [data["context"].strip()]
            elif isinstance(data.get("context"), list):
                result["context"] = [str(c).strip() for c in data["context"] if c]
            return result
        except Exception:
            return None

    @beartype
    @require(lambda path: isinstance(path, Path), "Path must be Path")
    @ensure(lambda result: result is None or isinstance(result, dict), "Must return dict or None")
    def parse_spec_md(self, path: Path) -> dict[str, Any] | None:
        """
        Parse OpenSpec spec.md file (feature specification).

        Args:
            path: Path to openspec/specs/{feature_id}/spec.md file

        Returns:
            Dictionary with parsed specification:
            - "requirements": List of requirements
            - "scenarios": List of scenarios
            - "raw_content": Full markdown content
        """
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            parsed = self._parse_spec_content(content)
            parsed["raw_content"] = content
            return parsed
        except Exception:
            # Return None on parse error (consistent with missing file)
            return None

    @beartype
    @require(lambda path: isinstance(path, Path), "Path must be Path")
    @ensure(lambda result: result is None or isinstance(result, dict), "Must return dict or None")
    def parse_change_proposal(self, path: Path) -> dict[str, Any] | None:
        """
        Parse OpenSpec change proposal.md file.

        Args:
            path: Path to openspec/changes/{change_name}/proposal.md file

        Returns:
            Dictionary with parsed proposal or None if file doesn't exist:
            - "summary": Summary section
            - "rationale": Rationale section
            - "why": Why section
            - "what_changes": What Changes section
            - "impact": Impact section
            - "raw_content": Full markdown content
        """
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            parsed = self._parse_proposal_content(content)
            parsed["raw_content"] = content
            return parsed
        except Exception:
            # Return None on parse error (consistent with missing file)
            return None

    @beartype
    @require(lambda path: isinstance(path, Path), "Path must be Path")
    @ensure(lambda result: result is None or isinstance(result, dict), "Must return dict or None")
    def parse_change_spec_delta(self, path: Path) -> dict[str, Any] | None:
        """
        Parse OpenSpec change spec delta (spec.md with ADDED/MODIFIED/REMOVED markers).

        Args:
            path: Path to openspec/changes/{change_name}/specs/{feature_id}/spec.md file

        Returns:
            Dictionary with parsed delta or None if file doesn't exist:
            - "type": "ADDED", "MODIFIED", or "REMOVED"
            - "feature_id": Feature ID
            - "content": Delta content
            - "raw_content": Full markdown content
        """
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            parsed = self._parse_delta_content(content)
            parsed["raw_content"] = content
            return parsed
        except Exception:
            # Return None on parse error (consistent with missing file)
            return None

    @beartype
    @require(lambda base_path: isinstance(base_path, Path), "Base path must be Path")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def list_active_changes(self, base_path: Path) -> list[str]:
        """
        List all active changes in openspec/changes/ directory.

        Args:
            base_path: Path to repository root or external base path

        Returns:
            List of change names (directory names in openspec/changes/)
        """
        changes_dir = base_path / "openspec" / "changes"

        if not changes_dir.exists():
            return []

        changes: list[str] = []
        for item in changes_dir.iterdir():
            if item.is_dir():
                # Check if it has a proposal.md file (active change)
                proposal_path = item / "proposal.md"
                if proposal_path.exists():
                    changes.append(item.name)

        return sorted(changes)

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be str")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _parse_markdown_sections(self, content: str) -> dict[str, Any]:
        """
        Parse markdown content into sections.

        Args:
            content: Markdown content

        Returns:
            Dictionary with section names as keys and content as values (lists for purpose/context)
        """
        sections: dict[str, Any] = {
            "purpose": [],
            "context": [],
            "tech_stack": "",
            "conventions": "",
        }

        current_section: str | None = None
        current_content: list[str] = []

        for line in content.splitlines():
            # Check for section headers (## or ###)
            if line.startswith("##"):
                # Save previous section
                if current_section:
                    section_key = current_section.lower()
                    if section_key in sections:
                        if section_key in ("purpose", "context"):
                            # Store as list for these sections (always a list)
                            content_text = "\n".join(current_content).strip()
                            if content_text:
                                sections[section_key] = [
                                    item.strip() for item in content_text.split("\n") if item.strip()
                                ]
                            else:
                                sections[section_key] = []
                        else:
                            sections[section_key] = "\n".join(current_content).strip()
                # Start new section
                current_section = line.lstrip("#").strip().lower()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        # Save last section
        if current_section:
            section_key = current_section.lower()
            if section_key in sections:
                if section_key in ("purpose", "context"):
                    # Store as list for these sections (always a list)
                    content_text = "\n".join(current_content).strip()
                    if content_text:
                        sections[section_key] = [item.strip() for item in content_text.split("\n") if item.strip()]
                    else:
                        sections[section_key] = []
                else:
                    sections[section_key] = "\n".join(current_content).strip()

        return sections

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be str")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _parse_spec_content(self, content: str) -> dict[str, Any]:
        """
        Parse spec.md content to extract overview, requirements and scenarios.

        Args:
            content: Spec markdown content

        Returns:
            Dictionary with "overview", "requirements" and "scenarios"
        """
        overview: str = ""
        requirements: list[str] = []
        scenarios: list[str] = []

        current_section: str | None = None
        current_items: list[str] = []
        current_text: list[str] = []

        for line in content.splitlines():
            # Check for section headers
            if line.startswith("##"):
                # Save previous section
                if current_section == "overview":
                    overview = "\n".join(current_text).strip()
                elif current_section == "requirements":
                    requirements = current_items
                elif current_section == "scenarios":
                    scenarios = current_items
                # Start new section
                current_section = line.lstrip("#").strip().lower()
                current_items = []
                current_text = []
            elif line.strip().startswith("-") or line.strip().startswith("*"):
                # List item
                item = line.strip().lstrip("-*").strip()
                if item:
                    current_items.append(item)
            elif current_section:
                if current_section == "overview":
                    current_text.append(line)
                elif current_section in ("requirements", "scenarios") and line.strip():
                    # Also handle text before list items
                    current_text.append(line)

        # Save last section
        if current_section == "overview":
            overview = "\n".join(current_text).strip()
        elif current_section == "requirements":
            requirements = current_items
        elif current_section == "scenarios":
            scenarios = current_items

        return {
            "overview": overview,
            "requirements": requirements,
            "scenarios": scenarios,
        }

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be str")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _parse_proposal_content(self, content: str) -> dict[str, str]:
        """
        Parse proposal.md content to extract Why, What Changes, Impact sections.

        Args:
            content: Proposal markdown content

        Returns:
            Dictionary with "why", "what_changes", "impact" sections
        """
        sections: dict[str, str] = {
            "summary": "",
            "rationale": "",
            "why": "",
            "what_changes": "",
            "impact": "",
        }

        current_section: str | None = None
        current_content: list[str] = []

        for line in content.splitlines():
            # Check for section headers
            if line.startswith("##"):
                # Save previous section
                if current_section:
                    section_key = self._normalize_section_name(current_section)
                    if section_key and section_key in sections:
                        sections[section_key] = "\n".join(current_content).strip()
                # Start new section
                current_section = line.lstrip("#").strip()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        # Save last section
        if current_section:
            section_key = self._normalize_section_name(current_section)
            if section_key and section_key in sections:
                sections[section_key] = "\n".join(current_content).strip()

        return sections

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be str")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _parse_delta_content(self, content: str) -> dict[str, Any]:
        """
        Parse delta spec content to extract ADDED/MODIFIED/REMOVED markers.

        Args:
            content: Delta spec markdown content

        Returns:
            Dictionary with "type", "feature_id", and "content"
        """
        change_type: str | None = None
        feature_id: str | None = None
        delta_content: list[str] = []

        current_section: str | None = None

        # Parse markdown sections
        for line in content.splitlines():
            if line.startswith("##"):
                # Section header - normalize section name
                current_section = line.lstrip("#").strip().lower()
            elif current_section:
                # Process content based on current section
                if current_section == "type":
                    # Extract type value (should be on the line after ## Type)
                    if line.strip():
                        change_type = line.strip().upper()
                elif current_section == "feature id" or current_section == "feature_id":
                    # Extract feature ID
                    if line.strip():
                        feature_id = line.strip()
                elif current_section == "content":
                    # Collect content
                    delta_content.append(line)

        return {
            "type": change_type,
            "feature_id": feature_id,
            "content": "\n".join(delta_content).strip(),
        }

    @beartype
    @require(lambda section_name: isinstance(section_name, str), "Section name must be str")
    @ensure(lambda result: isinstance(result, str), "Must return str")
    def _normalize_section_name(self, section_name: str) -> str:
        """
        Normalize section name to standard keys.

        Args:
            section_name: Section name from markdown

        Returns:
            Normalized section key
        """
        normalized = section_name.lower().strip()
        # Map common variations - exact matches first
        if normalized == "summary":
            return "summary"
        if normalized == "rationale":
            return "rationale"
        if normalized == "why":
            return "why"
        if normalized in ("what changes", "what_changes"):
            return "what_changes"
        if normalized == "impact":
            return "impact"
        # Try with underscores/spaces normalized
        normalized_alt = normalized.replace(" ", "_").replace("-", "_")
        if normalized_alt == "summary":
            return "summary"
        if normalized_alt == "rationale":
            return "rationale"
        if normalized_alt == "why":
            return "why"
        if normalized_alt == "what_changes":
            return "what_changes"
        if normalized_alt == "impact":
            return "impact"
        return normalized_alt
