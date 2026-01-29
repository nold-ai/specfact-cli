"""
Plan command - Manage greenfield development plans.

This module provides commands for creating and managing development plans,
features, and stories.
"""

from __future__ import annotations

import json
from contextlib import suppress
from datetime import UTC
from pathlib import Path
from typing import Any

import typer
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.table import Table

from specfact_cli import runtime
from specfact_cli.analyzers.ambiguity_scanner import AmbiguityFinding
from specfact_cli.comparators.plan_comparator import PlanComparator
from specfact_cli.generators.report_generator import ReportFormat, ReportGenerator
from specfact_cli.models.deviation import Deviation, DeviationSeverity, DeviationType, ValidationReport
from specfact_cli.models.enforcement import EnforcementConfig
from specfact_cli.models.plan import Business, Feature, Idea, PlanBundle, Product, Release, Story
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
from specfact_cli.models.sdd import SDDHow, SDDManifest, SDDWhat, SDDWhy
from specfact_cli.modes import detect_mode
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.telemetry import telemetry
from specfact_cli.utils import (
    display_summary,
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
    prompt_confirm,
    prompt_dict,
    prompt_list,
    prompt_text,
)
from specfact_cli.utils.progress import load_bundle_with_progress, save_bundle_with_progress
from specfact_cli.utils.structured_io import StructuredFormat, load_structured_file
from specfact_cli.validators.schema import validate_plan_bundle


app = typer.Typer(help="Manage development plans, features, and stories")
console = Console()


# Use shared progress utilities for consistency (aliased to maintain existing function names)
def _load_bundle_with_progress(bundle_dir: Path, validate_hashes: bool = False) -> ProjectBundle:
    """Load project bundle with unified progress display."""
    return load_bundle_with_progress(bundle_dir, validate_hashes=validate_hashes, console_instance=console)


def _save_bundle_with_progress(bundle: ProjectBundle, bundle_dir: Path, atomic: bool = True) -> None:
    """Save project bundle with unified progress display."""
    save_bundle_with_progress(bundle, bundle_dir, atomic=atomic, console_instance=console)


@app.command("init")
@beartype
@require(lambda bundle: isinstance(bundle, str) and len(bundle) > 0, "Bundle name must be non-empty string")
def init(
    # Target/Input
    bundle: str = typer.Argument(..., help="Project bundle name (e.g., legacy-api, auth-module)"),
    # Behavior/Options
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Interactive mode with prompts. Default: True (interactive)",
    ),
    scaffold: bool = typer.Option(
        True,
        "--scaffold/--no-scaffold",
        help="Create complete .specfact directory structure. Default: True (scaffold enabled)",
    ),
) -> None:
    """
    Initialize a new modular project bundle.

    Creates a new modular project bundle with idea, product, and features structure.
    The bundle is created in .specfact/projects/<bundle-name>/ directory.

    **Parameter Groups:**
    - **Target/Input**: bundle (required argument)
    - **Behavior/Options**: --interactive/--no-interactive, --scaffold/--no-scaffold

    **Examples:**
        specfact plan init legacy-api                    # Interactive with scaffold
        specfact plan init auth-module --no-interactive  # Minimal bundle
        specfact plan init my-project --no-scaffold      # Bundle without directory structure
    """
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {
        "bundle": bundle,
        "interactive": interactive,
        "scaffold": scaffold,
    }

    if is_debug_mode():
        debug_log_operation(
            "command",
            "plan init",
            "started",
            extra={"bundle": bundle, "interactive": interactive, "scaffold": scaffold},
        )
        debug_print("[dim]plan init: started[/dim]")

    with telemetry.track_command("plan.init", telemetry_metadata) as record:
        print_section("SpecFact CLI - Project Bundle Builder")

        # Create .specfact structure if requested
        if scaffold:
            print_info("Creating .specfact/ directory structure...")
            SpecFactStructure.scaffold_project()
            print_success("Directory structure created")
        else:
            # Ensure minimum structure exists
            SpecFactStructure.ensure_structure()

        # Get project bundle directory
        bundle_dir = SpecFactStructure.project_dir(bundle_name=bundle)
        if bundle_dir.exists():
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "plan init",
                    "failed",
                    error=f"Project bundle already exists: {bundle_dir}",
                    extra={"reason": "bundle_exists", "bundle": bundle},
                )
            print_error(f"Project bundle already exists: {bundle_dir}")
            print_info("Use a different bundle name or remove the existing bundle")
            raise typer.Exit(1)

        # Ensure project structure exists
        SpecFactStructure.ensure_project_structure(bundle_name=bundle)

        if not interactive:
            # Non-interactive mode: create minimal bundle
            _create_minimal_bundle(bundle, bundle_dir)
            record({"bundle_type": "minimal"})
            return

        # Interactive mode: guided bundle creation
        try:
            project_bundle = _build_bundle_interactively(bundle)

            # Save bundle
            _save_bundle_with_progress(project_bundle, bundle_dir, atomic=True)

            # Record bundle statistics
            record(
                {
                    "bundle_type": "interactive",
                    "features_count": len(project_bundle.features),
                    "stories_count": sum(len(f.stories) for f in project_bundle.features.values()),
                }
            )

            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "plan init",
                    "success",
                    extra={"bundle": bundle, "bundle_dir": str(bundle_dir)},
                )
                debug_print("[dim]plan init: success[/dim]")
            print_success(f"Project bundle created successfully: {bundle_dir}")

        except KeyboardInterrupt:
            print_warning("\nBundle creation cancelled")
            raise typer.Exit(1) from None
        except Exception as e:
            if is_debug_mode():
                debug_log_operation(
                    "command",
                    "plan init",
                    "failed",
                    error=str(e),
                    extra={"reason": type(e).__name__, "bundle": bundle},
                )
            print_error(f"Failed to create bundle: {e}")
            raise typer.Exit(1) from e


def _create_minimal_bundle(bundle_name: str, bundle_dir: Path) -> None:
    """Create a minimal project bundle."""

    manifest = BundleManifest(
        versions=BundleVersions(schema="1.0", project="0.1.0"),
        schema_metadata=None,
        project_metadata=None,
    )

    bundle = ProjectBundle(
        manifest=manifest,
        bundle_name=bundle_name,
        idea=None,
        business=None,
        product=Product(themes=[], releases=[]),
        features={},
        clarifications=None,
    )

    _save_bundle_with_progress(bundle, bundle_dir, atomic=True)
    print_success(f"Minimal project bundle created: {bundle_dir}")


def _build_bundle_interactively(bundle_name: str) -> ProjectBundle:
    """Build a plan bundle through interactive prompts."""
    # Section 1: Idea
    print_section("1. Idea - What are you building?")

    idea_title = prompt_text("Project title", required=True)
    idea_narrative = prompt_text("Project narrative (brief description)", required=True)

    add_idea_details = prompt_confirm("Add optional idea details? (target users, metrics)", default=False)

    idea_data: dict[str, Any] = {"title": idea_title, "narrative": idea_narrative}

    if add_idea_details:
        target_users = prompt_list("Target users")
        value_hypothesis = prompt_text("Value hypothesis", required=False)

        if target_users:
            idea_data["target_users"] = target_users
        if value_hypothesis:
            idea_data["value_hypothesis"] = value_hypothesis

        if prompt_confirm("Add success metrics?", default=False):
            metrics = prompt_dict("Success Metrics")
            if metrics:
                idea_data["metrics"] = metrics

    idea = Idea(**idea_data)
    display_summary("Idea Summary", idea_data)

    # Section 2: Business (optional)
    print_section("2. Business Context (optional)")

    business = None
    if prompt_confirm("Add business context?", default=False):
        segments = prompt_list("Market segments")
        problems = prompt_list("Problems you're solving")
        solutions = prompt_list("Your solutions")
        differentiation = prompt_list("How you differentiate")
        risks = prompt_list("Business risks")

        business = Business(
            segments=segments if segments else [],
            problems=problems if problems else [],
            solutions=solutions if solutions else [],
            differentiation=differentiation if differentiation else [],
            risks=risks if risks else [],
        )

    # Section 3: Product
    print_section("3. Product - Themes and Releases")

    themes = prompt_list("Product themes (e.g., AI/ML, Security)")
    releases: list[Release] = []

    if prompt_confirm("Define releases?", default=True):
        while True:
            release_name = prompt_text("Release name (e.g., v1.0 - MVP)", required=False)
            if not release_name:
                break

            objectives = prompt_list("Release objectives")
            scope = prompt_list("Feature keys in scope (e.g., FEATURE-001)")
            risks = prompt_list("Release risks")

            releases.append(
                Release(
                    name=release_name,
                    objectives=objectives if objectives else [],
                    scope=scope if scope else [],
                    risks=risks if risks else [],
                )
            )

            if not prompt_confirm("Add another release?", default=False):
                break

    product = Product(themes=themes if themes else [], releases=releases)

    # Section 4: Features
    print_section("4. Features - What will you build?")

    features: list[Feature] = []
    while prompt_confirm("Add a feature?", default=True):
        feature = _prompt_feature()
        features.append(feature)

        if not prompt_confirm("Add another feature?", default=False):
            break

    # Create project bundle

    manifest = BundleManifest(
        versions=BundleVersions(schema="1.0", project="0.1.0"),
        schema_metadata=None,
        project_metadata=None,
    )

    # Convert features list to dict
    features_dict: dict[str, Feature] = {f.key: f for f in features}

    project_bundle = ProjectBundle(
        manifest=manifest,
        bundle_name=bundle_name,
        idea=idea,
        business=business,
        product=product,
        features=features_dict,
        clarifications=None,
    )

    # Final summary
    print_section("Project Bundle Summary")
    console.print(f"[cyan]Bundle:[/cyan] {bundle_name}")
    console.print(f"[cyan]Title:[/cyan] {idea.title}")
    console.print(f"[cyan]Themes:[/cyan] {', '.join(product.themes)}")
    console.print(f"[cyan]Features:[/cyan] {len(features)}")
    console.print(f"[cyan]Releases:[/cyan] {len(product.releases)}")

    return project_bundle


def _prompt_feature() -> Feature:
    """Prompt for feature details."""
    print_info("\nNew Feature")

    key = prompt_text("Feature key (e.g., FEATURE-001)", required=True)
    title = prompt_text("Feature title", required=True)
    outcomes = prompt_list("Expected outcomes")
    acceptance = prompt_list("Acceptance criteria")

    add_details = prompt_confirm("Add optional details?", default=False)

    feature_data = {
        "key": key,
        "title": title,
        "outcomes": outcomes if outcomes else [],
        "acceptance": acceptance if acceptance else [],
    }

    if add_details:
        constraints = prompt_list("Constraints")
        if constraints:
            feature_data["constraints"] = constraints

        confidence = prompt_text("Confidence (0.0-1.0)", required=False)
        if confidence:
            with suppress(ValueError):
                feature_data["confidence"] = float(confidence)

        draft = prompt_confirm("Mark as draft?", default=False)
        feature_data["draft"] = draft

    # Add stories
    stories: list[Story] = []
    if prompt_confirm("Add stories to this feature?", default=True):
        while True:
            story = _prompt_story()
            stories.append(story)

            if not prompt_confirm("Add another story?", default=False):
                break

    feature_data["stories"] = stories

    return Feature(**feature_data)


def _prompt_story() -> Story:
    """Prompt for story details."""
    print_info("  New Story")

    key = prompt_text("  Story key (e.g., STORY-001)", required=True)
    title = prompt_text("  Story title", required=True)
    acceptance = prompt_list("  Acceptance criteria")

    story_data = {
        "key": key,
        "title": title,
        "acceptance": acceptance if acceptance else [],
    }

    if prompt_confirm("  Add optional details?", default=False):
        tags = prompt_list("  Tags (e.g., critical, backend)")
        if tags:
            story_data["tags"] = tags

        confidence = prompt_text("  Confidence (0.0-1.0)", required=False)
        if confidence:
            with suppress(ValueError):
                story_data["confidence"] = float(confidence)

        draft = prompt_confirm("  Mark as draft?", default=False)
        story_data["draft"] = draft

    return Story(**story_data)


@app.command("add-feature")
@beartype
@require(lambda key: isinstance(key, str) and len(key) > 0, "Key must be non-empty string")
@require(lambda title: isinstance(title, str) and len(title) > 0, "Title must be non-empty string")
@require(lambda bundle: bundle is None or isinstance(bundle, str), "Bundle must be None or string")
def add_feature(
    # Target/Input
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (required, e.g., legacy-api). If not specified, attempts to use default bundle.",
    ),
    key: str = typer.Option(..., "--key", help="Feature key (e.g., FEATURE-001)"),
    title: str = typer.Option(..., "--title", help="Feature title"),
    outcomes: str | None = typer.Option(None, "--outcomes", help="Expected outcomes (comma-separated)"),
    acceptance: str | None = typer.Option(None, "--acceptance", help="Acceptance criteria (comma-separated)"),
) -> None:
    """
    Add a new feature to an existing project bundle.

    **Parameter Groups:**
    - **Target/Input**: --bundle, --key, --title, --outcomes, --acceptance

    **Examples:**
        specfact plan add-feature --key FEATURE-001 --title "User Auth" --outcomes "Secure login" --acceptance "Login works" --bundle legacy-api
        specfact plan add-feature --key FEATURE-002 --title "Payment Processing" --bundle legacy-api
    """

    telemetry_metadata = {
        "feature_key": key,
    }

    with telemetry.track_command("plan.add_feature", telemetry_metadata) as record:
        from specfact_cli.utils.structure import SpecFactStructure

        # Find bundle directory
        if bundle is None:
            # Try to use active plan first
            bundle = SpecFactStructure.get_active_bundle_name(Path("."))
            if bundle:
                print_info(f"Using active plan: {bundle}")
            else:
                # Fallback: Try to find default bundle (first bundle in projects directory)
                projects_dir = Path(".specfact/projects")
                if projects_dir.exists():
                    bundles = [
                        d.name for d in projects_dir.iterdir() if d.is_dir() and (d / "bundle.manifest.yaml").exists()
                    ]
                    if bundles:
                        bundle = bundles[0]
                        print_info(f"Using default bundle: {bundle}")
                        print_info(f"Tip: Use 'specfact plan select {bundle}' to set as active plan")
                    else:
                        print_error(f"No project bundles found in {projects_dir}")
                        print_error("Create one with: specfact plan init <bundle-name>")
                        print_error("Or specify --bundle <bundle-name> if the bundle exists")
                        raise typer.Exit(1)
                else:
                    print_error(f"Projects directory not found: {projects_dir}")
                print_error("Create one with: specfact plan init <bundle-name>")
                print_error("Or specify --bundle <bundle-name> if the bundle exists")
                raise typer.Exit(1)

        bundle_dir = _find_bundle_dir(bundle)
        if bundle_dir is None:
            raise typer.Exit(1)

        print_section("SpecFact CLI - Add Feature")

        try:
            # Load existing project bundle
            project_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

            # Convert to PlanBundle for compatibility
            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

            # Check if feature key already exists
            existing_keys = {f.key for f in plan_bundle.features}
            if key in existing_keys:
                print_error(f"Feature '{key}' already exists in bundle")
                raise typer.Exit(1)

            # Parse outcomes and acceptance (comma-separated strings)
            outcomes_list = [o.strip() for o in outcomes.split(",")] if outcomes else []
            acceptance_list = [a.strip() for a in acceptance.split(",")] if acceptance else []

            # Create new feature
            new_feature = Feature(
                key=key,
                title=title,
                outcomes=outcomes_list,
                acceptance=acceptance_list,
                constraints=[],
                stories=[],
                confidence=1.0,
                draft=False,
                source_tracking=None,
                contract=None,
                protocol=None,
            )

            # Add feature to plan bundle
            plan_bundle.features.append(new_feature)

            # Convert back to ProjectBundle and save
            updated_project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle)
            _save_bundle_with_progress(updated_project_bundle, bundle_dir, atomic=True)

            record(
                {
                    "total_features": len(plan_bundle.features),
                    "outcomes_count": len(outcomes_list),
                    "acceptance_count": len(acceptance_list),
                }
            )

            print_success(f"Feature '{key}' added successfully")
            console.print(f"[dim]Feature: {title}[/dim]")
            if outcomes_list:
                console.print(f"[dim]Outcomes: {', '.join(outcomes_list)}[/dim]")
            if acceptance_list:
                console.print(f"[dim]Acceptance: {', '.join(acceptance_list)}[/dim]")

        except Exception as e:
            print_error(f"Failed to add feature: {e}")
            raise typer.Exit(1) from e


@app.command("add-story")
@beartype
@require(lambda feature: isinstance(feature, str) and len(feature) > 0, "Feature must be non-empty string")
@require(lambda key: isinstance(key, str) and len(key) > 0, "Key must be non-empty string")
@require(lambda title: isinstance(title, str) and len(title) > 0, "Title must be non-empty string")
@require(
    lambda story_points: story_points is None or (story_points >= 0 and story_points <= 100),
    "Story points must be 0-100 if provided",
)
@require(
    lambda value_points: value_points is None or (value_points >= 0 and value_points <= 100),
    "Value points must be 0-100 if provided",
)
@require(lambda bundle: bundle is None or isinstance(bundle, str), "Bundle must be None or string")
def add_story(
    # Target/Input
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (required, e.g., legacy-api). If not specified, attempts to use default bundle.",
    ),
    feature: str = typer.Option(..., "--feature", help="Parent feature key"),
    key: str = typer.Option(..., "--key", help="Story key (e.g., STORY-001)"),
    title: str = typer.Option(..., "--title", help="Story title"),
    acceptance: str | None = typer.Option(None, "--acceptance", help="Acceptance criteria (comma-separated)"),
    story_points: int | None = typer.Option(None, "--story-points", help="Story points (complexity)"),
    value_points: int | None = typer.Option(None, "--value-points", help="Value points (business value)"),
    # Behavior/Options
    draft: bool = typer.Option(False, "--draft", help="Mark story as draft"),
) -> None:
    """
    Add a new story to a feature.

    **Parameter Groups:**
    - **Target/Input**: --bundle, --feature, --key, --title, --acceptance, --story-points, --value-points
    - **Behavior/Options**: --draft

    **Examples:**
        specfact plan add-story --feature FEATURE-001 --key STORY-001 --title "Login API" --acceptance "API works" --story-points 5 --bundle legacy-api
        specfact plan add-story --feature FEATURE-001 --key STORY-002 --title "Logout API" --bundle legacy-api --draft
    """

    telemetry_metadata = {
        "feature_key": feature,
        "story_key": key,
    }

    with telemetry.track_command("plan.add_story", telemetry_metadata) as record:
        from specfact_cli.utils.structure import SpecFactStructure

        # Find bundle directory
        if bundle is None:
            # Try to use active plan first
            bundle = SpecFactStructure.get_active_bundle_name(Path("."))
            if bundle:
                print_info(f"Using active plan: {bundle}")
            else:
                # Fallback: Try to find default bundle (first bundle in projects directory)
                projects_dir = Path(".specfact/projects")
                if projects_dir.exists():
                    bundles = [
                        d.name for d in projects_dir.iterdir() if d.is_dir() and (d / "bundle.manifest.yaml").exists()
                    ]
                    if bundles:
                        bundle = bundles[0]
                        print_info(f"Using default bundle: {bundle}")
                        print_info(f"Tip: Use 'specfact plan select {bundle}' to set as active plan")
                    else:
                        print_error(f"No project bundles found in {projects_dir}")
                        print_error("Create one with: specfact plan init <bundle-name>")
                        print_error("Or specify --bundle <bundle-name> if the bundle exists")
                        raise typer.Exit(1)
                else:
                    print_error(f"Projects directory not found: {projects_dir}")
                print_error("Create one with: specfact plan init <bundle-name>")
                print_error("Or specify --bundle <bundle-name> if the bundle exists")
                raise typer.Exit(1)

        bundle_dir = _find_bundle_dir(bundle)
        if bundle_dir is None:
            raise typer.Exit(1)

        print_section("SpecFact CLI - Add Story")

        try:
            # Load existing project bundle
            project_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

            # Convert to PlanBundle for compatibility
            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

            # Find parent feature
            parent_feature = None
            for f in plan_bundle.features:
                if f.key == feature:
                    parent_feature = f
                    break

            if parent_feature is None:
                print_error(f"Feature '{feature}' not found in bundle")
                console.print(f"[dim]Available features: {', '.join(f.key for f in plan_bundle.features)}[/dim]")
                raise typer.Exit(1)

            # Check if story key already exists in feature
            existing_story_keys = {s.key for s in parent_feature.stories}
            if key in existing_story_keys:
                print_error(f"Story '{key}' already exists in feature '{feature}'")
                raise typer.Exit(1)

            # Parse acceptance (comma-separated string)
            acceptance_list = [a.strip() for a in acceptance.split(",")] if acceptance else []

            # Create new story
            new_story = Story(
                key=key,
                title=title,
                acceptance=acceptance_list,
                tags=[],
                story_points=story_points,
                value_points=value_points,
                tasks=[],
                confidence=1.0,
                draft=draft,
                contracts=None,
                scenarios=None,
            )

            # Add story to feature
            parent_feature.stories.append(new_story)

            # Convert back to ProjectBundle and save
            updated_project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle)
            _save_bundle_with_progress(updated_project_bundle, bundle_dir, atomic=True)

            record(
                {
                    "total_stories": len(parent_feature.stories),
                    "acceptance_count": len(acceptance_list),
                    "story_points": story_points if story_points else 0,
                    "value_points": value_points if value_points else 0,
                }
            )

            print_success(f"Story '{key}' added to feature '{feature}'")
            console.print(f"[dim]Story: {title}[/dim]")
            if acceptance_list:
                console.print(f"[dim]Acceptance: {', '.join(acceptance_list)}[/dim]")
            if story_points:
                console.print(f"[dim]Story Points: {story_points}[/dim]")
            if value_points:
                console.print(f"[dim]Value Points: {value_points}[/dim]")

        except Exception as e:
            print_error(f"Failed to add story: {e}")
            raise typer.Exit(1) from e


