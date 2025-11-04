"""
Spec-Kit to SpecFact converter.

This module converts Spec-Kit markdown artifacts (spec.md, plan.md, tasks.md, constitution.md)
to SpecFact format (plans, protocols).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.generators.protocol_generator import ProtocolGenerator
from specfact_cli.generators.workflow_generator import WorkflowGenerator
from specfact_cli.importers.speckit_scanner import SpecKitScanner
from specfact_cli.models.plan import Feature, Idea, PlanBundle, Product, Release, Story
from specfact_cli.models.protocol import Protocol
from specfact_cli.utils.structure import SpecFactStructure


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
        self.mapping_file = mapping_file

    @beartype
    @ensure(lambda result: isinstance(result, Protocol), "Must return Protocol")
    @ensure(lambda result: len(result.states) >= 2, "Must have at least INIT and COMPLETE states")
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
                feature_key = feature.get("feature_key", "UNKNOWN")
                states.append(feature_key)
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
            self.protocol_generator.generate(protocol, output_path)
        else:
            # Use default path - construct .specfact/protocols/workflow.protocol.yaml
            output_path = self.repo_path / ".specfact" / "protocols" / "workflow.protocol.yaml"
            SpecFactStructure.ensure_structure(self.repo_path)
            self.protocol_generator.generate(protocol, output_path)

        return protocol

    @beartype
    @ensure(lambda result: isinstance(result, PlanBundle), "Must return PlanBundle")
    @ensure(lambda result: result.version == "1.0", "Must have version 1.0")
    def convert_plan(self, output_path: Path | None = None) -> PlanBundle:
        """
        Convert Spec-Kit markdown artifacts to SpecFact plan bundle.

        Args:
            output_path: Optional path to write plan bundle (default: .specfact/plans/main.bundle.yaml)

        Returns:
            Generated PlanBundle model
        """
        # Discover features from markdown artifacts
        discovered_features = self.scanner.discover_features()

        # Extract features from markdown data
        features = self._extract_features_from_markdown(discovered_features)

        # Parse constitution for constraints
        structure = self.scanner.scan_structure()
        memory_dir = Path(structure.get("specify_memory_dir", "")) if structure.get("specify_memory_dir") else None
        constraints: list[str] = []
        if memory_dir and Path(memory_dir).exists():
            memory_data = self.scanner.parse_memory_files(Path(memory_dir))
            constraints = memory_data.get("constraints", [])

        # Create idea from repository
        repo_name = self.repo_path.name or "Imported Project"
        idea = Idea(
            title=self._humanize_name(repo_name),
            narrative=f"Imported from Spec-Kit project: {repo_name}",
            target_users=[],
            value_hypothesis="",
            constraints=constraints,
            metrics=None,
        )

        # Create product with themes (extract from feature titles)
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

        # Create plan bundle
        plan_bundle = PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=features,
            metadata=None,
        )

        # Write to file if output path provided
        if output_path:
            SpecFactStructure.ensure_structure(output_path.parent)
            self.plan_generator.generate(plan_bundle, output_path)
        else:
            # Use default path - construct .specfact/plans/main.bundle.yaml
            output_path = self.repo_path / ".specfact" / "plans" / "main.bundle.yaml"
            SpecFactStructure.ensure_structure(self.repo_path)
            self.plan_generator.generate(plan_bundle, output_path)

        return plan_bundle

    @beartype
    @require(lambda discovered_features: isinstance(discovered_features, list), "Must be list")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    @ensure(lambda result: all(isinstance(f, Feature) for f in result), "All items must be Features")
    def _extract_features_from_markdown(self, discovered_features: list[dict[str, Any]]) -> list[Feature]:
        """Extract features from Spec-Kit markdown artifacts."""
        features: list[Feature] = []

        for feature_data in discovered_features:
            feature_key = feature_data.get("feature_key", "UNKNOWN")
            feature_title = feature_data.get("feature_title", "Unknown Feature")

            # Extract stories from spec.md
            stories = self._extract_stories_from_spec(feature_data)

            # Extract outcomes from requirements
            requirements = feature_data.get("requirements", [])
            outcomes: list[str] = []
            for req in requirements:
                if isinstance(req, dict):
                    outcomes.append(req.get("text", ""))
                elif isinstance(req, str):
                    outcomes.append(req)

            # Extract acceptance criteria from success criteria
            success_criteria = feature_data.get("success_criteria", [])
            acceptance: list[str] = []
            for sc in success_criteria:
                if isinstance(sc, dict):
                    acceptance.append(sc.get("text", ""))
                elif isinstance(sc, str):
                    acceptance.append(sc)

            # Calculate confidence based on completeness
            confidence = 0.5
            if feature_title and feature_title != "Unknown Feature":
                confidence += 0.2
            if stories:
                confidence += 0.2
            if outcomes:
                confidence += 0.1

            feature = Feature(
                key=feature_key,
                title=feature_title,
                outcomes=outcomes if outcomes else [f"Provides {feature_title} functionality"],
                acceptance=acceptance if acceptance else [f"{feature_title} is functional"],
                constraints=feature_data.get("edge_cases", []),
                stories=stories,
                confidence=min(confidence, 1.0),
                draft=False,
            )

            features.append(feature)

        return features

    @beartype
    @require(lambda feature_data: isinstance(feature_data, dict), "Must be dict")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    @ensure(lambda result: all(isinstance(s, Story) for s in result), "All items must be Stories")
    def _extract_stories_from_spec(self, feature_data: dict[str, Any]) -> list[Story]:
        """Extract user stories from Spec-Kit spec.md data."""
        stories: list[Story] = []
        spec_stories = feature_data.get("stories", [])

        for story_data in spec_stories:
            story_key = story_data.get("key", "UNKNOWN")
            story_title = story_data.get("title", "Unknown Story")
            priority = story_data.get("priority", "P3")

            # Calculate story points from priority
            priority_map = {"P1": 8, "P2": 5, "P3": 3, "P4": 1}
            story_points = priority_map.get(priority, 3)
            value_points = story_points  # Use same value for simplicity

            # Extract acceptance criteria
            acceptance = story_data.get("acceptance", [])

            # Extract tasks from tasks.md if available
            tasks_data = feature_data.get("tasks", {})
            tasks: list[str] = []
            if tasks_data and "tasks" in tasks_data:
                for task in tasks_data["tasks"]:
                    if isinstance(task, dict):
                        story_ref = task.get("story_ref", "")
                        # Match story reference to this story
                        if (story_ref and story_ref in story_key) or not story_ref:
                            tasks.append(task.get("description", ""))

            story = Story(
                key=story_key,
                title=story_title,
                acceptance=acceptance if acceptance else [f"{story_title} is implemented"],
                tags=[priority],
                story_points=story_points,
                value_points=value_points,
                tasks=tasks,
                confidence=0.8,  # High confidence from spec
                draft=False,
            )
            stories.append(story)

        return stories

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

        return sorted(list(themes))

    @beartype
    @ensure(lambda result: result.exists(), "Output path must exist")
    @ensure(lambda result: result.suffix == ".yml", "Must be YAML file")
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
    @require(lambda python_version: python_version.startswith("3."), "Python version must be 3.x")
    @ensure(lambda result: result.exists(), "Output path must exist")
    @ensure(lambda result: result.suffix == ".yml", "Must be YAML file")
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
    @require(lambda plan_bundle: isinstance(plan_bundle, PlanBundle), "Must be PlanBundle instance")
    @ensure(lambda result: isinstance(result, int), "Must return int (number of features converted)")
    @ensure(lambda result: result >= 0, "Result must be non-negative")
    def convert_to_speckit(self, plan_bundle: PlanBundle) -> int:
        """
        Convert SpecFact plan bundle to Spec-Kit markdown artifacts.

        Generates spec.md, plan.md, and tasks.md files for each feature in the plan bundle.

        Args:
            plan_bundle: SpecFact plan bundle to convert

        Returns:
            Number of features converted
        """
        features_converted = 0

        for feature in plan_bundle.features:
            # Generate feature directory name from key (FEATURE-001 -> 001-feature-name)
            feature_num = self._extract_feature_number(feature.key)
            feature_name = self._to_feature_dir_name(feature.title)

            # Create feature directory
            feature_dir = self.repo_path / "specs" / f"{feature_num:03d}-{feature_name}"
            feature_dir.mkdir(parents=True, exist_ok=True)

            # Generate spec.md
            spec_content = self._generate_spec_markdown(feature)
            (feature_dir / "spec.md").write_text(spec_content, encoding="utf-8")

            # Generate plan.md
            plan_content = self._generate_plan_markdown(feature)
            (feature_dir / "plan.md").write_text(plan_content, encoding="utf-8")

            # Generate tasks.md
            tasks_content = self._generate_tasks_markdown(feature)
            (feature_dir / "tasks.md").write_text(tasks_content, encoding="utf-8")

            features_converted += 1

        return features_converted

    @beartype
    @require(lambda feature: isinstance(feature, Feature), "Must be Feature instance")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    @ensure(lambda result: len(result) > 0, "Result must be non-empty")
    def _generate_spec_markdown(self, feature: Feature) -> str:
        """Generate Spec-Kit spec.md content from SpecFact feature."""
        from datetime import datetime

        # Extract feature branch from feature key (FEATURE-001 -> 001-feature-name)
        feature_num = self._extract_feature_number(feature.key)
        feature_name = self._to_feature_dir_name(feature.title)
        feature_branch = f"{feature_num:03d}-{feature_name}"

        # Generate frontmatter (CRITICAL for Spec-Kit compatibility)
        lines = [
            "---",
            f"**Feature Branch**: `{feature_branch}`",
            f"**Created**: {datetime.now().strftime('%Y-%m-%d')}",
            "**Status**: Draft",
            "---",
            "",
            f"# Feature Specification: {feature.title}",
            "",
        ]

        # Add stories
        if feature.stories:
            lines.append("## User Scenarios & Testing")
            lines.append("")

            for idx, story in enumerate(feature.stories, start=1):
                # Extract priority from tags or default to P3
                priority = "P3"
                if story.tags:
                    for tag in story.tags:
                        if tag.startswith("P") and tag[1:].isdigit():
                            priority = tag
                            break

                lines.append(f"### User Story {idx} - {story.title} (Priority: {priority})")
                lines.append(f"Users can {story.title}")
                lines.append("")
                lines.append("**Why this priority**: Core functionality")
                lines.append("")

                # INVSEST criteria (CRITICAL for /speckit.analyze and /speckit.checklist)
                lines.append("**Independent**: YES")
                lines.append("**Negotiable**: YES")
                lines.append("**Valuable**: YES")
                lines.append("**Estimable**: YES")
                lines.append("**Small**: YES")
                lines.append("**Testable**: YES")
                lines.append("")

                lines.append("**Acceptance Criteria:**")
                lines.append("")

                scenarios_primary: list[str] = []
                scenarios_alternate: list[str] = []
                scenarios_exception: list[str] = []
                scenarios_recovery: list[str] = []

                for acc_idx, acc in enumerate(story.acceptance, start=1):
                    # Parse Given/When/Then if available
                    if "Given" in acc and "When" in acc and "Then" in acc:
                        parts = acc.split(", ")
                        given = parts[0].replace("Given ", "").strip()
                        when = parts[1].replace("When ", "").strip()
                        then = parts[2].replace("Then ", "").strip()
                        lines.append(f"{acc_idx}. **Given** {given}, **When** {when}, **Then** {then}")

                        # Categorize scenarios based on keywords
                        scenario_text = f"{given}, {when}, {then}"
                        acc_lower = acc.lower()
                        if any(keyword in acc_lower for keyword in ["error", "exception", "fail", "invalid"]):
                            scenarios_exception.append(scenario_text)
                        elif any(keyword in acc_lower for keyword in ["recover", "retry", "fallback"]):
                            scenarios_recovery.append(scenario_text)
                        elif any(keyword in acc_lower for keyword in ["alternate", "alternative", "different"]):
                            scenarios_alternate.append(scenario_text)
                        else:
                            scenarios_primary.append(scenario_text)
                    else:
                        lines.append(f"{acc_idx}. {acc}")
                        scenarios_primary.append(acc)

                lines.append("")

                # Scenarios section (CRITICAL for /speckit.analyze and /speckit.checklist)
                if scenarios_primary or scenarios_alternate or scenarios_exception or scenarios_recovery:
                    lines.append("**Scenarios:**")
                    lines.append("")

                    if scenarios_primary:
                        for scenario in scenarios_primary:
                            lines.append(f"- **Primary Scenario**: {scenario}")
                    else:
                        lines.append("- **Primary Scenario**: Standard user flow")

                    if scenarios_alternate:
                        for scenario in scenarios_alternate:
                            lines.append(f"- **Alternate Scenario**: {scenario}")
                    else:
                        lines.append("- **Alternate Scenario**: Alternative user flow")

                    if scenarios_exception:
                        for scenario in scenarios_exception:
                            lines.append(f"- **Exception Scenario**: {scenario}")
                    else:
                        lines.append("- **Exception Scenario**: Error handling")

                    if scenarios_recovery:
                        for scenario in scenarios_recovery:
                            lines.append(f"- **Recovery Scenario**: {scenario}")
                    else:
                        lines.append("- **Recovery Scenario**: Recovery from errors")

                    lines.append("")
                lines.append("")

        # Add functional requirements from outcomes
        if feature.outcomes:
            lines.append("## Functional Requirements")
            lines.append("")

            for idx, outcome in enumerate(feature.outcomes, start=1):
                lines.append(f"**FR-{idx:03d}**: System MUST {outcome}")
            lines.append("")

        # Add success criteria from acceptance
        if feature.acceptance:
            lines.append("## Success Criteria")
            lines.append("")

            for idx, acc in enumerate(feature.acceptance, start=1):
                lines.append(f"**SC-{idx:03d}**: {acc}")
            lines.append("")

        # Add edge cases from constraints
        if feature.constraints:
            lines.append("### Edge Cases")
            lines.append("")

            for constraint in feature.constraints:
                lines.append(f"- {constraint}")
            lines.append("")

        return "\n".join(lines)

    @beartype
    @require(lambda feature: isinstance(feature, Feature), "Must be Feature instance")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _generate_plan_markdown(self, feature: Feature) -> str:
        """Generate Spec-Kit plan.md content from SpecFact feature."""
        lines = [f"# Implementation Plan: {feature.title}", ""]
        lines.append("## Summary")
        lines.append(f"Implementation plan for {feature.title}.")
        lines.append("")

        lines.append("## Technical Context")
        lines.append("")
        lines.append("**Language/Version**: Python 3.11+")
        lines.append("")

        lines.append("**Primary Dependencies:**")
        lines.append("")
        # Could extract from feature context if available
        lines.append("- `typer` - CLI framework")
        lines.append("- `pydantic` - Data validation")
        lines.append("")

        lines.append("**Technology Stack:**")
        lines.append("")
        lines.append("- Python 3.11+")
        lines.append("- Typer for CLI")
        lines.append("- Pydantic for data validation")
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

        # Constitution Check section (CRITICAL for /speckit.analyze)
        lines.append("## Constitution Check")
        lines.append("")
        lines.append("**Article VII (Simplicity)**:")
        lines.append("- [ ] Using ≤3 projects?")
        lines.append("- [ ] No future-proofing?")
        lines.append("")
        lines.append("**Article VIII (Anti-Abstraction)**:")
        lines.append("- [ ] Using framework directly?")
        lines.append("- [ ] Single model representation?")
        lines.append("")
        lines.append("**Article IX (Integration-First)**:")
        lines.append("- [ ] Contracts defined?")
        lines.append("- [ ] Contract tests written?")
        lines.append("")
        lines.append("**Status**: PASS")
        lines.append("")

        # Phases section
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

        return "\n".join(lines)

    @beartype
    @require(lambda feature: isinstance(feature, Feature), "Must be Feature instance")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _generate_tasks_markdown(self, feature: Feature) -> str:
        """Generate Spec-Kit tasks.md content from SpecFact feature."""
        lines = ["# Tasks", ""]

        task_counter = 1

        # Phase 1: Setup (initial tasks if any)
        setup_tasks: list[tuple[int, str, int]] = []  # (task_num, description, story_num)
        foundational_tasks: list[tuple[int, str, int]] = []
        story_tasks: dict[int, list[tuple[int, str]]] = {}  # story_num -> [(task_num, description)]

        # Organize tasks by phase
        for story_idx, story in enumerate(feature.stories, start=1):
            story_num = self._extract_story_number(story.key)

            if story.tasks:
                for task_desc in story.tasks:
                    # Check if task is setup/foundational (common patterns)
                    task_lower = task_desc.lower()
                    if any(
                        keyword in task_lower
                        for keyword in ["setup", "install", "configure", "create project", "initialize"]
                    ):
                        setup_tasks.append((task_counter, task_desc, story_num))
                        task_counter += 1
                    elif any(
                        keyword in task_lower
                        for keyword in ["implement", "create model", "set up database", "middleware"]
                    ):
                        foundational_tasks.append((task_counter, task_desc, story_num))
                        task_counter += 1
                    else:
                        if story_num not in story_tasks:
                            story_tasks[story_num] = []
                        story_tasks[story_num].append((task_counter, task_desc))
                        task_counter += 1
            else:
                # Generate default task - put in foundational phase
                foundational_tasks.append((task_counter, f"Implement {story.title}", story_num))
                task_counter += 1

        # Generate Phase 1: Setup
        if setup_tasks:
            lines.append("## Phase 1: Setup")
            lines.append("")
            for task_num, task_desc, story_num in setup_tasks:
                lines.append(f"- [ ] [T{task_num:03d}] [P] [US{story_num}] {task_desc}")
            lines.append("")

        # Generate Phase 2: Foundational
        if foundational_tasks:
            lines.append("## Phase 2: Foundational")
            lines.append("")
            for task_num, task_desc, story_num in foundational_tasks:
                lines.append(f"- [ ] [T{task_num:03d}] [P] [US{story_num}] {task_desc}")
            lines.append("")

        # Generate Phase 3+: User Stories (one phase per story)
        for story_idx, story in enumerate(feature.stories, start=1):
            story_num = self._extract_story_number(story.key)
            phase_num = story_idx + 2  # Phase 3, 4, 5, etc.

            # Get tasks for this story
            story_task_list = story_tasks.get(story_num, [])

            if story_task_list:
                # Extract priority from tags
                priority = "P3"
                if story.tags:
                    for tag in story.tags:
                        if tag.startswith("P") and tag[1:].isdigit():
                            priority = tag
                            break

                lines.append(f"## Phase {phase_num}: User Story {story_idx} (Priority: {priority})")
                lines.append("")
                for task_num, task_desc in story_task_list:
                    lines.append(f"- [ ] [T{task_num:03d}] [US{story_idx}] {task_desc}")
                lines.append("")

        # If no stories, create a default task in Phase 1
        if not feature.stories:
            lines.append("## Phase 1: Setup")
            lines.append("")
            lines.append(f"- [ ] [T001] Implement {feature.title}")
            lines.append("")

        return "\n".join(lines)

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
