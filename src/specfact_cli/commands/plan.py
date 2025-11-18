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

from specfact_cli.analyzers.ambiguity_scanner import AmbiguityFinding
from specfact_cli.comparators.plan_comparator import PlanComparator
from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.generators.report_generator import ReportFormat, ReportGenerator
from specfact_cli.models.deviation import Deviation, ValidationReport
from specfact_cli.models.enforcement import EnforcementConfig
from specfact_cli.models.plan import Business, Feature, Idea, Metadata, PlanBundle, Product, Release, Story
from specfact_cli.modes import detect_mode
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
from specfact_cli.validators.schema import validate_plan_bundle


app = typer.Typer(help="Manage development plans, features, and stories")
console = Console()


@app.command("init")
@beartype
@require(lambda out: out is None or isinstance(out, Path), "Output must be None or Path")
def init(
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Interactive mode with prompts",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output plan bundle path (default: .specfact/plans/main.bundle.yaml)",
    ),
    scaffold: bool = typer.Option(
        True,
        "--scaffold/--no-scaffold",
        help="Create complete .specfact directory structure",
    ),
) -> None:
    """
    Initialize a new development plan.

    Creates a new plan bundle with idea, product, and features structure.
    Optionally scaffolds the complete .specfact/ directory structure.

    Example:
        specfact plan init                     # Interactive with scaffold
        specfact plan init --no-interactive    # Minimal plan
        specfact plan init --out .specfact/plans/feature-auth.bundle.yaml
    """
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {
        "interactive": interactive,
        "scaffold": scaffold,
    }

    with telemetry.track_command("plan.init", telemetry_metadata) as record:
        print_section("SpecFact CLI - Plan Builder")

        # Create .specfact structure if requested
        if scaffold:
            print_info("Creating .specfact/ directory structure...")
            SpecFactStructure.scaffold_project()
            print_success("Directory structure created")
        else:
            # Ensure minimum structure exists
            SpecFactStructure.ensure_structure()

        # Use default path if not specified
        if out is None:
            out = SpecFactStructure.get_default_plan_path()

        if not interactive:
            # Non-interactive mode: create minimal plan
            _create_minimal_plan(out)
            record({"plan_type": "minimal"})
            return

        # Interactive mode: guided plan creation
        try:
            plan = _build_plan_interactively()

            # Generate plan file
            out.parent.mkdir(parents=True, exist_ok=True)
            generator = PlanGenerator()
            generator.generate(plan, out)

            # Record plan statistics
            record(
                {
                    "plan_type": "interactive",
                    "features_count": len(plan.features) if plan.features else 0,
                    "stories_count": sum(len(f.stories) for f in plan.features) if plan.features else 0,
                }
            )

            print_success(f"Plan created successfully: {out}")

            # Validate
            is_valid, error, _ = validate_plan_bundle(out)
            if is_valid:
                print_success("Plan validation passed")
            else:
                print_warning(f"Plan has validation issues: {error}")

        except KeyboardInterrupt:
            print_warning("\nPlan creation cancelled")
            raise typer.Exit(1) from None
        except Exception as e:
            print_error(f"Failed to create plan: {e}")
            raise typer.Exit(1) from e


def _create_minimal_plan(out: Path) -> None:
    """Create a minimal plan bundle."""
    plan = PlanBundle(
        version="1.0",
        idea=None,
        business=None,
        product=Product(themes=[], releases=[]),
        features=[],
        metadata=None,
        clarifications=None,
    )

    generator = PlanGenerator()
    generator.generate(plan, out)
    print_success(f"Minimal plan created: {out}")


