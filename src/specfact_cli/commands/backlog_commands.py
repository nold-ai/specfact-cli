"""
Backlog refinement commands.

This module provides the `specfact backlog refine` command for AI-assisted
backlog refinement with template detection and matching.

SpecFact CLI Architecture:
- SpecFact CLI generates prompts/instructions for IDE AI copilots
- IDE AI copilots execute those instructions using their native LLM
- IDE AI copilots feed results back to SpecFact CLI
- SpecFact CLI validates and processes the results
"""

from __future__ import annotations

from pathlib import Path

import typer
from beartype import beartype
from icontract import require
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.backlog.ai_refiner import BacklogAIRefiner
from specfact_cli.backlog.template_detector import TemplateDetector
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.models.dor_config import DefinitionOfReady
from specfact_cli.templates.registry import TemplateRegistry


app = typer.Typer(
    name="backlog",
    help="Backlog refinement and template management",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _apply_filters(
    items: list[BacklogItem],
    labels: list[str] | None = None,
    state: str | None = None,
    assignee: str | None = None,
    iteration: str | None = None,
    sprint: str | None = None,
    release: str | None = None,
) -> list[BacklogItem]:
    """
    Apply post-fetch filters to backlog items.

    Args:
        items: List of BacklogItem instances to filter
        labels: Filter by labels/tags (any label must match)
        state: Filter by state (exact match)
        assignee: Filter by assignee (exact match)
        iteration: Filter by iteration path (exact match)
        sprint: Filter by sprint (exact match)
        release: Filter by release (exact match)

    Returns:
        Filtered list of BacklogItem instances
    """
    filtered = items

    # Filter by labels/tags (any label must match)
    if labels:
        filtered = [
            item for item in filtered if any(label.lower() in [tag.lower() for tag in item.tags] for label in labels)
        ]

    # Filter by state
    if state:
        filtered = [item for item in filtered if item.state.lower() == state.lower()]

    # Filter by assignee
    if assignee:
        filtered = [item for item in filtered if any(assignee.lower() == a.lower() for a in item.assignees)]

    # Filter by iteration
    if iteration:
        filtered = [item for item in filtered if item.iteration and item.iteration.lower() == iteration.lower()]

    # Filter by sprint
    if sprint:
        filtered = [item for item in filtered if item.sprint and item.sprint.lower() == sprint.lower()]

    # Filter by release
    if release:
        filtered = [item for item in filtered if item.release and item.release.lower() == release.lower()]

    return filtered


def _fetch_backlog_items(
    adapter_name: str,
    search_query: str | None = None,
    labels: list[str] | None = None,
    state: str | None = None,
    assignee: str | None = None,
    iteration: str | None = None,
    sprint: str | None = None,
    release: str | None = None,
    limit: int = 100,
) -> list[BacklogItem]:
    """
    Fetch backlog items using the specified adapter with filtering support.

    Args:
        adapter_name: Adapter name (github, ado, etc.)
        search_query: Optional search query to filter items (provider-specific syntax)
        labels: Filter by labels/tags (post-fetch filtering)
        state: Filter by state (post-fetch filtering)
        assignee: Filter by assignee (post-fetch filtering)
        iteration: Filter by iteration path (post-fetch filtering)
        sprint: Filter by sprint (post-fetch filtering)
        release: Filter by release (post-fetch filtering)
        limit: Maximum number of items to fetch

    Returns:
        List of BacklogItem instances (filtered)
    """
    registry = AdapterRegistry()
    _adapter = registry.get_adapter(adapter_name)  # Adapter fetched but not yet used for search

    items: list[BacklogItem] = []

    if adapter_name.lower() == "github":
        # Convert GitHub issues to BacklogItem
        # Note: Actual fetching will be implemented when adapter.search_issues() is available
        # For now, this is a placeholder that shows the conversion pattern
        console.print("[yellow]Note: GitHub issue fetching requires adapter.search_issues() implementation[/yellow]")
        # When implemented, would do:
        # issues = adapter.search_issues(query=search_query, limit=limit)
        # items = [convert_github_issue_to_backlog_item(issue) for issue in issues]
        # Then apply post-fetch filters
        return _apply_filters(
            items, labels=labels, state=state, assignee=assignee, iteration=iteration, sprint=sprint, release=release
        )

    if adapter_name.lower() == "ado":
        # Convert ADO work items to BacklogItem
        # Note: Actual fetching will be implemented when adapter.list_work_items() is available
        console.print("[yellow]Note: ADO work item fetching requires adapter.list_work_items() implementation[/yellow]")
        # When implemented, would do:
        # work_items = adapter.list_work_items(query=search_query, limit=limit)
        # items = [convert_ado_work_item_to_backlog_item(wi) for wi in work_items]
        # Then apply post-fetch filters
        return _apply_filters(
            items, labels=labels, state=state, assignee=assignee, iteration=iteration, sprint=sprint, release=release
        )

    msg = f"Adapter {adapter_name} is not yet supported. Supported: github, ado"
    raise NotImplementedError(msg)


@beartype
@app.command()
@require(
    lambda adapter: isinstance(adapter, str) and len(adapter) > 0,
    "Adapter must be non-empty string",
)
def refine(
    adapter: str = typer.Argument(..., help="Backlog adapter name (github, ado, etc.)"),
    # Common filters
    labels: list[str] | None = typer.Option(
        None, "--labels", "--tags", help="Filter by labels/tags (can specify multiple)"
    ),
    state: str | None = typer.Option(None, "--state", help="Filter by state (open, closed, etc.)"),
    assignee: str | None = typer.Option(None, "--assignee", help="Filter by assignee username"),
    # Iteration/sprint filters
    iteration: str | None = typer.Option(None, "--iteration", help="Filter by iteration path"),
    sprint: str | None = typer.Option(None, "--sprint", help="Filter by sprint identifier"),
    release: str | None = typer.Option(None, "--release", help="Filter by release identifier"),
    # Template filters
    persona: str | None = typer.Option(
        None, "--persona", help="Filter templates by persona (product-owner, architect, developer)"
    ),
    framework: str | None = typer.Option(
        None, "--framework", help="Filter templates by framework (agile, scrum, safe, kanban)"
    ),
    # Existing options
    search: str | None = typer.Option(
        None, "--search", "-s", help="Search query to filter backlog items (provider-specific syntax)"
    ),
    template_id: str | None = typer.Option(None, "--template", "-t", help="Target template ID (default: auto-detect)"),
    auto_accept_high_confidence: bool = typer.Option(
        False, "--auto-accept-high-confidence", help="Auto-accept refinements with confidence >= 0.85"
    ),
    bundle: str | None = typer.Option(None, "--bundle", "-b", help="OpenSpec bundle path to import refined items"),
    auto_bundle: bool = typer.Option(False, "--auto-bundle", help="Auto-import refined items to OpenSpec bundle"),
    # Preview/write flags (production safety)
    preview: bool = typer.Option(
        True,
        "--preview/--no-preview",
        help="Preview mode: show what will be written without updating backlog (default: True)",
    ),
    write: bool = typer.Option(
        False, "--write", help="Write mode: explicitly opt-in to update remote backlog (requires --write flag)"
    ),
    # DoR validation
    check_dor: bool = typer.Option(
        False, "--check-dor", help="Check Definition of Ready (DoR) rules before refinement"
    ),
) -> None:
    """
    Refine backlog items using AI-assisted template matching.

    This command:
    1. Fetches backlog items from the specified adapter
    2. Detects template matches with confidence scores
    3. Identifies items needing refinement (low confidence or no match)
    4. Generates prompts for IDE AI copilot to refine items
    5. Validates refined content from IDE AI copilot
    6. Updates remote backlog with refined content
    7. Optionally imports refined items to OpenSpec bundle

    SpecFact CLI Architecture:
    - This command generates prompts for IDE AI copilots (Cursor, Claude Code, etc.)
    - IDE AI copilots execute those prompts using their native LLM
    - IDE AI copilots feed refined content back to this command
    - This command validates and processes the refined content
    """
    try:
        # Initialize template registry and load default templates
        registry = TemplateRegistry()
        defaults_dir = Path(__file__).parent.parent / "templates" / "defaults"
        if defaults_dir.exists():
            registry.load_templates_from_directory(defaults_dir)

        # Initialize template detector
        detector = TemplateDetector(registry)

        # Initialize AI refiner (prompt generator and validator)
        refiner = BacklogAIRefiner()

        # Load DoR configuration (if --check-dor flag set)
        dor_config: DefinitionOfReady | None = None
        if check_dor:
            repo_path = Path(".")
            dor_config = DefinitionOfReady.load_from_repo(repo_path)
            if dor_config:
                console.print("[green]✓ Loaded DoR configuration from .specfact/dor.yaml[/green]")
            else:
                console.print("[yellow]⚠ DoR config not found (.specfact/dor.yaml), using default DoR rules[/yellow]")
                # Use default DoR rules
                dor_config = DefinitionOfReady(
                    rules={
                        "story_points": True,
                        "value_points": False,  # Optional by default
                        "priority": True,
                        "business_value": True,
                        "acceptance_criteria": True,
                        "dependencies": False,  # Optional by default
                    }
                )

        # Fetch backlog items with filters
        console.print(f"[bold]Fetching backlog items from {adapter}...[/bold]")
        items = _fetch_backlog_items(
            adapter,
            search_query=search,
            labels=labels,
            state=state,
            assignee=assignee,
            iteration=iteration,
            sprint=sprint,
            release=release,
        )

        if not items:
            console.print("[yellow]No backlog items found.[/yellow]")
            return

        console.print(f"[green]Found {len(items)} backlog items[/green]")

        # Process each item
        refined_count = 0
        skipped_count = 0

        for item in items:
            console.print(f"\n[bold]Processing: {item.title}[/bold]")

            # Check DoR (if enabled)
            if check_dor and dor_config:
                item_dict = item.model_dump()
                dor_errors = dor_config.validate_item(item_dict)
                if dor_errors:
                    console.print("[yellow]⚠ Definition of Ready (DoR) issues:[/yellow]")
                    for error in dor_errors:
                        console.print(f"  - {error}")
                    console.print("[yellow]Item may not be ready for sprint planning[/yellow]")
                else:
                    console.print("[green]✓ Definition of Ready (DoR) satisfied[/green]")

            # Detect template with persona/framework/provider filtering
            detection_result = detector.detect_template(item, provider=adapter, framework=framework, persona=persona)

            if detection_result.template_id:
                console.print(
                    f"[green]✓ Detected template: {detection_result.template_id} (confidence: {detection_result.confidence:.2f})[/green]"
                )
                item.detected_template = detection_result.template_id
                item.template_confidence = detection_result.confidence
                item.template_missing_fields = detection_result.missing_fields

                # High confidence - no refinement needed
                if detection_result.confidence >= 0.8:
                    console.print("[green]High confidence match - no refinement needed[/green]")
                    continue

            # Low confidence or no match - needs refinement
            # Get target template using priority-based resolution
            target_template = None
            if template_id:
                target_template = registry.get_template(template_id)
                if not target_template:
                    console.print(f"[yellow]Template {template_id} not found, using auto-detection[/yellow]")
            elif detection_result.template_id:
                target_template = registry.get_template(detection_result.template_id)
            else:
                # Use priority-based template resolution
                target_template = registry.resolve_template(provider=adapter, framework=framework, persona=persona)
                if target_template:
                    console.print(
                        f"[yellow]No template detected, using resolved template: {target_template.template_id}[/yellow]"
                    )
                else:
                    # Fallback: Use first available template as default
                    templates = registry.list_templates(scope="corporate")
                    if templates:
                        target_template = templates[0]
                        console.print(
                            f"[yellow]No template resolved, using default: {target_template.template_id}[/yellow]"
                        )

            if not target_template:
                console.print("[yellow]No template available for refinement[/yellow]")
                skipped_count += 1
                continue

            # Generate prompt for IDE AI copilot
            console.print(f"[bold]Generating refinement prompt for template: {target_template.name}...[/bold]")
            prompt = refiner.generate_refinement_prompt(item, target_template)

            # Display prompt for IDE AI copilot
            console.print("\n[bold]Refinement Prompt for IDE AI Copilot:[/bold]")
            console.print(Panel(prompt, title="Copy this prompt to your IDE AI copilot"))

            # Prompt user to get refined content from IDE AI copilot
            console.print("\n[yellow]Instructions:[/yellow]")
            console.print("1. Copy the prompt above to your IDE AI copilot (Cursor, Claude Code, etc.)")
            console.print("2. Execute the prompt in your IDE AI copilot")
            console.print("3. Copy the refined content from the AI copilot response")
            console.print("4. Paste the refined content below when prompted\n")

            refined_content = Prompt.ask("Paste refined content from IDE AI copilot", default="")

            if not refined_content.strip():
                console.print("[yellow]No refined content provided - skipping[/yellow]")
                skipped_count += 1
                continue

            # Validate and score refined content
            try:
                refinement_result = refiner.validate_and_score_refinement(
                    refined_content, item.body_markdown, target_template
                )

                # Display validation result
                console.print("\n[bold]Refinement Validation Result:[/bold]")
                console.print(f"[green]Confidence: {refinement_result.confidence:.2f}[/green]")
                if refinement_result.has_todo_markers:
                    console.print("[yellow]⚠ Contains TODO markers[/yellow]")
                if refinement_result.has_notes_section:
                    console.print("[yellow]⚠ Contains NOTES section[/yellow]")

                # Show preview with field preservation information
                console.print("\n[bold]Preview: What will be updated[/bold]")
                console.print("[dim]Fields that will be UPDATED:[/dim]")
                console.print("  - title: Will be updated if changed")
                console.print("  - body_markdown: Will be updated with refined content")
                console.print("[dim]Fields that will be PRESERVED (not modified):[/dim]")
                console.print("  - assignees: Preserved")
                console.print("  - tags: Preserved")
                console.print("  - state: Preserved")
                console.print("  - priority: Preserved (if present in provider_fields)")
                console.print("  - due_date: Preserved (if present in provider_fields)")
                console.print("  - story_points: Preserved (if present in provider_fields)")
                console.print("  - All other metadata: Preserved in provider_fields")

                console.print("\n[bold]Original:[/bold]")
                console.print(
                    Panel(item.body_markdown[:500] + "..." if len(item.body_markdown) > 500 else item.body_markdown)
                )
                console.print("\n[bold]Refined:[/bold]")
                console.print(
                    Panel(
                        refinement_result.refined_body[:500] + "..."
                        if len(refinement_result.refined_body) > 500
                        else refinement_result.refined_body
                    )
                )

                # Store refined body for preview/write
                item.refined_body = refinement_result.refined_body

                # Preview mode (default) - don't write, just show preview
                if preview and not write:
                    console.print("\n[yellow]Preview mode: Refinement will NOT be written to backlog[/yellow]")
                    console.print("[yellow]Use --write flag to explicitly opt-in to writeback[/yellow]")
                    refined_count += 1  # Count as refined for preview purposes
                    continue

                # Write mode - requires explicit --write flag
                if write:
                    # Auto-accept high confidence
                    if auto_accept_high_confidence and refinement_result.confidence >= 0.85:
                        console.print("[green]Auto-accepting high-confidence refinement and writing to backlog[/green]")
                        item.apply_refinement()
                        # TODO: Implement writeback to remote backlog using adapter methods
                        console.print(
                            "[yellow]Note: Writeback to remote backlog requires adapter update methods[/yellow]"
                        )
                        refined_count += 1
                    else:
                        # Interactive prompt
                        accept = Confirm.ask("Accept refinement and write to backlog?", default=False)
                        if accept:
                            item.apply_refinement()
                            # TODO: Implement writeback to remote backlog using adapter methods
                            console.print(
                                "[yellow]Note: Writeback to remote backlog requires adapter update methods[/yellow]"
                            )
                            refined_count += 1
                        else:
                            console.print("[yellow]Refinement rejected - not writing to backlog[/yellow]")
                            skipped_count += 1
                else:
                    # Preview mode but user didn't explicitly set --write
                    console.print("[yellow]Preview mode: Use --write to update backlog[/yellow]")
                    refined_count += 1

            except ValueError as e:
                console.print(f"[red]Validation failed: {e}[/red]")
                console.print("[yellow]Please fix the refined content and try again[/yellow]")
                skipped_count += 1
                continue

        # Summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"[green]Refined: {refined_count}[/green]")
        console.print(f"[yellow]Skipped: {skipped_count}[/yellow]")

        # TODO: Update remote backlog with refined items
        # TODO: Import to OpenSpec bundle if specified

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e