@app.command("update-idea")
@beartype
@require(lambda bundle: bundle is None or isinstance(bundle, str), "Bundle must be None or string")
def update_idea(
    # Target/Input
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (required, e.g., legacy-api). If not specified, attempts to use default bundle.",
    ),
    title: str | None = typer.Option(None, "--title", help="Idea title"),
    narrative: str | None = typer.Option(None, "--narrative", help="Idea narrative (brief description)"),
    target_users: str | None = typer.Option(None, "--target-users", help="Target user personas (comma-separated)"),
    value_hypothesis: str | None = typer.Option(None, "--value-hypothesis", help="Value hypothesis statement"),
    constraints: str | None = typer.Option(None, "--constraints", help="Idea-level constraints (comma-separated)"),
) -> None:
    """
    Update idea section metadata in a project bundle (optional business context).

    This command allows updating idea properties (title, narrative, target users,
    value hypothesis, constraints) in non-interactive environments (CI/CD, Copilot).

    Note: The idea section is OPTIONAL - it provides business context and metadata,
    not technical implementation details. All parameters are optional.

    **Parameter Groups:**
    - **Target/Input**: --bundle, --title, --narrative, --target-users, --value-hypothesis, --constraints

    **Examples:**
        specfact plan update-idea --target-users "Developers, DevOps" --value-hypothesis "Reduce technical debt" --bundle legacy-api
        specfact plan update-idea --constraints "Python 3.11+, Maintain backward compatibility" --bundle legacy-api
    """

    telemetry_metadata = {}

    with telemetry.track_command("plan.update_idea", telemetry_metadata) as record:
        from specfact_cli.utils.structure import SpecFactStructure

        # Find bundle directory
        if bundle is None:
            # Try to use active plan first
            bundle = SpecFactStructure.get_active_bundle_name(Path("."))
            if bundle:
                print_info(f"Using active plan: {bundle}")
            else:
                # Fallback: Try to find default bundle (first bundle in projects directory)
                projects_dir = Path(".specfact/projects")
                if projects_dir.exists():
                    bundles = [
                        d.name for d in projects_dir.iterdir() if d.is_dir() and (d / "bundle.manifest.yaml").exists()
                    ]
                    if bundles:
                        bundle = bundles[0]
                        print_info(f"Using default bundle: {bundle}")
                        print_info(f"Tip: Use 'specfact plan select {bundle}' to set as active plan")
                    else:
                        print_error(f"No project bundles found in {projects_dir}")
                        print_error("Create one with: specfact plan init <bundle-name>")
                        print_error("Or specify --bundle <bundle-name> if the bundle exists")
                        raise typer.Exit(1)
                else:
                    print_error(f"Projects directory not found: {projects_dir}")
                print_error("Create one with: specfact plan init <bundle-name>")
                print_error("Or specify --bundle <bundle-name> if the bundle exists")
                raise typer.Exit(1)

        bundle_dir = _find_bundle_dir(bundle)
        if bundle_dir is None:
            raise typer.Exit(1)

        print_section("SpecFact CLI - Update Idea")

        try:
            # Load existing project bundle
            project_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

            # Convert to PlanBundle for compatibility
            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

            # Create idea section if it doesn't exist
            if plan_bundle.idea is None:
                plan_bundle.idea = Idea(
                    title=title or "Untitled",
                    narrative=narrative or "",
                    target_users=[],
                    value_hypothesis="",
                    constraints=[],
                    metrics=None,
                )
                print_info("Created new idea section")

            # Track what was updated
            updates_made = []

            # Update title if provided
            if title is not None:
                plan_bundle.idea.title = title
                updates_made.append("title")

            # Update narrative if provided
            if narrative is not None:
                plan_bundle.idea.narrative = narrative
                updates_made.append("narrative")

            # Update target_users if provided
            if target_users is not None:
                target_users_list = [u.strip() for u in target_users.split(",")] if target_users else []
                plan_bundle.idea.target_users = target_users_list
                updates_made.append("target_users")

            # Update value_hypothesis if provided
            if value_hypothesis is not None:
                plan_bundle.idea.value_hypothesis = value_hypothesis
                updates_made.append("value_hypothesis")

            # Update constraints if provided
            if constraints is not None:
                constraints_list = [c.strip() for c in constraints.split(",")] if constraints else []
                plan_bundle.idea.constraints = constraints_list
                updates_made.append("constraints")

            if not updates_made:
                print_warning(
                    "No updates specified. Use --title, --narrative, --target-users, --value-hypothesis, or --constraints"
                )
                raise typer.Exit(1)

            # Convert back to ProjectBundle and save
            updated_project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle)
            _save_bundle_with_progress(updated_project_bundle, bundle_dir, atomic=True)

            record(
                {
                    "updates": updates_made,
                    "idea_exists": plan_bundle.idea is not None,
                }
            )

            print_success("Idea section updated successfully")
            console.print(f"[dim]Updated fields: {', '.join(updates_made)}[/dim]")
            if title:
                console.print(f"[dim]Title: {title}[/dim]")
            if narrative:
                console.print(
                    f"[dim]Narrative: {narrative[:80]}...[/dim]"
                    if len(narrative) > 80
                    else f"[dim]Narrative: {narrative}[/dim]"
                )
            if target_users:
                target_users_list = [u.strip() for u in target_users.split(",")] if target_users else []
                console.print(f"[dim]Target Users: {', '.join(target_users_list)}[/dim]")
            if value_hypothesis:
                console.print(
                    f"[dim]Value Hypothesis: {value_hypothesis[:80]}...[/dim]"
                    if len(value_hypothesis) > 80
                    else f"[dim]Value Hypothesis: {value_hypothesis}[/dim]"
                )
            if constraints:
                constraints_list = [c.strip() for c in constraints.split(",")] if constraints else []
                console.print(f"[dim]Constraints: {', '.join(constraints_list)}[/dim]")

        except Exception as e:
            print_error(f"Failed to update idea: {e}")
            raise typer.Exit(1) from e


@app.command("update-feature")
@beartype
@require(lambda bundle: bundle is None or isinstance(bundle, str), "Bundle must be None or string")
def update_feature(
    # Target/Input
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (required, e.g., legacy-api). If not specified, attempts to use default bundle.",
    ),
    key: str | None = typer.Option(
        None, "--key", help="Feature key to update (e.g., FEATURE-001). Required unless --batch-updates is provided."
    ),
    title: str | None = typer.Option(None, "--title", help="Feature title"),
    outcomes: str | None = typer.Option(None, "--outcomes", help="Expected outcomes (comma-separated)"),
    acceptance: str | None = typer.Option(None, "--acceptance", help="Acceptance criteria (comma-separated)"),
    constraints: str | None = typer.Option(None, "--constraints", help="Constraints (comma-separated)"),
    confidence: float | None = typer.Option(None, "--confidence", help="Confidence score (0.0-1.0)"),
    draft: bool | None = typer.Option(
        None,
        "--draft/--no-draft",
        help="Mark as draft (use --draft to set True, --no-draft to set False, omit to leave unchanged)",
    ),
    batch_updates: Path | None = typer.Option(
        None,
        "--batch-updates",
        help="Path to JSON/YAML file with multiple feature updates. File format: list of objects with 'key' and update fields (title, outcomes, acceptance, constraints, confidence, draft).",
    ),
) -> None:
    """
    Update an existing feature's metadata in a project bundle.

    This command allows updating feature properties (title, outcomes, acceptance criteria,
    constraints, confidence, draft status) in non-interactive environments (CI/CD, Copilot).

    Supports both single feature updates and batch updates via --batch-updates file.

    **Parameter Groups:**
    - **Target/Input**: --bundle, --key, --title, --outcomes, --acceptance, --constraints, --confidence, --batch-updates
    - **Behavior/Options**: --draft/--no-draft

    **Examples:**
        # Single feature update
        specfact plan update-feature --key FEATURE-001 --title "Updated Title" --outcomes "Outcome 1, Outcome 2" --bundle legacy-api
        specfact plan update-feature --key FEATURE-001 --acceptance "Criterion 1, Criterion 2" --confidence 0.9 --bundle legacy-api

        # Batch updates from file
        specfact plan update-feature --batch-updates updates.json --bundle legacy-api
    """
    from specfact_cli.utils.structure import SpecFactStructure

    # Validate that either key or batch_updates is provided
    if not key and not batch_updates:
        print_error("Either --key or --batch-updates must be provided")
        raise typer.Exit(1)

    if key and batch_updates:
        print_error("Cannot use both --key and --batch-updates. Use --batch-updates for multiple updates.")
        raise typer.Exit(1)

    telemetry_metadata = {
        "batch_mode": batch_updates is not None,
    }

    with telemetry.track_command("plan.update_feature", telemetry_metadata) as record:
        # Find bundle directory
        if bundle is None:
            # Try to use active plan first
            bundle = SpecFactStructure.get_active_bundle_name(Path("."))
            if bundle:
                print_info(f"Using active plan: {bundle}")
            else:
                # Fallback: Try to find default bundle (first bundle in projects directory)
                projects_dir = Path(".specfact/projects")
                if projects_dir.exists():
                    bundles = [
                        d.name for d in projects_dir.iterdir() if d.is_dir() and (d / "bundle.manifest.yaml").exists()
                    ]
                    if bundles:
                        bundle = bundles[0]
                        print_info(f"Using default bundle: {bundle}")
                        print_info(f"Tip: Use 'specfact plan select {bundle}' to set as active plan")
                    else:
                        print_error("No bundles found. Create one with: specfact plan init <bundle-name>")
                        raise typer.Exit(1)
                else:
                    print_error("No bundles found. Create one with: specfact plan init <bundle-name>")
                    raise typer.Exit(1)

        bundle_dir = SpecFactStructure.project_dir(bundle_name=bundle)
        if not bundle_dir.exists():
            print_error(f"Bundle '{bundle}' not found: {bundle_dir}\nCreate one with: specfact plan init {bundle}")
            raise typer.Exit(1)

        print_section("SpecFact CLI - Update Feature")

        try:
            # Load existing project bundle
            project_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

            # Convert to PlanBundle for compatibility
            existing_plan = _convert_project_bundle_to_plan_bundle(project_bundle)

            # Handle batch updates
            if batch_updates:
                if not batch_updates.exists():
                    print_error(f"Batch updates file not found: {batch_updates}")
                    raise typer.Exit(1)

                print_info(f"Loading batch updates from: {batch_updates}")
                batch_data = load_structured_file(batch_updates)

                if not isinstance(batch_data, list):
                    print_error("Batch updates file must contain a list of update objects")
                    raise typer.Exit(1)

                total_updates = 0
                successful_updates = 0
                failed_updates = []

                for update_item in batch_data:
                    if not isinstance(update_item, dict):
                        failed_updates.append({"item": update_item, "error": "Not a dictionary"})
                        continue

                    update_key = update_item.get("key")
                    if not update_key:
                        failed_updates.append({"item": update_item, "error": "Missing 'key' field"})
                        continue

                    total_updates += 1

                    # Find feature to update
                    feature_to_update = None
                    for f in existing_plan.features:
                        if f.key == update_key:
                            feature_to_update = f
                            break

                    if feature_to_update is None:
                        failed_updates.append({"key": update_key, "error": f"Feature '{update_key}' not found in plan"})
                        continue

                    # Track what was updated
                    updates_made = []

                    # Update fields from batch item
                    if "title" in update_item:
                        feature_to_update.title = update_item["title"]
                        updates_made.append("title")

                    if "outcomes" in update_item:
                        outcomes_val = update_item["outcomes"]
                        if isinstance(outcomes_val, str):
                            outcomes_list = [o.strip() for o in outcomes_val.split(",")] if outcomes_val else []
                        elif isinstance(outcomes_val, list):
                            outcomes_list = outcomes_val
                        else:
                            failed_updates.append({"key": update_key, "error": "Invalid 'outcomes' format"})
                            continue
                        feature_to_update.outcomes = outcomes_list
                        updates_made.append("outcomes")

                    if "acceptance" in update_item:
                        acceptance_val = update_item["acceptance"]
                        if isinstance(acceptance_val, str):
                            acceptance_list = [a.strip() for a in acceptance_val.split(",")] if acceptance_val else []
                        elif isinstance(acceptance_val, list):
                            acceptance_list = acceptance_val
                        else:
                            failed_updates.append({"key": update_key, "error": "Invalid 'acceptance' format"})
                            continue
                        feature_to_update.acceptance = acceptance_list
                        updates_made.append("acceptance")

                    if "constraints" in update_item:
                        constraints_val = update_item["constraints"]
                        if isinstance(constraints_val, str):
                            constraints_list = (
                                [c.strip() for c in constraints_val.split(",")] if constraints_val else []
                            )
                        elif isinstance(constraints_val, list):
                            constraints_list = constraints_val
                        else:
                            failed_updates.append({"key": update_key, "error": "Invalid 'constraints' format"})
                            continue
                        feature_to_update.constraints = constraints_list
                        updates_made.append("constraints")

                    if "confidence" in update_item:
                        conf_val = update_item["confidence"]
                        if not isinstance(conf_val, (int, float)) or not (0.0 <= conf_val <= 1.0):
                            failed_updates.append({"key": update_key, "error": "Confidence must be 0.0-1.0"})
                            continue
                        feature_to_update.confidence = float(conf_val)
                        updates_made.append("confidence")

                    if "draft" in update_item:
                        feature_to_update.draft = bool(update_item["draft"])
                        updates_made.append("draft")

                    if updates_made:
                        successful_updates += 1
                        console.print(f"[dim]✓ Updated {update_key}: {', '.join(updates_made)}[/dim]")
                    else:
                        failed_updates.append({"key": update_key, "error": "No valid update fields provided"})

                # Convert back to ProjectBundle and save
                print_info("Validating updated plan...")
                updated_project_bundle = _convert_plan_bundle_to_project_bundle(existing_plan, bundle)
                _save_bundle_with_progress(updated_project_bundle, bundle_dir, atomic=True)

                record(
                    {
                        "batch_total": total_updates,
                        "batch_successful": successful_updates,
                        "batch_failed": len(failed_updates),
                        "total_features": len(existing_plan.features),
                    }
                )

                print_success(f"Batch update complete: {successful_updates}/{total_updates} features updated")
                if failed_updates:
                    print_warning(f"{len(failed_updates)} update(s) failed:")
                    for failed in failed_updates:
                        console.print(
                            f"[dim]  - {failed.get('key', 'Unknown')}: {failed.get('error', 'Unknown error')}[/dim]"
                        )

            else:
                # Single feature update (existing logic)
                if not key:
                    print_error("--key is required when not using --batch-updates")
                    raise typer.Exit(1)

                # Find feature to update
                feature_to_update = None
                for f in existing_plan.features:
                    if f.key == key:
                        feature_to_update = f
                        break

                if feature_to_update is None:
                    print_error(f"Feature '{key}' not found in plan")
                    console.print(f"[dim]Available features: {', '.join(f.key for f in existing_plan.features)}[/dim]")
                    raise typer.Exit(1)

                # Track what was updated
                updates_made = []

                # Update title if provided
                if title is not None:
                    feature_to_update.title = title
                    updates_made.append("title")

                # Update outcomes if provided
                if outcomes is not None:
                    outcomes_list = [o.strip() for o in outcomes.split(",")] if outcomes else []
                    feature_to_update.outcomes = outcomes_list
                    updates_made.append("outcomes")

                # Update acceptance criteria if provided
                if acceptance is not None:
                    acceptance_list = [a.strip() for a in acceptance.split(",")] if acceptance else []
                    feature_to_update.acceptance = acceptance_list
                    updates_made.append("acceptance")

                # Update constraints if provided
                if constraints is not None:
                    constraints_list = [c.strip() for c in constraints.split(",")] if constraints else []
                    feature_to_update.constraints = constraints_list
                    updates_made.append("constraints")

                # Update confidence if provided
                if confidence is not None:
                    if not (0.0 <= confidence <= 1.0):
                        print_error(f"Confidence must be between 0.0 and 1.0, got: {confidence}")
                        raise typer.Exit(1)
                    feature_to_update.confidence = confidence
                    updates_made.append("confidence")

                # Update draft status if provided
                if draft is not None:
                    feature_to_update.draft = draft
                    updates_made.append("draft")

                if not updates_made:
                    print_warning(
                        "No updates specified. Use --title, --outcomes, --acceptance, --constraints, --confidence, or --draft"
                    )
                    raise typer.Exit(1)

                # Convert back to ProjectBundle and save
                print_info("Validating updated plan...")
                updated_project_bundle = _convert_plan_bundle_to_project_bundle(existing_plan, bundle)
                _save_bundle_with_progress(updated_project_bundle, bundle_dir, atomic=True)

                record(
                    {
                        "updates": updates_made,
                        "total_features": len(existing_plan.features),
                    }
                )

                print_success(f"Feature '{key}' updated successfully")
                console.print(f"[dim]Updated fields: {', '.join(updates_made)}[/dim]")
                if title:
                    console.print(f"[dim]Title: {title}[/dim]")
                if outcomes:
                    outcomes_list = [o.strip() for o in outcomes.split(",")] if outcomes else []
                    console.print(f"[dim]Outcomes: {', '.join(outcomes_list)}[/dim]")
                if acceptance:
                    acceptance_list = [a.strip() for a in acceptance.split(",")] if acceptance else []
                    console.print(f"[dim]Acceptance: {', '.join(acceptance_list)}[/dim]")

        except Exception as e:
            print_error(f"Failed to update feature: {e}")
            raise typer.Exit(1) from e


@app.command("update-story")
@beartype
@require(lambda bundle: bundle is None or isinstance(bundle, str), "Bundle must be None or string")
@require(
    lambda story_points: story_points is None or (story_points >= 0 and story_points <= 100),
    "Story points must be 0-100 if provided",
)
@require(
    lambda value_points: value_points is None or (value_points >= 0 and value_points <= 100),
    "Value points must be 0-100 if provided",
)
@require(lambda confidence: confidence is None or (0.0 <= confidence <= 1.0), "Confidence must be 0.0-1.0 if provided")
def update_story(
    # Target/Input
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (required, e.g., legacy-api). If not specified, attempts to use default bundle.",
    ),
    feature: str | None = typer.Option(
        None, "--feature", help="Parent feature key (e.g., FEATURE-001). Required unless --batch-updates is provided."
    ),
    key: str | None = typer.Option(
        None, "--key", help="Story key to update (e.g., STORY-001). Required unless --batch-updates is provided."
    ),
    title: str | None = typer.Option(None, "--title", help="Story title"),
    acceptance: str | None = typer.Option(None, "--acceptance", help="Acceptance criteria (comma-separated)"),
    story_points: int | None = typer.Option(None, "--story-points", help="Story points (complexity: 0-100)"),
    value_points: int | None = typer.Option(None, "--value-points", help="Value points (business value: 0-100)"),
    confidence: float | None = typer.Option(None, "--confidence", help="Confidence score (0.0-1.0)"),
    draft: bool | None = typer.Option(
        None,
        "--draft/--no-draft",
        help="Mark as draft (use --draft to set True, --no-draft to set False, omit to leave unchanged)",
    ),
    batch_updates: Path | None = typer.Option(
        None,
        "--batch-updates",
        help="Path to JSON/YAML file with multiple story updates. File format: list of objects with 'feature', 'key' and update fields (title, acceptance, story_points, value_points, confidence, draft).",
    ),
) -> None:
    """
    Update an existing story's metadata in a project bundle.

    This command allows updating story properties (title, acceptance criteria,
    story points, value points, confidence, draft status) in non-interactive
    environments (CI/CD, Copilot).

    Supports both single story updates and batch updates via --batch-updates file.

    **Parameter Groups:**
    - **Target/Input**: --bundle, --feature, --key, --title, --acceptance, --story-points, --value-points, --confidence, --batch-updates
    - **Behavior/Options**: --draft/--no-draft

    **Examples:**
        # Single story update
        specfact plan update-story --feature FEATURE-001 --key STORY-001 --title "Updated Title" --bundle legacy-api
        specfact plan update-story --feature FEATURE-001 --key STORY-001 --acceptance "Criterion 1, Criterion 2" --confidence 0.9 --bundle legacy-api

        # Batch updates from file
        specfact plan update-story --batch-updates updates.json --bundle legacy-api
    """
    from specfact_cli.utils.structure import SpecFactStructure

    # Validate that either (feature and key) or batch_updates is provided
    if not (feature and key) and not batch_updates:
        print_error("Either (--feature and --key) or --batch-updates must be provided")
        raise typer.Exit(1)

    if (feature or key) and batch_updates:
        print_error("Cannot use both (--feature/--key) and --batch-updates. Use --batch-updates for multiple updates.")
        raise typer.Exit(1)

    telemetry_metadata = {
        "batch_mode": batch_updates is not None,
    }

    with telemetry.track_command("plan.update_story", telemetry_metadata) as record:
        # Find bundle directory
        if bundle is None:
            # Try to use active plan first
            bundle = SpecFactStructure.get_active_bundle_name(Path("."))
            if bundle:
                print_info(f"Using active plan: {bundle}")
            else:
                # Fallback: Try to find default bundle (first bundle in projects directory)
                projects_dir = Path(".specfact/projects")
                if projects_dir.exists():
                    bundles = [
                        d.name for d in projects_dir.iterdir() if d.is_dir() and (d / "bundle.manifest.yaml").exists()
                    ]
                    if bundles:
                        bundle = bundles[0]
                        print_info(f"Using default bundle: {bundle}")
                        print_info(f"Tip: Use 'specfact plan select {bundle}' to set as active plan")
                    else:
                        print_error("No bundles found. Create one with: specfact plan init <bundle-name>")
                        raise typer.Exit(1)
                else:
                    print_error("No bundles found. Create one with: specfact plan init <bundle-name>")
                    raise typer.Exit(1)

        bundle_dir = SpecFactStructure.project_dir(bundle_name=bundle)
        if not bundle_dir.exists():
            print_error(f"Bundle '{bundle}' not found: {bundle_dir}\nCreate one with: specfact plan init {bundle}")
            raise typer.Exit(1)

        print_section("SpecFact CLI - Update Story")

        try:
            # Load existing project bundle
            project_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

            # Convert to PlanBundle for compatibility
            existing_plan = _convert_project_bundle_to_plan_bundle(project_bundle)

            # Handle batch updates
            if batch_updates:
                if not batch_updates.exists():
                    print_error(f"Batch updates file not found: {batch_updates}")
                    raise typer.Exit(1)

                print_info(f"Loading batch updates from: {batch_updates}")
                batch_data = load_structured_file(batch_updates)

                if not isinstance(batch_data, list):
                    print_error("Batch updates file must contain a list of update objects")
                    raise typer.Exit(1)

                total_updates = 0
                successful_updates = 0
                failed_updates = []

                for update_item in batch_data:
                    if not isinstance(update_item, dict):
                        failed_updates.append({"item": update_item, "error": "Not a dictionary"})
                        continue

                    update_feature = update_item.get("feature")
                    update_key = update_item.get("key")
                    if not update_feature or not update_key:
                        failed_updates.append({"item": update_item, "error": "Missing 'feature' or 'key' field"})
                        continue

                    total_updates += 1

                    # Find parent feature
                    parent_feature = None
                    for f in existing_plan.features:
                        if f.key == update_feature:
                            parent_feature = f
                            break

                    if parent_feature is None:
                        failed_updates.append(
                            {
                                "feature": update_feature,
                                "key": update_key,
                                "error": f"Feature '{update_feature}' not found in plan",
                            }
                        )
                        continue

                    # Find story to update
                    story_to_update = None
                    for s in parent_feature.stories:
                        if s.key == update_key:
                            story_to_update = s
                            break

                    if story_to_update is None:
                        failed_updates.append(
                            {
                                "feature": update_feature,
                                "key": update_key,
                                "error": f"Story '{update_key}' not found in feature '{update_feature}'",
                            }
                        )
                        continue

                    # Track what was updated
                    updates_made = []

                    # Update fields from batch item
                    if "title" in update_item:
                        story_to_update.title = update_item["title"]
                        updates_made.append("title")

                    if "acceptance" in update_item:
                        acceptance_val = update_item["acceptance"]
                        if isinstance(acceptance_val, str):
                            acceptance_list = [a.strip() for a in acceptance_val.split(",")] if acceptance_val else []
                        elif isinstance(acceptance_val, list):
                            acceptance_list = acceptance_val
                        else:
                            failed_updates.append(
                                {"feature": update_feature, "key": update_key, "error": "Invalid 'acceptance' format"}
                            )
                            continue
                        story_to_update.acceptance = acceptance_list
                        updates_made.append("acceptance")

                    if "story_points" in update_item:
                        sp_val = update_item["story_points"]
                        if not isinstance(sp_val, int) or not (0 <= sp_val <= 100):
                            failed_updates.append(
                                {"feature": update_feature, "key": update_key, "error": "Story points must be 0-100"}
                            )
                            continue
                        story_to_update.story_points = sp_val
                        updates_made.append("story_points")

                    if "value_points" in update_item:
                        vp_val = update_item["value_points"]
                        if not isinstance(vp_val, int) or not (0 <= vp_val <= 100):
                            failed_updates.append(
                                {"feature": update_feature, "key": update_key, "error": "Value points must be 0-100"}
                            )
                            continue
                        story_to_update.value_points = vp_val
                        updates_made.append("value_points")

                    if "confidence" in update_item:
                        conf_val = update_item["confidence"]
                        if not isinstance(conf_val, (int, float)) or not (0.0 <= conf_val <= 1.0):
                            failed_updates.append(
                                {"feature": update_feature, "key": update_key, "error": "Confidence must be 0.0-1.0"}
                            )
                            continue
                        story_to_update.confidence = float(conf_val)
                        updates_made.append("confidence")

                    if "draft" in update_item:
                        story_to_update.draft = bool(update_item["draft"])
                        updates_made.append("draft")

                    if updates_made:
                        successful_updates += 1
                        console.print(f"[dim]✓ Updated {update_feature}/{update_key}: {', '.join(updates_made)}[/dim]")
                    else:
                        failed_updates.append(
                            {"feature": update_feature, "key": update_key, "error": "No valid update fields provided"}
                        )

                # Convert back to ProjectBundle and save
                print_info("Validating updated plan...")
                updated_project_bundle = _convert_plan_bundle_to_project_bundle(existing_plan, bundle)
                _save_bundle_with_progress(updated_project_bundle, bundle_dir, atomic=True)

                record(
                    {
                        "batch_total": total_updates,
                        "batch_successful": successful_updates,
                        "batch_failed": len(failed_updates),
                    }
                )

                print_success(f"Batch update complete: {successful_updates}/{total_updates} stories updated")
                if failed_updates:
                    print_warning(f"{len(failed_updates)} update(s) failed:")
                    for failed in failed_updates:
                        console.print(
                            f"[dim]  - {failed.get('feature', 'Unknown')}/{failed.get('key', 'Unknown')}: {failed.get('error', 'Unknown error')}[/dim]"
                        )

            else:
                # Single story update (existing logic)
                if not feature or not key:
                    print_error("--feature and --key are required when not using --batch-updates")
                    raise typer.Exit(1)

                # Find parent feature
                parent_feature = None
                for f in existing_plan.features:
                    if f.key == feature:
                        parent_feature = f
                        break

                if parent_feature is None:
                    print_error(f"Feature '{feature}' not found in plan")
                    console.print(f"[dim]Available features: {', '.join(f.key for f in existing_plan.features)}[/dim]")
                    raise typer.Exit(1)

                # Find story to update
                story_to_update = None
                for s in parent_feature.stories:
                    if s.key == key:
                        story_to_update = s
                        break

                if story_to_update is None:
                    print_error(f"Story '{key}' not found in feature '{feature}'")
                    console.print(f"[dim]Available stories: {', '.join(s.key for s in parent_feature.stories)}[/dim]")
                    raise typer.Exit(1)

                # Track what was updated
                updates_made = []

                # Update title if provided
                if title is not None:
                    story_to_update.title = title
                    updates_made.append("title")

                # Update acceptance criteria if provided
                if acceptance is not None:
                    acceptance_list = [a.strip() for a in acceptance.split(",")] if acceptance else []
                    story_to_update.acceptance = acceptance_list
                    updates_made.append("acceptance")

                # Update story points if provided
                if story_points is not None:
                    story_to_update.story_points = story_points
                    updates_made.append("story_points")

                # Update value points if provided
                if value_points is not None:
                    story_to_update.value_points = value_points
                    updates_made.append("value_points")

                # Update confidence if provided
                if confidence is not None:
                    if not (0.0 <= confidence <= 1.0):
                        print_error(f"Confidence must be between 0.0 and 1.0, got: {confidence}")
                        raise typer.Exit(1)
                    story_to_update.confidence = confidence
                    updates_made.append("confidence")

                # Update draft status if provided
                if draft is not None:
                    story_to_update.draft = draft
                    updates_made.append("draft")

                if not updates_made:
                    print_warning(
                        "No updates specified. Use --title, --acceptance, --story-points, --value-points, --confidence, or --draft"
                    )
                    raise typer.Exit(1)

                # Convert back to ProjectBundle and save
                print_info("Validating updated plan...")
                updated_project_bundle = _convert_plan_bundle_to_project_bundle(existing_plan, bundle)
                _save_bundle_with_progress(updated_project_bundle, bundle_dir, atomic=True)

                record(
                    {
                        "updates": updates_made,
                        "total_stories": len(parent_feature.stories),
                    }
                )

                print_success(f"Story '{key}' in feature '{feature}' updated successfully")
                console.print(f"[dim]Updated fields: {', '.join(updates_made)}[/dim]")
                if title:
                    console.print(f"[dim]Title: {title}[/dim]")
                if acceptance:
                    acceptance_list = [a.strip() for a in acceptance.split(",")] if acceptance else []
                    console.print(f"[dim]Acceptance: {', '.join(acceptance_list)}[/dim]")
                if story_points is not None:
                    console.print(f"[dim]Story Points: {story_points}[/dim]")
                if value_points is not None:
                    console.print(f"[dim]Value Points: {value_points}[/dim]")
                if confidence is not None:
                    console.print(f"[dim]Confidence: {confidence}[/dim]")

        except Exception as e:
            print_error(f"Failed to update story: {e}")
            raise typer.Exit(1) from e


