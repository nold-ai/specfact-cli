"""
Spec-to-code sync - Prepare LLM prompts for code generation.

This module provides utilities for preparing LLM prompt context when
specifications change and code needs to be generated or updated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import Feature
from specfact_cli.sync.change_detector import SpecChange


@dataclass
class LLMPromptContext:
    """Context prepared for LLM code generation."""

    changes: list[SpecChange] = field(default_factory=list)
    existing_patterns: dict = field(default_factory=dict)  # Codebase style patterns
    dependencies: list[str] = field(default_factory=list)  # From requirements.txt
    style_guide: dict = field(default_factory=dict)  # Detected style patterns
    target_files: list[str] = field(default_factory=list)  # Files to generate/modify
    feature_specs: dict[str, Feature] = field(default_factory=dict)  # Feature specifications


class SpecToCodeSync:
    """Sync specification changes to code by preparing LLM prompts."""

    def __init__(self, repo_path: Path) -> None:
        """
        Initialize spec-to-code sync.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path.resolve()

    @beartype
    @require(lambda self, changes: isinstance(changes, list), "Changes must be list")
    @require(lambda self, changes: all(isinstance(c, SpecChange) for c in changes), "All items must be SpecChange")
    @require(lambda self, repo_path: isinstance(repo_path, Path), "Repository path must be Path")
    @ensure(lambda self, repo_path, result: isinstance(result, LLMPromptContext), "Must return LLMPromptContext")
    def prepare_llm_context(self, changes: list[SpecChange], repo_path: Path) -> LLMPromptContext:
        """
        Prepare context for LLM code generation.

        CLI orchestrates, LLM writes code.

        Args:
            changes: List of specification changes
            repo_path: Path to repository

        Returns:
            LLMPromptContext with all necessary information for LLM
        """
        from specfact_cli.utils.bundle_loader import load_project_bundle
        from specfact_cli.utils.structure import SpecFactStructure

        # Load project bundle to get feature specs
        bundle_name = self._detect_bundle_name(repo_path)
        if bundle_name:
            bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle_name)
            if bundle_dir.exists():
                project_bundle = load_project_bundle(bundle_dir)
                feature_specs = project_bundle.features
            else:
                feature_specs = {}
        else:
            feature_specs = {}

        # Analyze codebase patterns
        existing_patterns = self._analyze_codebase_patterns(repo_path)

        # Read dependencies
        dependencies = self._read_requirements(repo_path)

        # Detect style guide
        style_guide = self._detect_style_patterns(repo_path)

        # Determine target files
        target_files = self._determine_target_files(changes, feature_specs)

        return LLMPromptContext(
            changes=changes,
            existing_patterns=existing_patterns,
            dependencies=dependencies,
            style_guide=style_guide,
            target_files=target_files,
            feature_specs=feature_specs,
        )

    @beartype
    @require(lambda self, context: isinstance(context, LLMPromptContext), "Context must be LLMPromptContext")
    @ensure(lambda self, context, result: isinstance(result, str), "Must return string")
    def generate_llm_prompt(self, context: LLMPromptContext) -> str:
        """
        Generate LLM prompt for code generation.

        Args:
            context: LLM prompt context

        Returns:
            Formatted prompt string for LLM
        """
        prompt_parts = []

        # Header
        prompt_parts.append("# Code Generation Request")
        prompt_parts.append("")
        prompt_parts.append("## Specification Changes")
        prompt_parts.append("")

        for change in context.changes:
            prompt_parts.append(f"### Feature: {change.feature_key}")
            if change.contract_path:
                prompt_parts.append(f"- Contract changed: {change.contract_path}")
            if change.protocol_path:
                prompt_parts.append(f"- Protocol changed: {change.protocol_path}")
            prompt_parts.append("")

        # Feature specifications
        if context.feature_specs:
            prompt_parts.append("## Feature Specifications")
            prompt_parts.append("")
            for feature_key, feature in context.feature_specs.items():
                if any(c.feature_key == feature_key for c in context.changes):
                    prompt_parts.append(f"### {feature.title} ({feature_key})")
                    prompt_parts.append(f"**Outcomes:** {', '.join(feature.outcomes)}")
                    prompt_parts.append(f"**Constraints:** {', '.join(feature.constraints)}")
                    prompt_parts.append("**Stories:**")
                    for story in feature.stories:
                        prompt_parts.append(f"- {story.title}")
                        if story.acceptance:
                            prompt_parts.append(f"  - {story.acceptance[0]}")
                    prompt_parts.append("")

        # Existing patterns
        if context.existing_patterns:
            prompt_parts.append("## Existing Codebase Patterns")
            prompt_parts.append("")
            prompt_parts.append("```json")
            prompt_parts.append(json.dumps(context.existing_patterns, indent=2))
            prompt_parts.append("```")
            prompt_parts.append("")

        # Dependencies
        if context.dependencies:
            prompt_parts.append("## Dependencies")
            prompt_parts.append("")
            prompt_parts.append("```")
            for dep in context.dependencies:
                prompt_parts.append(dep)
            prompt_parts.append("```")
            prompt_parts.append("")

        # Style guide
        if context.style_guide:
            prompt_parts.append("## Style Guide")
            prompt_parts.append("")
            prompt_parts.append("```json")
            prompt_parts.append(json.dumps(context.style_guide, indent=2))
            prompt_parts.append("```")
            prompt_parts.append("")

        # Target files
        if context.target_files:
            prompt_parts.append("## Target Files")
            prompt_parts.append("")
            for target_file in context.target_files:
                prompt_parts.append(f"- {target_file}")
            prompt_parts.append("")

        # Instructions
        prompt_parts.append("## Instructions")
        prompt_parts.append("")
        prompt_parts.append("Generate or update the code files listed above based on the specification changes.")
        prompt_parts.append("Follow the existing codebase patterns and style guide.")
        prompt_parts.append("Ensure all contracts and protocols are properly implemented.")
        prompt_parts.append("")

        return "\n".join(prompt_parts)

    def _detect_bundle_name(self, repo_path: Path) -> str | None:
        """Detect bundle name from repository."""
        from specfact_cli.utils.structure import SpecFactStructure

        projects_dir = SpecFactStructure.projects_dir(base_path=repo_path)
        if projects_dir.exists():
            bundles = [d.name for d in projects_dir.iterdir() if d.is_dir()]
            if bundles:
                return bundles[0]  # Return first bundle found
        return None

    def _analyze_codebase_patterns(self, repo_path: Path) -> dict:
        """Analyze codebase to extract patterns."""
        # Simple pattern detection - can be enhanced
        return {
            "import_style": "absolute",  # Could detect relative vs absolute
            "naming_convention": "snake_case",  # Could detect from existing code
            "docstring_style": "google",  # Could detect from existing docstrings
        }

    def _read_requirements(self, repo_path: Path) -> list[str]:
        """Read dependencies from requirements.txt or pyproject.toml."""
        dependencies: list[str] = []

        # Try requirements.txt
        requirements_file = repo_path / "requirements.txt"
        if requirements_file.exists():
            with requirements_file.open(encoding="utf-8") as f:
                dependencies.extend(line.strip() for line in f if line.strip() and not line.startswith("#"))

        # Try pyproject.toml
        pyproject_file = repo_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import tomli

                with pyproject_file.open("rb") as f:
                    data = tomli.load(f)
                    if "project" in data and "dependencies" in data["project"]:
                        dependencies.extend(data["project"]["dependencies"])
            except Exception:
                pass  # Ignore parsing errors

        return dependencies

    def _detect_style_patterns(self, repo_path: Path) -> dict:
        """Detect code style patterns from existing code."""
        # Simple style detection - can be enhanced
        return {
            "line_length": 120,  # Could detect from existing code
            "indentation": 4,  # Could detect from existing code
            "quote_style": "double",  # Could detect from existing code
        }

    def _determine_target_files(self, changes: list[SpecChange], features: dict[str, Feature]) -> list[str]:
        """Determine which files need to be generated or modified."""
        target_files: list[str] = []

        for change in changes:
            feature = features.get(change.feature_key)
            if feature and feature.source_tracking:
                # Use existing implementation files if available
                target_files.extend(feature.source_tracking.implementation_files)
            else:
                # Generate new file path based on feature key
                feature_name = change.feature_key.lower().replace("feature-", "").replace("-", "_")
                target_files.append(f"src/{feature_name}.py")

        return list(set(target_files))  # Remove duplicates
