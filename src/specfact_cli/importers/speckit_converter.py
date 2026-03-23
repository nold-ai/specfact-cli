"""
Spec-Kit to SpecFact converter.

This module converts Spec-Kit markdown artifacts (spec.md, plan.md, tasks.md, constitution.md)
to SpecFact format (plans, protocols).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel

from specfact_cli import runtime
from specfact_cli.analyzers.constitution_evidence_extractor import ConstitutionEvidenceExtractor
from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.generators.protocol_generator import ProtocolGenerator
from specfact_cli.generators.workflow_generator import WorkflowGenerator
from specfact_cli.importers.speckit_scanner import SpecKitScanner
from specfact_cli.migrations.plan_migrator import get_current_schema_version
from specfact_cli.models.plan import Feature, Idea, PlanBundle, Product, Release, Story
from specfact_cli.models.protocol import Protocol
from specfact_cli.utils.icontract_helpers import ensure_path_exists_yaml_suffix
from specfact_cli.utils.structure import SpecFactStructure


def _protocol_has_min_states(result: Protocol) -> bool:
    return len(result.states) >= 2


def _plan_bundle_matches_schema_version(result: PlanBundle) -> bool:
    return result.version == get_current_schema_version()


def _require_python_3_prefix(python_version: str) -> bool:
    return python_version.startswith("3.")


class SpecKitConverter:
    """
    Converter from Spec-Kit format to SpecFact format.

    Converts markdown artifacts (spec.md, plan.md, tasks.md, constitution.md) → plan bundles.
    """

    @beartype
    def __init__(self, repo_path: Path, mapping_file: Path | None = None) -> None:
        """
        Initialize Spec-Kit converter.

        Args:
            repo_path: Path to Spec-Kit repository
            mapping_file: Optional custom mapping file (default: built-in)
        """
        self.repo_path = Path(repo_path)
        self.scanner = SpecKitScanner(repo_path)
        self.protocol_generator = ProtocolGenerator()
        self.plan_generator = PlanGenerator()
        self.workflow_generator = WorkflowGenerator()
        self.constitution_extractor = ConstitutionEvidenceExtractor(repo_path)
        self.mapping_file = mapping_file

    @beartype
    @ensure(lambda result: isinstance(result, Protocol), "Must return Protocol")
    @ensure(_protocol_has_min_states, "Must have at least INIT and COMPLETE states")
    def convert_protocol(self, output_path: Path | None = None) -> Protocol:
        """
        Convert Spec-Kit features to SpecFact protocol.

        Creates a minimal protocol from feature states.
        Since Spec-Kit markdown artifacts don't explicitly define FSM protocols,
        this generates a simple protocol based on feature workflow.

        Args:
            output_path: Optional path to write protocol.yaml (default: .specfact/protocols/workflow.protocol.yaml)

        Returns:
            Generated Protocol model
        """
        # For markdown-based Spec-Kit, create a minimal protocol
        # States based on feature workflow: INIT -> FEATURE_1 -> ... -> COMPLETE
        features = self.scanner.discover_features()

        if not features:
            # Default minimal protocol if no features found
            states = ["INIT", "COMPLETE"]
        else:
            states = ["INIT"]
            for feature in features:
                fd: dict[str, Any] = feature
                feature_key = fd.get("feature_key", "UNKNOWN")
                states.append(str(feature_key))
            states.append("COMPLETE")

        protocol = Protocol(
            states=states,
            start="INIT",
            transitions=[],
            guards={},
        )

        # Write to file if output path provided
        if output_path:
            SpecFactStructure.ensure_structure(output_path.parent)
            # Only suppress FileExistsError if file already exists (idempotent)
            if output_path.exists():
                return protocol
            self.protocol_generator.generate(protocol, output_path)
        else:
            # Use default path - construct .specfact/protocols/workflow.protocol.yaml
            output_path = self.repo_path / ".specfact" / "protocols" / "workflow.protocol.yaml"
            SpecFactStructure.ensure_structure(self.repo_path)
            # Only suppress FileExistsError if file already exists (idempotent)
            if output_path.exists():
                return protocol
            self.protocol_generator.generate(protocol, output_path)

        return protocol

    def _constraints_from_memory_structure(self) -> list[str]:
        structure: dict[str, Any] = self.scanner.scan_structure()
        mem_raw = structure.get("specify_memory_dir")
        memory_dir = Path(str(mem_raw)) if mem_raw else None
        if not memory_dir or not Path(memory_dir).exists():
            return []
        memory_data = self.scanner.parse_memory_files(Path(memory_dir))
        return memory_data.get("constraints", [])

    def _write_plan_bundle_to_path(self, plan_bundle: PlanBundle, output_path: Path | None) -> None:
        if output_path:
            if output_path.is_dir():
                resolved = output_path / SpecFactStructure.ensure_plan_filename(output_path.name)
            else:
                resolved = output_path.with_name(SpecFactStructure.ensure_plan_filename(output_path.name))
            SpecFactStructure.ensure_structure(resolved.parent)
            self.plan_generator.generate(plan_bundle, resolved)
            return
        resolved = SpecFactStructure.get_default_plan_path(
            base_path=self.repo_path, preferred_format=runtime.get_output_format()
        )
        if resolved.parent.name == "projects":
            return
        if resolved.exists() and resolved.is_dir():
            plan_filename = SpecFactStructure.ensure_plan_filename(resolved.name)
            resolved = resolved / plan_filename
        elif not resolved.exists():
            resolved = resolved.with_name(SpecFactStructure.ensure_plan_filename(resolved.name))
        SpecFactStructure.ensure_structure(resolved.parent)
        self.plan_generator.generate(plan_bundle, resolved)

    @beartype
    @ensure(lambda result: isinstance(result, PlanBundle), "Must return PlanBundle")
    @ensure(
        _plan_bundle_matches_schema_version,
        "Must have current schema version",
    )
    def convert_plan(self, output_path: Path | None = None) -> PlanBundle:
        """
        Convert Spec-Kit markdown artifacts to SpecFact plan bundle.

        Args:
            output_path: Optional path to write plan bundle (default: .specfact/plans/main.bundle.<format>)

        Returns:
            Generated PlanBundle model
        """
        discovered_features = self.scanner.discover_features()
        features = self._extract_features_from_markdown(discovered_features) if discovered_features else []
        constraints = self._constraints_from_memory_structure()
        repo_name = self.repo_path.name or "Imported Project"
        idea = Idea(
            title=self._humanize_name(repo_name),
            narrative=f"Imported from Spec-Kit project: {repo_name}",
            target_users=[],
            value_hypothesis="",
            constraints=constraints,
            metrics=None,
        )
        themes = self._extract_themes_from_features(features)
        product = Product(
            themes=themes,
            releases=[
                Release(
                    name="v0.1",
                    objectives=["Migrate from Spec-Kit"],
                    scope=[f.key for f in features],
                    risks=[],
                )
            ],
        )
        plan_bundle = PlanBundle(
            version=get_current_schema_version(),
            idea=idea,
            business=None,
            product=product,
            features=features,
            metadata=None,
            clarifications=None,
        )
        self._write_plan_bundle_to_path(plan_bundle, output_path)
        return plan_bundle

    @staticmethod
    def _text_items_from_dict_or_str_list(items: list[Any]) -> list[str]:
        result: list[str] = []
        for item in items:
            if isinstance(item, dict):
                rd: dict[str, Any] = item
                result.append(str(rd.get("text", "")))
            elif isinstance(item, str):
                result.append(item)
        return result

    def _confidence_for_feature(self, feature_title: str, stories: list[Story], outcomes: list[str]) -> float:
        confidence = 0.5
        if feature_title and feature_title != "Unknown Feature":
            confidence += 0.2
        if stories:
            confidence += 0.2
        if outcomes:
            confidence += 0.1
        return min(confidence, 1.0)

    def _feature_from_discovered_data(self, feature_data: dict[str, Any]) -> Feature:
        feature_key = feature_data.get("feature_key", "UNKNOWN")
        feature_title = feature_data.get("feature_title", "Unknown Feature")
        stories = self._extract_stories_from_spec(feature_data)
        outcomes = self._text_items_from_dict_or_str_list(feature_data.get("requirements", []))
        acceptance = self._text_items_from_dict_or_str_list(feature_data.get("success_criteria", []))
        confidence = self._confidence_for_feature(feature_title, stories, outcomes)
        return Feature(
            key=feature_key,
            title=feature_title,
            outcomes=outcomes if outcomes else [f"Provides {feature_title} functionality"],
            acceptance=acceptance if acceptance else [f"{feature_title} is functional"],
            constraints=feature_data.get("edge_cases", []),
            stories=stories,
            confidence=confidence,
            draft=False,
            source_tracking=None,
            contract=None,
            protocol=None,
        )

    @beartype
    @require(lambda discovered_features: isinstance(discovered_features, list), "Must be list")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    @ensure(lambda result: all(isinstance(f, Feature) for f in result), "All items must be Features")
    def _extract_features_from_markdown(self, discovered_features: list[dict[str, Any]]) -> list[Feature]:
        """Extract features from Spec-Kit markdown artifacts."""
        return [self._feature_from_discovered_data(fd) for fd in discovered_features]

    def _story_tasks_from_feature_data(self, feature_data: dict[str, Any], story_key: str) -> list[str]:
        tasks: list[str] = []
        tasks_data = feature_data.get("tasks", {})
        if not tasks_data or "tasks" not in tasks_data:
            return tasks
        for task in tasks_data["tasks"]:
            if not isinstance(task, dict):
                continue
            td: dict[str, Any] = task
            story_ref = str(td.get("story_ref", ""))
            if (story_ref and story_ref in story_key) or not story_ref:
                tasks.append(str(td.get("description", "")))
        return tasks

    @staticmethod
    def _normalize_story_scenarios(scenarios: Any) -> dict[str, list[str]] | None:
        if not scenarios or not isinstance(scenarios, dict):
            return None
        filtered = {k: v for k, v in scenarios.items() if v and isinstance(v, list) and len(v) > 0}
        return filtered if filtered else None

    def _story_from_spec_entry(self, feature_data: dict[str, Any], story_data: dict[str, Any]) -> Story:
        story_key = story_data.get("key", "UNKNOWN")
        story_title = story_data.get("title", "Unknown Story")
        priority = story_data.get("priority", "P3")
        priority_map = {"P1": 8, "P2": 5, "P3": 3, "P4": 1}
        story_points = priority_map.get(str(priority), 3)
        acceptance = story_data.get("acceptance", [])
        tasks = self._story_tasks_from_feature_data(feature_data, story_key)
        scenarios = self._normalize_story_scenarios(story_data.get("scenarios"))
        return Story(
            key=story_key,
            title=story_title,
            acceptance=acceptance if acceptance else [f"{story_title} is implemented"],
            tags=[priority],
            story_points=story_points,
            value_points=story_points,
            tasks=tasks,
            confidence=0.8,
            draft=False,
            scenarios=scenarios,
            contracts=None,
        )

    @beartype
    @require(lambda feature_data: isinstance(feature_data, dict), "Must be dict")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    @ensure(lambda result: all(isinstance(s, Story) for s in result), "All items must be Stories")
    def _extract_stories_from_spec(self, feature_data: dict[str, Any]) -> list[Story]:
        """Extract user stories from Spec-Kit spec.md data."""
        spec_stories = feature_data.get("stories", [])
        return [self._story_from_spec_entry(feature_data, sd) for sd in spec_stories]

    @beartype
    @require(lambda features: isinstance(features, list), "Must be list")
    @require(lambda features: all(isinstance(f, Feature) for f in features), "All items must be Features")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    @ensure(lambda result: all(isinstance(t, str) for t in result), "All items must be strings")
    @ensure(lambda result: len(result) > 0, "Must have at least one theme")
    def _extract_themes_from_features(self, features: list[Feature]) -> list[str]:
        """Extract themes from feature titles."""
        themes: set[str] = set()
        themes.add("Core")

        for feature in features:
            # Extract theme from feature title (first word or key pattern)
            title = feature.title
            if title:
                # Try to extract meaningful theme from title
                words = title.split()
                if words:
                    # Use first significant word as theme
                    theme = words[0]
                    if len(theme) > 2:
                        themes.add(theme)

        return sorted(themes)

    @beartype
    @ensure(lambda result: ensure_path_exists_yaml_suffix(result), "Output path must exist and be YAML")
    def generate_semgrep_rules(self, output_path: Path | None = None) -> Path:
        """
        Generate Semgrep async rules for the repository.

        Args:
            output_path: Optional path to write Semgrep rules (default: .semgrep/async-anti-patterns.yml)

        Returns:
            Path to generated Semgrep rules file
        """
        if output_path is None:
            # Use default path
            output_path = self.repo_path / ".semgrep" / "async-anti-patterns.yml"

        self.workflow_generator.generate_semgrep_rules(output_path)
        return output_path

    @beartype
    @require(lambda budget: budget > 0, "Budget must be positive")
    @require(_require_python_3_prefix, "Python version must be 3.x")
    @ensure(lambda result: ensure_path_exists_yaml_suffix(result), "Output path must exist and be YAML")
    def generate_github_action(
        self,
        output_path: Path | None = None,
        repo_name: str | None = None,
        budget: int = 90,
        python_version: str = "3.12",
    ) -> Path:
        """
        Generate GitHub Action workflow for SpecFact validation.

        Args:
            output_path: Optional path to write workflow (default: .github/workflows/specfact-gate.yml)
            repo_name: Repository name for context
            budget: Time budget in seconds for validation (must be > 0)
            python_version: Python version for workflow (must be 3.x)

        Returns:
            Path to generated GitHub Action workflow file
        """
        if output_path is None:
            # Use default path
            output_path = self.repo_path / ".github" / "workflows" / "specfact-gate.yml"

        if repo_name is None:
            repo_name = self.repo_path.name or "specfact-project"

        self.workflow_generator.generate_github_action(output_path, repo_name, budget, python_version)
        return output_path

    @beartype
    @ensure(lambda result: isinstance(result, int), "Must return int (number of features converted)")
    @ensure(lambda result: result >= 0, "Result must be non-negative")
    def convert_to_speckit(
        self,
        plan_bundle: PlanBundle | BaseModel | dict[str, Any],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> int:
        """
        Convert SpecFact plan bundle to Spec-Kit markdown artifacts.

        Generates spec.md, plan.md, and tasks.md files for each feature in the plan bundle.

        Args:
            plan_bundle: SpecFact plan bundle to convert
            progress_callback: Optional callback function(current, total) to report progress

        Returns:
            Number of features converted
        """
        if isinstance(plan_bundle, PlanBundle):
            normalized_bundle = plan_bundle
        elif isinstance(plan_bundle, BaseModel):
            normalized_bundle = PlanBundle.model_validate(plan_bundle.model_dump(mode="python"))
        else:
            normalized_bundle = PlanBundle.model_validate(plan_bundle)

        features_converted = 0
        total_features = len(normalized_bundle.features)
        # Track used feature numbers to avoid duplicates
        used_feature_nums: set[int] = set()

        for idx, feature in enumerate(normalized_bundle.features, start=1):
            # Report progress if callback provided
            if progress_callback:
                progress_callback(idx, total_features)
            # Generate feature directory name from key (FEATURE-001 -> 001-feature-name)
            # Use number from key if available and not already used, otherwise use sequential index
            extracted_num = self._extract_feature_number(feature.key)
            if extracted_num == 0 or extracted_num in used_feature_nums:
                # No number found in key, or number already used - use sequential numbering
                # Find next available sequential number starting from idx
                feature_num = idx
                while feature_num in used_feature_nums:
                    feature_num += 1
            else:
                feature_num = extracted_num
            used_feature_nums.add(feature_num)
            feature_name = self._to_feature_dir_name(feature.title)

            # Create feature directory
            feature_dir = self.repo_path / "specs" / f"{feature_num:03d}-{feature_name}"
            feature_dir.mkdir(parents=True, exist_ok=True)

            # Generate spec.md (pass calculated feature_num to avoid recalculation)
            spec_content = self._generate_spec_markdown(feature, feature_num=feature_num)
            (feature_dir / "spec.md").write_text(spec_content, encoding="utf-8")

            # Generate plan.md
            plan_content = self._generate_plan_markdown(feature, normalized_bundle)
            (feature_dir / "plan.md").write_text(plan_content, encoding="utf-8")

            # Generate tasks.md
            tasks_content = self._generate_tasks_markdown(feature)
            (feature_dir / "tasks.md").write_text(tasks_content, encoding="utf-8")

            features_converted += 1

        return features_converted

    @staticmethod
    def _gwt_explicit_from_text(acc: str) -> tuple[str, str, str] | None:
        if "Given" not in acc or "When" not in acc or "Then" not in acc:
            return None
        gwt_pattern = r"Given\s+(.+?),\s*When\s+(.+?),\s*Then\s+(.+?)(?:$|,)"
        m = re.search(gwt_pattern, acc, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        parts = acc.split(", ")
        given = parts[0].replace("Given ", "").strip() if len(parts) > 0 else ""
        when = parts[1].replace("When ", "").strip() if len(parts) > 1 else ""
        then = parts[2].replace("Then ", "").strip() if len(parts) > 2 else ""
        return given, when, then

    @staticmethod
    def _gwt_heuristic_from_modal_verbs(acc: str) -> tuple[str, str, str]:
        acc_lower = acc.lower()
        if "must" not in acc_lower and "should" not in acc_lower and "will" not in acc_lower:
            return "", "", ""
        if "verify" in acc_lower or "validate" in acc_lower:
            action = (
                acc.replace("Must verify", "")
                .replace("Must validate", "")
                .replace("Should verify", "")
                .replace("Should validate", "")
                .strip()
            )
            return "user performs action", f"system {action}", f"{action} succeeds"
        if "handle" in acc_lower or "display" in acc_lower:
            action = (
                acc.replace("Must handle", "")
                .replace("Must display", "")
                .replace("Should handle", "")
                .replace("Should display", "")
                .strip()
            )
            return "error condition occurs", "system processes error", f"system {action}"
        return (
            "user interacts with system",
            "action is performed",
            acc.replace("Must", "").replace("Should", "").replace("Will", "").strip(),
        )

    def _gwt_from_acceptance(self, acc: str) -> tuple[str, str, str]:
        """
        Parse or synthesise Given/When/Then components from an acceptance criterion string.

        Args:
            acc: Acceptance criterion text

        Returns:
            Tuple of (given, when, then) strings
        """
        explicit = self._gwt_explicit_from_text(acc)
        if explicit is not None:
            return explicit
        return self._gwt_heuristic_from_modal_verbs(acc)

    def _categorise_scenario(
        self,
        scenario_text: str,
        acc_lower: str,
        primaries: list[str],
        alternates: list[str],
        exceptions: list[str],
        recoveries: list[str],
    ) -> None:
        """
        Append a scenario text to the correct category bucket in-place.

        Args:
            scenario_text: Scenario text to categorise
            acc_lower: Lower-cased acceptance criterion for keyword matching
            primaries: Primary scenario bucket
            alternates: Alternate scenario bucket
            exceptions: Exception scenario bucket
            recoveries: Recovery scenario bucket
        """
        if any(kw in acc_lower for kw in ["error", "exception", "fail", "invalid", "reject", "handle error"]):
            exceptions.append(scenario_text)
        elif any(kw in acc_lower for kw in ["recover", "retry", "fallback"]):
            recoveries.append(scenario_text)
        elif any(kw in acc_lower for kw in ["alternate", "alternative", "different", "optional"]):
            alternates.append(scenario_text)
        else:
            primaries.append(scenario_text)

    def _priority_rationale_for_story(self, story: Any, feature_outcomes: list[str]) -> str:
        priority_rationale = "Core functionality"
        if story.tags:
            for tag in story.tags:
                if tag.startswith(("priority:", "rationale:")):
                    priority_rationale = tag.split(":", 1)[1].strip()
                    break
        if priority_rationale != "Core functionality" or not feature_outcomes:
            return priority_rationale
        first = feature_outcomes[0]
        return first if len(first) < 100 else "Core functionality"

    @staticmethod
    def _append_labeled_scenario_rows(lines: list[str], items: list[str], label: str, *, empty_fallback: str) -> None:
        for s in items:
            lines.append(f"- **{label}**: {s}")
        if not items:
            lines.append(f"- **{label}**: {empty_fallback}")

    @staticmethod
    def _append_bucketed_scenario_lines(
        lines: list[str],
        primaries: list[str],
        alternates: list[str],
        exceptions: list[str],
        recoveries: list[str],
    ) -> None:
        if not (primaries or alternates or exceptions or recoveries):
            return
        lines += ["**Scenarios:**", ""]
        SpecKitConverter._append_labeled_scenario_rows(
            lines, primaries, "Primary Scenario", empty_fallback="Standard user flow"
        )
        SpecKitConverter._append_labeled_scenario_rows(
            lines, alternates, "Alternate Scenario", empty_fallback="Alternative user flow"
        )
        SpecKitConverter._append_labeled_scenario_rows(
            lines, exceptions, "Exception Scenario", empty_fallback="Error handling"
        )
        SpecKitConverter._append_labeled_scenario_rows(
            lines, recoveries, "Recovery Scenario", empty_fallback="Recovery from errors"
        )
        lines.append("")

    def _append_acceptance_lines_for_story(
        self,
        story: Any,
        lines: list[str],
        primaries: list[str],
        alternates: list[str],
        exceptions: list[str],
        recoveries: list[str],
    ) -> None:
        for acc_idx, acc in enumerate(story.acceptance, start=1):
            given, when, then = self._gwt_from_acceptance(acc)
            acc_lower = acc.lower()
            if given or when or then:
                lines.append(f"{acc_idx}. **Given** {given}, **When** {when}, **Then** {then}")
                self._categorise_scenario(
                    f"{given}, {when}, {then}", acc_lower, primaries, alternates, exceptions, recoveries
                )
            else:
                lines.append(f"{acc_idx}. {acc}")
                self._categorise_scenario(acc, acc_lower, primaries, alternates, exceptions, recoveries)

    def _render_story_acceptance(self, story: Any, feature_outcomes: list[str], lines: list[str]) -> None:
        """
        Render the acceptance criteria and scenario sections for a single story.

        Appends lines to `lines` in-place.

        Args:
            story: Story model instance
            feature_outcomes: Parent feature outcomes (used as fallback for priority rationale)
            lines: Line buffer to append to
        """
        priority_rationale = self._priority_rationale_for_story(story, feature_outcomes)
        lines += [
            f"Users can {story.title}",
            "",
            f"**Why this priority**: {priority_rationale}",
            "",
            "**Independent**: YES",
            "**Negotiable**: YES",
            "**Valuable**: YES",
            "**Estimable**: YES",
            "**Small**: YES",
            "**Testable**: YES",
            "",
            "**Acceptance Criteria:**",
            "",
        ]
        primaries: list[str] = []
        alternates: list[str] = []
        exceptions: list[str] = []
        recoveries: list[str] = []
        self._append_acceptance_lines_for_story(story, lines, primaries, alternates, exceptions, recoveries)
        lines.append("")
        self._append_bucketed_scenario_lines(lines, primaries, alternates, exceptions, recoveries)
        lines.append("")

    def _append_spec_user_stories_section(self, feature: Feature, lines: list[str]) -> None:
        if not feature.stories:
            return
        lines += ["## User Scenarios & Testing", ""]
        for idx, story in enumerate(feature.stories, start=1):
            priority = self._priority_from_story_tags(story)
            lines.append(f"### User Story {idx} - {story.title} (Priority: {priority})")
            self._render_story_acceptance(story, feature.outcomes, lines)

    @staticmethod
    def _append_spec_functional_requirements(feature: Feature, lines: list[str]) -> None:
        if not feature.outcomes:
            return
        lines += ["## Functional Requirements", ""]
        for idx, outcome in enumerate(feature.outcomes, start=1):
            lines.append(f"**FR-{idx:03d}**: System MUST {outcome}")
        lines.append("")

    @staticmethod
    def _append_spec_success_criteria(feature: Feature, lines: list[str]) -> None:
        if not feature.acceptance:
            return
        lines += ["## Success Criteria", ""]
        for idx, acc in enumerate(feature.acceptance, start=1):
            lines.append(f"**SC-{idx:03d}**: {acc}")
        lines.append("")

    @staticmethod
    def _append_spec_edge_cases(feature: Feature, lines: list[str]) -> None:
        if not feature.constraints:
            return
        lines += ["### Edge Cases", ""]
        for constraint in feature.constraints:
            lines.append(f"- {constraint}")
        lines.append("")

    @beartype
    @require(lambda feature: isinstance(feature, Feature), "Must be Feature instance")
    @require(
        lambda feature_num: feature_num is None or feature_num > 0,
        "Feature number must be None or positive",
    )
    @ensure(lambda result: isinstance(result, str), "Must return string")
    @ensure(lambda result: len(result) > 0, "Result must be non-empty")
    def _generate_spec_markdown(self, feature: Feature, feature_num: int | None = None) -> str:
        """
        Generate Spec-Kit spec.md content from SpecFact feature.

        Args:
            feature: Feature to generate spec for
            feature_num: Optional pre-calculated feature number (avoids recalculation with fallback)
        """
        from datetime import datetime

        if feature_num is None:
            feature_num = self._extract_feature_number(feature.key)
            if feature_num == 0:
                feature_num = 1
        feature_branch = f"{feature_num:03d}-{self._to_feature_dir_name(feature.title)}"

        lines: list[str] = [
            "---",
            f"**Feature Branch**: `{feature_branch}`",
            f"**Created**: {datetime.now().strftime('%Y-%m-%d')}",
            "**Status**: Draft",
            "---",
            "",
            f"# Feature Specification: {feature.title}",
            "",
        ]

        self._append_spec_user_stories_section(feature, lines)
        self._append_spec_functional_requirements(feature, lines)
        self._append_spec_success_criteria(feature, lines)
        self._append_spec_edge_cases(feature, lines)

        return "\n".join(lines)

    @staticmethod
    def _dependency_bullet_for_stack_item(dep: str) -> str | None:
        dep_lower = dep.lower()
        if "fastapi" in dep_lower:
            return "- `fastapi` - Web framework"
        if "django" in dep_lower:
            return "- `django` - Web framework"
        if "flask" in dep_lower:
            return "- `flask` - Web framework"
        if "typer" in dep_lower:
            return "- `typer` - CLI framework"
        if "pydantic" in dep_lower:
            return "- `pydantic` - Data validation"
        if "sqlalchemy" in dep_lower:
            return "- `sqlalchemy` - ORM"
        return f"- {dep}"

    def _append_plan_dependencies_block(self, lines: list[str], technology_stack: list[str]) -> None:
        fw_markers = ("typer", "fastapi", "django", "flask", "pydantic", "sqlalchemy")
        dependencies = [s for s in technology_stack if any(fw in s.lower() for fw in fw_markers)]
        lines.append("**Primary Dependencies:**")
        lines.append("")
        if not dependencies:
            lines.append("- `typer` - CLI framework")
            lines.append("- `pydantic` - Data validation")
            lines.append("")
            return
        for dep in dependencies[:5]:
            bullet = self._dependency_bullet_for_stack_item(dep)
            if bullet:
                lines.append(bullet)
        lines.append("")

    def _append_constitution_fallback_block(self, lines: list[str], contracts_defined: bool) -> None:
        lines.append("## Constitution Check")
        lines.append("")
        lines.append("**Article VII (Simplicity)**:")
        lines.append("- [ ] Evidence extraction pending")
        lines.append("")
        lines.append("**Article VIII (Anti-Abstraction)**:")
        lines.append("- [ ] Evidence extraction pending")
        lines.append("")
        lines.append("**Article IX (Integration-First)**:")
        lines.append("- [x] Contracts defined?" if contracts_defined else "- [ ] Contracts defined?")
        lines.append("- [ ] Contract tests written?")
        lines.append("")
        lines.append("**Status**: PENDING")
        lines.append("")

    @staticmethod
    def _append_contract_parameters_section(lines: list[str], contracts: dict[str, Any]) -> None:
        if not contracts.get("parameters"):
            return
        lines.append("**Parameters:**")
        for param in contracts["parameters"]:
            param_type = param.get("type", "Any")
            required = "required" if param.get("required", True) else "optional"
            default = f" (default: {param.get('default')})" if param.get("default") is not None else ""
            lines.append(f"- `{param['name']}`: {param_type} ({required}){default}")
        lines.append("")

    @staticmethod
    def _append_contract_return_type_section(lines: list[str], contracts: dict[str, Any]) -> None:
        if not contracts.get("return_type"):
            return
        return_type = contracts["return_type"].get("type", "Any")
        lines.append(f"**Return Type**: `{return_type}`")
        lines.append("")

    @staticmethod
    def _append_contract_bulleted_section(lines: list[str], contracts: dict[str, Any], key: str, title: str) -> None:
        if not contracts.get(key):
            return
        lines.append(f"**{title}:**")
        for item in contracts[key]:
            lines.append(f"- {item}")
        lines.append("")

    @staticmethod
    def _append_contract_error_contracts_section(lines: list[str], contracts: dict[str, Any]) -> None:
        if not contracts.get("error_contracts"):
            return
        lines.append("**Error Contracts:**")
        for error_contract in contracts["error_contracts"]:
            exc_type = error_contract.get("exception_type", "Exception")
            condition = error_contract.get("condition", "Error condition")
            lines.append(f"- `{exc_type}`: {condition}")
        lines.append("")

    def _append_contract_story_block(self, lines: list[str], story: Story) -> None:
        if not story.contracts:
            return
        lines.append(f"#### {story.title}")
        lines.append("")
        contracts = story.contracts
        self._append_contract_parameters_section(lines, contracts)
        self._append_contract_return_type_section(lines, contracts)
        self._append_contract_bulleted_section(lines, contracts, "preconditions", "Preconditions")
        self._append_contract_bulleted_section(lines, contracts, "postconditions", "Postconditions")
        self._append_contract_error_contracts_section(lines, contracts)

    def _append_contract_definitions_for_feature(self, lines: list[str], feature: Feature) -> None:
        lines.append("### Contract Definitions")
        lines.append("")
        for story in feature.stories:
            self._append_contract_story_block(lines, story)
        lines.append("")

    def _append_plan_phases_footer(self, lines: list[str], feature: Feature) -> None:
        lines.append("## Phase 0: Research")
        lines.append("")
        lines.append(f"Research and technical decisions for {feature.title}.")
        lines.append("")
        lines.append("## Phase 1: Design")
        lines.append("")
        lines.append(f"Design phase for {feature.title}.")
        lines.append("")
        lines.append("## Phase 2: Implementation")
        lines.append("")
        lines.append(f"Implementation phase for {feature.title}.")
        lines.append("")
        lines.append("## Phase -1: Pre-Implementation Gates")
        lines.append("")
        lines.append("Pre-implementation gate checks:")
        lines.append("- [ ] Constitution check passed")
        lines.append("- [ ] Contracts defined")
        lines.append("- [ ] Technical context validated")
        lines.append("")

    @beartype
    @require(
        lambda feature, plan_bundle: isinstance(feature, Feature) and isinstance(plan_bundle, PlanBundle),
        "Must be Feature and PlanBundle instances",
    )
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _generate_plan_markdown(self, feature: Feature, plan_bundle: PlanBundle) -> str:
        """Generate Spec-Kit plan.md content from SpecFact feature."""
        lines = [
            f"# Implementation Plan: {feature.title}",
            "",
            "## Summary",
            f"Implementation plan for {feature.title}.",
            "",
            "## Technical Context",
            "",
        ]
        technology_stack = self._extract_technology_stack(feature, plan_bundle)
        language_version = next((s for s in technology_stack if "Python" in s), "Python 3.11+")
        lines.append(f"**Language/Version**: {language_version}")
        lines.append("")
        self._append_plan_dependencies_block(lines, technology_stack)
        lines.append("**Technology Stack:**")
        lines.append("")
        for stack_item in technology_stack:
            lines.append(f"- {stack_item}")
        lines.append("")
        lines.append("**Constraints:**")
        lines.append("")
        if feature.constraints:
            for constraint in feature.constraints:
                lines.append(f"- {constraint}")
        else:
            lines.append("- None specified")
        lines.append("")
        lines.append("**Unknowns:**")
        lines.append("")
        lines.append("- None at this time")
        lines.append("")
        contracts_defined = any(story.contracts for story in feature.stories if story.contracts)
        try:
            constitution_evidence = self.constitution_extractor.extract_all_evidence(self.repo_path)
            constitution_section = self.constitution_extractor.generate_constitution_check_section(
                constitution_evidence
            )
            lines.append(constitution_section)
        except Exception:
            self._append_constitution_fallback_block(lines, contracts_defined)
        if contracts_defined:
            self._append_contract_definitions_for_feature(lines, feature)
        self._append_plan_phases_footer(lines, feature)
        return "\n".join(lines)

    @staticmethod
    def _classify_task_bucket(task_desc: str) -> str:
        task_lower = task_desc.lower()
        setup_kw = ("setup", "install", "configure", "create project", "initialize")
        if any(keyword in task_lower for keyword in setup_kw):
            return "setup"
        found_kw = ("implement", "create model", "set up database", "middleware")
        if any(keyword in task_lower for keyword in found_kw):
            return "foundational"
        return "story"

    def _collect_task_phases(
        self, feature: Feature
    ) -> tuple[
        list[tuple[int, str, int]],
        list[tuple[int, str, int]],
        dict[int, list[tuple[int, str]]],
    ]:
        setup_tasks: list[tuple[int, str, int]] = []
        foundational_tasks: list[tuple[int, str, int]] = []
        story_tasks: dict[int, list[tuple[int, str]]] = {}
        task_counter = 1
        for story in feature.stories:
            story_num = self._extract_story_number(story.key)
            if not story.tasks:
                foundational_tasks.append((task_counter, f"Implement {story.title}", story_num))
                task_counter += 1
                continue
            for task_desc in story.tasks:
                bucket = self._classify_task_bucket(task_desc)
                if bucket == "setup":
                    setup_tasks.append((task_counter, task_desc, story_num))
                elif bucket == "foundational":
                    foundational_tasks.append((task_counter, task_desc, story_num))
                else:
                    story_tasks.setdefault(story_num, []).append((task_counter, task_desc))
                task_counter += 1
        return setup_tasks, foundational_tasks, story_tasks

    @staticmethod
    def _priority_from_story_tags(story: Any) -> str:
        if not story.tags:
            return "P3"
        for tag in story.tags:
            if tag.startswith("P") and tag[1:].isdigit():
                return tag
        return "P3"

    def _append_tasks_phase_section(self, lines: list[str], title: str, rows: list[tuple[int, str, int]]) -> None:
        lines.append(title)
        lines.append("")
        for task_num, task_desc, story_ref in rows:
            lines.append(f"- [ ] [T{task_num:03d}] [P] [US{story_ref}] {task_desc}")
        lines.append("")

    @beartype
    @require(lambda feature: isinstance(feature, Feature), "Must be Feature instance")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _generate_tasks_markdown(self, feature: Feature) -> str:
        """Generate Spec-Kit tasks.md content from SpecFact feature."""
        lines = ["# Tasks", ""]
        if not feature.stories:
            lines.append("## Phase 1: Setup")
            lines.append("")
            lines.append(f"- [ ] [T001] Implement {feature.title}")
            lines.append("")
            return "\n".join(lines)
        setup_tasks, foundational_tasks, story_tasks = self._collect_task_phases(feature)
        if setup_tasks:
            self._append_tasks_phase_section(lines, "## Phase 1: Setup", setup_tasks)
        if foundational_tasks:
            self._append_tasks_phase_section(lines, "## Phase 2: Foundational", foundational_tasks)
        for story_idx, story in enumerate(feature.stories, start=1):
            story_num = self._extract_story_number(story.key)
            story_task_list = story_tasks.get(story_num, [])
            if not story_task_list:
                continue
            phase_num = story_idx + 2
            priority = self._priority_from_story_tags(story)
            lines.append(f"## Phase {phase_num}: User Story {story_idx} (Priority: {priority})")
            lines.append("")
            for task_num, task_desc in story_task_list:
                lines.append(f"- [ ] [T{task_num:03d}] [US{story_idx}] {task_desc}")
            lines.append("")
        return "\n".join(lines)

    _FW_KEYS = ("fastapi", "django", "flask", "typer", "tornado", "bottle")
    _DB_KEYS = ("postgres", "postgresql", "mysql", "sqlite", "redis", "mongodb", "cassandra")
    _TEST_KEYS = ("pytest", "unittest", "nose", "tox")
    _DEPLOY_KEYS = ("docker", "kubernetes", "aws", "gcp", "azure")

    def _constraint_adds_idea_stack_item(self, constraint: str, stack: list[str], seen: set[str]) -> None:
        if constraint in seen:
            return
        cl = constraint.lower()
        if "python" in cl:
            stack.append(constraint)
            seen.add(constraint)
            return
        if any(fw in cl for fw in self._FW_KEYS):
            stack.append(constraint)
            seen.add(constraint)
            return
        if any(db in cl for db in self._DB_KEYS):
            stack.append(constraint)
            seen.add(constraint)

    def _extract_stack_from_idea(self, plan_bundle: PlanBundle, stack: list[str], seen: set[str]) -> None:
        if not plan_bundle.idea or not plan_bundle.idea.constraints:
            return
        for constraint in plan_bundle.idea.constraints:
            self._constraint_adds_idea_stack_item(constraint, stack, seen)

    def _extract_stack_from_feature_constraints(self, feature: Feature, stack: list[str], seen: set[str]) -> None:
        if not feature.constraints:
            return
        for constraint in feature.constraints:
            if constraint in seen:
                continue
            cl = constraint.lower()
            if any(k in cl for k in (*self._FW_KEYS, *self._DB_KEYS, *self._TEST_KEYS, *self._DEPLOY_KEYS)):
                stack.append(constraint)
                seen.add(constraint)

    @beartype
    @require(lambda feature: isinstance(feature, Feature), "Must be Feature instance")
    @require(lambda plan_bundle: isinstance(plan_bundle, PlanBundle), "Must be PlanBundle instance")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    @ensure(lambda result: len(result) > 0, "Must have at least one stack item")
    def _extract_technology_stack(self, feature: Feature, plan_bundle: PlanBundle) -> list[str]:
        """
        Extract technology stack from feature and plan bundle constraints.

        Args:
            feature: Feature to extract stack from
            plan_bundle: Plan bundle containing idea-level constraints

        Returns:
            List of technology stack items
        """
        stack: list[str] = []
        seen: set[str] = set()
        self._extract_stack_from_idea(plan_bundle, stack, seen)
        self._extract_stack_from_feature_constraints(feature, stack, seen)
        if not stack:
            return ["Python 3.11+", "Typer for CLI", "Pydantic for data validation"]
        return stack

    @beartype
    @require(lambda feature_key: isinstance(feature_key, str), "Must be string")
    @ensure(lambda result: isinstance(result, int), "Must return int")
    def _extract_feature_number(self, feature_key: str) -> int:
        """Extract feature number from key (FEATURE-001 -> 1)."""
        import re

        match = re.search(r"(\d+)", feature_key)
        return int(match.group(1)) if match else 0

    @beartype
    @require(lambda story_key: isinstance(story_key, str), "Must be string")
    @ensure(lambda result: isinstance(result, int), "Must return int")
    def _extract_story_number(self, story_key: str) -> int:
        """Extract story number from key (STORY-001 -> 1)."""
        import re

        match = re.search(r"(\d+)", story_key)
        return int(match.group(1)) if match else 0

    @beartype
    @require(lambda title: isinstance(title, str), "Must be string")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    @ensure(lambda result: len(result) > 0, "Result must be non-empty")
    def _to_feature_dir_name(self, title: str) -> str:
        """Convert feature title to directory name (User Authentication -> user-authentication)."""
        import re

        # Convert to lowercase, replace spaces and special chars with hyphens
        name = title.lower()
        name = re.sub(r"[^a-z0-9]+", "-", name)
        name = re.sub(r"-+", "-", name)  # Collapse multiple hyphens
        return name.strip("-")

    @beartype
    @require(lambda name: isinstance(name, str) and len(name) > 0, "Name must be non-empty string")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    @ensure(lambda result: len(result) > 0, "Result must be non-empty")
    def _humanize_name(self, name: str) -> str:
        """Convert component name to human-readable title."""
        import re

        # Handle PascalCase
        name = re.sub(r"([A-Z])", r" \1", name).strip()
        # Handle snake_case
        name = name.replace("_", " ").replace("-", " ")
        return name.title()