@app.command("compare")
@beartype
@require(lambda manual: manual is None or isinstance(manual, Path), "Manual must be None or Path")
@require(lambda auto: auto is None or isinstance(auto, Path), "Auto must be None or Path")
@require(lambda bundle: bundle is None or isinstance(bundle, str), "Bundle must be None or string")
@require(
    lambda output_format: isinstance(output_format, str) and output_format.lower() in ("markdown", "json", "yaml"),
    "Output format must be markdown, json, or yaml",
)
@require(lambda out: out is None or isinstance(out, Path), "Out must be None or Path")
def compare(
    # Target/Input
    bundle: str | None = typer.Option(
        None,
        "--bundle",
        help="Project bundle name (e.g., legacy-api). If specified, compares bundles instead of legacy plan files.",
    ),
    manual: Path | None = typer.Option(
        None,
        "--manual",
        help="Manual plan bundle path (bundle directory: .specfact/projects/<bundle>/). Ignored if --bundle is specified.",
    ),
    auto: Path | None = typer.Option(
        None,
        "--auto",
        help="Auto-derived plan bundle path (bundle directory: .specfact/projects/<bundle>/). Ignored if --bundle is specified.",
    ),
    # Output/Results
    output_format: str = typer.Option(
        "markdown",
        "--output-format",
        help="Output format (markdown, json, yaml)",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output file path (default: .specfact/projects/<bundle-name>/reports/comparison/report-<timestamp>.md when --bundle is provided).",
    ),
    # Behavior/Options
    code_vs_plan: bool = typer.Option(
        False,
        "--code-vs-plan",
        help="Alias for comparing code-derived plan vs manual plan (auto-detects latest auto plan)",
    ),
) -> None:
    """
    Compare manual and auto-derived plans to detect code vs plan drift.

    Detects deviations between manually created plans (intended design) and
    reverse-engineered plans from code (actual implementation). This comparison
    identifies code vs plan drift automatically.

    Use --code-vs-plan for convenience: automatically compares the latest
    code-derived plan against the manual plan.

    **Parameter Groups:**
    - **Target/Input**: --bundle, --manual, --auto
    - **Output/Results**: --output-format, --out
    - **Behavior/Options**: --code-vs-plan

    **Examples:**
        specfact plan compare --manual .specfact/projects/manual-bundle --auto .specfact/projects/auto-bundle
        specfact plan compare --code-vs-plan  # Convenience alias (requires bundle-based paths)
        specfact plan compare --bundle legacy-api --output-format json
    """
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {
        "code_vs_plan": code_vs_plan,
        "output_format": output_format.lower(),
    }

    with telemetry.track_command("plan.compare", telemetry_metadata) as record:
        # Ensure .specfact structure exists
        SpecFactStructure.ensure_structure()

        # Handle --code-vs-plan convenience alias
        if code_vs_plan:
            # Auto-detect manual plan (default)
            if manual is None:
                manual = SpecFactStructure.get_default_plan_path()
                if not manual.exists():
                    print_error(
                        "Default manual bundle not found.\nCreate one with: specfact plan init <bundle-name> --interactive"
                    )
                    raise typer.Exit(1)
                print_info(f"Using default manual bundle: {manual}")

            # Auto-detect latest code-derived plan
            if auto is None:
                auto = SpecFactStructure.get_latest_brownfield_report()
                if auto is None:
                    print_error(
                        "No code-derived bundles found in .specfact/projects/*/reports/brownfield/.\n"
                        "Generate one with: specfact import from-code <bundle-name> --repo ."
                    )
                    raise typer.Exit(1)
                print_info(f"Using latest code-derived bundle report: {auto}")

            # Override help text to emphasize code vs plan drift
            print_section("Code vs Plan Drift Detection")
            console.print(
                "[dim]Comparing intended design (manual plan) vs actual implementation (code-derived plan)[/dim]\n"
            )

        # Use default paths if not specified (smart defaults)
        if manual is None:
            manual = SpecFactStructure.get_default_plan_path()
            if not manual.exists():
                print_error(
                    "Default manual bundle not found.\nCreate one with: specfact plan init <bundle-name> --interactive"
                )
                raise typer.Exit(1)
            print_info(f"Using default manual bundle: {manual}")

        if auto is None:
            # Use smart default: find latest auto-derived plan
            auto = SpecFactStructure.get_latest_brownfield_report()
            if auto is None:
                print_error(
                    "No auto-derived bundles found in .specfact/projects/*/reports/brownfield/.\n"
                    "Generate one with: specfact import from-code <bundle-name> --repo ."
                )
                raise typer.Exit(1)
            print_info(f"Using latest auto-derived bundle: {auto}")

        if out is None:
            # Use smart default: timestamped comparison report
            extension = {"markdown": "md", "json": "json", "yaml": "yaml"}[output_format.lower()]
            # Phase 8.5: Use bundle-specific path if bundle context available
            # Try to infer bundle from manual plan path or use bundle parameter
            bundle_name = None
            if bundle is not None:
                bundle_name = bundle
            elif manual is not None:
                # Try to extract bundle name from manual plan path
                manual_str = str(manual)
                if "/projects/" in manual_str:
                    # Extract bundle name from path like .specfact/projects/<bundle-name>/...
                    parts = manual_str.split("/projects/")
                    if len(parts) > 1:
                        bundle_part = parts[1].split("/")[0]
                        if bundle_part:
                            bundle_name = bundle_part

            if bundle_name:
                # Use bundle-specific comparison report path (Phase 8.5)
                out = SpecFactStructure.get_bundle_comparison_report_path(
                    bundle_name=bundle_name, base_path=Path("."), format=extension
                )
            else:
                # Fallback to global path (backward compatibility during transition)
                out = SpecFactStructure.get_comparison_report_path(format=extension)
            print_info(f"Writing comparison report to: {out}")

        print_section("SpecFact CLI - Plan Comparison")

        # Validate inputs (after defaults are set)
        if manual is not None and not manual.exists():
            print_error(f"Manual plan not found: {manual}")
            raise typer.Exit(1)

        if auto is not None and not auto.exists():
            print_error(f"Auto plan not found: {auto}")
            raise typer.Exit(1)

        # Validate output format
        if output_format.lower() not in ("markdown", "json", "yaml"):
            print_error(f"Invalid output format: {output_format}. Must be markdown, json, or yaml")
            raise typer.Exit(1)

        try:
            # Load plans
            # Note: validate_plan_bundle returns tuple[bool, str | None, PlanBundle | None] when given a Path
            print_info(f"Loading manual plan: {manual}")
            validation_result = validate_plan_bundle(manual)
            # Type narrowing: when Path is passed, always returns tuple
            assert isinstance(validation_result, tuple), "Expected tuple from validate_plan_bundle for Path"
            is_valid, error, manual_plan = validation_result
            if not is_valid or manual_plan is None:
                print_error(f"Manual plan validation failed: {error}")
                raise typer.Exit(1)

            print_info(f"Loading auto plan: {auto}")
            validation_result = validate_plan_bundle(auto)
            # Type narrowing: when Path is passed, always returns tuple
            assert isinstance(validation_result, tuple), "Expected tuple from validate_plan_bundle for Path"
            is_valid, error, auto_plan = validation_result
            if not is_valid or auto_plan is None:
                print_error(f"Auto plan validation failed: {error}")
                raise typer.Exit(1)

            # Compare plans
            print_info("Comparing plans...")
            comparator = PlanComparator()
            report = comparator.compare(
                manual_plan,
                auto_plan,
                manual_label=str(manual),
                auto_label=str(auto),
            )

            # Record comparison results
            record(
                {
                    "total_deviations": report.total_deviations,
                    "high_count": report.high_count,
                    "medium_count": report.medium_count,
                    "low_count": report.low_count,
                    "manual_features": len(manual_plan.features) if manual_plan.features else 0,
                    "auto_features": len(auto_plan.features) if auto_plan.features else 0,
                }
            )

            # Display results
            print_section("Comparison Results")

            console.print(f"[cyan]Manual Plan:[/cyan] {manual}")
            console.print(f"[cyan]Auto Plan:[/cyan] {auto}")
            console.print(f"[cyan]Total Deviations:[/cyan] {report.total_deviations}\n")

            if report.total_deviations == 0:
                print_success("No deviations found! Plans are identical.")
            else:
                # Show severity summary
                console.print("[bold]Deviation Summary:[/bold]")
                console.print(f"  🔴 [bold red]HIGH:[/bold red] {report.high_count}")
                console.print(f"  🟡 [bold yellow]MEDIUM:[/bold yellow] {report.medium_count}")
                console.print(f"  🔵 [bold blue]LOW:[/bold blue] {report.low_count}\n")

                # Show detailed table
                table = Table(title="Deviations by Type and Severity")
                table.add_column("Severity", style="bold")
                table.add_column("Type", style="cyan")
                table.add_column("Description", style="white", no_wrap=False)
                table.add_column("Location", style="dim")

                for deviation in report.deviations:
                    severity_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵"}[deviation.severity.value]
                    table.add_row(
                        f"{severity_icon} {deviation.severity.value}",
                        deviation.type.value.replace("_", " ").title(),
                        deviation.description[:80] + "..."
                        if len(deviation.description) > 80
                        else deviation.description,
                        deviation.location,
                    )

                console.print(table)

            # Generate report file if requested
            if out:
                print_info(f"Generating {output_format} report...")
                generator = ReportGenerator()

                # Map format string to enum
                format_map = {
                    "markdown": ReportFormat.MARKDOWN,
                    "json": ReportFormat.JSON,
                    "yaml": ReportFormat.YAML,
                }

                report_format = format_map.get(output_format.lower(), ReportFormat.MARKDOWN)
                generator.generate_deviation_report(report, out, report_format)

                print_success(f"Report written to: {out}")

            # Apply enforcement rules if config exists
            from specfact_cli.utils.structure import SpecFactStructure

            # Determine base path from plan paths (use manual plan's parent directory)
            base_path = manual.parent if manual else None
            # If base_path is not a repository root, find the repository root
            if base_path:
                # Walk up to find repository root (where .specfact would be)
                current = base_path.resolve()
                while current != current.parent:
                    if (current / SpecFactStructure.ROOT).exists():
                        base_path = current
                        break
                    current = current.parent
                else:
                    # If we didn't find .specfact, use the plan's directory
                    # But resolve to absolute path first
                    base_path = manual.parent.resolve()

            config_path = SpecFactStructure.get_enforcement_config_path(base_path)
            if config_path.exists():
                try:
                    from specfact_cli.utils.yaml_utils import load_yaml

                    config_data = load_yaml(config_path)
                    enforcement_config = EnforcementConfig(**config_data)

                    if enforcement_config.enabled and report.total_deviations > 0:
                        print_section("Enforcement Rules")
                        console.print(f"[dim]Using enforcement config: {config_path}[/dim]\n")

                        # Check for blocking deviations
                        blocking_deviations: list[Deviation] = []
                        for deviation in report.deviations:
                            action = enforcement_config.get_action(deviation.severity.value)
                            action_icon = {"BLOCK": "🚫", "WARN": "⚠️", "LOG": "📝"}[action.value]

                            console.print(
                                f"{action_icon} [{deviation.severity.value}] {deviation.type.value}: "
                                f"[dim]{action.value}[/dim]"
                            )

                            if enforcement_config.should_block_deviation(deviation.severity.value):
                                blocking_deviations.append(deviation)

                        if blocking_deviations:
                            print_error(
                                f"\n❌ Enforcement BLOCKED: {len(blocking_deviations)} deviation(s) violate quality gates"
                            )
                            console.print("[dim]Fix the blocking deviations or adjust enforcement config[/dim]")
                            raise typer.Exit(1)
                        print_success("\n✅ Enforcement PASSED: No blocking deviations")

                except Exception as e:
                    print_warning(f"Could not load enforcement config: {e}")
                    raise typer.Exit(1) from e

            # Note: Finding deviations without enforcement is a successful comparison result
            # Exit code 0 indicates successful execution (even if deviations were found)
            # Use the report file, stdout, or enforcement config to determine if deviations are critical
            if report.total_deviations > 0:
                print_warning(f"\n{report.total_deviations} deviation(s) found")

        except KeyboardInterrupt:
            print_warning("\nComparison cancelled")
            raise typer.Exit(1) from None
        except Exception as e:
            print_error(f"Comparison failed: {e}")
            raise typer.Exit(1) from e


