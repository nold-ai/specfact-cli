"""
Plan command - Manage greenfield development plans.

This module provides commands for creating and managing development plans,
features, and stories.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import UTC
from pathlib import Path
from typing import Any, Optional

import typer
from beartype import beartype
from icontract import require
from rich.console import Console
from rich.table import Table

from specfact_cli.comparators.plan_comparator import PlanComparator
from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.generators.report_generator import ReportFormat, ReportGenerator
from specfact_cli.models.deviation import ValidationReport
from specfact_cli.models.enforcement import EnforcementConfig
from specfact_cli.models.plan import Business, Feature, Idea, Metadata, PlanBundle, Product, Release, Story
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
    out: Optional[Path] = typer.Option(
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
        return

    # Interactive mode: guided plan creation
    try:
        plan = _build_plan_interactively()

        # Generate plan file
        out.parent.mkdir(parents=True, exist_ok=True)
        generator = PlanGenerator()
        generator.generate(plan, out)

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
    releases = []

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

    features = []
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
    stories = []
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
    plan: Optional[Path] = typer.Option(
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

        print_success(f"Feature '{key}' added successfully")
        console.print(f"[dim]Feature: {title}[/dim]")
        if outcomes_list:
            console.print(f"[dim]Outcomes: {', '.join(outcomes_list)}[/dim]")
        if acceptance_list:
            console.print(f"[dim]Acceptance: {', '.join(acceptance_list)}[/dim]")

    except typer.Exit:
        raise
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
    plan: Optional[Path] = typer.Option(
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
        )

        # Add story to feature
        parent_feature.stories.append(new_story)

        # Validate updated plan (always passes for PlanBundle model)
        print_info("Validating updated plan...")

        # Save updated plan
        print_info(f"Saving plan to: {plan}")
        generator = PlanGenerator()
        generator.generate(existing_plan, plan)

        print_success(f"Story '{key}' added to feature '{feature}'")
        console.print(f"[dim]Story: {title}[/dim]")
        if acceptance_list:
            console.print(f"[dim]Acceptance: {', '.join(acceptance_list)}[/dim]")
        if story_points:
            console.print(f"[dim]Story Points: {story_points}[/dim]")
        if value_points:
            console.print(f"[dim]Value Points: {value_points}[/dim]")

    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Failed to add story: {e}")
        raise typer.Exit(1) from e


@app.command("compare")
@beartype
def compare(
    manual: Optional[Path] = typer.Option(
        None,
        "--manual",
        help="Manual plan bundle path (default: .specfact/plans/main.bundle.yaml)",
    ),
    auto: Optional[Path] = typer.Option(
        None,
        "--auto",
        help="Auto-derived plan bundle path (default: latest in .specfact/plans/)",
    ),
    format: str = typer.Option(
        "markdown",
        "--format",
        help="Output format (markdown, json, yaml)",
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        help="Output file path (default: .specfact/reports/comparison/deviations-<timestamp>.md)",
    ),
) -> None:
    """
    Compare manual and auto-derived plans.

    Detects deviations between manually created plans and
    reverse-engineered plans from code.

    Example:
        specfact plan compare --manual .specfact/plans/main.bundle.yaml --auto .specfact/plans/auto-derived-<timestamp>.bundle.yaml
    """
    from specfact_cli.utils.structure import SpecFactStructure

    # Ensure .specfact structure exists
    SpecFactStructure.ensure_structure()

    # Use default paths if not specified (smart defaults)
    if manual is None:
        manual = SpecFactStructure.get_default_plan_path()
        if not manual.exists():
            print_error(f"Default manual plan not found: {manual}\nCreate one with: specfact plan init --interactive")
            raise typer.Exit(1)
        print_info(f"Using default manual plan: {manual}")

    if auto is None:
        # Use smart default: find latest auto-derived plan
        auto = SpecFactStructure.get_latest_brownfield_report()
        if auto is None:
            plans_dir = Path(SpecFactStructure.PLANS)
            print_error(
                f"No auto-derived plans found in {plans_dir}\n"
                "Generate one with: specfact import from-code --repo ."
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
                    deviation.description[:80] + "..." if len(deviation.description) > 80 else deviation.description,
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

        config_path = SpecFactStructure.get_enforcement_config_path()
        if config_path.exists():
            try:
                from specfact_cli.utils.yaml_utils import load_yaml

                config_data = load_yaml(config_path)
                enforcement_config = EnforcementConfig(**config_data)

                if enforcement_config.enabled and report.total_deviations > 0:
                    print_section("Enforcement Rules")
                    console.print(f"[dim]Using enforcement config: {config_path}[/dim]\n")

                    # Check for blocking deviations
                    blocking_deviations = []
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

            except typer.Exit:
                # Re-raise typer.Exit (for enforcement blocking)
                raise
            except Exception as e:
                print_warning(f"Could not load enforcement config: {e}")

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
    plan: Optional[str] = typer.Argument(
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

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Status", style="dim", width=10)
        table.add_column("Plan Name", style="bold", width=50)
        table.add_column("Features", justify="right", width=10)
        table.add_column("Stories", justify="right", width=10)
        table.add_column("Stage", width=12)
        table.add_column("Modified", style="dim", width=20)

        for i, p in enumerate(plans, 1):
            status = "[ACTIVE]" if p.get("active") else ""
            plan_name = str(p["name"])
            features_count = str(p["features"])
            stories_count = str(p["stories"])
            stage = str(p.get("stage", "unknown"))
            modified = str(p["modified"])
            modified_display = modified[:19] if len(modified) > 19 else modified
            table.add_row(
                str(i),
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
            selection = prompt_text("Select a plan by number (1-%d) or 'q' to quit: " % len(plans)).strip()

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

    print_success(f"Active plan set to: {plan_name}")
    print_info(f"  Features: {selected_plan['features']}")
    print_info(f"  Stories: {selected_plan['stories']}")
    print_info(f"  Stage: {selected_plan.get('stage', 'unknown')}")

    print_info("\nThis plan will now be used as the default for:")
    print_info("  - specfact plan compare")
    print_info("  - specfact plan promote")
    print_info("  - specfact plan add-feature")
    print_info("  - specfact plan add-story")
    print_info("  - specfact sync spec-kit")


@app.command("promote")
@beartype
@require(lambda plan: plan is None or isinstance(plan, Path), "Plan must be None or Path")
@require(
    lambda stage: stage in ("draft", "review", "approved", "released"),
    "Stage must be draft, review, approved, or released",
)
def promote(
    stage: str = typer.Option(..., "--stage", help="Target stage (draft, review, approved, released)"),
    plan: Optional[Path] = typer.Option(
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

        # Review → Approved: All features must pass validation
        if current_stage == "review" and stage == "approved":
            if validate:
                print_info("Validating all features...")
                incomplete_features = []
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
            bundle.metadata = Metadata(stage=stage, promoted_at=None, promoted_by=None)

        bundle.metadata.stage = stage
        bundle.metadata.promoted_at = datetime.now(UTC).isoformat()
        bundle.metadata.promoted_by = promoted_by

        # Write updated plan
        print_info(f"Saving plan to: {plan}")
        generator = PlanGenerator()
        generator.generate(bundle, plan)

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

    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Failed to promote plan: {e}")
        raise typer.Exit(1) from e