def _build_plan_interactively() -> PlanBundle:
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

    # Create plan bundle
    plan = PlanBundle(
        version="1.0",
        idea=idea,
        business=business,
        product=product,
        features=features,
        metadata=None,
        clarifications=None,
    )

    # Final summary
    print_section("Plan Summary")
    console.print(f"[cyan]Title:[/cyan] {idea.title}")
    console.print(f"[cyan]Themes:[/cyan] {', '.join(product.themes)}")
    console.print(f"[cyan]Features:[/cyan] {len(features)}")
    console.print(f"[cyan]Releases:[/cyan] {len(product.releases)}")

    return plan


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
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
def add_feature(
    key: str = typer.Option(..., "--key", help="Feature key (e.g., FEATURE-001)"),
    title: str = typer.Option(..., "--title", help="Feature title"),
    outcomes: str | None = typer.Option(None, "--outcomes", help="Expected outcomes (comma-separated)"),
    acceptance: str | None = typer.Option(None, "--acceptance", help="Acceptance criteria (comma-separated)"),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to plan bundle (default: .specfact/plans/main.bundle.yaml)",
    ),
) -> None:
    """
    Add a new feature to an existing plan.

    Example:
        specfact plan add-feature --key FEATURE-001 --title "User Auth" --outcomes "Secure login" --acceptance "Login works"
    """
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {
        "feature_key": key,
    }

    with telemetry.track_command("plan.add_feature", telemetry_metadata) as record:
        # Use default path if not specified
        if plan is None:
            plan = SpecFactStructure.get_default_plan_path()
            if not plan.exists():
                print_error(f"Default plan not found: {plan}\nCreate one with: specfact plan init --interactive")
                raise typer.Exit(1)
            print_info(f"Using default plan: {plan}")

        if not plan.exists():
            print_error(f"Plan bundle not found: {plan}")
            raise typer.Exit(1)

        print_section("SpecFact CLI - Add Feature")

        try:
            # Load existing plan
            print_info(f"Loading plan: {plan}")
            validation_result = validate_plan_bundle(plan)
            assert isinstance(validation_result, tuple), "Expected tuple from validate_plan_bundle for Path"
            is_valid, error, existing_plan = validation_result

            if not is_valid or existing_plan is None:
                print_error(f"Plan validation failed: {error}")
                raise typer.Exit(1)

            # Check if feature key already exists
            existing_keys = {f.key for f in existing_plan.features}
            if key in existing_keys:
                print_error(f"Feature '{key}' already exists in plan")
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
            )

            # Add feature to plan
            existing_plan.features.append(new_feature)

            # Validate updated plan (always passes for PlanBundle model)
            print_info("Validating updated plan...")

            # Save updated plan
            print_info(f"Saving plan to: {plan}")
            generator = PlanGenerator()
            generator.generate(existing_plan, plan)

            record(
                {
                    "total_features": len(existing_plan.features),
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
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
def add_story(
    feature: str = typer.Option(..., "--feature", help="Parent feature key"),
    key: str = typer.Option(..., "--key", help="Story key (e.g., STORY-001)"),
    title: str = typer.Option(..., "--title", help="Story title"),
    acceptance: str | None = typer.Option(None, "--acceptance", help="Acceptance criteria (comma-separated)"),
    story_points: int | None = typer.Option(None, "--story-points", help="Story points (complexity)"),
    value_points: int | None = typer.Option(None, "--value-points", help="Value points (business value)"),
    draft: bool = typer.Option(False, "--draft", help="Mark story as draft"),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to plan bundle (default: .specfact/plans/main.bundle.yaml)",
    ),
) -> None:
    """
    Add a new story to a feature.

    Example:
        specfact plan add-story --feature FEATURE-001 --key STORY-001 --title "Login API" --acceptance "API works" --story-points 5
    """
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {
        "feature_key": feature,
        "story_key": key,
    }

    with telemetry.track_command("plan.add_story", telemetry_metadata) as record:
        # Use default path if not specified
        if plan is None:
            plan = SpecFactStructure.get_default_plan_path()
            if not plan.exists():
                print_error(f"Default plan not found: {plan}\nCreate one with: specfact plan init --interactive")
                raise typer.Exit(1)
            print_info(f"Using default plan: {plan}")

        if not plan.exists():
            print_error(f"Plan bundle not found: {plan}")
            raise typer.Exit(1)

        print_section("SpecFact CLI - Add Story")

        try:
            # Load existing plan
            print_info(f"Loading plan: {plan}")
            validation_result = validate_plan_bundle(plan)
            assert isinstance(validation_result, tuple), "Expected tuple from validate_plan_bundle for Path"
            is_valid, error, existing_plan = validation_result

            if not is_valid or existing_plan is None:
                print_error(f"Plan validation failed: {error}")
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

            # Validate updated plan (always passes for PlanBundle model)
            print_info("Validating updated plan...")

            # Save updated plan
            print_info(f"Saving plan to: {plan}")
            generator = PlanGenerator()
            generator.generate(existing_plan, plan)

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
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
def update_idea(
    title: str | None = typer.Option(None, "--title", help="Idea title"),
    narrative: str | None = typer.Option(None, "--narrative", help="Idea narrative (brief description)"),
    target_users: str | None = typer.Option(None, "--target-users", help="Target user personas (comma-separated)"),
    value_hypothesis: str | None = typer.Option(None, "--value-hypothesis", help="Value hypothesis statement"),
    constraints: str | None = typer.Option(None, "--constraints", help="Idea-level constraints (comma-separated)"),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to plan bundle (default: active plan or latest)",
    ),
) -> None:
    """
    Update idea section metadata in a plan bundle (optional business context).

    This command allows updating idea properties (title, narrative, target users,
    value hypothesis, constraints) in non-interactive environments (CI/CD, Copilot).

    Note: The idea section is OPTIONAL - it provides business context and metadata,
    not technical implementation details. All parameters are optional.

    Example:
        specfact plan update-idea --target-users "Developers, DevOps" --value-hypothesis "Reduce technical debt"
        specfact plan update-idea --constraints "Python 3.11+, Maintain backward compatibility"
    """
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {}

    with telemetry.track_command("plan.update_idea", telemetry_metadata) as record:
        # Use default path if not specified
        if plan is None:
            default_plan = SpecFactStructure.get_default_plan_path()
            if default_plan.exists():
                plan = default_plan
                print_info(f"Using default plan: {plan}")
            else:
                # Find latest plan bundle
                base_path = Path(".")
                plans_dir = base_path / SpecFactStructure.PLANS
                if plans_dir.exists():
                    plan_files = sorted(plans_dir.glob("*.bundle.yaml"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if plan_files:
                        plan = plan_files[0]
                        print_info(f"Using latest plan: {plan}")
                    else:
                        print_error(f"No plan bundles found in {plans_dir}")
                        print_error("Create one with: specfact plan init --interactive")
                        raise typer.Exit(1)
                else:
                    print_error(f"Plans directory not found: {plans_dir}")
                    print_error("Create one with: specfact plan init --interactive")
                    raise typer.Exit(1)

        # Type guard: ensure plan is not None
        if plan is None:
            print_error("Plan bundle path is required")
            raise typer.Exit(1)

        if not plan.exists():
            print_error(f"Plan bundle not found: {plan}")
            raise typer.Exit(1)

        print_section("SpecFact CLI - Update Idea")

        try:
            # Load existing plan
            print_info(f"Loading plan: {plan}")
            validation_result = validate_plan_bundle(plan)
            assert isinstance(validation_result, tuple), "Expected tuple from validate_plan_bundle for Path"
            is_valid, error, existing_plan = validation_result

            if not is_valid or existing_plan is None:
                print_error(f"Plan validation failed: {error}")
                raise typer.Exit(1)

            # Create idea section if it doesn't exist
            if existing_plan.idea is None:
                existing_plan.idea = Idea(
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
                existing_plan.idea.title = title
                updates_made.append("title")

            # Update narrative if provided
            if narrative is not None:
                existing_plan.idea.narrative = narrative
                updates_made.append("narrative")

            # Update target_users if provided
            if target_users is not None:
                target_users_list = [u.strip() for u in target_users.split(",")] if target_users else []
                existing_plan.idea.target_users = target_users_list
                updates_made.append("target_users")

            # Update value_hypothesis if provided
            if value_hypothesis is not None:
                existing_plan.idea.value_hypothesis = value_hypothesis
                updates_made.append("value_hypothesis")

            # Update constraints if provided
            if constraints is not None:
                constraints_list = [c.strip() for c in constraints.split(",")] if constraints else []
                existing_plan.idea.constraints = constraints_list
                updates_made.append("constraints")

            if not updates_made:
                print_warning(
                    "No updates specified. Use --title, --narrative, --target-users, --value-hypothesis, or --constraints"
                )
                raise typer.Exit(1)

            # Validate updated plan (always passes for PlanBundle model)
            print_info("Validating updated plan...")

            # Save updated plan
            # Type guard: ensure plan is not None (should never happen here, but type checker needs it)
            if plan is None:
                print_error("Plan bundle path is required")
                raise typer.Exit(1)
            print_info(f"Saving plan to: {plan}")
            generator = PlanGenerator()
            generator.generate(existing_plan, plan)

            record(
                {
                    "updates": updates_made,
                    "idea_exists": existing_plan.idea is not None,
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
@require(lambda key: isinstance(key, str) and len(key) > 0, "Key must be non-empty string")
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
def update_feature(
    key: str = typer.Option(..., "--key", help="Feature key to update (e.g., FEATURE-001)"),
    title: str | None = typer.Option(None, "--title", help="Feature title"),
    outcomes: str | None = typer.Option(None, "--outcomes", help="Expected outcomes (comma-separated)"),
    acceptance: str | None = typer.Option(None, "--acceptance", help="Acceptance criteria (comma-separated)"),
    constraints: str | None = typer.Option(None, "--constraints", help="Constraints (comma-separated)"),
    confidence: float | None = typer.Option(None, "--confidence", help="Confidence score (0.0-1.0)"),
    draft: bool | None = typer.Option(None, "--draft", help="Mark as draft (true/false)"),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to plan bundle (default: .specfact/plans/main.bundle.yaml)",
    ),
) -> None:
    """
    Update an existing feature's metadata in a plan bundle.

    This command allows updating feature properties (title, outcomes, acceptance criteria,
    constraints, confidence, draft status) in non-interactive environments (CI/CD, Copilot).

    Example:
        specfact plan update-feature --key FEATURE-001 --title "Updated Title" --outcomes "Outcome 1, Outcome 2"
        specfact plan update-feature --key FEATURE-001 --acceptance "Criterion 1, Criterion 2" --confidence 0.9
    """
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {
        "feature_key": key,
    }

    with telemetry.track_command("plan.update_feature", telemetry_metadata) as record:
        # Use default path if not specified
        if plan is None:
            plan = SpecFactStructure.get_default_plan_path()
            if not plan.exists():
                print_error(f"Default plan not found: {plan}\nCreate one with: specfact plan init --interactive")
                raise typer.Exit(1)
            print_info(f"Using default plan: {plan}")

        if not plan.exists():
            print_error(f"Plan bundle not found: {plan}")
            raise typer.Exit(1)

        print_section("SpecFact CLI - Update Feature")

        try:
            # Load existing plan
            print_info(f"Loading plan: {plan}")
            validation_result = validate_plan_bundle(plan)
            assert isinstance(validation_result, tuple), "Expected tuple from validate_plan_bundle for Path"
            is_valid, error, existing_plan = validation_result

            if not is_valid or existing_plan is None:
                print_error(f"Plan validation failed: {error}")
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

            # Validate updated plan (always passes for PlanBundle model)
            print_info("Validating updated plan...")

            # Save updated plan
            print_info(f"Saving plan to: {plan}")
            generator = PlanGenerator()
            generator.generate(existing_plan, plan)

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


@app.command("compare")
@beartype
@require(lambda manual: manual is None or isinstance(manual, Path), "Manual must be None or Path")
@require(lambda auto: auto is None or isinstance(auto, Path), "Auto must be None or Path")
@require(
    lambda format: isinstance(format, str) and format.lower() in ("markdown", "json", "yaml"),
    "Format must be markdown, json, or yaml",
)
@require(lambda out: out is None or isinstance(out, Path), "Out must be None or Path")
def compare(
    manual: Path | None = typer.Option(
        None,
        "--manual",
        help="Manual plan bundle path (default: .specfact/plans/main.bundle.yaml)",
    ),
    auto: Path | None = typer.Option(
        None,
        "--auto",
        help="Auto-derived plan bundle path (default: latest in .specfact/plans/)",
    ),
    code_vs_plan: bool = typer.Option(
        False,
        "--code-vs-plan",
        help="Alias for comparing code-derived plan vs manual plan (auto-detects latest auto plan)",
    ),
    format: str = typer.Option(
        "markdown",
        "--format",
        help="Output format (markdown, json, yaml)",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Output file path (default: .specfact/reports/comparison/deviations-<timestamp>.md)",
    ),
) -> None:
    """
    Compare manual and auto-derived plans to detect code vs plan drift.

    Detects deviations between manually created plans (intended design) and
    reverse-engineered plans from code (actual implementation). This comparison
    identifies code vs plan drift automatically.

    Use --code-vs-plan for convenience: automatically compares the latest
    code-derived plan against the manual plan.

    Example:
        specfact plan compare --manual .specfact/plans/main.bundle.yaml --auto .specfact/plans/auto-derived-<timestamp>.bundle.yaml
        specfact plan compare --code-vs-plan  # Convenience alias
    """
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {
        "code_vs_plan": code_vs_plan,
        "format": format.lower(),
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
                        f"Default manual plan not found: {manual}\nCreate one with: specfact plan init --interactive"
                    )
                    raise typer.Exit(1)
                print_info(f"Using default manual plan: {manual}")

            # Auto-detect latest code-derived plan
            if auto is None:
                auto = SpecFactStructure.get_latest_brownfield_report()
                if auto is None:
                    plans_dir = Path(SpecFactStructure.PLANS)
                    print_error(
                        f"No code-derived plans found in {plans_dir}\nGenerate one with: specfact import from-code --repo ."
                    )
                    raise typer.Exit(1)
                print_info(f"Using latest code-derived plan: {auto}")

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
                    f"Default manual plan not found: {manual}\nCreate one with: specfact plan init --interactive"
                )
                raise typer.Exit(1)
            print_info(f"Using default manual plan: {manual}")

        if auto is None:
            # Use smart default: find latest auto-derived plan
            auto = SpecFactStructure.get_latest_brownfield_report()
            if auto is None:
                plans_dir = Path(SpecFactStructure.PLANS)
                print_error(
                    f"No auto-derived plans found in {plans_dir}\nGenerate one with: specfact import from-code --repo ."
                )
                raise typer.Exit(1)
            print_info(f"Using latest auto-derived plan: {auto}")

        if out is None:
            # Use smart default: timestamped comparison report
            extension = {"markdown": "md", "json": "json", "yaml": "yaml"}[format.lower()]
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

        # Validate format
        if format.lower() not in ("markdown", "json", "yaml"):
            print_error(f"Invalid format: {format}. Must be markdown, json, or yaml")
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
                print_info(f"Generating {format} report...")
                generator = ReportGenerator()

                # Map format string to enum
                format_map = {
                    "markdown": ReportFormat.MARKDOWN,
                    "json": ReportFormat.JSON,
                    "yaml": ReportFormat.YAML,
                }

                report_format = format_map.get(format.lower(), ReportFormat.MARKDOWN)
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
def select(
    plan: str | None = typer.Argument(
        None,
        help="Plan name or number to select (e.g., 'main.bundle.yaml' or '1')",
    ),
) -> None:
    """
    Select active plan from available plan bundles.

    Displays a numbered list of available plans and allows selection by number or name.
    The selected plan becomes the active plan tracked in `.specfact/plans/config.yaml`.

    Example:
        specfact plan select                    # Interactive selection
        specfact plan select 1                 # Select by number
        specfact plan select main.bundle.yaml   # Select by name
    """
    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {}

    with telemetry.track_command("plan.select", telemetry_metadata) as record:
        print_section("SpecFact CLI - Plan Selection")

        # List all available plans
        plans = SpecFactStructure.list_plans()

        if not plans:
            print_warning("No plan bundles found in .specfact/plans/")
            print_info("Create a plan with:")
            print_info("  - specfact plan init")
            print_info("  - specfact import from-code")
            raise typer.Exit(1)

        # If plan provided, try to resolve it
        if plan is not None:
            # Try as number first
            if isinstance(plan, str) and plan.isdigit():
                plan_num = int(plan)
                if 1 <= plan_num <= len(plans):
                    selected_plan = plans[plan_num - 1]
                else:
                    print_error(f"Invalid plan number: {plan_num}. Must be between 1 and {len(plans)}")
                    raise typer.Exit(1)
            else:
                # Try as name
                plan_name = str(plan)
                # Remove .bundle.yaml suffix if present
                if plan_name.endswith(".bundle.yaml"):
                    plan_name = plan_name
                elif not plan_name.endswith(".yaml"):
                    plan_name = f"{plan_name}.bundle.yaml"

                # Find matching plan
                selected_plan = None
                for p in plans:
                    if p["name"] == plan_name or p["name"] == plan:
                        selected_plan = p
                        break

                if selected_plan is None:
                    print_error(f"Plan not found: {plan}")
                    print_info("Available plans:")
                    for i, p in enumerate(plans, 1):
                        print_info(f"  {i}. {p['name']}")
                    raise typer.Exit(1)
        else:
            # Interactive selection - display numbered list
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

            for i, p in enumerate(plans, 1):
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

            # Prompt for selection
            selection = ""
            try:
                selection = prompt_text(f"Select a plan by number (1-{len(plans)}) or 'q' to quit: ").strip()

                if selection.lower() in ("q", "quit", ""):
                    print_info("Selection cancelled")
                    raise typer.Exit(0)

                plan_num = int(selection)
                if not (1 <= plan_num <= len(plans)):
                    print_error(f"Invalid selection: {plan_num}. Must be between 1 and {len(plans)}")
                    raise typer.Exit(1)

                selected_plan = plans[plan_num - 1]
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
                "selected_plan": plan_name,
                "features": selected_plan["features"],
                "stories": selected_plan["stories"],
            }
        )

        print_success(f"Active plan set to: {plan_name}")
        print_info(f"  Features: {selected_plan['features']}")
        print_info(f"  Stories: {selected_plan['stories']}")
        print_info(f"  Stage: {selected_plan.get('stage', 'unknown')}")

        print_info("\nThis plan will now be used as the default for:")
        print_info("  - specfact plan compare")
        print_info("  - specfact plan promote")
        print_info("  - specfact plan add-feature")
        print_info("  - specfact plan add-story")
        print_info("  - specfact plan sync --shared")
        print_info("  - specfact sync spec-kit")


@app.command("sync")
@beartype
@require(lambda repo: repo is None or isinstance(repo, Path), "Repo must be None or Path")
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@require(lambda overwrite: isinstance(overwrite, bool), "Overwrite must be bool")
@require(lambda watch: isinstance(watch, bool), "Watch must be bool")
@require(lambda interval: isinstance(interval, int) and interval >= 1, "Interval must be int >= 1")
def sync(
    shared: bool = typer.Option(
        False,
        "--shared",
        help="Enable shared plans sync (bidirectional sync with Spec-Kit)",
    ),
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


@app.command("promote")
@beartype
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@require(
    lambda stage: stage in ("draft", "review", "approved", "released"),
    "Stage must be draft, review, approved, or released",
)
def promote(
    stage: str = typer.Option(..., "--stage", help="Target stage (draft, review, approved, released)"),
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to plan bundle (default: .specfact/plans/main.bundle.yaml)",
    ),
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
    Promote a plan bundle through development stages.

    Stages: draft → review → approved → released

    Example:
        specfact plan promote --stage review
        specfact plan promote --stage approved --validate
        specfact plan promote --stage released --force
    """
    import os
    from datetime import datetime

    from specfact_cli.utils.structure import SpecFactStructure

    telemetry_metadata = {
        "target_stage": stage,
        "validate": validate,
        "force": force,
    }

    with telemetry.track_command("plan.promote", telemetry_metadata) as record:
        # Use default path if not specified
        if plan is None:
            plan = SpecFactStructure.get_default_plan_path()
            if not plan.exists():
                print_error(f"Default plan not found: {plan}\nCreate one with: specfact plan init --interactive")
                raise typer.Exit(1)
            print_info(f"Using default plan: {plan}")

        if not plan.exists():
            print_error(f"Plan bundle not found: {plan}")
            raise typer.Exit(1)

        print_section("SpecFact CLI - Plan Promotion")

        try:
            # Load existing plan
            print_info(f"Loading plan: {plan}")
            validation_result = validate_plan_bundle(plan)
            assert isinstance(validation_result, tuple), "Expected tuple from validate_plan_bundle for Path"
            is_valid, error, bundle = validation_result

            if not is_valid or bundle is None:
                print_error(f"Plan validation failed: {error}")
                raise typer.Exit(1)

            # Check current stage
            current_stage = "draft"
            if bundle.metadata:
                current_stage = bundle.metadata.stage

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

            # Draft → Review: All features must have at least one story
            if current_stage == "draft" and stage == "review":
                features_without_stories = [f for f in bundle.features if len(f.stories) == 0]
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
                    report = scanner.scan(bundle)

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
                print_info("Validating all features...")
                incomplete_features: list[Feature] = []
                for f in bundle.features:
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
                report_approved = scanner_approved.scan(bundle)

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
                validation_result = validate_plan_bundle(bundle)
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

            # Update metadata
            print_info(f"Promoting plan: {current_stage} → {stage}")

            # Get user info
            promoted_by = (
                os.environ.get("USER") or os.environ.get("USERNAME") or os.environ.get("GIT_AUTHOR_NAME") or "unknown"
            )

            # Create or update metadata
            if bundle.metadata is None:
                bundle.metadata = Metadata(
                    stage=stage,
                    promoted_at=None,
                    promoted_by=None,
                    analysis_scope=None,
                    entry_point=None,
                    external_dependencies=[],
                )

            bundle.metadata.stage = stage
            bundle.metadata.promoted_at = datetime.now(UTC).isoformat()
            bundle.metadata.promoted_by = promoted_by

            # Write updated plan
            print_info(f"Saving plan to: {plan}")
            generator = PlanGenerator()
            generator.generate(bundle, plan)

            record(
                {
                    "current_stage": current_stage,
                    "target_stage": stage,
                    "features_count": len(bundle.features) if bundle.features else 0,
                }
            )

            # Display summary
            print_success(f"Plan promoted: {current_stage} → {stage}")
            console.print(f"[dim]Promoted at: {bundle.metadata.promoted_at}[/dim]")
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


@app.command("review")
@beartype
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@require(lambda max_questions: max_questions > 0, "Max questions must be positive")
def review(
    plan: Path | None = typer.Option(
        None,
        "--plan",
        help="Path to plan bundle (default: active plan or latest)",
    ),
    max_questions: int = typer.Option(
        5,
        "--max-questions",
        min=1,
        max=10,
        help="Maximum questions per session (default: 5)",
    ),
    category: str | None = typer.Option(
        None,
        "--category",
        help="Focus on specific taxonomy category (optional)",
    ),
    list_questions: bool = typer.Option(
        False,
        "--list-questions",
        help="Output questions in JSON format without asking (for Copilot mode)",
    ),
    answers: str | None = typer.Option(
        None,
        "--answers",
        help="JSON object with question_id -> answer mappings (for non-interactive mode). Can be JSON string or path to JSON file.",
    ),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Non-interactive mode (for CI/CD automation)",
    ),
    auto_enrich: bool = typer.Option(
        False,
        "--auto-enrich",
        help="Automatically enrich vague acceptance criteria, incomplete requirements, and generic tasks using LLM-enhanced pattern matching",
    ),
) -> None:
    """
    Review plan bundle to identify and resolve ambiguities.

    Analyzes the plan bundle for missing information, unclear requirements,
    and unknowns. Asks targeted questions to resolve ambiguities and make
    the plan ready for promotion.

    Example:
        specfact plan review
        specfact plan review --plan .specfact/plans/main.bundle.yaml
        specfact plan review --max-questions 3 --category "Functional Scope"
        specfact plan review --list-questions  # Output questions as JSON
        specfact plan review --answers '{"Q001": "answer1", "Q002": "answer2"}'  # Non-interactive
    """
    from datetime import date, datetime

    from specfact_cli.analyzers.ambiguity_scanner import (
        AmbiguityScanner,
        AmbiguityStatus,
        TaxonomyCategory,
    )
    from specfact_cli.models.plan import Clarification, Clarifications, ClarificationSession
    from specfact_cli.utils.structure import SpecFactStructure

    # Detect operational mode
    mode = detect_mode()
    is_non_interactive = non_interactive or (answers is not None) or list_questions

    telemetry_metadata = {
        "max_questions": max_questions,
        "category": category,
        "list_questions": list_questions,
        "non_interactive": is_non_interactive,
        "mode": mode.value,
    }

    with telemetry.track_command("plan.review", telemetry_metadata) as record:
        # Use default path if not specified
        if plan is None:
            # Try to find active plan or latest
            default_plan = SpecFactStructure.get_default_plan_path()
            if default_plan.exists():
                plan = default_plan
                print_info(f"Using default plan: {plan}")
            else:
                # Find latest plan bundle
                base_path = Path(".")
                plans_dir = base_path / SpecFactStructure.PLANS
                if plans_dir.exists():
                    plan_files = sorted(plans_dir.glob("*.bundle.yaml"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if plan_files:
                        plan = plan_files[0]
                        print_info(f"Using latest plan: {plan}")
                    else:
                        print_error(f"No plan bundles found in {plans_dir}")
                        print_error("Create one with: specfact plan init --interactive")
                        raise typer.Exit(1)
                else:
                    print_error(f"Plans directory not found: {plans_dir}")
                    print_error("Create one with: specfact plan init --interactive")
                    raise typer.Exit(1)

        # Type guard: ensure plan is not None
        if plan is None:
            print_error("Plan bundle path is required")
            raise typer.Exit(1)

        if not plan.exists():
            print_error(f"Plan bundle not found: {plan}")
            raise typer.Exit(1)

        print_section("SpecFact CLI - Plan Review")

        try:
            # Load existing plan
            print_info(f"Loading plan: {plan}")
            validation_result = validate_plan_bundle(plan)
            assert isinstance(validation_result, tuple), "Expected tuple from validate_plan_bundle for Path"
            is_valid, error, bundle = validation_result

            if not is_valid or bundle is None:
                print_error(f"Plan validation failed: {error}")
                raise typer.Exit(1)

            # Check current stage
            current_stage = "draft"
            if bundle.metadata:
                current_stage = bundle.metadata.stage

            print_info(f"Current stage: {current_stage}")

            if current_stage not in ("draft", "review"):
                print_warning("Review is typically run on 'draft' or 'review' stage plans")
                if not is_non_interactive and not prompt_confirm("Continue anyway?", default=False):
                    raise typer.Exit(0)
                if is_non_interactive:
                    print_info("Continuing in non-interactive mode")

            # Initialize clarifications if needed
            if bundle.clarifications is None:
                bundle.clarifications = Clarifications(sessions=[])

            # Auto-enrich if requested (before scanning for ambiguities)
            if auto_enrich:
                print_info(
                    "Auto-enriching plan bundle (enhancing vague acceptance criteria, incomplete requirements, generic tasks)..."
                )
                from specfact_cli.enrichers.plan_enricher import PlanEnricher

                enricher = PlanEnricher()
                enrichment_summary = enricher.enrich_plan(bundle)

                if enrichment_summary["features_updated"] > 0 or enrichment_summary["stories_updated"] > 0:
                    # Save enriched plan bundle
                    generator = PlanGenerator()
                    generator.generate(bundle, plan)
                    print_success(
                        f"✓ Auto-enriched plan bundle: {enrichment_summary['features_updated']} features, "
                        f"{enrichment_summary['stories_updated']} stories updated"
                    )
                    if enrichment_summary["acceptance_criteria_enhanced"] > 0:
                        console.print(
                            f"[dim]  - Enhanced {enrichment_summary['acceptance_criteria_enhanced']} acceptance criteria[/dim]"
                        )
                    if enrichment_summary["requirements_enhanced"] > 0:
                        console.print(
                            f"[dim]  - Enhanced {enrichment_summary['requirements_enhanced']} requirements[/dim]"
                        )
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

            # Scan for ambiguities
            print_info("Scanning plan bundle for ambiguities...")
            scanner = AmbiguityScanner()
            report = scanner.scan(bundle)

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
            for session in bundle.clarifications.sessions:
                for q in session.questions:
                    existing_question_ids.add(q.id)

            # Generate question IDs and filter
            question_counter = 1
            candidate_questions: list[tuple[AmbiguityFinding, str]] = []
            for finding in prioritized_findings:
                if finding.question and (question_id := f"Q{question_counter:03d}") not in existing_question_ids:
                    # Generate question ID and add if not already answered
                    question_counter += 1
                    candidate_questions.append((finding, question_id))

            # Limit to max_questions
            questions_to_ask = candidate_questions[:max_questions]

            if not questions_to_ask:
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
                                "✅"
                                if status == AmbiguityStatus.CLEAR
                                else "⚠️"
                                if status == AmbiguityStatus.PARTIAL
                                else "❌"
                            )
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
                                "✅"
                                if status == AmbiguityStatus.CLEAR
                                else "⚠️"
                                if status == AmbiguityStatus.PARTIAL
                                else "❌"
                            )
                            console.print(f"  {status_icon} {cat.value}: {status.value}")
                raise typer.Exit(0)

            # Handle --list-questions mode
            if list_questions:
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
                # Output JSON to stdout (for Copilot mode parsing)
                import sys

                sys.stdout.write(json.dumps({"questions": questions_json, "total": len(questions_json)}, indent=2))
                sys.stdout.write("\n")
                sys.stdout.flush()
                raise typer.Exit(0)

            # Parse answers if provided
            answers_dict: dict[str, str] = {}
            if answers:
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
                except (json.JSONDecodeError, ValueError) as e:
                    print_error(f"Invalid JSON in --answers: {e}")
                    raise typer.Exit(1) from e

            print_info(f"Found {len(questions_to_ask)} question(s) to resolve")

            # Create or get today's session
            today = date.today().isoformat()
            today_session: ClarificationSession | None = None
            for session in bundle.clarifications.sessions:
                if session.date == today:
                    today_session = session
                    break

            if today_session is None:
                today_session = ClarificationSession(date=today, questions=[])
                bundle.clarifications.sessions.append(today_session)

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
                else:
                    # Interactive: prompt user
                    if is_non_interactive:
                        # In non-interactive mode without --answers, skip this question
                        print_warning(f"Skipping {question_id}: no answer provided in non-interactive mode")
                        continue

                    console.print(f"\n[bold cyan]Question {questions_asked}/{len(questions_to_ask)}[/bold cyan]")
                    console.print(f"[dim]Category: {finding.category.value}[/dim]")
                    console.print(f"[bold]Q: {finding.question}[/bold]")

                    # Get answer from user
                    answer = prompt_text("Your answer (<=5 words recommended):", required=True)

                # Validate answer length (warn if too long, but allow)
                if len(answer.split()) > 5:
                    print_warning("Answer is longer than 5 words. Consider a shorter, more focused answer.")

                # Integrate answer into plan bundle
                integration_points = _integrate_clarification(bundle, finding, answer)

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

                # Save plan bundle after each answer (atomic)
                print_info("Saving plan bundle...")
                if plan is not None:
                    generator = PlanGenerator()
                    generator.generate(bundle, plan)

                print_success("Answer recorded and integrated into plan bundle")

                # Ask if user wants to continue (only in interactive mode)
                if (
                    not is_non_interactive
                    and questions_asked < len(questions_to_ask)
                    and not prompt_confirm("Continue to next question?", default=True)
                ):
                    break

            # Final validation
            print_info("Validating updated plan bundle...")
            validation_result = validate_plan_bundle(bundle)
            if isinstance(validation_result, ValidationReport):
                if not validation_result.passed:
                    print_warning(f"Validation found {len(validation_result.deviations)} issue(s)")
                else:
                    print_success("Validation passed")
            else:
                print_success("Validation passed")

            # Display summary
            print_success(f"Review complete: {questions_asked} question(s) answered")
            console.print(f"\n[bold]Plan Bundle:[/bold] {plan}")
            console.print(f"[bold]Questions Asked:[/bold] {questions_asked}")

            if today_session.questions:
                console.print("\n[bold]Sections Touched:[/bold]")
                all_sections = set()
                for q in today_session.questions:
                    all_sections.update(q.integrated_into)
                for section in sorted(all_sections):
                    console.print(f"  • {section}")

            # Coverage summary
            console.print("\n[bold]Coverage Summary:[/bold]")
            if report.coverage:
                for cat, status in report.coverage.items():
                    status_icon = (
                        "✅" if status == AmbiguityStatus.CLEAR else "⚠️" if status == AmbiguityStatus.PARTIAL else "❌"
                    )
                    console.print(f"  {status_icon} {cat.value}: {status.value}")

            # Next steps
            console.print("\n[bold]Next Steps:[/bold]")
            if current_stage == "draft":
                console.print("  • Review plan bundle for completeness")
                console.print("  • Run: specfact plan promote --stage review")
            elif current_stage == "review":
                console.print("  • Plan is ready for approval")
                console.print("  • Run: specfact plan promote --stage approved")

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

    # Edge Cases, Completion Signals → features[].acceptance, stories[].acceptance
    elif category in (TaxonomyCategory.EDGE_CASES, TaxonomyCategory.COMPLETION_SIGNALS):
        related_sections = finding.related_sections or []
        for section in related_sections:
            if section.startswith("features."):
                parts = section.split(".")
                if len(parts) >= 3:
                    feature_key = parts[1]
                    if parts[2] == "acceptance":
                        for feature in bundle.features:
                            if feature.key == feature_key:
                                if answer not in feature.acceptance:
                                    feature.acceptance.append(answer)
                                    integration_points.append(section)
                                break
                    elif parts[2] == "stories" and len(parts) >= 5:
                        story_key = parts[3]
                        if parts[4] == "acceptance":
                            for feature in bundle.features:
                                if feature.key == feature_key:
                                    for story in feature.stories:
                                        if story.key == story_key:
                                            if answer not in story.acceptance:
                                                story.acceptance.append(answer)
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