@app.command("select")
@beartype
@require(lambda plan: plan is None or isinstance(plan, str), "Plan must be None or str")
@require(lambda last: last is None or last > 0, "Last must be None or positive integer")
def select(
    # Target/Input
    plan: str | None = typer.Argument(
        None,
        help="Plan name or number to select (e.g., 'main.bundle.<format>' or '1')",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        help="Select bundle by exact bundle name (non-interactive, e.g., 'main')",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    plan_id: str | None = typer.Option(
        None,
        "--id",
        help="Select plan by content hash ID (non-interactive, from metadata.summary.content_hash)",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Disables interactive prompts.",
    ),
    # Advanced/Configuration
    current: bool = typer.Option(
        False,
        "--current",
        help="Show only the currently active plan",
    ),
    stages: str | None = typer.Option(
        None,
        "--stages",
        help="Filter by stages (comma-separated, e.g., 'draft,review,approved')",
    ),
    last: int | None = typer.Option(
        None,
        "--last",
        help="Show last N plans by modification time (most recent first)",
        min=1,
    ),
) -> None:
    """
    Select active project bundle from available bundles.

    Displays a numbered list of available project bundles and allows selection by number or name.
    The selected bundle becomes the active bundle tracked in `.specfact/config.yaml`.

    Filter Options:
        --current          Show only the currently active bundle (non-interactive, auto-selects)
        --stages STAGES    Filter by stages (comma-separated: draft,review,approved,released)
        --last N           Show last N bundles by modification time (most recent first)
        --name NAME        Select by exact bundle name (non-interactive, e.g., 'main')
        --id HASH          Select by content hash ID (non-interactive, from bundle manifest)

    Example:
        specfact plan select                              # Interactive selection
        specfact plan select 1                           # Select by number
        specfact plan select main                        # Select by bundle name (positional)
        specfact plan select --current                   # Show only active bundle (auto-selects)
        specfact plan select --stages draft,review       # Filter by stages
        specfact plan select --last 5                    # Show last 5 bundles
        specfact plan select --no-interactive --last 1  # CI/CD: get most recent bundle
        specfact plan select --name main                 # CI/CD: select by exact bundle name
        specfact plan select --id abc123def456          # CI/CD: select by content hash
    """
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {
        "no_interactive": no_interactive,
        "current": current,
        "stages": stages,
        "last": last,
        "name": name is not None,
        "plan_id": plan_id is not None,
    }

    with telemetry.track_command("plan.select", telemetry_metadata) as record:
        print_section("SpecFact CLI - Plan Selection")

        # List all available plans
        # Performance optimization: If --last N is specified, only process N+10 most recent files
        # This avoids processing all 31 files when user only wants last 5
        max_files_to_process = None
        if last is not None:
            # Process a few more files than requested to account for filtering
            max_files_to_process = last + 10

        plans = SpecFactStructure.list_plans(max_files=max_files_to_process)

        if not plans:
            print_warning("No project bundles found in .specfact/projects/")
            print_info("Create a project bundle with:")
            print_info("  - specfact plan init <bundle-name>")
            print_info("  - specfact import from-code <bundle-name>")
            raise typer.Exit(1)

        # Apply filters
        filtered_plans = plans.copy()

        # Filter by current/active (non-interactive: auto-selects if single match)
        if current:
            filtered_plans = [p for p in filtered_plans if p.get("active", False)]
            if not filtered_plans:
                print_warning("No active plan found")
                raise typer.Exit(1)
            # Auto-select in non-interactive mode when --current is provided
            if no_interactive and len(filtered_plans) == 1:
                selected_plan = filtered_plans[0]
                plan_name = str(selected_plan["name"])
                SpecFactStructure.set_active_plan(plan_name)
                record(
                    {
                        "plans_available": len(plans),
                        "plans_filtered": len(filtered_plans),
                        "selected_plan": plan_name,
                        "features": selected_plan["features"],
                        "stories": selected_plan["stories"],
                        "auto_selected": True,
                    }
                )
                print_success(f"Active plan (--current): {plan_name}")
                print_info(f"  Features: {selected_plan['features']}")
                print_info(f"  Stories: {selected_plan['stories']}")
                print_info(f"  Stage: {selected_plan.get('stage', 'unknown')}")
                raise typer.Exit(0)

        # Filter by stages
        if stages:
            stage_list = [s.strip().lower() for s in stages.split(",")]
            valid_stages = {"draft", "review", "approved", "released", "unknown"}
            invalid_stages = [s for s in stage_list if s not in valid_stages]
            if invalid_stages:
                print_error(f"Invalid stage(s): {', '.join(invalid_stages)}")
                print_info(f"Valid stages: {', '.join(sorted(valid_stages))}")
                raise typer.Exit(1)
            filtered_plans = [p for p in filtered_plans if str(p.get("stage", "unknown")).lower() in stage_list]

        # Filter by last N (most recent first)
        if last:
            # Sort by modification time (most recent first) and take last N
            # Handle None values by using empty string as fallback for sorting
            filtered_plans = sorted(filtered_plans, key=lambda p: p.get("modified") or "", reverse=True)[:last]

        if not filtered_plans:
            print_warning("No plans match the specified filters")
            raise typer.Exit(1)

        # Handle --name flag (non-interactive selection by exact filename)
        if name is not None:
            no_interactive = True  # Force non-interactive when --name is used
            plan_name = SpecFactStructure.ensure_plan_filename(str(name))

            selected_plan = None
            for p in plans:  # Search all plans, not just filtered
                if p["name"] == plan_name:
                    selected_plan = p
                    break

            if selected_plan is None:
                print_error(f"Plan not found: {plan_name}")
                raise typer.Exit(1)

            # Set as active and exit
            SpecFactStructure.set_active_plan(plan_name)
            record(
                {
                    "plans_available": len(plans),
                    "plans_filtered": len(filtered_plans),
                    "selected_plan": plan_name,
                    "features": selected_plan["features"],
                    "stories": selected_plan["stories"],
                    "selected_by": "name",
                }
            )
            print_success(f"Active plan (--name): {plan_name}")
            print_info(f"  Features: {selected_plan['features']}")
            print_info(f"  Stories: {selected_plan['stories']}")
            print_info(f"  Stage: {selected_plan.get('stage', 'unknown')}")
            raise typer.Exit(0)

        # Handle --id flag (non-interactive selection by content hash)
        if plan_id is not None:
            no_interactive = True  # Force non-interactive when --id is used
            # Match by content hash (from bundle manifest summary)
            selected_plan = None
            for p in plans:
                content_hash = p.get("content_hash")
                if content_hash and (content_hash == plan_id or content_hash.startswith(plan_id)):
                    selected_plan = p
                    break

            if selected_plan is None:
                print_error(f"Plan not found with ID: {plan_id}")
                print_info("Tip: Use 'specfact plan select' to see available plans and their IDs")
                raise typer.Exit(1)

            # Set as active and exit
            plan_name = str(selected_plan["name"])
            SpecFactStructure.set_active_plan(plan_name)
            record(
                {
                    "plans_available": len(plans),
                    "plans_filtered": len(filtered_plans),
                    "selected_plan": plan_name,
                    "features": selected_plan["features"],
                    "stories": selected_plan["stories"],
                    "selected_by": "id",
                }
            )
            print_success(f"Active plan (--id): {plan_name}")
            print_info(f"  Features: {selected_plan['features']}")
            print_info(f"  Stories: {selected_plan['stories']}")
            print_info(f"  Stage: {selected_plan.get('stage', 'unknown')}")
            raise typer.Exit(0)

        # If plan provided, try to resolve it
        if plan is not None:
            # Try as number first (using filtered list)
            if isinstance(plan, str) and plan.isdigit():
                plan_num = int(plan)
                if 1 <= plan_num <= len(filtered_plans):
                    selected_plan = filtered_plans[plan_num - 1]
                else:
                    print_error(f"Invalid plan number: {plan_num}. Must be between 1 and {len(filtered_plans)}")
                    raise typer.Exit(1)
            else:
                # Try as bundle name (search in filtered list first, then all plans)
                bundle_name = str(plan)

                # Find matching bundle in filtered list first
                selected_plan = None
                for p in filtered_plans:
                    if p["name"] == bundle_name:
                        selected_plan = p
                        break

                # If not found in filtered list, search all plans (for better error message)
                if selected_plan is None:
                    for p in plans:
                        if p["name"] == bundle_name:
                            print_warning(f"Bundle '{bundle_name}' exists but is filtered out by current options")
                            print_info("Available filtered bundles:")
                            for i, p in enumerate(filtered_plans, 1):
                                print_info(f"  {i}. {p['name']}")
                            raise typer.Exit(1)

            if selected_plan is None:
                print_error(f"Plan not found: {plan}")
                print_info("Available filtered plans:")
                for i, p in enumerate(filtered_plans, 1):
                    print_info(f"  {i}. {p['name']}")
                raise typer.Exit(1)
        else:
            # Display numbered list
            console.print("\n[bold]Available Plans:[/bold]\n")

            # Create table with optimized column widths
            # "#" column: fixed at 4 chars (never shrinks)
            # Features/Stories/Stage: minimal widths to avoid wasting space
            # Plan Name: flexible to use remaining space (most important)
            table = Table(show_header=True, header_style="bold cyan", expand=False)
            table.add_column("#", style="bold yellow", justify="right", width=4, min_width=4, no_wrap=True)
            table.add_column("Status", style="dim", width=8, min_width=6)
            table.add_column("Plan Name", style="bold", min_width=30)  # Flexible, gets most space
            table.add_column("Features", justify="right", width=8, min_width=6)  # Reduced from 10
            table.add_column("Stories", justify="right", width=8, min_width=6)  # Reduced from 10
            table.add_column("Stage", width=8, min_width=6)  # Reduced from 10 to 8 (draft/review/approved/released fit)
            table.add_column("Modified", style="dim", width=19, min_width=15)  # Slightly reduced

            for i, p in enumerate(filtered_plans, 1):
                status = "[ACTIVE]" if p.get("active") else ""
                plan_name = str(p["name"])
                features_count = str(p["features"])
                stories_count = str(p["stories"])
                stage = str(p.get("stage", "unknown"))
                modified = str(p["modified"])
                modified_display = modified[:19] if len(modified) > 19 else modified
                table.add_row(
                    f"[bold yellow]{i}[/bold yellow]",
                    status,
                    plan_name,
                    features_count,
                    stories_count,
                    stage,
                    modified_display,
                )

            console.print(table)
            console.print()

            # Handle selection (interactive or non-interactive)
            if no_interactive:
                # Non-interactive mode: select first plan (or error if multiple)
                if len(filtered_plans) == 1:
                    selected_plan = filtered_plans[0]
                    print_info(f"Non-interactive mode: auto-selecting plan '{selected_plan['name']}'")
                else:
                    print_error(
                        f"Non-interactive mode requires exactly one plan, but {len(filtered_plans)} plans match filters"
                    )
                    print_info("Use --current, --last 1, or specify a plan name/number to select a single plan")
                    raise typer.Exit(1)
            else:
                # Interactive selection - prompt for selection
                selection = ""
                try:
                    selection = prompt_text(
                        f"Select a plan by number (1-{len(filtered_plans)}) or 'q' to quit: "
                    ).strip()

                    if selection.lower() in ("q", "quit", ""):
                        print_info("Selection cancelled")
                        raise typer.Exit(0)

                    plan_num = int(selection)
                    if not (1 <= plan_num <= len(filtered_plans)):
                        print_error(f"Invalid selection: {plan_num}. Must be between 1 and {len(filtered_plans)}")
                        raise typer.Exit(1)

                    selected_plan = filtered_plans[plan_num - 1]
                except ValueError:
                    print_error(f"Invalid input: {selection}. Please enter a number.")
                    raise typer.Exit(1) from None
                except KeyboardInterrupt:
                    print_warning("\nSelection cancelled")
                    raise typer.Exit(1) from None

        # Set as active plan
        plan_name = str(selected_plan["name"])
        SpecFactStructure.set_active_plan(plan_name)

        record(
            {
                "plans_available": len(plans),
                "plans_filtered": len(filtered_plans),
                "selected_plan": plan_name,
                "features": selected_plan["features"],
                "stories": selected_plan["stories"],
            }
        )

        print_success(f"Active plan set to: {plan_name}")
        print_info(f"  Features: {selected_plan['features']}")
        print_info(f"  Stories: {selected_plan['stories']}")
        print_info(f"  Stage: {selected_plan.get('stage', 'unknown')}")

        print_info("\nThis plan will now be used as the default for all commands with --bundle option:")
        print_info("  • Plan management: plan compare, plan promote, plan add-feature, plan add-story,")
        print_info("    plan update-idea, plan update-feature, plan update-story, plan review")
        print_info("  • Analysis & generation: import from-code, generate contracts, analyze contracts")
        print_info("  • Synchronization: sync bridge, sync intelligent")
        print_info("  • Enforcement & migration: enforce sdd, migrate to-contracts, drift detect")
        print_info("\n  Use --bundle <name> to override the active plan for any command.")


@app.command("upgrade")
@beartype
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@require(lambda all_plans: isinstance(all_plans, bool), "All plans must be bool")
@require(lambda dry_run: isinstance(dry_run, bool), "Dry run must be bool")
def upgrade(
    # Target/Input
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to specific plan bundle to upgrade (default: active plan)",
    ),
    # Behavior/Options
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be upgraded without making changes",
    ),
    all_plans: bool = typer.Option(
        False,
        "--all",
        help="Upgrade all plan bundles in .specfact/plans/",
    ),
) -> None:
    """
    Upgrade plan bundles to the latest schema version.

    Migrates plan bundles from older schema versions to the current version.
    This ensures compatibility with the latest features and performance optimizations.

    Examples:
        specfact plan upgrade                    # Upgrade active plan
        specfact plan upgrade --plan path/to/plan.bundle.<format>  # Upgrade specific plan
        specfact plan upgrade --all             # Upgrade all plans
        specfact plan upgrade --all --dry-run   # Preview upgrades without changes
    """
    from specfact_cli.migrations.plan_migrator import PlanMigrator, get_current_schema_version
    from specfact_cli.utils.structure import SpecFactStructure

    current_version = get_current_schema_version()
    migrator = PlanMigrator()

    print_section(f"Plan Bundle Upgrade (Schema {current_version})")

    # Determine which plans to upgrade
    plans_to_upgrade: list[Path] = []

    if all_plans:
        # Get all monolithic plan bundles from .specfact/plans/
        plans_dir = Path(".specfact/plans")
        if plans_dir.exists():
            for plan_file in plans_dir.glob("*.bundle.*"):
                if any(str(plan_file).endswith(suffix) for suffix in SpecFactStructure.PLAN_SUFFIXES):
                    plans_to_upgrade.append(plan_file)

        # Also get modular project bundles (though they're already in new format, they might need schema updates)
        projects = SpecFactStructure.list_plans()
        projects_dir = Path(".specfact/projects")
        for project_info in projects:
            bundle_dir = projects_dir / str(project_info["name"])
            manifest_path = bundle_dir / "bundle.manifest.yaml"
            if manifest_path.exists():
                # For modular bundles, we upgrade the manifest file
                plans_to_upgrade.append(manifest_path)
    elif plan:
        # Use specified plan
        if not plan.exists():
            print_error(f"Plan file not found: {plan}")
            raise typer.Exit(1)
        plans_to_upgrade.append(plan)
    else:
        # Use active plan (modular bundle system)
        active_bundle_name = SpecFactStructure.get_active_bundle_name(Path("."))
        if active_bundle_name:
            bundle_dir = SpecFactStructure.project_dir(base_path=Path("."), bundle_name=active_bundle_name)
            if bundle_dir.exists():
                manifest_path = bundle_dir / "bundle.manifest.yaml"
                if manifest_path.exists():
                    plans_to_upgrade.append(manifest_path)
                    print_info(f"Using active plan: {active_bundle_name}")
                else:
                    print_error(f"Bundle manifest not found: {manifest_path}")
                    print_error(f"Bundle directory exists but manifest is missing: {bundle_dir}")
                    raise typer.Exit(1)
            else:
                print_error(f"Active bundle directory not found: {bundle_dir}")
                print_error(f"Active bundle name: {active_bundle_name}")
                raise typer.Exit(1)
        else:
            # Fallback: Try to find default bundle (first bundle in projects directory)
            projects_dir = Path(".specfact/projects")
            if projects_dir.exists():
                bundles = [
                    d.name for d in projects_dir.iterdir() if d.is_dir() and (d / "bundle.manifest.yaml").exists()
                ]
                if bundles:
                    bundle_name = bundles[0]
                    bundle_dir = SpecFactStructure.project_dir(base_path=Path("."), bundle_name=bundle_name)
                    manifest_path = bundle_dir / "bundle.manifest.yaml"
                    plans_to_upgrade.append(manifest_path)
                    print_info(f"Using default bundle: {bundle_name}")
                    print_info(f"Tip: Use 'specfact plan select {bundle_name}' to set as active plan")
                else:
                    print_error("No project bundles found. Use --plan to specify a plan or --all to upgrade all plans.")
                    print_error("Create one with: specfact plan init <bundle-name>")
                    raise typer.Exit(1)
            else:
                print_error("No plan configuration found. Use --plan to specify a plan or --all to upgrade all plans.")
                print_error("Create one with: specfact plan init <bundle-name>")
                raise typer.Exit(1)

    if not plans_to_upgrade:
        print_warning("No plans found to upgrade")
        raise typer.Exit(0)

    # Check and upgrade each plan
    upgraded_count = 0
    skipped_count = 0
    error_count = 0

    for plan_path in plans_to_upgrade:
        try:
            needs_migration, reason = migrator.check_migration_needed(plan_path)
            if not needs_migration:
                print_info(f"✓ {plan_path.name}: {reason}")
                skipped_count += 1
                continue

            if dry_run:
                print_warning(f"Would upgrade: {plan_path.name} ({reason})")
                upgraded_count += 1
            else:
                print_info(f"Upgrading: {plan_path.name} ({reason})...")
                bundle, was_migrated = migrator.load_and_migrate(plan_path, dry_run=False)
                if was_migrated:
                    print_success(f"✓ Upgraded {plan_path.name} to schema {bundle.version}")
                    upgraded_count += 1
                else:
                    print_info(f"✓ {plan_path.name}: Already up to date")
                    skipped_count += 1
        except Exception as e:
            print_error(f"✗ Failed to upgrade {plan_path.name}: {e}")
            error_count += 1

    # Summary
    print()
    if dry_run:
        print_info(f"Dry run complete: {upgraded_count} would be upgraded, {skipped_count} up to date")
    else:
        print_success(f"Upgrade complete: {upgraded_count} upgraded, {skipped_count} up to date")
        if error_count > 0:
            print_warning(f"{error_count} errors occurred")

    if error_count > 0:
        raise typer.Exit(1)


@app.command("sync")
@beartype
@require(lambda repo: repo is None or isinstance(repo, Path), "Repo must be None or Path")
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@require(lambda overwrite: isinstance(overwrite, bool), "Overwrite must be bool")
@require(lambda watch: isinstance(watch, bool), "Watch must be bool")
@require(lambda interval: isinstance(interval, int) and interval >= 1, "Interval must be int >= 1")
def sync(
    # Target/Input
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Path to repository (default: current directory)",
    ),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to SpecFact plan bundle for SpecFact → Spec-Kit conversion (default: active plan)",
    ),
    # Behavior/Options
    shared: bool = typer.Option(
        False,
        "--shared",
        help="Enable shared plans sync (bidirectional sync with Spec-Kit)",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing Spec-Kit artifacts (delete all existing before sync)",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        help="Watch mode for continuous sync",
    ),
    # Advanced/Configuration
    interval: int = typer.Option(
        5,
        "--interval",
        help="Watch interval in seconds (default: 5)",
        min=1,
    ),
) -> None:
    """
    Sync shared plans between Spec-Kit and SpecFact (bidirectional sync).

    This is a convenience wrapper around `specfact sync spec-kit --bidirectional`
    that enables team collaboration through shared structured plans. The bidirectional
    sync keeps Spec-Kit artifacts and SpecFact plans synchronized automatically.

    Shared plans enable:
    - Team collaboration: Multiple developers can work on the same plan
    - Automated sync: Changes in Spec-Kit automatically sync to SpecFact
    - Deviation detection: Compare code vs plan drift automatically
    - Conflict resolution: Automatic conflict detection and resolution

    Example:
        specfact plan sync --shared                    # One-time sync
        specfact plan sync --shared --watch            # Continuous sync
        specfact plan sync --shared --repo ./project   # Sync specific repo
    """
    from specfact_cli.commands.sync import sync_spec_kit
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {
        "shared": shared,
        "watch": watch,
        "overwrite": overwrite,
        "interval": interval,
    }

    with telemetry.track_command("plan.sync", telemetry_metadata) as record:
        if not shared:
            print_error("This command requires --shared flag")
            print_info("Use 'specfact plan sync --shared' to enable shared plans sync")
            print_info("Or use 'specfact sync spec-kit --bidirectional' for direct sync")
            raise typer.Exit(1)

        # Use default repo if not specified
        if repo is None:
            repo = Path(".").resolve()
            print_info(f"Using current directory: {repo}")

        # Use default plan if not specified
        if plan is None:
            plan = SpecFactStructure.get_default_plan_path()
            if not plan.exists():
                print_warning(f"Default plan not found: {plan}")
                print_info("Using default plan path (will be created if needed)")
            else:
                print_info(f"Using active plan: {plan}")

        print_section("Shared Plans Sync")
        console.print("[dim]Bidirectional sync between Spec-Kit and SpecFact for team collaboration[/dim]\n")

        # Call the underlying sync command
        try:
            # Call sync_spec_kit with bidirectional=True
            sync_spec_kit(
                repo=repo,
                bidirectional=True,  # Always bidirectional for shared plans
                plan=plan,
                overwrite=overwrite,
                watch=watch,
                interval=interval,
            )
            record({"sync_completed": True})
        except Exception as e:
            print_error(f"Shared plans sync failed: {e}")
            raise typer.Exit(1) from e


def _validate_stage(value: str) -> str:
    """Validate stage parameter and provide user-friendly error message."""
    valid_stages = ("draft", "review", "approved", "released")
    if value not in valid_stages:
        console.print(f"[bold red]✗[/bold red] Invalid stage: {value}")
        console.print(f"Valid stages: {', '.join(valid_stages)}")
        raise typer.Exit(1)
    return value


@app.command("promote")
@beartype
@require(lambda bundle: isinstance(bundle, str) and len(bundle) > 0, "Bundle name must be non-empty string")
@require(
    lambda stage: stage in ("draft", "review", "approved", "released"),
    "Stage must be draft, review, approved, or released",
)
def promote(
    # Target/Input
    bundle: str | None = typer.Argument(
        None,
        help="Project bundle name (e.g., legacy-api, auth-module). Default: active plan from 'specfact plan select'",
    ),
    stage: str = typer.Option(
        ..., "--stage", callback=_validate_stage, help="Target stage (draft, review, approved, released)"
    ),
    # Behavior/Options
    validate: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Run validation before promotion (default: true)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force promotion even if validation fails (default: false)",
    ),
) -> None:
    """
    Promote a project bundle through development stages.

    Stages: draft → review → approved → released

    **Parameter Groups:**
    - **Target/Input**: bundle (required argument), --stage
    - **Behavior/Options**: --validate/--no-validate, --force

    **Examples:**
        specfact plan promote legacy-api --stage review
        specfact plan promote auth-module --stage approved --validate
        specfact plan promote legacy-api --stage released --force
    """
    import os
    from datetime import datetime

    from rich.console import Console

    from specfact_cli.utils.structure import SpecFactStructure

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(Path("."))
        if bundle is None:
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print("[yellow]→[/yellow] Use --bundle option or run 'specfact plan select' to set active plan")
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")

    telemetry_metadata = {
        "target_stage": stage,
        "validate": validate,
        "force": force,
    }

    with telemetry.track_command("plan.promote", telemetry_metadata) as record:
        # Find bundle directory
        bundle_dir = _find_bundle_dir(bundle)
        if bundle_dir is None:
            raise typer.Exit(1)

        print_section("SpecFact CLI - Plan Promotion")

        try:
            # Load project bundle
            project_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

            # Convert to PlanBundle for compatibility with validation functions
            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

            # Check current stage (ProjectBundle doesn't have metadata.stage, use default)
            current_stage = "draft"  # TODO: Add promotion status to ProjectBundle manifest

            print_info(f"Current stage: {current_stage}")
            print_info(f"Target stage: {stage}")

            # Validate stage progression
            stage_order = {"draft": 0, "review": 1, "approved": 2, "released": 3}
            current_order = stage_order.get(current_stage, 0)
            target_order = stage_order.get(stage, 0)

            if target_order < current_order:
                print_error(f"Cannot promote backward: {current_stage} → {stage}")
                print_error("Only forward promotion is allowed (draft → review → approved → released)")
                raise typer.Exit(1)

            if target_order == current_order:
                print_warning(f"Plan is already at stage: {stage}")
                raise typer.Exit(0)

            # Validate promotion rules
            print_info("Checking promotion rules...")

            # Require SDD manifest for promotion to "review" or higher stages
            if stage in ("review", "approved", "released"):
                print_info("Checking SDD manifest...")
                sdd_valid, sdd_manifest, sdd_report = _validate_sdd_for_bundle(plan_bundle, bundle, require_sdd=True)

                if sdd_manifest is None:
                    print_error("SDD manifest is required for promotion to 'review' or higher stages")
                    console.print("[dim]Run 'specfact plan harden' to create SDD manifest[/dim]")
                    if not force:
                        raise typer.Exit(1)
                    print_warning("Promoting with --force despite missing SDD manifest")
                elif not sdd_valid:
                    print_error("SDD manifest validation failed:")
                    for deviation in sdd_report.deviations:
                        if deviation.severity == DeviationSeverity.HIGH:
                            console.print(f"  [bold red]✗[/bold red] {deviation.description}")
                            console.print(f"     [dim]Fix: {deviation.fix_hint}[/dim]")
                    if sdd_report.high_count > 0:
                        console.print(
                            f"\n[bold red]Cannot promote: {sdd_report.high_count} high severity deviation(s)[/bold red]"
                        )
                        if not force:
                            raise typer.Exit(1)
                        print_warning("Promoting with --force despite SDD validation failures")
                    elif sdd_report.medium_count > 0 or sdd_report.low_count > 0:
                        print_warning(
                            f"SDD has {sdd_report.medium_count} medium and {sdd_report.low_count} low severity deviation(s)"
                        )
                        console.print("[dim]Run 'specfact enforce sdd' for detailed report[/dim]")
                        if not force and not prompt_confirm(
                            "Continue with promotion despite coverage threshold warnings?", default=False
                        ):
                            raise typer.Exit(1)
                else:
                    print_success("SDD manifest validated successfully")
                    if sdd_report.total_deviations > 0:
                        console.print(f"[dim]Found {sdd_report.total_deviations} coverage threshold warning(s)[/dim]")

            # Draft → Review: All features must have at least one story
            if current_stage == "draft" and stage == "review":
                features_without_stories = [f for f in plan_bundle.features if len(f.stories) == 0]
                if features_without_stories:
                    print_error(f"Cannot promote to review: {len(features_without_stories)} feature(s) without stories")
                    console.print("[dim]Features without stories:[/dim]")
                    for f in features_without_stories[:5]:
                        console.print(f"  - {f.key}: {f.title}")
                    if len(features_without_stories) > 5:
                        console.print(f"  ... and {len(features_without_stories) - 5} more")
                    if not force:
                        raise typer.Exit(1)

                # Check coverage status for critical categories
                if validate:
                    from specfact_cli.analyzers.ambiguity_scanner import (
                        AmbiguityScanner,
                        AmbiguityStatus,
                        TaxonomyCategory,
                    )

                    print_info("Checking coverage status...")
                    scanner = AmbiguityScanner()
                    report = scanner.scan(plan_bundle)

                    # Critical categories that block promotion if Missing
                    critical_categories = [
                        TaxonomyCategory.FUNCTIONAL_SCOPE,
                        TaxonomyCategory.FEATURE_COMPLETENESS,
                        TaxonomyCategory.CONSTRAINTS,
                    ]

                    # Important categories that warn if Missing or Partial
                    important_categories = [
                        TaxonomyCategory.DATA_MODEL,
                        TaxonomyCategory.INTEGRATION,
                        TaxonomyCategory.NON_FUNCTIONAL,
                    ]

                    missing_critical: list[TaxonomyCategory] = []
                    missing_important: list[TaxonomyCategory] = []
                    partial_important: list[TaxonomyCategory] = []

                    if report.coverage:
                        for category, status in report.coverage.items():
                            if category in critical_categories and status == AmbiguityStatus.MISSING:
                                missing_critical.append(category)
                            elif category in important_categories:
                                if status == AmbiguityStatus.MISSING:
                                    missing_important.append(category)
                                elif status == AmbiguityStatus.PARTIAL:
                                    partial_important.append(category)

                    # Block promotion if critical categories are Missing
                    if missing_critical:
                        print_error(
                            f"Cannot promote to review: {len(missing_critical)} critical category(ies) are Missing"
                        )
                        console.print("[dim]Missing critical categories:[/dim]")
                        for cat in missing_critical:
                            console.print(f"  - {cat.value}")
                        console.print("\n[dim]Run 'specfact plan review' to resolve these ambiguities[/dim]")
                        if not force:
                            raise typer.Exit(1)

                    # Warn if important categories are Missing or Partial
                    if missing_important or partial_important:
                        print_warning(
                            f"Plan has {len(missing_important)} missing and {len(partial_important)} partial important category(ies)"
                        )
                        if missing_important:
                            console.print("[dim]Missing important categories:[/dim]")
                            for cat in missing_important:
                                console.print(f"  - {cat.value}")
                        if partial_important:
                            console.print("[dim]Partial important categories:[/dim]")
                            for cat in partial_important:
                                console.print(f"  - {cat.value}")
                        if not force:
                            console.print("\n[dim]Consider running 'specfact plan review' to improve coverage[/dim]")
                            console.print("[dim]Use --force to promote anyway[/dim]")
                            if not prompt_confirm(
                                "Continue with promotion despite missing/partial categories?", default=False
                            ):
                                raise typer.Exit(1)

            # Review → Approved: All features must pass validation
            if current_stage == "review" and stage == "approved" and validate:
                # SDD validation is already checked above for "review" or higher stages
                # But we can add additional checks here if needed

                print_info("Validating all features...")
                incomplete_features: list[Feature] = []
                for f in plan_bundle.features:
                    if not f.acceptance:
                        incomplete_features.append(f)
                    for s in f.stories:
                        if not s.acceptance:
                            incomplete_features.append(f)
                            break

                if incomplete_features:
                    print_warning(f"{len(incomplete_features)} feature(s) have incomplete acceptance criteria")
                    if not force:
                        console.print("[dim]Use --force to promote anyway[/dim]")
                        raise typer.Exit(1)

                # Check coverage status for critical categories
                from specfact_cli.analyzers.ambiguity_scanner import (
                    AmbiguityScanner,
                    AmbiguityStatus,
                    TaxonomyCategory,
                )

                print_info("Checking coverage status...")
                scanner_approved = AmbiguityScanner()
                report_approved = scanner_approved.scan(plan_bundle)

                # Critical categories that block promotion if Missing
                critical_categories_approved = [
                    TaxonomyCategory.FUNCTIONAL_SCOPE,
                    TaxonomyCategory.FEATURE_COMPLETENESS,
                    TaxonomyCategory.CONSTRAINTS,
                ]

                missing_critical_approved: list[TaxonomyCategory] = []

                if report_approved.coverage:
                    for category, status in report_approved.coverage.items():
                        if category in critical_categories_approved and status == AmbiguityStatus.MISSING:
                            missing_critical_approved.append(category)

                # Block promotion if critical categories are Missing
                if missing_critical_approved:
                    print_error(
                        f"Cannot promote to approved: {len(missing_critical_approved)} critical category(ies) are Missing"
                    )
                    console.print("[dim]Missing critical categories:[/dim]")
                    for cat in missing_critical_approved:
                        console.print(f"  - {cat.value}")
                    console.print("\n[dim]Run 'specfact plan review' to resolve these ambiguities[/dim]")
                    if not force:
                        raise typer.Exit(1)

            # Approved → Released: All features must be implemented (future check)
            if current_stage == "approved" and stage == "released":
                print_warning("Release promotion: Implementation verification not yet implemented")
                if not force:
                    console.print("[dim]Use --force to promote to released stage[/dim]")
                    raise typer.Exit(1)

            # Run validation if enabled
            if validate:
                print_info("Running validation...")
                validation_result = validate_plan_bundle(plan_bundle)
                if isinstance(validation_result, ValidationReport):
                    if not validation_result.passed:
                        deviation_count = len(validation_result.deviations)
                        print_warning(f"Validation found {deviation_count} issue(s)")
                        if not force:
                            console.print("[dim]Use --force to promote anyway[/dim]")
                            raise typer.Exit(1)
                    else:
                        print_success("Validation passed")
                else:
                    print_success("Validation passed")

            # Update promotion status (TODO: Add promotion status to ProjectBundle manifest)
            print_info(f"Promoting bundle to stage: {stage}")
            promoted_by = (
                os.environ.get("USER") or os.environ.get("USERNAME") or os.environ.get("GIT_AUTHOR_NAME") or "unknown"
            )

            # Save updated project bundle
            # TODO: Update ProjectBundle manifest with promotion status
            # For now, just save the bundle (promotion status will be added in a future update)
            _save_bundle_with_progress(project_bundle, bundle_dir, atomic=True)

            record(
                {
                    "current_stage": current_stage,
                    "target_stage": stage,
                    "features_count": len(plan_bundle.features) if plan_bundle.features else 0,
                }
            )

            # Display summary
            print_success(f"Plan promoted: {current_stage} → {stage}")
            promoted_at = datetime.now(UTC).isoformat()
            console.print(f"[dim]Promoted at: {promoted_at}[/dim]")
            console.print(f"[dim]Promoted by: {promoted_by}[/dim]")

            # Show next steps
            console.print("\n[bold]Next Steps:[/bold]")
            if stage == "review":
                console.print("  • Review plan bundle for completeness")
                console.print("  • Add stories to features if missing")
                console.print("  • Run: specfact plan promote --stage approved")
            elif stage == "approved":
                console.print("  • Plan is approved for implementation")
                console.print("  • Begin feature development")
                console.print("  • Run: specfact plan promote --stage released (after implementation)")
            elif stage == "released":
                console.print("  • Plan is released and should be immutable")
                console.print("  • Create new plan bundle for future changes")

        except Exception as e:
            print_error(f"Failed to promote plan: {e}")
            raise typer.Exit(1) from e


@beartype
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@ensure(lambda result: result is None or isinstance(result, Path), "Must return Path or None")
def _find_plan_path(plan: Path | None) -> Path | None:
    """
    Find plan path (default, latest, or provided).

    Args:
        plan: Provided plan path or None

    Returns:
        Plan path or None if not found
    """
    from specfact_cli.utils.structure import SpecFactStructure

    if plan is not None:
        return plan

    # Try to find active plan or latest
    default_plan = SpecFactStructure.get_default_plan_path()
    if default_plan.exists():
        print_info(f"Using default plan: {default_plan}")
        return default_plan

    # Find latest plan bundle
    base_path = Path(".")
    plans_dir = base_path / SpecFactStructure.PLANS
    if plans_dir.exists():
        plan_files = [
            p
            for p in plans_dir.glob("*.bundle.*")
            if any(str(p).endswith(suffix) for suffix in SpecFactStructure.PLAN_SUFFIXES)
        ]
        plan_files = sorted(plan_files, key=lambda p: p.stat().st_mtime, reverse=True)
        if plan_files:
            print_info(f"Using latest plan: {plan_files[0]}")
            return plan_files[0]
        print_error(f"No plan bundles found in {plans_dir}")
        print_error("Create one with: specfact plan init --interactive")
        return None
    print_error(f"Plans directory not found: {plans_dir}")
    print_error("Create one with: specfact plan init --interactive")
    return None


@beartype
@require(lambda plan: plan is not None and isinstance(plan, Path), "Plan must be non-None Path")
@ensure(lambda result: isinstance(result, tuple) and len(result) == 2, "Must return (bool, PlanBundle | None) tuple")
def _load_and_validate_plan(plan: Path) -> tuple[bool, PlanBundle | None]:
    """
    Load and validate plan bundle.

    Args:
        plan: Path to plan bundle

    Returns:
        Tuple of (is_valid, plan_bundle)
    """
    print_info(f"Loading plan: {plan}")
    validation_result = validate_plan_bundle(plan)
    assert isinstance(validation_result, tuple), "Expected tuple from validate_plan_bundle for Path"
    is_valid, error, bundle = validation_result

    if not is_valid or bundle is None:
        print_error(f"Plan validation failed: {error}")
        return (False, None)

    return (True, bundle)


@beartype
@require(
    lambda bundle, bundle_dir, auto_enrich: isinstance(bundle, PlanBundle)
    and bundle_dir is not None
    and isinstance(bundle_dir, Path),
    "Bundle must be PlanBundle and bundle_dir must be non-None Path",
)
@ensure(lambda result: result is None, "Must return None")
def _handle_auto_enrichment(bundle: PlanBundle, bundle_dir: Path, auto_enrich: bool) -> None:
    """
    Handle auto-enrichment if requested.

    Args:
        bundle: Plan bundle to enrich (converted from ProjectBundle)
        bundle_dir: Project bundle directory
        auto_enrich: Whether to auto-enrich
    """
    if not auto_enrich:
        return

    print_info(
        "Auto-enriching project bundle (enhancing vague acceptance criteria, incomplete requirements, generic tasks)..."
    )
    from specfact_cli.enrichers.plan_enricher import PlanEnricher

    enricher = PlanEnricher()
    enrichment_summary = enricher.enrich_plan(bundle)

    if enrichment_summary["features_updated"] > 0 or enrichment_summary["stories_updated"] > 0:
        # Convert back to ProjectBundle and save

        # Reload to get current state
        project_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)
        # Update features from enriched bundle
        project_bundle.features = {f.key: f for f in bundle.features}
        _save_bundle_with_progress(project_bundle, bundle_dir, atomic=True)
        print_success(
            f"✓ Auto-enriched plan bundle: {enrichment_summary['features_updated']} features, "
            f"{enrichment_summary['stories_updated']} stories updated"
        )
        if enrichment_summary["acceptance_criteria_enhanced"] > 0:
            console.print(
                f"[dim]  - Enhanced {enrichment_summary['acceptance_criteria_enhanced']} acceptance criteria[/dim]"
            )
        if enrichment_summary["requirements_enhanced"] > 0:
            console.print(f"[dim]  - Enhanced {enrichment_summary['requirements_enhanced']} requirements[/dim]")
        if enrichment_summary["tasks_enhanced"] > 0:
            console.print(f"[dim]  - Enhanced {enrichment_summary['tasks_enhanced']} tasks[/dim]")
        if enrichment_summary["changes"]:
            console.print("\n[bold]Changes made:[/bold]")
            for change in enrichment_summary["changes"][:10]:  # Show first 10 changes
                console.print(f"[dim]  - {change}[/dim]")
            if len(enrichment_summary["changes"]) > 10:
                console.print(f"[dim]  ... and {len(enrichment_summary['changes']) - 10} more[/dim]")
    else:
        print_info("No enrichments needed - plan bundle is already well-specified")


@beartype
@require(lambda report: report is not None, "Report must not be None")
@require(
    lambda findings_format: findings_format is None or isinstance(findings_format, str),
    "Findings format must be None or str",
)
@require(lambda is_non_interactive: isinstance(is_non_interactive, bool), "Is non-interactive must be bool")
@ensure(lambda result: result is None, "Must return None")
def _output_findings(
    report: Any,  # AmbiguityReport (imported locally to avoid circular dependency)
    findings_format: str | None,
    is_non_interactive: bool,
    output_path: Path | None = None,
) -> None:
    """
    Output findings in structured format or table.

    Args:
        report: Ambiguity report
        findings_format: Output format (json, yaml, table)
        is_non_interactive: Whether in non-interactive mode
        output_path: Optional file path to save findings. If None, outputs to stdout.
    """
    from rich.console import Console
    from rich.table import Table

    from specfact_cli.analyzers.ambiguity_scanner import AmbiguityStatus

    console = Console()

    # Determine output format
    output_format_str = findings_format
    if not output_format_str:
        # Default: json for non-interactive, table for interactive
        output_format_str = "json" if is_non_interactive else "table"

    output_format_str = output_format_str.lower()

    if output_format_str == "table":
        # Interactive table output
        findings_table = Table(title="Plan Review Findings", show_header=True, header_style="bold magenta")
        findings_table.add_column("Category", style="cyan", no_wrap=True)
        findings_table.add_column("Status", style="yellow")
        findings_table.add_column("Description", style="white")
        findings_table.add_column("Impact", justify="right", style="green")
        findings_table.add_column("Uncertainty", justify="right", style="blue")
        findings_table.add_column("Priority", justify="right", style="bold")

        findings_list = report.findings or []
        for finding in sorted(findings_list, key=lambda f: f.impact * f.uncertainty, reverse=True):
            status_icon = (
                "✅"
                if finding.status == AmbiguityStatus.CLEAR
                else "⚠️"
                if finding.status == AmbiguityStatus.PARTIAL
                else "❌"
            )
            priority = finding.impact * finding.uncertainty
            findings_table.add_row(
                finding.category.value,
                f"{status_icon} {finding.status.value}",
                finding.description[:80] + "..." if len(finding.description) > 80 else finding.description,
                f"{finding.impact:.2f}",
                f"{finding.uncertainty:.2f}",
                f"{priority:.2f}",
            )

        console.print("\n")
        console.print(findings_table)

        # Also show coverage summary
        if report.coverage:
            from specfact_cli.analyzers.ambiguity_scanner import TaxonomyCategory

            console.print("\n[bold]Coverage Summary:[/bold]")
            # Count findings per category by status
            total_findings_by_category: dict[TaxonomyCategory, int] = {}
            clear_findings_by_category: dict[TaxonomyCategory, int] = {}
            partial_findings_by_category: dict[TaxonomyCategory, int] = {}
            for finding in findings_list:
                cat = finding.category
                total_findings_by_category[cat] = total_findings_by_category.get(cat, 0) + 1
                # Count by finding status
                if finding.status == AmbiguityStatus.CLEAR:
                    clear_findings_by_category[cat] = clear_findings_by_category.get(cat, 0) + 1
                elif finding.status == AmbiguityStatus.PARTIAL:
                    partial_findings_by_category[cat] = partial_findings_by_category.get(cat, 0) + 1

            for cat, status in report.coverage.items():
                status_icon = (
                    "✅" if status == AmbiguityStatus.CLEAR else "⚠️" if status == AmbiguityStatus.PARTIAL else "❌"
                )
                total = total_findings_by_category.get(cat, 0)
                clear_count = clear_findings_by_category.get(cat, 0)
                partial_count = partial_findings_by_category.get(cat, 0)
                # Show format based on status:
                # - Clear: If no findings (total=0), just show status. Otherwise show clear_count/total
                # - Partial: Show partial_count/total (count of findings with PARTIAL status = unclear findings)
                if status == AmbiguityStatus.CLEAR:
                    if total == 0:
                        # No findings - just show status without counts
                        console.print(f"  {status_icon} {cat.value}: {status.value}")
                    else:
                        console.print(f"  {status_icon} {cat.value}: {clear_count}/{total} {status.value}")
                elif status == AmbiguityStatus.PARTIAL:
                    # Show count of partial (unclear) findings
                    # If all are unclear, just show the count without the fraction
                    if partial_count == total:
                        console.print(f"  {status_icon} {cat.value}: {partial_count} {status.value}")
                    else:
                        console.print(f"  {status_icon} {cat.value}: {partial_count}/{total} {status.value}")
                else:  # MISSING
                    console.print(f"  {status_icon} {cat.value}: {status.value}")

    elif output_format_str in ("json", "yaml"):
        # Structured output (JSON or YAML)
        findings_data = {
            "findings": [
                {
                    "category": f.category.value,
                    "status": f.status.value,
                    "description": f.description,
                    "impact": f.impact,
                    "uncertainty": f.uncertainty,
                    "priority": f.impact * f.uncertainty,
                    "question": f.question,
                    "related_sections": f.related_sections or [],
                }
                for f in (report.findings or [])
            ],
            "coverage": {cat.value: status.value for cat, status in (report.coverage or {}).items()},
            "total_findings": len(report.findings or []),
            "priority_score": report.priority_score,
        }

        import sys

        if output_format_str == "json":
            formatted_output = json.dumps(findings_data, indent=2) + "\n"
        else:  # yaml
            from ruamel.yaml import YAML

            yaml = YAML()
            yaml.default_flow_style = False
            yaml.preserve_quotes = True
            from io import StringIO

            output = StringIO()
            yaml.dump(findings_data, output)
            formatted_output = output.getvalue()

        if output_path:
            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(formatted_output, encoding="utf-8")
            from rich.console import Console

            console = Console()
            console.print(f"[green]✓[/green] Findings saved to: {output_path}")
        else:
            # Output to stdout
            sys.stdout.write(formatted_output)
            sys.stdout.flush()
    else:
        print_error(f"Invalid findings format: {findings_format}. Must be 'json', 'yaml', or 'table'")
        raise typer.Exit(1)


@beartype
@require(lambda bundle: isinstance(bundle, PlanBundle), "Bundle must be PlanBundle")
@require(lambda bundle: bundle is not None, "Bundle must not be None")
@ensure(lambda result: isinstance(result, int), "Must return int")
def _deduplicate_features(bundle: PlanBundle) -> int:
    """
    Deduplicate features by normalized key (clean up duplicates from previous syncs).

    Uses prefix matching to handle abbreviated vs full names (e.g., IDEINTEGRATION vs IDEINTEGRATIONSYSTEM).

    Args:
        bundle: Plan bundle to deduplicate

    Returns:
        Number of duplicates removed
    """
    from specfact_cli.utils.feature_keys import normalize_feature_key

    seen_normalized_keys: set[str] = set()
    deduplicated_features: list[Feature] = []

    for existing_feature in bundle.features:
        normalized_key = normalize_feature_key(existing_feature.key)

        # Check for exact match first
        if normalized_key in seen_normalized_keys:
            continue

        # Check for prefix match (abbreviated vs full names)
        # e.g., IDEINTEGRATION vs IDEINTEGRATIONSYSTEM
        # Only match if shorter is a PREFIX of longer with significant length difference
        # AND at least one key has a numbered prefix (041_, 042-, etc.) indicating Spec-Kit origin
        # This avoids false positives like SMARTCOVERAGE vs SMARTCOVERAGEMANAGER (both from code analysis)
        matched = False
        for seen_key in seen_normalized_keys:
            shorter = min(normalized_key, seen_key, key=len)
            longer = max(normalized_key, seen_key, key=len)

            # Check if at least one of the original keys has a numbered prefix (Spec-Kit format)
            import re

            has_speckit_key = bool(
                re.match(r"^\d{3}[_-]", existing_feature.key)
                or any(
                    re.match(r"^\d{3}[_-]", f.key)
                    for f in deduplicated_features
                    if normalize_feature_key(f.key) == seen_key
                )
            )

            # More conservative matching:
            # 1. At least one key must have numbered prefix (Spec-Kit origin)
            # 2. Shorter must be at least 10 chars
            # 3. Longer must start with shorter (prefix match)
            # 4. Length difference must be at least 6 chars
            # 5. Shorter must be < 75% of longer (to ensure significant difference)
            length_diff = len(longer) - len(shorter)
            length_ratio = len(shorter) / len(longer) if len(longer) > 0 else 1.0

            if (
                has_speckit_key
                and len(shorter) >= 10
                and longer.startswith(shorter)
                and length_diff >= 6
                and length_ratio < 0.75
            ):
                matched = True
                # Prefer the longer (full) name - update the existing feature's key if needed
                if len(normalized_key) > len(seen_key):
                    # Current feature has longer name - update the existing one
                    for dedup_feature in deduplicated_features:
                        if normalize_feature_key(dedup_feature.key) == seen_key:
                            dedup_feature.key = existing_feature.key
                            break
                break

        if not matched:
            seen_normalized_keys.add(normalized_key)
            deduplicated_features.append(existing_feature)

    duplicates_removed = len(bundle.features) - len(deduplicated_features)
    if duplicates_removed > 0:
        bundle.features = deduplicated_features

    return duplicates_removed


@beartype
@require(lambda bundle: isinstance(bundle, PlanBundle), "Bundle must be PlanBundle")
@require(
    lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty string"
)
@require(lambda project_hash: project_hash is None or isinstance(project_hash, str), "Project hash must be None or str")
@ensure(
    lambda result: isinstance(result, tuple) and len(result) == 3,
    "Must return (bool, SDDManifest | None, ValidationReport) tuple",
)
def _validate_sdd_for_bundle(
    bundle: PlanBundle, bundle_name: str, require_sdd: bool = False, project_hash: str | None = None
) -> tuple[bool, SDDManifest | None, ValidationReport]:
    """
    Validate SDD manifest for project bundle.

    Args:
        bundle: Plan bundle to validate (converted from ProjectBundle)
        bundle_name: Project bundle name
        require_sdd: If True, return False if SDD is missing (for promotion gates)
        project_hash: Optional hash computed from ProjectBundle BEFORE modifications (for consistency with plan harden)

    Returns:
        Tuple of (is_valid, sdd_manifest, validation_report)
    """
    from specfact_cli.models.deviation import Deviation, DeviationSeverity, ValidationReport
    from specfact_cli.models.sdd import SDDManifest

    report = ValidationReport()
    # Find SDD using discovery utility
    from specfact_cli.utils.sdd_discovery import find_sdd_for_bundle

    base_path = Path.cwd()
    sdd_path = find_sdd_for_bundle(bundle_name, base_path)

    # Check if SDD manifest exists
    if sdd_path is None:
        if require_sdd:
            deviation = Deviation(
                type=DeviationType.COVERAGE_THRESHOLD,
                severity=DeviationSeverity.HIGH,
                description="SDD manifest is required for plan promotion but not found",
                location=str(sdd_path),
                fix_hint=f"Run 'specfact plan harden {bundle_name}' to create SDD manifest",
            )
            report.add_deviation(deviation)
            return (False, None, report)
        # SDD not required, just return None
        return (True, None, report)

    # Load SDD manifest
    try:
        sdd_data = load_structured_file(sdd_path)
        sdd_manifest = SDDManifest.model_validate(sdd_data)
    except Exception as e:
        deviation = Deviation(
            type=DeviationType.COVERAGE_THRESHOLD,
            severity=DeviationSeverity.HIGH,
            description=f"Failed to load SDD manifest: {e}",
            location=str(sdd_path),
            fix_hint=f"Run 'specfact plan harden {bundle_name}' to recreate SDD manifest",
        )
        report.add_deviation(deviation)
        return (False, None, report)

    # Validate hash match
    # IMPORTANT: Use project_hash if provided (computed from ProjectBundle BEFORE modifications)
    # This ensures consistency with plan harden which computes hash from ProjectBundle.
    # If not provided, fall back to computing from PlanBundle (for backward compatibility).
    if project_hash:
        bundle_hash = project_hash
    else:
        bundle.update_summary(include_hash=True)
        bundle_hash = bundle.metadata.summary.content_hash if bundle.metadata and bundle.metadata.summary else None

    if bundle_hash and sdd_manifest.plan_bundle_hash != bundle_hash:
        deviation = Deviation(
            type=DeviationType.HASH_MISMATCH,
            severity=DeviationSeverity.HIGH,
            description=f"SDD bundle hash mismatch: expected {bundle_hash[:16]}..., got {sdd_manifest.plan_bundle_hash[:16]}...",
            location=str(sdd_path),
            fix_hint=f"Run 'specfact plan harden {bundle_name}' to update SDD manifest",
        )
        report.add_deviation(deviation)
        return (False, sdd_manifest, report)

    # Validate coverage thresholds
    from specfact_cli.validators.contract_validator import calculate_contract_density, validate_contract_density

    metrics = calculate_contract_density(sdd_manifest, bundle)
    density_deviations = validate_contract_density(sdd_manifest, bundle, metrics)
    for deviation in density_deviations:
        report.add_deviation(deviation)

    is_valid = report.total_deviations == 0
    return (is_valid, sdd_manifest, report)


def _validate_sdd_for_plan(
    bundle: PlanBundle, plan_path: Path, require_sdd: bool = False
) -> tuple[bool, SDDManifest | None, ValidationReport]:
    """
    Validate SDD manifest for plan bundle.

    Args:
        bundle: Plan bundle to validate
        plan_path: Path to plan bundle
        require_sdd: If True, return False if SDD is missing (for promotion gates)

    Returns:
        Tuple of (is_valid, sdd_manifest, validation_report)
    """
    from specfact_cli.models.deviation import Deviation, DeviationSeverity, ValidationReport
    from specfact_cli.models.sdd import SDDManifest
    from specfact_cli.utils.structure import SpecFactStructure

    report = ValidationReport()
    # Construct bundle-specific SDD path (Phase 8.5+)
    base_path = Path.cwd()
    if not plan_path.is_dir():
        print_error(
            "Legacy monolithic plan detected. Please migrate to bundle directories via 'specfact migrate artifacts --repo .'."
        )
        raise typer.Exit(1)
    bundle_name = plan_path.name
    from specfact_cli.utils.structured_io import StructuredFormat

    sdd_path = SpecFactStructure.get_bundle_sdd_path(bundle_name, base_path, StructuredFormat.YAML)
    if not sdd_path.exists():
        sdd_path = SpecFactStructure.get_bundle_sdd_path(bundle_name, base_path, StructuredFormat.JSON)

    # Check if SDD manifest exists
    if not sdd_path.exists():
        if require_sdd:
            deviation = Deviation(
                type=DeviationType.COVERAGE_THRESHOLD,
                severity=DeviationSeverity.HIGH,
                description="SDD manifest is required for plan promotion but not found",
                location=".specfact/projects/<bundle>/sdd.yaml",
                fix_hint="Run 'specfact plan harden' to create SDD manifest",
            )
            report.add_deviation(deviation)
            return (False, None, report)
        # SDD not required, just return None
        return (True, None, report)

    # Load SDD manifest
    try:
        sdd_data = load_structured_file(sdd_path)
        sdd_manifest = SDDManifest.model_validate(sdd_data)
    except Exception as e:
        deviation = Deviation(
            type=DeviationType.COVERAGE_THRESHOLD,
            severity=DeviationSeverity.HIGH,
            description=f"Failed to load SDD manifest: {e}",
            location=str(sdd_path),
            fix_hint="Run 'specfact plan harden' to regenerate SDD manifest",
        )
        report.add_deviation(deviation)
        return (False, None, report)

    # Validate hash match
    bundle.update_summary(include_hash=True)
    plan_hash = bundle.metadata.summary.content_hash if bundle.metadata and bundle.metadata.summary else None

    if not plan_hash:
        deviation = Deviation(
            type=DeviationType.COVERAGE_THRESHOLD,
            severity=DeviationSeverity.HIGH,
            description="Failed to compute plan bundle hash",
            location=str(plan_path),
            fix_hint="Plan bundle may be corrupted",
        )
        report.add_deviation(deviation)
        return (False, sdd_manifest, report)

    if sdd_manifest.plan_bundle_hash != plan_hash:
        deviation = Deviation(
            type=DeviationType.HASH_MISMATCH,
            severity=DeviationSeverity.HIGH,
            description=f"SDD plan bundle hash mismatch: expected {plan_hash[:16]}..., got {sdd_manifest.plan_bundle_hash[:16]}...",
            location=".specfact/projects/<bundle>/sdd.yaml",
            fix_hint="Run 'specfact plan harden' to update SDD manifest with current plan hash",
        )
        report.add_deviation(deviation)
        return (False, sdd_manifest, report)

    # Validate coverage thresholds using contract validator
    from specfact_cli.validators.contract_validator import calculate_contract_density, validate_contract_density

    metrics = calculate_contract_density(sdd_manifest, bundle)
    density_deviations = validate_contract_density(sdd_manifest, bundle, metrics)

    for deviation in density_deviations:
        report.add_deviation(deviation)

    # Valid if no HIGH severity deviations
    is_valid = report.high_count == 0
    return (is_valid, sdd_manifest, report)


@beartype
@require(lambda project_bundle: isinstance(project_bundle, ProjectBundle), "Project bundle must be ProjectBundle")
@require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle dir must be Path")
@require(lambda bundle_name: isinstance(bundle_name, str), "Bundle name must be str")
@require(lambda auto_enrich: isinstance(auto_enrich, bool), "Auto enrich must be bool")
@ensure(lambda result: isinstance(result, tuple) and len(result) == 2, "Must return tuple of PlanBundle and str")
def _prepare_review_bundle(
    project_bundle: ProjectBundle, bundle_dir: Path, bundle_name: str, auto_enrich: bool
) -> tuple[PlanBundle, str]:
    """
    Prepare plan bundle for review.

    Args:
        project_bundle: Loaded project bundle
        bundle_dir: Path to bundle directory
        bundle_name: Bundle name
        auto_enrich: Whether to auto-enrich the bundle

    Returns:
        Tuple of (plan_bundle, current_stage)
    """
    # Compute hash from ProjectBundle BEFORE any modifications (same as plan harden does)
    # This ensures hash consistency with SDD manifest created by plan harden
    project_summary = project_bundle.compute_summary(include_hash=True)
    project_hash = project_summary.content_hash
    if not project_hash:
        print_warning("Failed to compute project bundle hash for SDD validation")

    # Convert to PlanBundle for compatibility with review functions
    plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

    # Deduplicate features by normalized key (clean up duplicates from previous syncs)
    duplicates_removed = _deduplicate_features(plan_bundle)
    if duplicates_removed > 0:
        # Convert back to ProjectBundle and save
        # Update project bundle with deduplicated features
        project_bundle.features = {f.key: f for f in plan_bundle.features}
        _save_bundle_with_progress(project_bundle, bundle_dir, atomic=True)
        print_success(f"✓ Removed {duplicates_removed} duplicate features from project bundle")

    # Check current stage (ProjectBundle doesn't have metadata.stage, use default)
    current_stage = "draft"  # TODO: Add promotion status to ProjectBundle manifest

    print_info(f"Current stage: {current_stage}")

    # Validate SDD manifest (warn if missing, validate thresholds if present)
    # Pass project_hash computed BEFORE modifications to ensure consistency
    print_info("Checking SDD manifest...")
    sdd_valid, sdd_manifest, sdd_report = _validate_sdd_for_bundle(
        plan_bundle, bundle_name, require_sdd=False, project_hash=project_hash
    )

    if sdd_manifest is None:
        print_warning("SDD manifest not found. Consider running 'specfact plan harden' to create one.")
        from rich.console import Console

        console = Console()
        console.print("[dim]SDD manifest is recommended for plan review and promotion[/dim]")
    elif not sdd_valid:
        print_warning("SDD manifest validation failed:")
        from rich.console import Console

        from specfact_cli.models.deviation import DeviationSeverity

        console = Console()
        for deviation in sdd_report.deviations:
            if deviation.severity == DeviationSeverity.HIGH:
                console.print(f"  [bold red]✗[/bold red] {deviation.description}")
            elif deviation.severity == DeviationSeverity.MEDIUM:
                console.print(f"  [bold yellow]⚠[/bold yellow] {deviation.description}")
            else:
                console.print(f"  [dim]ℹ[/dim] {deviation.description}")
        console.print("\n[dim]Run 'specfact enforce sdd' for detailed validation report[/dim]")
    else:
        print_success("SDD manifest validated successfully")

        # Display contract density metrics
        from rich.console import Console

        from specfact_cli.validators.contract_validator import calculate_contract_density

        console = Console()
        metrics = calculate_contract_density(sdd_manifest, plan_bundle)
        thresholds = sdd_manifest.coverage_thresholds

        console.print("\n[bold]Contract Density Metrics:[/bold]")
        console.print(
            f"  Contracts/story: {metrics.contracts_per_story:.2f} (threshold: {thresholds.contracts_per_story})"
        )
        console.print(
            f"  Invariants/feature: {metrics.invariants_per_feature:.2f} (threshold: {thresholds.invariants_per_feature})"
        )
        console.print(
            f"  Architecture facets: {metrics.architecture_facets} (threshold: {thresholds.architecture_facets})"
        )

        if sdd_report.total_deviations > 0:
            console.print(f"\n[dim]Found {sdd_report.total_deviations} coverage threshold warning(s)[/dim]")
            console.print("[dim]Run 'specfact enforce sdd' for detailed report[/dim]")

    # Initialize clarifications if needed
    from specfact_cli.models.plan import Clarifications

    if plan_bundle.clarifications is None:
        plan_bundle.clarifications = Clarifications(sessions=[])

    # Auto-enrich if requested (before scanning for ambiguities)
    _handle_auto_enrichment(plan_bundle, bundle_dir, auto_enrich)

    return (plan_bundle, current_stage)


@beartype
@require(lambda plan_bundle: isinstance(plan_bundle, PlanBundle), "Plan bundle must be PlanBundle")
@require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle dir must be Path")
@require(lambda category: category is None or isinstance(category, str), "Category must be None or str")
@require(lambda max_questions: max_questions > 0, "Max questions must be positive")
@ensure(
    lambda result: isinstance(result, tuple) and len(result) == 3 and isinstance(result[0], list),
    "Must return tuple of questions, report, scanner",
)
def _scan_and_prepare_questions(
    plan_bundle: PlanBundle, bundle_dir: Path, category: str | None, max_questions: int
) -> tuple[list[tuple[Any, str]], Any, Any]:  # Returns (questions_to_ask, report, scanner)
    """
    Scan plan bundle and prepare questions for review.

    Args:
        plan_bundle: Plan bundle to scan
        bundle_dir: Bundle directory path (for finding repo path)
        category: Optional category filter
        max_questions: Maximum questions to prepare

    Returns:
        Tuple of (questions_to_ask, report, scanner)
    """
    from specfact_cli.analyzers.ambiguity_scanner import (
        AmbiguityScanner,
        TaxonomyCategory,
    )

    # Scan for ambiguities
    print_info("Scanning plan bundle for ambiguities...")
    # Try to find repo path from bundle directory (go up to find .specfact parent, then repo root)
    repo_path: Path | None = None
    if bundle_dir.exists():
        # bundle_dir is typically .specfact/projects/<bundle-name>
        # Go up to .specfact, then up to repo root
        specfact_dir = bundle_dir.parent.parent if bundle_dir.parent.name == "projects" else bundle_dir.parent
        if specfact_dir.name == ".specfact" and specfact_dir.parent.exists():
            repo_path = specfact_dir.parent
        else:
            # Fallback: try current directory
            repo_path = Path(".")
    else:
        repo_path = Path(".")

    scanner = AmbiguityScanner(repo_path=repo_path)
    report = scanner.scan(plan_bundle)

    # Filter by category if specified
    if category:
        try:
            target_category = TaxonomyCategory(category)
            if report.findings:
                report.findings = [f for f in report.findings if f.category == target_category]
        except ValueError:
            print_warning(f"Unknown category: {category}, ignoring filter")
            category = None

    # Prioritize questions by (Impact x Uncertainty)
    findings_list = report.findings or []
    prioritized_findings = sorted(
        findings_list,
        key=lambda f: f.impact * f.uncertainty,
        reverse=True,
    )

    # Filter out findings that already have clarifications
    existing_question_ids = set()
    if plan_bundle.clarifications:
        for session in plan_bundle.clarifications.sessions:
            for q in session.questions:
                existing_question_ids.add(q.id)

    # Generate question IDs and filter
    question_counter = 1
    candidate_questions: list[tuple[Any, str]] = []
    for finding in prioritized_findings:
        if finding.question:
            # Skip to next available question ID if current one is already used
            while (question_id := f"Q{question_counter:03d}") in existing_question_ids:
                question_counter += 1
            # Generate question ID and add if not already answered
            candidate_questions.append((finding, question_id))
            question_counter += 1

    # Limit to max_questions
    questions_to_ask = candidate_questions[:max_questions]

    return (questions_to_ask, report, scanner)


@beartype
@require(lambda questions_to_ask: isinstance(questions_to_ask, list), "Questions must be list")
@require(lambda report: report is not None, "Report must not be None")
@ensure(lambda result: result is None, "Must return None")
def _handle_no_questions_case(
    questions_to_ask: list[tuple[Any, str]],
    report: Any,  # AmbiguityReport
) -> None:
    """
    Handle case when there are no questions to ask.

    Args:
        questions_to_ask: List of questions (should be empty)
        report: Ambiguity report
    """
    from rich.console import Console

    from specfact_cli.analyzers.ambiguity_scanner import AmbiguityStatus, TaxonomyCategory

    console = Console()

    # Check coverage status to determine if plan is truly ready for promotion
    critical_categories = [
        TaxonomyCategory.FUNCTIONAL_SCOPE,
        TaxonomyCategory.FEATURE_COMPLETENESS,
        TaxonomyCategory.CONSTRAINTS,
    ]

    missing_critical: list[TaxonomyCategory] = []
    if report.coverage:
        for category, status in report.coverage.items():
            if category in critical_categories and status == AmbiguityStatus.MISSING:
                missing_critical.append(category)

    # Count total findings per category (shared for both branches)
    total_findings_by_category: dict[TaxonomyCategory, int] = {}
    if report.findings:
        for finding in report.findings:
            cat = finding.category
            total_findings_by_category[cat] = total_findings_by_category.get(cat, 0) + 1

    if missing_critical:
        print_warning(
            f"Plan has {len(missing_critical)} critical category(ies) marked as Missing, but no high-priority questions remain"
        )
        console.print("[dim]Missing critical categories:[/dim]")
        for cat in missing_critical:
            console.print(f"  - {cat.value}")
        console.print("\n[bold]Coverage Summary:[/bold]")
        if report.coverage:
            for cat, status in report.coverage.items():
                status_icon = (
                    "✅" if status == AmbiguityStatus.CLEAR else "⚠️" if status == AmbiguityStatus.PARTIAL else "❌"
                )
                total = total_findings_by_category.get(cat, 0)
                # Count findings by status
                clear_count = sum(
                    1 for f in (report.findings or []) if f.category == cat and f.status == AmbiguityStatus.CLEAR
                )
                partial_count = sum(
                    1 for f in (report.findings or []) if f.category == cat and f.status == AmbiguityStatus.PARTIAL
                )
                # Show format based on status:
                # - Clear: If no findings (total=0), just show status. Otherwise show clear_count/total
                # - Partial: Show partial_count/total (count of findings with PARTIAL status)
                if status == AmbiguityStatus.CLEAR:
                    if total == 0:
                        # No findings - just show status without counts
                        console.print(f"  {status_icon} {cat.value}: {status.value}")
                    else:
                        console.print(f"  {status_icon} {cat.value}: {clear_count}/{total} {status.value}")
                elif status == AmbiguityStatus.PARTIAL:
                    console.print(f"  {status_icon} {cat.value}: {partial_count}/{total} {status.value}")
                else:  # MISSING
                    console.print(f"  {status_icon} {cat.value}: {status.value}")
        console.print(
            "\n[bold]⚠️ Warning:[/bold] Plan may not be ready for promotion due to missing critical categories"
        )
        console.print("[dim]Consider addressing these categories before promoting[/dim]")
    else:
        print_success("No critical ambiguities detected. Plan is ready for promotion.")
        console.print("\n[bold]Coverage Summary:[/bold]")
        if report.coverage:
            for cat, status in report.coverage.items():
                status_icon = (
                    "✅" if status == AmbiguityStatus.CLEAR else "⚠️" if status == AmbiguityStatus.PARTIAL else "❌"
                )
                total = total_findings_by_category.get(cat, 0)
                # Count findings by status
                clear_count = sum(
                    1 for f in (report.findings or []) if f.category == cat and f.status == AmbiguityStatus.CLEAR
                )
                partial_count = sum(
                    1 for f in (report.findings or []) if f.category == cat and f.status == AmbiguityStatus.PARTIAL
                )
                # Show format based on status:
                # - Clear: If no findings (total=0), just show status. Otherwise show clear_count/total
                # - Partial: Show partial_count/total (count of findings with PARTIAL status)
                if status == AmbiguityStatus.CLEAR:
                    if total == 0:
                        # No findings - just show status without counts
                        console.print(f"  {status_icon} {cat.value}: {status.value}")
                    else:
                        console.print(f"  {status_icon} {cat.value}: {clear_count}/{total} {status.value}")
                elif status == AmbiguityStatus.PARTIAL:
                    console.print(f"  {status_icon} {cat.value}: {partial_count}/{total} {status.value}")
                else:  # MISSING
                    console.print(f"  {status_icon} {cat.value}: {status.value}")

    return


@beartype
@require(lambda questions_to_ask: isinstance(questions_to_ask, list), "Questions must be list")
@ensure(lambda result: result is None, "Must return None")
def _handle_list_questions_mode(questions_to_ask: list[tuple[Any, str]], output_path: Path | None = None) -> None:
    """
    Handle --list-questions mode by outputting questions as JSON.

    Args:
        questions_to_ask: List of (finding, question_id) tuples
        output_path: Optional file path to save questions. If None, outputs to stdout.
    """
    import json
    import sys

    questions_json = []
    for finding, question_id in questions_to_ask:
        questions_json.append(
            {
                "id": question_id,
                "category": finding.category.value,
                "question": finding.question,
                "impact": finding.impact,
                "uncertainty": finding.uncertainty,
                "related_sections": finding.related_sections or [],
            }
        )

    json_output = json.dumps({"questions": questions_json, "total": len(questions_json)}, indent=2)

    if output_path:
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_output + "\n", encoding="utf-8")
        from rich.console import Console

        console = Console()
        console.print(f"[green]✓[/green] Questions saved to: {output_path}")
    else:
        # Output JSON to stdout (for Copilot mode parsing)
        sys.stdout.write(json_output)
        sys.stdout.write("\n")
        sys.stdout.flush()

    return


@beartype
@require(lambda answers: isinstance(answers, str), "Answers must be string")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def _parse_answers_dict(answers: str) -> dict[str, str]:
    """
    Parse --answers JSON string or file path.

    Args:
        answers: JSON string or file path

    Returns:
        Dictionary mapping question_id -> answer
    """
    import json

    try:
        # Try to parse as JSON string first
        try:
            answers_dict = json.loads(answers)
        except json.JSONDecodeError:
            # If JSON parsing fails, try as file path
            answers_path = Path(answers)
            if answers_path.exists() and answers_path.is_file():
                answers_dict = json.loads(answers_path.read_text())
            else:
                raise ValueError(f"Invalid JSON string and file not found: {answers}") from None

        if not isinstance(answers_dict, dict):
            print_error("--answers must be a JSON object with question_id -> answer mappings")
            raise typer.Exit(1)
        return answers_dict
    except (json.JSONDecodeError, ValueError) as e:
        print_error(f"Invalid JSON in --answers: {e}")
        raise typer.Exit(1) from e


@beartype
@require(lambda plan_bundle: isinstance(plan_bundle, PlanBundle), "Plan bundle must be PlanBundle")
@require(lambda questions_to_ask: isinstance(questions_to_ask, list), "Questions must be list")
@require(lambda answers_dict: isinstance(answers_dict, dict), "Answers dict must be dict")
@require(lambda is_non_interactive: isinstance(is_non_interactive, bool), "Is non-interactive must be bool")
@require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle dir must be Path")
@require(lambda project_bundle: isinstance(project_bundle, ProjectBundle), "Project bundle must be ProjectBundle")
@ensure(lambda result: isinstance(result, int), "Must return int")
def _ask_questions_interactive(
    plan_bundle: PlanBundle,
    questions_to_ask: list[tuple[Any, str]],
    answers_dict: dict[str, str],
    is_non_interactive: bool,
    bundle_dir: Path,
    project_bundle: ProjectBundle,
) -> int:
    """
    Ask questions interactively and integrate answers.

    Args:
        plan_bundle: Plan bundle to update
        questions_to_ask: List of (finding, question_id) tuples
        answers_dict: Pre-provided answers dict (may be empty)
        is_non_interactive: Whether in non-interactive mode
        bundle_dir: Bundle directory path
        project_bundle: Project bundle to save

    Returns:
        Number of questions asked
    """
    from datetime import date, datetime

    from rich.console import Console

    from specfact_cli.models.plan import Clarification, ClarificationSession

    console = Console()

    # Create or get today's session
    today = date.today().isoformat()
    today_session: ClarificationSession | None = None
    if plan_bundle.clarifications:
        for session in plan_bundle.clarifications.sessions:
            if session.date == today:
                today_session = session
                break

    if today_session is None:
        today_session = ClarificationSession(date=today, questions=[])
        if plan_bundle.clarifications:
            plan_bundle.clarifications.sessions.append(today_session)

    # Ask questions sequentially
    questions_asked = 0
    for finding, question_id in questions_to_ask:
        questions_asked += 1

        # Get answer (interactive or from --answers)
        if question_id in answers_dict:
            # Non-interactive: use provided answer
            answer = answers_dict[question_id]
            if not isinstance(answer, str) or not answer.strip():
                print_error(f"Answer for {question_id} must be a non-empty string")
                raise typer.Exit(1)
            console.print(f"\n[bold cyan]Question {questions_asked}/{len(questions_to_ask)}[/bold cyan]")
            console.print(f"[dim]Category: {finding.category.value}[/dim]")
            console.print(f"[bold]Q: {finding.question}[/bold]")
            console.print(f"[dim]Answer (from --answers): {answer}[/dim]")
            default_value = None
        else:
            # Interactive: prompt user
            if is_non_interactive:
                # In non-interactive mode without --answers, skip this question
                print_warning(f"Skipping {question_id}: no answer provided in non-interactive mode")
                continue

            console.print(f"\n[bold cyan]Question {questions_asked}/{len(questions_to_ask)}[/bold cyan]")
            console.print(f"[dim]Category: {finding.category.value}[/dim]")
            console.print(f"[bold]Q: {finding.question}[/bold]")

            # Show current settings for related sections before asking and get default value
            default_value = _show_current_settings_for_finding(plan_bundle, finding, console_instance=console)

            # Get answer from user with smart Yes/No handling (with default to confirm existing)
            answer = _get_smart_answer(finding, plan_bundle, is_non_interactive, default_value=default_value)

        # Validate answer length (warn if too long, but only if user typed something new)
        # Don't warn if user confirmed existing default value
        # Check if answer matches default (normalize whitespace for comparison)
        is_confirmed_default = False
        if default_value:
            # Normalize both for comparison (strip and compare)
            answer_normalized = answer.strip()
            default_normalized = default_value.strip()
            # Check exact match or if answer is empty and we have default (Enter pressed)
            is_confirmed_default = answer_normalized == default_normalized or (
                not answer_normalized and default_normalized
            )
        if not is_confirmed_default and len(answer.split()) > 5:
            print_warning("Answer is longer than 5 words. Consider a shorter, more focused answer.")

        # Integrate answer into plan bundle
        integration_points = _integrate_clarification(plan_bundle, finding, answer)

        # Create clarification record
        clarification = Clarification(
            id=question_id,
            category=finding.category.value,
            question=finding.question or "",
            answer=answer,
            integrated_into=integration_points,
            timestamp=datetime.now(UTC).isoformat(),
        )

        today_session.questions.append(clarification)

        # Answer integrated into bundle (will save at end for performance)
        print_success("Answer recorded and integrated into plan bundle")

        # Ask if user wants to continue (only in interactive mode)
        if (
            not is_non_interactive
            and questions_asked < len(questions_to_ask)
            and not prompt_confirm("Continue to next question?", default=True)
        ):
            break

    # Save project bundle once at the end (more efficient than saving after each question)
    # Update existing project_bundle in memory (no need to reload - we already have it)
    # Preserve manifest from original bundle
    project_bundle.idea = plan_bundle.idea
    project_bundle.business = plan_bundle.business
    project_bundle.product = plan_bundle.product
    project_bundle.features = {f.key: f for f in plan_bundle.features}
    project_bundle.clarifications = plan_bundle.clarifications
    _save_bundle_with_progress(project_bundle, bundle_dir, atomic=True)
    print_success("Project bundle saved")

    return questions_asked


@beartype
@require(lambda plan_bundle: isinstance(plan_bundle, PlanBundle), "Plan bundle must be PlanBundle")
@require(lambda scanner: scanner is not None, "Scanner must not be None")
@require(lambda bundle: isinstance(bundle, str), "Bundle must be str")
@require(lambda questions_asked: questions_asked >= 0, "Questions asked must be non-negative")
@require(lambda report: report is not None, "Report must not be None")
@require(lambda current_stage: isinstance(current_stage, str), "Current stage must be str")
@require(lambda today_session: today_session is not None, "Today session must not be None")
@ensure(lambda result: result is None, "Must return None")
def _display_review_summary(
    plan_bundle: PlanBundle,
    scanner: Any,  # AmbiguityScanner
    bundle: str,
    questions_asked: int,
    report: Any,  # AmbiguityReport
    current_stage: str,
    today_session: Any,  # ClarificationSession
) -> None:
    """
    Display final review summary and updated coverage.

    Args:
        plan_bundle: Updated plan bundle
        scanner: Ambiguity scanner instance
        bundle: Bundle name
        questions_asked: Number of questions asked
        report: Original ambiguity report
        current_stage: Current plan stage
        today_session: Today's clarification session
    """
    from rich.console import Console

    from specfact_cli.analyzers.ambiguity_scanner import AmbiguityStatus

    console = Console()

    # Final validation
    print_info("Validating updated plan bundle...")
    validation_result = validate_plan_bundle(plan_bundle)
    if isinstance(validation_result, ValidationReport):
        if not validation_result.passed:
            print_warning(f"Validation found {len(validation_result.deviations)} issue(s)")
        else:
            print_success("Validation passed")
    else:
        print_success("Validation passed")

    # Display summary
    print_success(f"Review complete: {questions_asked} question(s) answered")
    console.print(f"\n[bold]Project Bundle:[/bold] {bundle}")
    console.print(f"[bold]Questions Asked:[/bold] {questions_asked}")

    if today_session.questions:
        console.print("\n[bold]Sections Touched:[/bold]")
        all_sections = set()
        for q in today_session.questions:
            all_sections.update(q.integrated_into)
        for section in sorted(all_sections):
            console.print(f"  • {section}")

    # Re-scan plan bundle after questions to get updated coverage summary
    print_info("Re-scanning plan bundle for updated coverage...")
    updated_report = scanner.scan(plan_bundle)

    # Coverage summary (updated after questions)
    console.print("\n[bold]Updated Coverage Summary:[/bold]")
    if updated_report.coverage:
        from specfact_cli.analyzers.ambiguity_scanner import TaxonomyCategory

        # Count findings that can still generate questions (unclear findings)
        # Use the same logic as _scan_and_prepare_questions to count unclear findings
        existing_question_ids = set()
        if plan_bundle.clarifications:
            for session in plan_bundle.clarifications.sessions:
                for q in session.questions:
                    existing_question_ids.add(q.id)

        # Prioritize findings by (Impact x Uncertainty) - same as _scan_and_prepare_questions
        findings_list = updated_report.findings or []
        prioritized_findings = sorted(
            findings_list,
            key=lambda f: f.impact * f.uncertainty,
            reverse=True,
        )

        # Count total findings and unclear findings per category
        # A finding is unclear if it can still generate a question (same logic as _scan_and_prepare_questions)
        total_findings_by_category: dict[TaxonomyCategory, int] = {}
        unclear_findings_by_category: dict[TaxonomyCategory, int] = {}
        clear_findings_by_category: dict[TaxonomyCategory, int] = {}

        question_counter = 1
        for finding in prioritized_findings:
            cat = finding.category
            total_findings_by_category[cat] = total_findings_by_category.get(cat, 0) + 1

            # Count by finding status
            if finding.status == AmbiguityStatus.CLEAR:
                clear_findings_by_category[cat] = clear_findings_by_category.get(cat, 0) + 1
            elif finding.status == AmbiguityStatus.PARTIAL:
                # A finding is unclear if it can generate a question (same logic as _scan_and_prepare_questions)
                if finding.question:
                    # Skip to next available question ID if current one is already used
                    while f"Q{question_counter:03d}" in existing_question_ids:
                        question_counter += 1
                    # This finding can generate a question, so it's unclear
                    unclear_findings_by_category[cat] = unclear_findings_by_category.get(cat, 0) + 1
                    question_counter += 1
                else:
                    # Finding has no question, so it's unclear
                    unclear_findings_by_category[cat] = unclear_findings_by_category.get(cat, 0) + 1

        for cat, status in updated_report.coverage.items():
            status_icon = (
                "✅" if status == AmbiguityStatus.CLEAR else "⚠️" if status == AmbiguityStatus.PARTIAL else "❌"
            )
            total = total_findings_by_category.get(cat, 0)
            unclear = unclear_findings_by_category.get(cat, 0)
            clear_count = clear_findings_by_category.get(cat, 0)
            # Show format based on status:
            # - Clear: If no findings (total=0), just show status. Otherwise show clear_count/total
            # - Partial: Show unclear_count/total (how many findings are still unclear)
            if status == AmbiguityStatus.CLEAR:
                if total == 0:
                    # No findings - just show status without counts
                    console.print(f"  {status_icon} {cat.value}: {status.value}")
                else:
                    console.print(f"  {status_icon} {cat.value}: {clear_count}/{total} {status.value}")
            elif status == AmbiguityStatus.PARTIAL:
                # Show how many findings are still unclear
                # If all are unclear, just show the count without the fraction
                if unclear == total:
                    console.print(f"  {status_icon} {cat.value}: {unclear} {status.value}")
                else:
                    console.print(f"  {status_icon} {cat.value}: {unclear}/{total} {status.value}")
            else:  # MISSING
                console.print(f"  {status_icon} {cat.value}: {status.value}")

    # Next steps
    console.print("\n[bold]Next Steps:[/bold]")
    if current_stage == "draft":
        console.print("  • Review plan bundle for completeness")
        console.print("  • Run: specfact plan promote --stage review")
    elif current_stage == "review":
        console.print("  • Plan is ready for approval")
        console.print("  • Run: specfact plan promote --stage approved")

    return


@app.command("review")
@beartype
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle name must be None or non-empty string",
)
@require(lambda max_questions: max_questions > 0, "Max questions must be positive")
def review(
    # Target/Input
    bundle: str | None = typer.Argument(
        None,
        help="Project bundle name (e.g., legacy-api, auth-module). Default: active plan from 'specfact plan select'",
    ),
    category: str | None = typer.Option(
        None,
        "--category",
        help="Focus on specific taxonomy category (optional). Default: None (all categories)",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    # Output/Results
    list_questions: bool = typer.Option(
        False,
        "--list-questions",
        help="Output questions in JSON format without asking (for Copilot mode). Default: False",
    ),
    output_questions: Path | None = typer.Option(
        None,
        "--output-questions",
        help="Save questions to file (JSON format). If --list-questions is also set, questions are saved to file instead of stdout. Default: None",
    ),
    list_findings: bool = typer.Option(
        False,
        "--list-findings",
        help="Output all findings in structured format (JSON/YAML) or as table (interactive mode). Preferred for bulk updates via Copilot LLM enrichment. Default: False",
    ),
    findings_format: str | None = typer.Option(
        None,
        "--findings-format",
        help="Output format for --list-findings: json, yaml, or table. Default: json for non-interactive, table for interactive",
        case_sensitive=False,
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    output_findings: Path | None = typer.Option(
        None,
        "--output-findings",
        help="Save findings to file (JSON/YAML format). If --list-findings is also set, findings are saved to file instead of stdout. Default: None",
    ),
    # Behavior/Options
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Non-interactive mode (for CI/CD automation). Default: False (interactive mode)",
    ),
    answers: str | None = typer.Option(
        None,
        "--answers",
        help="JSON object with question_id -> answer mappings (for non-interactive mode). Can be JSON string or path to JSON file. Use with --output-questions to save questions, then edit and provide answers. Default: None",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
    auto_enrich: bool = typer.Option(
        False,
        "--auto-enrich",
        help="Automatically enrich vague acceptance criteria, incomplete requirements, and generic tasks using LLM-enhanced pattern matching. Default: False",
    ),
    # Advanced/Configuration
    max_questions: int = typer.Option(
        5,
        "--max-questions",
        min=1,
        max=10,
        help="Maximum questions per session. Default: 5 (range: 1-10)",
        hidden=True,  # Hidden by default, shown with --help-advanced
    ),
) -> None:
    """
    Review project bundle to identify and resolve ambiguities.

    Analyzes the project bundle for missing information, unclear requirements,
    and unknowns. Asks targeted questions to resolve ambiguities and make
    the bundle ready for promotion.

    **Parameter Groups:**
    - **Target/Input**: bundle (required argument), --category
    - **Output/Results**: --list-questions, --list-findings, --findings-format
    - **Behavior/Options**: --no-interactive, --answers, --auto-enrich
    - **Advanced/Configuration**: --max-questions

    **Examples:**
        specfact plan review legacy-api
        specfact plan review auth-module --max-questions 3 --category "Functional Scope"
        specfact plan review legacy-api --list-questions  # Output questions as JSON
        specfact plan review legacy-api --list-questions --output-questions /tmp/questions.json  # Save questions to file
        specfact plan review legacy-api --list-findings --findings-format json  # Output all findings as JSON
        specfact plan review legacy-api --list-findings --output-findings /tmp/findings.json  # Save findings to file
        specfact plan review legacy-api --answers '{"Q001": "answer1", "Q002": "answer2"}'  # Non-interactive
    """
    from rich.console import Console

    from specfact_cli.utils.structure import SpecFactStructure

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(Path("."))
        if bundle is None:
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print("[yellow]→[/yellow] Use --bundle option or run 'specfact plan select' to set active plan")
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")

    from datetime import date

    from specfact_cli.analyzers.ambiguity_scanner import (
        AmbiguityStatus,
    )
    from specfact_cli.models.plan import ClarificationSession

    # Detect operational mode
    mode = detect_mode()
    is_non_interactive = no_interactive or (answers is not None) or list_questions

    telemetry_metadata = {
        "max_questions": max_questions,
        "category": category,
        "list_questions": list_questions,
        "non_interactive": is_non_interactive,
        "mode": mode.value,
    }

    with telemetry.track_command("plan.review", telemetry_metadata) as record:
        # Find bundle directory
        bundle_dir = _find_bundle_dir(bundle)
        if bundle_dir is None:
            raise typer.Exit(1)

        print_section("SpecFact CLI - Plan Review")

        try:
            # Load and prepare bundle
            project_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)
            plan_bundle, current_stage = _prepare_review_bundle(project_bundle, bundle_dir, bundle, auto_enrich)

            if current_stage not in ("draft", "review"):
                print_warning("Review is typically run on 'draft' or 'review' stage plans")
                if not is_non_interactive and not prompt_confirm("Continue anyway?", default=False):
                    raise typer.Exit(0)
                if is_non_interactive:
                    print_info("Continuing in non-interactive mode")

            # Scan and prepare questions
            questions_to_ask, report, scanner = _scan_and_prepare_questions(
                plan_bundle, bundle_dir, category, max_questions
            )

            # Handle --list-findings mode
            if list_findings:
                _output_findings(report, findings_format, is_non_interactive, output_findings)
                raise typer.Exit(0)

            # Show initial coverage summary BEFORE questions (so user knows what's missing)
            if questions_to_ask:
                from specfact_cli.analyzers.ambiguity_scanner import AmbiguityStatus

                console.print("\n[bold]Initial Coverage Summary:[/bold]")
                if report.coverage:
                    from specfact_cli.analyzers.ambiguity_scanner import TaxonomyCategory

                    # Count findings that can still generate questions (unclear findings)
                    # Use the same logic as _scan_and_prepare_questions to count unclear findings
                    existing_question_ids = set()
                    if plan_bundle.clarifications:
                        for session in plan_bundle.clarifications.sessions:
                            for q in session.questions:
                                existing_question_ids.add(q.id)

                    # Prioritize findings by (Impact x Uncertainty) - same as _scan_and_prepare_questions
                    findings_list = report.findings or []
                    prioritized_findings = sorted(
                        findings_list,
                        key=lambda f: f.impact * f.uncertainty,
                        reverse=True,
                    )

                    # Count total findings and unclear findings per category
                    # A finding is unclear if it can still generate a question (same logic as _scan_and_prepare_questions)
                    total_findings_by_category: dict[TaxonomyCategory, int] = {}
                    unclear_findings_by_category: dict[TaxonomyCategory, int] = {}
                    clear_findings_by_category: dict[TaxonomyCategory, int] = {}

                    question_counter = 1
                    for finding in prioritized_findings:
                        cat = finding.category
                        total_findings_by_category[cat] = total_findings_by_category.get(cat, 0) + 1

                        # Count by finding status
                        if finding.status == AmbiguityStatus.CLEAR:
                            clear_findings_by_category[cat] = clear_findings_by_category.get(cat, 0) + 1
                        elif finding.status == AmbiguityStatus.PARTIAL:
                            # A finding is unclear if it can generate a question (same logic as _scan_and_prepare_questions)
                            if finding.question:
                                # Skip to next available question ID if current one is already used
                                while f"Q{question_counter:03d}" in existing_question_ids:
                                    question_counter += 1
                                # This finding can generate a question, so it's unclear
                                unclear_findings_by_category[cat] = unclear_findings_by_category.get(cat, 0) + 1
                                question_counter += 1
                            else:
                                # Finding has no question, so it's unclear
                                unclear_findings_by_category[cat] = unclear_findings_by_category.get(cat, 0) + 1

                    for cat, status in report.coverage.items():
                        status_icon = (
                            "✅"
                            if status == AmbiguityStatus.CLEAR
                            else "⚠️"
                            if status == AmbiguityStatus.PARTIAL
                            else "❌"
                        )
                        total = total_findings_by_category.get(cat, 0)
                        unclear = unclear_findings_by_category.get(cat, 0)
                        clear_count = clear_findings_by_category.get(cat, 0)
                        # Show format based on status:
                        # - Clear: If no findings (total=0), just show status. Otherwise show clear_count/total
                        # - Partial: Show unclear_count/total (how many findings are still unclear)
                        if status == AmbiguityStatus.CLEAR:
                            if total == 0:
                                # No findings - just show status without counts
                                console.print(f"  {status_icon} {cat.value}: {status.value}")
                            else:
                                console.print(f"  {status_icon} {cat.value}: {clear_count}/{total} {status.value}")
                        elif status == AmbiguityStatus.PARTIAL:
                            # Show how many findings are still unclear
                            # If all are unclear, just show the count without the fraction
                            if unclear == total:
                                console.print(f"  {status_icon} {cat.value}: {unclear} {status.value}")
                            else:
                                console.print(f"  {status_icon} {cat.value}: {unclear}/{total} {status.value}")
                        else:  # MISSING
                            console.print(f"  {status_icon} {cat.value}: {status.value}")
                console.print(f"\n[dim]Found {len(questions_to_ask)} question(s) to resolve[/dim]\n")

            # Handle --list-questions mode (must be before no-questions check)
            if list_questions:
                _handle_list_questions_mode(questions_to_ask, output_questions)
                raise typer.Exit(0)

            if not questions_to_ask:
                _handle_no_questions_case(questions_to_ask, report)
                raise typer.Exit(0)

            # Parse answers if provided
            answers_dict: dict[str, str] = {}
            if answers:
                answers_dict = _parse_answers_dict(answers)

            print_info(f"Found {len(questions_to_ask)} question(s) to resolve")

            # Ask questions interactively
            questions_asked = _ask_questions_interactive(
                plan_bundle, questions_to_ask, answers_dict, is_non_interactive, bundle_dir, project_bundle
            )

            # Get today's session for summary display
            from datetime import date

            from specfact_cli.models.plan import ClarificationSession

            today = date.today().isoformat()
            today_session: ClarificationSession | None = None
            if plan_bundle.clarifications:
                for session in plan_bundle.clarifications.sessions:
                    if session.date == today:
                        today_session = session
                        break
            if today_session is None:
                today_session = ClarificationSession(date=today, questions=[])

            # Display final summary
            _display_review_summary(plan_bundle, scanner, bundle, questions_asked, report, current_stage, today_session)

            record(
                {
                    "questions_asked": questions_asked,
                    "findings_count": len(report.findings) if report.findings else 0,
                    "priority_score": report.priority_score,
                }
            )

        except KeyboardInterrupt:
            print_warning("Review interrupted by user")
            raise typer.Exit(0) from None
        except typer.Exit:
            # Re-raise typer.Exit (used for --list-questions and other early exits)
            raise
        except Exception as e:
            print_error(f"Failed to review plan: {e}")
            raise typer.Exit(1) from e


def _convert_project_bundle_to_plan_bundle(project_bundle: ProjectBundle) -> PlanBundle:
    """
    Convert ProjectBundle to PlanBundle for compatibility with existing extraction functions.

    Args:
        project_bundle: ProjectBundle instance

    Returns:
        PlanBundle instance
    """
    return PlanBundle(
        version="1.0",
        idea=project_bundle.idea,
        business=project_bundle.business,
        product=project_bundle.product,
        features=list(project_bundle.features.values()),
        metadata=None,  # ProjectBundle doesn't use Metadata, uses manifest instead
        clarifications=project_bundle.clarifications,
    )


@beartype
def _convert_plan_bundle_to_project_bundle(plan_bundle: PlanBundle, bundle_name: str) -> ProjectBundle:
    """
    Convert PlanBundle to ProjectBundle (modular).

    Args:
        plan_bundle: PlanBundle instance to convert
        bundle_name: Project bundle name

    Returns:
        ProjectBundle instance
    """
    from specfact_cli.models.project import BundleManifest, BundleVersions

    # Create manifest
    manifest = BundleManifest(
        versions=BundleVersions(schema="1.0", project="0.1.0"),
        schema_metadata=None,
        project_metadata=None,
    )

    # Convert features list to dict
    features_dict: dict[str, Feature] = {f.key: f for f in plan_bundle.features}

    # Create and return ProjectBundle
    return ProjectBundle(
        manifest=manifest,
        bundle_name=bundle_name,
        idea=plan_bundle.idea,
        business=plan_bundle.business,
        product=plan_bundle.product,
        features=features_dict,
        clarifications=plan_bundle.clarifications,
    )


def _find_bundle_dir(bundle: str | None) -> Path | None:
    """
    Find project bundle directory with improved validation and error messages.

    Args:
        bundle: Bundle name or None

    Returns:
        Bundle directory path or None if not found
    """
    from specfact_cli.utils.structure import SpecFactStructure

    if bundle is None:
        print_error("Bundle name is required. Use --bundle <name>")
        print_info("Available bundles:")
        projects_dir = Path(".") / SpecFactStructure.PROJECTS
        if projects_dir.exists():
            bundles = [
                bundle_dir.name
                for bundle_dir in projects_dir.iterdir()
                if bundle_dir.is_dir() and (bundle_dir / "bundle.manifest.yaml").exists()
            ]
            if bundles:
                for bundle_name in bundles:
                    print_info(f"  - {bundle_name}")
            else:
                print_info("  (no bundles found)")
                print_info("Create one with: specfact plan init <bundle-name>")
        else:
            print_info("  (projects directory not found)")
            print_info("Create one with: specfact plan init <bundle-name>")
        return None

    bundle_dir = SpecFactStructure.project_dir(bundle_name=bundle)
    if not bundle_dir.exists():
        print_error(f"Project bundle '{bundle}' not found: {bundle_dir}")
        print_info(f"Create one with: specfact plan init {bundle}")

        # Suggest similar bundle names if available
        projects_dir = Path(".") / SpecFactStructure.PROJECTS
        if projects_dir.exists():
            available_bundles = [
                bundle_dir.name
                for bundle_dir in projects_dir.iterdir()
                if bundle_dir.is_dir() and (bundle_dir / "bundle.manifest.yaml").exists()
            ]
            if available_bundles:
                print_info("Available bundles:")
                for available_bundle in available_bundles:
                    print_info(f"  - {available_bundle}")
        return None

    return bundle_dir


@app.command("harden")
@beartype
@require(
    lambda bundle: bundle is None or (isinstance(bundle, str) and len(bundle) > 0),
    "Bundle name must be None or non-empty string",
)
@require(lambda sdd_path: sdd_path is None or isinstance(sdd_path, Path), "SDD path must be None or Path")
def harden(
    # Target/Input
    bundle: str | None = typer.Argument(
        None,
        help="Project bundle name (e.g., legacy-api, auth-module). Default: active plan from 'specfact plan select'",
    ),
    sdd_path: Path | None = typer.Option(
        None,
        "--sdd",
        help="Output SDD manifest path. Default: bundle-specific .specfact/projects/<bundle-name>/sdd.<format> (Phase 8.5)",
    ),
    # Output/Results
    output_format: StructuredFormat | None = typer.Option(
        None,
        "--output-format",
        help="SDD manifest format (yaml or json). Default: global --output-format (yaml)",
        case_sensitive=False,
    ),
    # Behavior/Options
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Interactive mode with prompts. Default: True (interactive, auto-detect)",
    ),
) -> None:
    """
    Create or update SDD manifest (hard spec) from project bundle.

    Generates a canonical SDD bundle that captures WHY (intent, constraints),
    WHAT (capabilities, acceptance), and HOW (high-level architecture, invariants,
    contracts) with promotion status.

    **Important**: SDD manifests are linked to specific project bundles via hash.
    Each project bundle has its own SDD manifest in `.specfact/projects/<bundle-name>/sdd.yaml` (Phase 8.5).

    **Parameter Groups:**
    - **Target/Input**: bundle (optional argument, defaults to active plan), --sdd
    - **Output/Results**: --output-format
    - **Behavior/Options**: --interactive/--no-interactive

    **Examples:**
        specfact plan harden                    # Uses active plan (set via 'plan select')
        specfact plan harden legacy-api       # Interactive
        specfact plan harden auth-module --no-interactive  # CI/CD mode
        specfact plan harden legacy-api --output-format json
    """
    from specfact_cli.models.sdd import (
        SDDCoverageThresholds,
        SDDEnforcementBudget,
        SDDManifest,
    )
    from specfact_cli.utils.structured_io import dump_structured_file

    effective_format = output_format or runtime.get_output_format()
    is_non_interactive = not interactive

    from rich.console import Console

    from specfact_cli.utils.structure import SpecFactStructure

    console = Console()

    # Use active plan as default if bundle not provided
    if bundle is None:
        bundle = SpecFactStructure.get_active_bundle_name(Path("."))
        if bundle is None:
            console.print("[bold red]✗[/bold red] Bundle name required")
            console.print(
                "[yellow]→[/yellow] Specify bundle name as argument or run 'specfact plan select' to set active plan"
            )
            raise typer.Exit(1)
        console.print(f"[dim]Using active plan: {bundle}[/dim]")

    telemetry_metadata = {
        "interactive": interactive,
        "output_format": effective_format.value,
    }

    with telemetry.track_command("plan.harden", telemetry_metadata) as record:
        print_section("SpecFact CLI - SDD Manifest Creation")

        # Find bundle directory
        bundle_dir = _find_bundle_dir(bundle)
        if bundle_dir is None:
            raise typer.Exit(1)

        try:
            # Load project bundle with progress indicator
            project_bundle = _load_bundle_with_progress(bundle_dir, validate_hashes=False)

            # Compute project bundle hash
            summary = project_bundle.compute_summary(include_hash=True)
            project_hash = summary.content_hash
            if not project_hash:
                print_error("Failed to compute project bundle hash")
                raise typer.Exit(1)

            # Determine SDD output path (bundle-specific: .specfact/projects/<bundle-name>/sdd.yaml, Phase 8.5)
            from specfact_cli.utils.sdd_discovery import get_default_sdd_path_for_bundle

            if sdd_path is None:
                base_path = Path(".")
                sdd_path = get_default_sdd_path_for_bundle(bundle, base_path, effective_format.value)
                sdd_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                # Ensure correct extension
                if effective_format == StructuredFormat.YAML:
                    sdd_path = sdd_path.with_suffix(".yaml")
                else:
                    sdd_path = sdd_path.with_suffix(".json")

            # Check if SDD already exists and reuse it if hash matches
            existing_sdd: SDDManifest | None = None
            # Convert to PlanBundle for extraction functions (temporary compatibility)
            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)

            if sdd_path.exists():
                try:
                    from specfact_cli.utils.structured_io import load_structured_file

                    existing_sdd_data = load_structured_file(sdd_path)
                    existing_sdd = SDDManifest.model_validate(existing_sdd_data)
                    if existing_sdd.plan_bundle_hash == project_hash:
                        # Hash matches - reuse existing SDD sections
                        print_info("SDD manifest exists with matching hash - reusing existing sections")
                        why = existing_sdd.why
                        what = existing_sdd.what
                        how = existing_sdd.how
                    else:
                        # Hash mismatch - warn and extract new, but reuse existing SDD as fallback
                        print_warning(
                            f"SDD manifest exists but is linked to a different bundle version.\n"
                            f"  Existing bundle hash: {existing_sdd.plan_bundle_hash[:16]}...\n"
                            f"  New bundle hash: {project_hash[:16]}...\n"
                            f"  This will overwrite the existing SDD manifest.\n"
                            f"  Note: SDD manifests are linked to specific bundle versions."
                        )
                        if not is_non_interactive:
                            # In interactive mode, ask for confirmation
                            from rich.prompt import Confirm

                            if not Confirm.ask("Overwrite existing SDD manifest?", default=False):
                                print_info("SDD manifest creation cancelled.")
                                raise typer.Exit(0)
                        # Extract from bundle, using existing SDD as fallback
                        why = _extract_sdd_why(plan_bundle, is_non_interactive, existing_sdd.why)
                        what = _extract_sdd_what(plan_bundle, is_non_interactive, existing_sdd.what)
                        how = _extract_sdd_how(
                            plan_bundle, is_non_interactive, existing_sdd.how, project_bundle, bundle_dir
                        )
                except Exception:
                    # If we can't read/validate existing SDD, just proceed (might be corrupted)
                    existing_sdd = None
                    # Extract from bundle without fallback
                    why = _extract_sdd_why(plan_bundle, is_non_interactive, None)
                    what = _extract_sdd_what(plan_bundle, is_non_interactive, None)
                    how = _extract_sdd_how(plan_bundle, is_non_interactive, None, project_bundle, bundle_dir)
            else:
                # No existing SDD found, extract from bundle
                why = _extract_sdd_why(plan_bundle, is_non_interactive, None)
                what = _extract_sdd_what(plan_bundle, is_non_interactive, None)
                how = _extract_sdd_how(plan_bundle, is_non_interactive, None, project_bundle, bundle_dir)

            # Type assertion: these variables are always set in valid code paths
            # (typer.Exit exits the function, so those paths don't need these variables)
            assert why is not None and what is not None and how is not None  # type: ignore[unreachable]

            # Create SDD manifest
            plan_bundle_id = project_hash[:16]  # Use first 16 chars as ID
            sdd_manifest = SDDManifest(
                version="1.0.0",
                plan_bundle_id=plan_bundle_id,
                plan_bundle_hash=project_hash,
                why=why,
                what=what,
                how=how,
                coverage_thresholds=SDDCoverageThresholds(
                    contracts_per_story=1.0,
                    invariants_per_feature=1.0,
                    architecture_facets=3,
                    openapi_coverage_percent=80.0,
                ),
                enforcement_budget=SDDEnforcementBudget(
                    shadow_budget_seconds=300,
                    warn_budget_seconds=180,
                    block_budget_seconds=90,
                ),
                promotion_status="draft",  # TODO: Add promotion status to ProjectBundle manifest
                provenance={
                    "source": "plan_harden",
                    "bundle_name": bundle,
                    "bundle_path": str(bundle_dir),
                    "created_by": "specfact_cli",
                },
            )

            # Save SDD manifest
            sdd_path.parent.mkdir(parents=True, exist_ok=True)
            sdd_data = sdd_manifest.model_dump(exclude_none=True)
            dump_structured_file(sdd_data, sdd_path, effective_format)

            print_success(f"SDD manifest created: {sdd_path}")

            # Display summary
            console.print("\n[bold]SDD Manifest Summary:[/bold]")
            console.print(f"[bold]Project Bundle:[/bold] {bundle_dir}")
            console.print(f"[bold]Bundle Hash:[/bold] {project_hash[:16]}...")
            console.print(f"[bold]SDD Path:[/bold] {sdd_path}")
            console.print("\n[bold]WHY (Intent):[/bold]")
            console.print(f"  {why.intent}")
            if why.constraints:
                console.print(f"[bold]Constraints:[/bold] {len(why.constraints)}")
            console.print(f"\n[bold]WHAT (Capabilities):[/bold] {len(what.capabilities)}")
            console.print("\n[bold]HOW (Architecture):[/bold]")
            if how.architecture:
                console.print(f"  {how.architecture[:100]}...")
            console.print(f"[bold]Invariants:[/bold] {len(how.invariants)}")
            console.print(f"[bold]Contracts:[/bold] {len(how.contracts)}")
            console.print(f"[bold]OpenAPI Contracts:[/bold] {len(how.openapi_contracts)}")

            record(
                {
                    "bundle_name": bundle,
                    "bundle_path": str(bundle_dir),
                    "sdd_path": str(sdd_path),
                    "capabilities_count": len(what.capabilities),
                    "invariants_count": len(how.invariants),
                }
            )

        except KeyboardInterrupt:
            print_warning("SDD creation interrupted by user")
            raise typer.Exit(0) from None
        except Exception as e:
            print_error(f"Failed to create SDD manifest: {e}")
            raise typer.Exit(1) from e


@beartype
@beartype
@require(lambda bundle: isinstance(bundle, PlanBundle), "Bundle must be PlanBundle")
@require(lambda is_non_interactive: isinstance(is_non_interactive, bool), "Is non-interactive must be bool")
def _extract_sdd_why(bundle: PlanBundle, is_non_interactive: bool, fallback: SDDWhy | None = None) -> SDDWhy:
    """
    Extract WHY section from plan bundle.

    Args:
        bundle: Plan bundle to extract from
        is_non_interactive: Whether in non-interactive mode

    Returns:
        SDDWhy instance
    """
    from specfact_cli.models.sdd import SDDWhy

    intent = ""
    constraints: list[str] = []
    target_users: str | None = None
    value_hypothesis: str | None = None

    if bundle.idea:
        intent = bundle.idea.narrative or bundle.idea.title or ""
        constraints = bundle.idea.constraints or []
        if bundle.idea.target_users:
            target_users = ", ".join(bundle.idea.target_users)
        value_hypothesis = bundle.idea.value_hypothesis or None

    # Use fallback from existing SDD if available
    if fallback:
        if not intent:
            intent = fallback.intent or ""
        if not constraints:
            constraints = fallback.constraints or []
        if not target_users:
            target_users = fallback.target_users
        if not value_hypothesis:
            value_hypothesis = fallback.value_hypothesis

    # If intent is empty, prompt or use default
    if not intent and not is_non_interactive:
        intent = prompt_text("Primary intent/goal (WHY):", required=True)
    elif not intent:
        intent = "Extracted from plan bundle"

    return SDDWhy(
        intent=intent,
        constraints=constraints,
        target_users=target_users,
        value_hypothesis=value_hypothesis,
    )


@beartype
@require(lambda bundle: isinstance(bundle, PlanBundle), "Bundle must be PlanBundle")
@require(lambda is_non_interactive: isinstance(is_non_interactive, bool), "Is non-interactive must be bool")
def _extract_sdd_what(bundle: PlanBundle, is_non_interactive: bool, fallback: SDDWhat | None = None) -> SDDWhat:
    """
    Extract WHAT section from plan bundle.

    Args:
        bundle: Plan bundle to extract from
        is_non_interactive: Whether in non-interactive mode

    Returns:
        SDDWhat instance
    """
    from specfact_cli.models.sdd import SDDWhat

    capabilities: list[str] = []
    acceptance_criteria: list[str] = []
    out_of_scope: list[str] = []

    # Extract capabilities from features
    for feature in bundle.features:
        if feature.title:
            capabilities.append(feature.title)
        # Collect acceptance criteria
        acceptance_criteria.extend(feature.acceptance or [])
        # Collect constraints that might indicate out-of-scope
        for constraint in feature.constraints or []:
            if "out of scope" in constraint.lower() or "not included" in constraint.lower():
                out_of_scope.append(constraint)

    # Use fallback from existing SDD if available
    if fallback:
        if not capabilities:
            capabilities = fallback.capabilities or []
        if not acceptance_criteria:
            acceptance_criteria = fallback.acceptance_criteria or []
        if not out_of_scope:
            out_of_scope = fallback.out_of_scope or []

    # If no capabilities, use default
    if not capabilities:
        if not is_non_interactive:
            capabilities_input = prompt_text("Core capabilities (comma-separated):", required=True)
            capabilities = [c.strip() for c in capabilities_input.split(",")]
        else:
            capabilities = ["Extracted from plan bundle"]

    return SDDWhat(
        capabilities=capabilities,
        acceptance_criteria=acceptance_criteria,
        out_of_scope=out_of_scope,
    )


@beartype
@require(lambda bundle: isinstance(bundle, PlanBundle), "Bundle must be PlanBundle")
@require(lambda is_non_interactive: isinstance(is_non_interactive, bool), "Is non-interactive must be bool")
def _extract_sdd_how(
    bundle: PlanBundle,
    is_non_interactive: bool,
    fallback: SDDHow | None = None,
    project_bundle: ProjectBundle | None = None,
    bundle_dir: Path | None = None,
) -> SDDHow:
    """
    Extract HOW section from plan bundle.

    Args:
        bundle: Plan bundle to extract from
        is_non_interactive: Whether in non-interactive mode
        fallback: Optional fallback SDDHow to reuse values from
        project_bundle: Optional ProjectBundle to extract OpenAPI contract references
        bundle_dir: Optional bundle directory path for contract file validation

    Returns:
        SDDHow instance
    """
    from specfact_cli.models.contract import count_endpoints, load_openapi_contract, validate_openapi_schema
    from specfact_cli.models.sdd import OpenAPIContractReference, SDDHow

    architecture: str | None = None
    invariants: list[str] = []
    contracts: list[str] = []
    module_boundaries: list[str] = []

    # Extract architecture from constraints
    architecture_parts: list[str] = []
    for feature in bundle.features:
        for constraint in feature.constraints or []:
            if any(keyword in constraint.lower() for keyword in ["architecture", "design", "structure", "component"]):
                architecture_parts.append(constraint)

    if architecture_parts:
        architecture = " ".join(architecture_parts[:3])  # Limit to first 3

    # Extract invariants from stories (acceptance criteria that are invariants)
    for feature in bundle.features:
        for story in feature.stories:
            for acceptance in story.acceptance or []:
                if any(keyword in acceptance.lower() for keyword in ["always", "never", "must", "invariant"]):
                    invariants.append(acceptance)

    # Extract contracts from story contracts
    for feature in bundle.features:
        for story in feature.stories:
            if story.contracts:
                contracts.append(f"{story.key}: {str(story.contracts)[:100]}")

    # Extract module boundaries from feature keys (as a simple heuristic)
    module_boundaries = [f.key for f in bundle.features[:10]]  # Limit to first 10

    # Extract OpenAPI contract references from project bundle if available
    openapi_contracts: list[OpenAPIContractReference] = []
    if project_bundle and bundle_dir:
        for feature_index in project_bundle.manifest.features:
            if feature_index.contract:
                contract_path = bundle_dir / feature_index.contract
                if contract_path.exists():
                    try:
                        contract_data = load_openapi_contract(contract_path)
                        if validate_openapi_schema(contract_data):
                            endpoints_count = count_endpoints(contract_data)
                            openapi_contracts.append(
                                OpenAPIContractReference(
                                    feature_key=feature_index.key,
                                    contract_file=feature_index.contract,
                                    endpoints_count=endpoints_count,
                                    status="validated",
                                )
                            )
                        else:
                            # Contract exists but is invalid
                            openapi_contracts.append(
                                OpenAPIContractReference(
                                    feature_key=feature_index.key,
                                    contract_file=feature_index.contract,
                                    endpoints_count=0,
                                    status="draft",
                                )
                            )
                    except Exception:
                        # Contract file exists but couldn't be loaded
                        openapi_contracts.append(
                            OpenAPIContractReference(
                                feature_key=feature_index.key,
                                contract_file=feature_index.contract,
                                endpoints_count=0,
                                status="draft",
                            )
                        )

    # Use fallback from existing SDD if available
    if fallback:
        if not architecture:
            architecture = fallback.architecture
        if not invariants:
            invariants = fallback.invariants or []
        if not contracts:
            contracts = fallback.contracts or []
        if not module_boundaries:
            module_boundaries = fallback.module_boundaries or []
        if not openapi_contracts:
            openapi_contracts = fallback.openapi_contracts or []

    # If no architecture, prompt or use default
    if not architecture and not is_non_interactive:
        # If we have a fallback, use it as default value in prompt
        default_arch = fallback.architecture if fallback else None
        if default_arch:
            architecture = (
                prompt_text(
                    f"High-level architecture description (optional, current: {default_arch[:50]}...):",
                    required=False,
                )
                or default_arch
            )
        else:
            architecture = prompt_text("High-level architecture description (optional):", required=False) or None
    elif not architecture:
        architecture = "Extracted from plan bundle constraints"

    return SDDHow(
        architecture=architecture,
        invariants=invariants[:10],  # Limit to first 10
        contracts=contracts[:10],  # Limit to first 10
        openapi_contracts=openapi_contracts,
        module_boundaries=module_boundaries,
    )


@beartype
@require(lambda answer: isinstance(answer, str), "Answer must be string")
@ensure(lambda result: isinstance(result, list), "Must return list of criteria strings")
def _extract_specific_criteria_from_answer(answer: str) -> list[str]:
    """
    Extract specific testable criteria from answer that contains replacement instructions.

    When answer contains "Replace generic 'works correctly' with testable criteria:",
    extracts the specific criteria (items in single quotes) and returns them as a list.

    Args:
        answer: Answer text that may contain replacement instructions

    Returns:
        List of specific criteria strings, or empty list if no extraction possible
    """
    import re

    # Check if answer contains replacement instructions
    if "testable criteria:" not in answer.lower() and "replace generic" not in answer.lower():
        # Answer doesn't contain replacement format, return as single item
        return [answer] if answer.strip() else []

    # Find the position after "testable criteria:" to only extract criteria from that point
    # This avoids extracting "works correctly" from the instruction text itself
    testable_criteria_marker = "testable criteria:"
    marker_pos = answer.lower().find(testable_criteria_marker)

    if marker_pos == -1:
        # Fallback: try "with testable criteria:"
        marker_pos = answer.lower().find("with testable criteria:")
        if marker_pos != -1:
            marker_pos += len("with testable criteria:")

    if marker_pos != -1:
        # Only search for criteria after the marker
        criteria_section = answer[marker_pos + len(testable_criteria_marker) :]
        # Extract criteria (items in single quotes)
        criteria_pattern = r"'([^']+)'"
        matches = re.findall(criteria_pattern, criteria_section)

        if matches:
            # Filter out "works correctly" if it appears (it's part of instruction, not a criterion)
            filtered = [
                criterion.strip()
                for criterion in matches
                if criterion.strip() and criterion.strip().lower() not in ("works correctly", "works as expected")
            ]
            if filtered:
                return filtered

    # Fallback: if no quoted criteria found, return original answer
    return [answer] if answer.strip() else []


@beartype
@require(lambda acceptance_list: isinstance(acceptance_list, list), "Acceptance list must be list")
@require(lambda finding: finding is not None, "Finding must not be None")
@ensure(lambda result: isinstance(result, list), "Must return list of acceptance strings")
def _identify_vague_criteria_to_remove(
    acceptance_list: list[str],
    finding: Any,  # AmbiguityFinding
) -> list[str]:
    """
    Identify vague acceptance criteria that should be removed when replacing with specific criteria.

    Args:
        acceptance_list: Current list of acceptance criteria
        finding: Ambiguity finding that triggered the question

    Returns:
        List of vague criteria strings to remove
    """
    from specfact_cli.utils.acceptance_criteria import (
        is_code_specific_criteria,
        is_simplified_format_criteria,
    )

    vague_to_remove: list[str] = []

    # Patterns that indicate vague criteria (from ambiguity scanner)
    vague_patterns = [
        "is implemented",
        "is functional",
        "works",
        "is done",
        "is complete",
        "is ready",
    ]

    for acc in acceptance_list:
        acc_lower = acc.lower()

        # Skip code-specific criteria (should not be removed)
        if is_code_specific_criteria(acc):
            continue

        # Skip simplified format criteria (valid format)
        if is_simplified_format_criteria(acc):
            continue

        # ALWAYS remove replacement instruction text (from previous answers)
        # These are meta-instructions, not actual acceptance criteria
        contains_replacement_instruction = (
            "replace generic" in acc_lower
            or ("should be more specific" in acc_lower and "testable criteria:" in acc_lower)
            or ("yes, these should be more specific" in acc_lower)
        )

        if contains_replacement_instruction:
            vague_to_remove.append(acc)
            continue

        # Check for vague patterns (but be more selective)
        # Only flag as vague if it contains "works correctly" without "see contract examples"
        # or other vague patterns in a standalone context
        is_vague = False
        if "works correctly" in acc_lower:
            # Only remove if it doesn't have "see contract examples" (simplified format is valid)
            if "see contract" not in acc_lower and "contract examples" not in acc_lower:
                is_vague = True
        else:
            # Check other vague patterns
            is_vague = any(
                pattern in acc_lower and len(acc.split()) < 10  # Only flag short, vague statements
                for pattern in vague_patterns
            )

        if is_vague:
            vague_to_remove.append(acc)

    return vague_to_remove


@beartype
@require(lambda bundle: isinstance(bundle, PlanBundle), "Bundle must be PlanBundle")
@require(lambda answer: isinstance(answer, str) and bool(answer.strip()), "Answer must be non-empty string")
@ensure(lambda result: isinstance(result, list), "Must return list of integration points")
def _integrate_clarification(
    bundle: PlanBundle,
    finding: AmbiguityFinding,
    answer: str,
) -> list[str]:
    """
    Integrate clarification answer into plan bundle.

    Args:
        bundle: Plan bundle to update
        finding: Ambiguity finding with related sections
        answer: User-provided answer

    Returns:
        List of integration points (section paths)
    """
    from specfact_cli.analyzers.ambiguity_scanner import TaxonomyCategory

    integration_points: list[str] = []

    category = finding.category

    # Functional Scope → idea.narrative, idea.target_users, features[].outcomes
    if category == TaxonomyCategory.FUNCTIONAL_SCOPE:
        related_sections = finding.related_sections or []
        if (
            "idea.narrative" in related_sections
            and bundle.idea
            and (not bundle.idea.narrative or len(bundle.idea.narrative) < 20)
        ):
            bundle.idea.narrative = answer
            integration_points.append("idea.narrative")
        elif "idea.target_users" in related_sections and bundle.idea:
            if bundle.idea.target_users is None:
                bundle.idea.target_users = []
            if answer not in bundle.idea.target_users:
                bundle.idea.target_users.append(answer)
                integration_points.append("idea.target_users")
        else:
            # Try to find feature by related section
            for section in related_sections:
                if section.startswith("features.") and ".outcomes" in section:
                    feature_key = section.split(".")[1]
                    for feature in bundle.features:
                        if feature.key == feature_key:
                            if answer not in feature.outcomes:
                                feature.outcomes.append(answer)
                                integration_points.append(section)
                            break

    # Data Model, Integration, Constraints → features[].constraints
    elif category in (
        TaxonomyCategory.DATA_MODEL,
        TaxonomyCategory.INTEGRATION,
        TaxonomyCategory.CONSTRAINTS,
    ):
        related_sections = finding.related_sections or []
        for section in related_sections:
            if section.startswith("features.") and ".constraints" in section:
                feature_key = section.split(".")[1]
                for feature in bundle.features:
                    if feature.key == feature_key:
                        if answer not in feature.constraints:
                            feature.constraints.append(answer)
                            integration_points.append(section)
                        break
            elif section == "idea.constraints" and bundle.idea:
                if bundle.idea.constraints is None:
                    bundle.idea.constraints = []
                if answer not in bundle.idea.constraints:
                    bundle.idea.constraints.append(answer)
                    integration_points.append(section)

    # Edge Cases, Completion Signals, Interaction & UX Flow → features[].acceptance, stories[].acceptance
    elif category in (
        TaxonomyCategory.EDGE_CASES,
        TaxonomyCategory.COMPLETION_SIGNALS,
        TaxonomyCategory.INTERACTION_UX,
    ):
        related_sections = finding.related_sections or []
        for section in related_sections:
            if section.startswith("features."):
                parts = section.split(".")
                if len(parts) >= 3:
                    feature_key = parts[1]
                    if parts[2] == "acceptance":
                        for feature in bundle.features:
                            if feature.key == feature_key:
                                # Extract specific criteria from answer
                                specific_criteria = _extract_specific_criteria_from_answer(answer)
                                # Identify and remove vague criteria
                                vague_to_remove = _identify_vague_criteria_to_remove(feature.acceptance, finding)
                                # Remove vague criteria
                                for vague in vague_to_remove:
                                    if vague in feature.acceptance:
                                        feature.acceptance.remove(vague)
                                # Add new specific criteria
                                for criterion in specific_criteria:
                                    if criterion not in feature.acceptance:
                                        feature.acceptance.append(criterion)
                                if specific_criteria:
                                    integration_points.append(section)
                                break
                    elif parts[2] == "stories" and len(parts) >= 5:
                        story_key = parts[3]
                        if parts[4] == "acceptance":
                            for feature in bundle.features:
                                if feature.key == feature_key:
                                    for story in feature.stories:
                                        if story.key == story_key:
                                            # Extract specific criteria from answer
                                            specific_criteria = _extract_specific_criteria_from_answer(answer)
                                            # Identify and remove vague criteria
                                            vague_to_remove = _identify_vague_criteria_to_remove(
                                                story.acceptance, finding
                                            )
                                            # Remove vague criteria
                                            for vague in vague_to_remove:
                                                if vague in story.acceptance:
                                                    story.acceptance.remove(vague)
                                            # Add new specific criteria
                                            for criterion in specific_criteria:
                                                if criterion not in story.acceptance:
                                                    story.acceptance.append(criterion)
                                            if specific_criteria:
                                                integration_points.append(section)
                                            break
                                    break

    # Feature Completeness → features[].stories, features[].acceptance
    elif category == TaxonomyCategory.FEATURE_COMPLETENESS:
        related_sections = finding.related_sections or []
        for section in related_sections:
            if section.startswith("features."):
                parts = section.split(".")
                if len(parts) >= 3:
                    feature_key = parts[1]
                    if parts[2] == "stories":
                        # This would require creating a new story - skip for now
                        # (stories should be added via add-story command)
                        pass
                    elif parts[2] == "acceptance":
                        for feature in bundle.features:
                            if feature.key == feature_key:
                                if answer not in feature.acceptance:
                                    feature.acceptance.append(answer)
                                    integration_points.append(section)
                                break

    # Non-Functional → idea.constraints (with quantification)
    elif (
        category == TaxonomyCategory.NON_FUNCTIONAL
        and finding.related_sections
        and "idea.constraints" in finding.related_sections
        and bundle.idea
    ):
        if bundle.idea.constraints is None:
            bundle.idea.constraints = []
        if answer not in bundle.idea.constraints:
            # Try to quantify vague terms
            quantified_answer = answer
            bundle.idea.constraints.append(quantified_answer)
            integration_points.append("idea.constraints")

    return integration_points


@beartype
@require(lambda bundle: isinstance(bundle, PlanBundle), "Bundle must be PlanBundle")
@require(lambda finding: finding is not None, "Finding must not be None")
def _show_current_settings_for_finding(
    bundle: PlanBundle,
    finding: Any,  # AmbiguityFinding (imported locally to avoid circular dependency)
    console_instance: Any | None = None,  # Console (imported locally, optional)
) -> str | None:
    """
    Show current settings for related sections before asking a question.

    Displays current values for target_users, constraints, outcomes, acceptance criteria,
    and narrative so users can confirm or modify them.

    Args:
        bundle: Plan bundle to inspect
        finding: Ambiguity finding with related sections
        console_instance: Rich console instance (defaults to module console)

    Returns:
        Default value string to use in prompt (or None if no current value)
    """
    from rich.console import Console

    console = console_instance or Console()

    related_sections = finding.related_sections or []
    if not related_sections:
        return None

    # Only show high-level plan attributes (idea-level), not individual features/stories
    # Only show where there are findings to fix
    current_values: dict[str, list[str] | str] = {}
    default_value: str | None = None

    for section in related_sections:
        # Only handle idea-level sections (high-level plan attributes)
        if section == "idea.narrative" and bundle.idea and bundle.idea.narrative:
            narrative_preview = (
                bundle.idea.narrative[:100] + "..." if len(bundle.idea.narrative) > 100 else bundle.idea.narrative
            )
            current_values["Idea Narrative"] = narrative_preview
            # Use full narrative as default (truncated for display only)
            default_value = bundle.idea.narrative

        elif section == "idea.target_users" and bundle.idea and bundle.idea.target_users:
            current_values["Target Users"] = bundle.idea.target_users
            # Use comma-separated list as default
            if not default_value:
                default_value = ", ".join(bundle.idea.target_users)

        elif section == "idea.constraints" and bundle.idea and bundle.idea.constraints:
            current_values["Idea Constraints"] = bundle.idea.constraints
            # Use comma-separated list as default
            if not default_value:
                default_value = ", ".join(bundle.idea.constraints)

        # For Completion Signals questions, also extract story acceptance criteria
        # (these are the specific values we're asking about)
        elif section.startswith("features.") and ".stories." in section and ".acceptance" in section:
            parts = section.split(".")
            if len(parts) >= 5:
                feature_key = parts[1]
                story_key = parts[3]
                feature = next((f for f in bundle.features if f.key == feature_key), None)
                if feature:
                    story = next((s for s in feature.stories if s.key == story_key), None)
                    if story and story.acceptance:
                        # Show current acceptance criteria as default (for confirming or modifying)
                        acceptance_str = ", ".join(story.acceptance)
                        current_values[f"Story {story_key} Acceptance"] = story.acceptance
                        # Use first acceptance criteria as default (or all if short)
                        if not default_value:
                            default_value = acceptance_str if len(acceptance_str) <= 200 else story.acceptance[0]

        # Skip other feature/story-level sections - only show high-level plan attributes
        # Other features and stories are handled through their specific questions

    # Display current values if any (only high-level attributes)
    if current_values:
        console.print("\n[dim]Current Plan Settings:[/dim]")
        for key, value in current_values.items():
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value) if value else "(none)"
            else:
                value_str = str(value)
            console.print(f"  [cyan]{key}:[/cyan] {value_str}")
        console.print("[dim]Press Enter to confirm current value, or type a new value[/dim]")

    return default_value


@beartype
@require(lambda finding: finding is not None, "Finding must not be None")
@require(lambda bundle: isinstance(bundle, PlanBundle), "Bundle must be PlanBundle")
@require(lambda is_non_interactive: isinstance(is_non_interactive, bool), "Is non-interactive must be bool")
@ensure(lambda result: isinstance(result, str) and bool(result.strip()), "Must return non-empty string")
def _get_smart_answer(
    finding: Any,  # AmbiguityFinding (imported locally)
    bundle: PlanBundle,
    is_non_interactive: bool,
    default_value: str | None = None,
) -> str:
    """
    Get answer from user with smart Yes/No handling.

    For Completion Signals questions asking "Should these be more specific?",
    if user answers "Yes", prompts for the actual specific criteria.
    If "No", marks as acceptable and returns appropriate response.

    Args:
        finding: Ambiguity finding with question
        bundle: Plan bundle (for context)
        is_non_interactive: Whether in non-interactive mode
        default_value: Default value to show in prompt (for confirming existing value)

    Returns:
        User answer (processed if Yes/No detected)
    """
    from rich.console import Console

    from specfact_cli.analyzers.ambiguity_scanner import TaxonomyCategory

    console = Console()

    # Build prompt message with default hint
    if default_value:
        # Truncate default for display if too long
        default_display = default_value[:60] + "..." if len(default_value) > 60 else default_value
        prompt_msg = f"Your answer (press Enter to confirm, or type new value/Yes/No): [{default_display}]"
    else:
        prompt_msg = "Your answer (<=5 words recommended, or Yes/No):"

    # Get initial answer (not required if default exists - user can press Enter)
    # When default exists, allow empty answer (Enter) to confirm
    answer = prompt_text(prompt_msg, default=default_value, required=not default_value)

    # If user pressed Enter with default, return the default value (confirm existing)
    if not answer.strip() and default_value:
        return default_value

    # Normalize Yes/No answers
    answer_lower = answer.strip().lower()
    is_yes = answer_lower in ("yes", "y", "true", "1")
    is_no = answer_lower in ("no", "n", "false", "0")

    # Handle Completion Signals questions about specificity
    if (
        finding.category == TaxonomyCategory.COMPLETION_SIGNALS
        and "should these be more specific" in finding.question.lower()
    ):
        if is_yes:
            # User wants to make it more specific - prompt for actual criteria
            console.print("\n[yellow]Please provide the specific acceptance criteria:[/yellow]")
            return prompt_text("Specific criteria:", required=True)
        if is_no:
            # User says no - mark as acceptable, return a note that it's acceptable as-is
            return "Acceptable as-is (details in OpenAPI contracts)"
        # Otherwise, return the original answer (might be a specific criteria already)
        return answer

    # Handle other Yes/No questions intelligently
    # For questions asking if something should be done/added
    if (is_yes or is_no) and ("should" in finding.question.lower() or "need" in finding.question.lower()):
        if is_yes:
            # Prompt for what should be added
            console.print("\n[yellow]What should be added?[/yellow]")
            return prompt_text("Details:", required=True)
        if is_no:
            return "Not needed"

    # Return original answer if not a Yes/No or if Yes/No handling didn't apply
    return answer
