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

import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
import yaml
from beartype import beartype
from icontract import require
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm

from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.ai_refiner import BacklogAIRefiner
from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.backlog.template_detector import TemplateDetector
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.models.dor_config import DefinitionOfReady
from specfact_cli.runtime import debug_log_operation, is_debug_mode
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

    # Filter by state (case-insensitive)
    if state:
        normalized_state = BacklogFilters.normalize_filter_value(state)
        filtered = [item for item in filtered if BacklogFilters.normalize_filter_value(item.state) == normalized_state]

    # Filter by assignee (case-insensitive)
    # Matches against any identifier in assignees list (displayName, uniqueName, or mail for ADO)
    if assignee:
        normalized_assignee = BacklogFilters.normalize_filter_value(assignee)
        filtered = [
            item
            for item in filtered
            if item.assignees  # Only check items with assignees
            and any(
                BacklogFilters.normalize_filter_value(a) == normalized_assignee
                for a in item.assignees
                if a  # Skip None or empty strings
            )
        ]

    # Filter by iteration (case-insensitive)
    if iteration:
        normalized_iteration = BacklogFilters.normalize_filter_value(iteration)
        filtered = [
            item
            for item in filtered
            if item.iteration and BacklogFilters.normalize_filter_value(item.iteration) == normalized_iteration
        ]

    # Filter by sprint (case-insensitive)
    if sprint:
        normalized_sprint = BacklogFilters.normalize_filter_value(sprint)
        filtered = [
            item
            for item in filtered
            if item.sprint and BacklogFilters.normalize_filter_value(item.sprint) == normalized_sprint
        ]

    # Filter by release (case-insensitive)
    if release:
        normalized_release = BacklogFilters.normalize_filter_value(release)
        filtered = [
            item
            for item in filtered
            if item.release and BacklogFilters.normalize_filter_value(item.release) == normalized_release
        ]

    return filtered


def _extract_openspec_change_id(body: str) -> str | None:
    """
    Extract OpenSpec change proposal ID from issue body.

    Looks for patterns like:
    - *OpenSpec Change Proposal: `id`*
    - OpenSpec Change Proposal: `id`
    - OpenSpec.*proposal: `id`

    Args:
        body: Issue body text

    Returns:
        Change proposal ID if found, None otherwise
    """
    import re

    openspec_patterns = [
        r"OpenSpec Change Proposal[:\s]+`?([a-z0-9-]+)`?",
        r"\*OpenSpec Change Proposal:\s*`([a-z0-9-]+)`",
        r"OpenSpec.*proposal[:\s]+`?([a-z0-9-]+)`?",
    ]
    for pattern in openspec_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _build_adapter_kwargs(
    adapter: str,
    repo_owner: str | None = None,
    repo_name: str | None = None,
    github_token: str | None = None,
    ado_org: str | None = None,
    ado_project: str | None = None,
    ado_team: str | None = None,
    ado_token: str | None = None,
) -> dict[str, Any]:
    """
    Build adapter kwargs based on adapter type and provided configuration.

    Args:
        adapter: Adapter name (github, ado, etc.)
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        github_token: GitHub API token
        ado_org: Azure DevOps organization
        ado_project: Azure DevOps project
        ado_token: Azure DevOps PAT

    Returns:
        Dictionary of adapter kwargs
    """
    kwargs: dict[str, Any] = {}
    if adapter.lower() == "github":
        if repo_owner:
            kwargs["repo_owner"] = repo_owner
        if repo_name:
            kwargs["repo_name"] = repo_name
        if github_token:
            kwargs["api_token"] = github_token
    elif adapter.lower() == "ado":
        if ado_org:
            kwargs["org"] = ado_org
        if ado_project:
            kwargs["project"] = ado_project
        if ado_team:
            kwargs["team"] = ado_team
        if ado_token:
            kwargs["api_token"] = ado_token
    return kwargs


def _extract_body_from_block(block: str) -> str:
    """
    Extract **Body** content from a refined export block, handling nested fenced code.

    The body is wrapped in ```markdown ... ```. If the body itself contains fenced
    code blocks (e.g. ```python ... ```), the closing fence is matched by tracking
    depth: a line that is exactly ``` closes the current fence (body or inner).
    """
    start_marker = "**Body**:"
    fence_open = "```markdown"
    if start_marker not in block or fence_open not in block:
        return ""
    idx = block.find(start_marker)
    rest = block[idx + len(start_marker) :].lstrip()
    if not rest.startswith("```"):
        return ""
    if not rest.startswith(fence_open + "\n") and not rest.startswith(fence_open + "\r\n"):
        return ""
    after_open = rest[len(fence_open) :].lstrip("\n\r")
    if not after_open:
        return ""
    lines = after_open.split("\n")
    body_lines: list[str] = []
    depth = 1
    for line in lines:
        stripped = line.rstrip()
        if stripped == "```":
            if depth == 1:
                break
            depth -= 1
            body_lines.append(line)
        elif stripped.startswith("```") and stripped != "```":
            depth += 1
            body_lines.append(line)
        else:
            body_lines.append(line)
    return "\n".join(body_lines).strip()


def _parse_refined_export_markdown(content: str) -> dict[str, dict[str, Any]]:
    """
    Parse refined export markdown (same format as --export-to-tmp) into id -> fields.

    Splits by ## Item blocks, extracts **ID**, **Body** (from ```markdown ... ```),
    **Acceptance Criteria**, and optionally title and **Metrics** (story_points,
    business_value, priority). Body extraction is fence-aware so bodies containing
    nested code blocks are parsed correctly. Returns a dict mapping item id to
    parsed fields (body_markdown, acceptance_criteria, title?, story_points?,
    business_value?, priority?).
    """
    result: dict[str, dict[str, Any]] = {}
    blocks = re.split(r"\n## Item \d+:", content)
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("# SpecFact") or "**ID**:" not in block:
            continue
        id_match = re.search(r"\*\*ID\*\*:\s*(.+?)(?:\n|$)", block)
        if not id_match:
            continue
        item_id = id_match.group(1).strip()
        fields: dict[str, Any] = {}

        fields["body_markdown"] = _extract_body_from_block(block)

        ac_match = re.search(r"\*\*Acceptance Criteria\*\*:\s*\n(.*?)(?=\n\*\*|\n---|\Z)", block, re.DOTALL)
        if ac_match:
            fields["acceptance_criteria"] = ac_match.group(1).strip() or None
        else:
            fields["acceptance_criteria"] = None

        first_line = block.split("\n")[0].strip() if block else ""
        if first_line and not first_line.startswith("**"):
            fields["title"] = first_line

        if "Story Points:" in block:
            sp_match = re.search(r"Story Points:\s*(\d+)", block)
            if sp_match:
                fields["story_points"] = int(sp_match.group(1))
        if "Business Value:" in block:
            bv_match = re.search(r"Business Value:\s*(\d+)", block)
            if bv_match:
                fields["business_value"] = int(bv_match.group(1))
        if "Priority:" in block:
            pri_match = re.search(r"Priority:\s*(\d+)", block)
            if pri_match:
                fields["priority"] = int(pri_match.group(1))

        result[item_id] = fields
    return result


@beartype
def _item_needs_refinement(
    item: BacklogItem,
    detector: TemplateDetector,
    registry: TemplateRegistry,
    template_id: str | None,
    normalized_adapter: str | None,
    normalized_framework: str | None,
    normalized_persona: str | None,
) -> bool:
    """
    Return True if the item needs refinement (should be processed); False if already refined (skip).

    Mirrors the "already refined" skip logic used in the refine loop: checkboxes + all required
    sections, or high confidence with no missing fields.
    """
    detection_result = detector.detect_template(
        item,
        provider=normalized_adapter,
        framework=normalized_framework,
        persona=normalized_persona,
    )
    if detection_result.template_id:
        target = registry.get_template(detection_result.template_id) if detection_result.template_id else None
        if target and target.required_sections:
            has_checkboxes = bool(
                re.search(r"^[\s]*- \[[ x]\]", item.body_markdown or "", re.MULTILINE | re.IGNORECASE)
            )
            all_present = all(
                bool(re.search(rf"^#+\s+{re.escape(s)}\s*$", item.body_markdown or "", re.MULTILINE | re.IGNORECASE))
                for s in target.required_sections
            )
            if has_checkboxes and all_present and not detection_result.missing_fields:
                return False
    already_refined = template_id is None and detection_result.confidence >= 0.8 and not detection_result.missing_fields
    return not already_refined


def _fetch_backlog_items(
    adapter_name: str,
    search_query: str | None = None,
    labels: list[str] | None = None,
    state: str | None = None,
    assignee: str | None = None,
    iteration: str | None = None,
    sprint: str | None = None,
    release: str | None = None,
    limit: int | None = None,
    repo_owner: str | None = None,
    repo_name: str | None = None,
    github_token: str | None = None,
    ado_org: str | None = None,
    ado_project: str | None = None,
    ado_team: str | None = None,
    ado_token: str | None = None,
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
    from specfact_cli.backlog.adapters.base import BacklogAdapter

    registry = AdapterRegistry()

    # Build adapter kwargs based on adapter type
    adapter_kwargs = _build_adapter_kwargs(
        adapter_name,
        repo_owner=repo_owner,
        repo_name=repo_name,
        github_token=github_token,
        ado_org=ado_org,
        ado_project=ado_project,
        ado_team=ado_team,
        ado_token=ado_token,
    )

    adapter = registry.get_adapter(adapter_name, **adapter_kwargs)

    # Check if adapter implements BacklogAdapter interface
    if not isinstance(adapter, BacklogAdapter):
        msg = f"Adapter {adapter_name} does not implement BacklogAdapter interface"
        raise NotImplementedError(msg)

    # Create BacklogFilters from parameters
    filters = BacklogFilters(
        assignee=assignee,
        state=state,
        labels=labels,
        search=search_query,
        iteration=iteration,
        sprint=sprint,
        release=release,
        limit=limit,
    )

    # Fetch items using the adapter
    items = adapter.fetch_backlog_items(filters)

    # Apply limit deterministically (slice after filtering)
    if limit is not None and len(items) > limit:
        items = items[:limit]

    return items


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
    state: str | None = typer.Option(
        None, "--state", help="Filter by state (case-insensitive, e.g., 'open', 'closed', 'Active', 'New')"
    ),
    assignee: str | None = typer.Option(
        None,
        "--assignee",
        help="Filter by assignee (case-insensitive). GitHub: login or @username. ADO: displayName, uniqueName, or mail",
    ),
    # Iteration/sprint filters
    iteration: str | None = typer.Option(
        None,
        "--iteration",
        help="Filter by iteration path (ADO format: 'Project\\Sprint 1' or 'current' for current iteration). Must be exact full path from ADO.",
    ),
    sprint: str | None = typer.Option(
        None,
        "--sprint",
        help="Filter by sprint (case-insensitive). ADO: use full iteration path (e.g., 'Project\\Sprint 1') to avoid ambiguity. If omitted, defaults to current active iteration.",
    ),
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
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Maximum number of items to process in this refinement session. Use to cap batch size and avoid processing too many items at once.",
    ),
    ignore_refined: bool = typer.Option(
        True,
        "--ignore-refined/--no-ignore-refined",
        help="When set (default), exclude already-refined items from the batch so --limit applies to items that need refinement. Use --no-ignore-refined to process the first N items in order (already-refined skipped in loop).",
    ),
    issue_id: str | None = typer.Option(
        None,
        "--id",
        help="Refine only this backlog item (issue or work item ID). Other items are ignored.",
    ),
    template_id: str | None = typer.Option(None, "--template", "-t", help="Target template ID (default: auto-detect)"),
    auto_accept_high_confidence: bool = typer.Option(
        False, "--auto-accept-high-confidence", help="Auto-accept refinements with confidence >= 0.85"
    ),
    bundle: str | None = typer.Option(None, "--bundle", "-b", help="OpenSpec bundle path to import refined items"),
    auto_bundle: bool = typer.Option(False, "--auto-bundle", help="Auto-import refined items to OpenSpec bundle"),
    openspec_comment: bool = typer.Option(
        False, "--openspec-comment", help="Add OpenSpec change proposal reference as comment (preserves original body)"
    ),
    # Preview/write flags (production safety)
    preview: bool = typer.Option(
        True,
        "--preview/--no-preview",
        help="Preview mode: show what will be written without updating backlog (default: True)",
    ),
    write: bool = typer.Option(
        False, "--write", help="Write mode: explicitly opt-in to update remote backlog (requires --write flag)"
    ),
    # Export/import for copilot processing
    export_to_tmp: bool = typer.Option(
        False,
        "--export-to-tmp",
        help="Export backlog items to temporary file for copilot processing (default: <system-temp>/specfact-backlog-refine-<timestamp>.md)",
    ),
    import_from_tmp: bool = typer.Option(
        False,
        "--import-from-tmp",
        help="Import refined content from temporary file after copilot processing (default: <system-temp>/specfact-backlog-refine-<timestamp>-refined.md)",
    ),
    tmp_file: Path | None = typer.Option(
        None,
        "--tmp-file",
        help="Custom temporary file path (overrides default)",
    ),
    # DoR validation
    check_dor: bool = typer.Option(
        False, "--check-dor", help="Check Definition of Ready (DoR) rules before refinement"
    ),
    # Adapter configuration (GitHub)
    repo_owner: str | None = typer.Option(
        None, "--repo-owner", help="GitHub repository owner (required for GitHub adapter)"
    ),
    repo_name: str | None = typer.Option(
        None, "--repo-name", help="GitHub repository name (required for GitHub adapter)"
    ),
    github_token: str | None = typer.Option(
        None, "--github-token", help="GitHub API token (optional, uses GITHUB_TOKEN env var or gh CLI if not provided)"
    ),
    # Adapter configuration (ADO)
    ado_org: str | None = typer.Option(None, "--ado-org", help="Azure DevOps organization (required for ADO adapter)"),
    ado_project: str | None = typer.Option(
        None, "--ado-project", help="Azure DevOps project (required for ADO adapter)"
    ),
    ado_team: str | None = typer.Option(
        None,
        "--ado-team",
        help="Azure DevOps team name for iteration lookup (defaults to project name). Used when resolving current iteration when --sprint is omitted.",
    ),
    ado_token: str | None = typer.Option(
        None, "--ado-token", help="Azure DevOps PAT (optional, uses AZURE_DEVOPS_TOKEN env var if not provided)"
    ),
    custom_field_mapping: str | None = typer.Option(
        None,
        "--custom-field-mapping",
        help="Path to custom ADO field mapping YAML file (overrides default mappings)",
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
        # Show initialization progress to provide feedback during setup
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as init_progress:
            # Initialize template registry and load templates
            init_task = init_progress.add_task("[cyan]Initializing templates...[/cyan]", total=None)
            registry = TemplateRegistry()

            # Determine template directories (built-in first so custom overrides take effect)
            from specfact_cli.utils.ide_setup import find_package_resources_path

            current_dir = Path.cwd()

            # 1. Load built-in templates from resources/templates/backlog/ (preferred location)
            # Try to find resources directory using package resource finder (for installed packages)
            resources_path = find_package_resources_path("specfact_cli", "resources/templates/backlog")
            built_in_loaded = False
            if resources_path and resources_path.exists():
                registry.load_templates_from_directory(resources_path)
                built_in_loaded = True
            else:
                # Fallback: Try relative to repo root (development mode)
                repo_root = Path(__file__).parent.parent.parent.parent
                resources_templates_dir = repo_root / "resources" / "templates" / "backlog"
                if resources_templates_dir.exists():
                    registry.load_templates_from_directory(resources_templates_dir)
                    built_in_loaded = True
                else:
                    # 2. Fallback to src/specfact_cli/templates/ for backward compatibility
                    src_templates_dir = Path(__file__).parent.parent / "templates"
                    if src_templates_dir.exists():
                        registry.load_templates_from_directory(src_templates_dir)
                        built_in_loaded = True

            if not built_in_loaded:
                console.print(
                    "[yellow]⚠ No built-in backlog templates found; continuing with custom templates only.[/yellow]"
                )

            # 3. Load custom templates from project directory (highest priority)
            project_templates_dir = current_dir / ".specfact" / "templates" / "backlog"
            if project_templates_dir.exists():
                registry.load_templates_from_directory(project_templates_dir)

            init_progress.update(init_task, description="[green]✓[/green] Templates initialized")

            # Initialize template detector
            detector_task = init_progress.add_task("[cyan]Initializing template detector...[/cyan]", total=None)
            detector = TemplateDetector(registry)
            init_progress.update(detector_task, description="[green]✓[/green] Template detector ready")

            # Initialize AI refiner (prompt generator and validator)
            refiner_task = init_progress.add_task("[cyan]Initializing AI refiner...[/cyan]", total=None)
            refiner = BacklogAIRefiner()
            init_progress.update(refiner_task, description="[green]✓[/green] AI refiner ready")

            # Get adapter registry for writeback
            adapter_task = init_progress.add_task("[cyan]Initializing adapter...[/cyan]", total=None)
            adapter_registry = AdapterRegistry()
            init_progress.update(adapter_task, description="[green]✓[/green] Adapter registry ready")

            # Load DoR configuration (if --check-dor flag set)
            dor_config: DefinitionOfReady | None = None
            if check_dor:
                dor_task = init_progress.add_task("[cyan]Loading DoR configuration...[/cyan]", total=None)
                repo_path = Path(".")
                dor_config = DefinitionOfReady.load_from_repo(repo_path)
                if dor_config:
                    init_progress.update(dor_task, description="[green]✓[/green] DoR configuration loaded")
                else:
                    init_progress.update(dor_task, description="[yellow]⚠[/yellow] Using default DoR rules")
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

            # Normalize adapter, framework, and persona to lowercase for template matching
            # Template metadata in YAML uses lowercase (e.g., provider: github, framework: scrum)
            # This ensures case-insensitive matching regardless of CLI input case
            normalized_adapter = adapter.lower() if adapter else None
            normalized_framework = framework.lower() if framework else None
            normalized_persona = persona.lower() if persona else None

            # Validate adapter-specific required parameters
            validate_task = init_progress.add_task("[cyan]Validating adapter configuration...[/cyan]", total=None)
            if normalized_adapter == "github" and (not repo_owner or not repo_name):
                init_progress.stop()
                console.print("[red]Error:[/red] GitHub adapter requires both --repo-owner and --repo-name options")
                console.print(
                    "[yellow]Example:[/yellow] specfact backlog refine github "
                    "--repo-owner 'nold-ai' --repo-name 'specfact-cli' --state open"
                )
                sys.exit(1)
            if normalized_adapter == "ado" and (not ado_org or not ado_project):
                init_progress.stop()
                console.print(
                    "[red]Error:[/red] Azure DevOps adapter requires both --ado-org and --ado-project options"
                )
                console.print(
                    "[yellow]Example:[/yellow] specfact backlog refine ado --ado-org 'my-org' --ado-project 'my-project' --state Active"
                )
                sys.exit(1)

            # Validate and set custom field mapping (if provided)
            if custom_field_mapping:
                mapping_path = Path(custom_field_mapping)
                if not mapping_path.exists():
                    init_progress.stop()
                    console.print(f"[red]Error:[/red] Custom field mapping file not found: {custom_field_mapping}")
                    sys.exit(1)
                if not mapping_path.is_file():
                    init_progress.stop()
                    console.print(f"[red]Error:[/red] Custom field mapping path is not a file: {custom_field_mapping}")
                    sys.exit(1)
                # Validate file format by attempting to load it
                try:
                    from specfact_cli.backlog.mappers.template_config import FieldMappingConfig

                    FieldMappingConfig.from_file(mapping_path)
                    init_progress.update(validate_task, description="[green]✓[/green] Field mapping validated")
                except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
                    init_progress.stop()
                    console.print(f"[red]Error:[/red] Invalid custom field mapping file: {e}")
                    sys.exit(1)
                # Set environment variable for converter to use
                os.environ["SPECFACT_ADO_CUSTOM_MAPPING"] = str(mapping_path.absolute())
            else:
                init_progress.update(validate_task, description="[green]✓[/green] Configuration validated")

        # Fetch backlog items with filters
        # When ignore_refined and limit are set, fetch more candidates so we have enough after filtering
        fetch_limit: int | None = limit
        if ignore_refined and limit is not None and limit > 0:
            fetch_limit = limit * 5
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            fetch_task = progress.add_task(f"[cyan]Fetching backlog items from {adapter}...[/cyan]", total=None)
            items = _fetch_backlog_items(
                adapter,
                search_query=search,
                labels=labels,
                state=state,
                assignee=assignee,
                iteration=iteration,
                sprint=sprint,
                release=release,
                limit=fetch_limit,
                repo_owner=repo_owner,
                repo_name=repo_name,
                github_token=github_token,
                ado_org=ado_org,
                ado_project=ado_project,
                ado_team=ado_team,
                ado_token=ado_token,
            )
            progress.update(fetch_task, description="[green]✓[/green] Fetched backlog items")

        if not items:
            # Provide helpful message when no items found, especially if filters were used
            filter_info = []
            if state:
                filter_info.append(f"state={state}")
            if assignee:
                filter_info.append(f"assignee={assignee}")
            if iteration:
                filter_info.append(f"iteration={iteration}")
            if sprint:
                filter_info.append(f"sprint={sprint}")
            if release:
                filter_info.append(f"release={release}")

            if filter_info:
                console.print(
                    f"[yellow]No backlog items found with the specified filters:[/yellow] {', '.join(filter_info)}\n"
                    f"[cyan]Tips:[/cyan]\n"
                    f"  • Verify the iteration path exists in Azure DevOps (Project Settings → Boards → Iterations)\n"
                    f"  • Try using [bold]--iteration current[/bold] to use the current active iteration\n"
                    f"  • Try using [bold]--sprint[/bold] with just the sprint name for automatic matching\n"
                    f"  • Check that items exist in the specified iteration/sprint"
                )
            else:
                console.print("[yellow]No backlog items found.[/yellow]")
            return

        # Filter by issue ID when --id is set
        if issue_id is not None:
            items = [i for i in items if str(i.id) == str(issue_id)]
            if not items:
                console.print(
                    f"[bold red]✗[/bold red] No backlog item with id {issue_id!r} found. "
                    "Check filters and adapter configuration."
                )
                raise typer.Exit(1)

        # When ignore_refined (default), keep only items that need refinement; then apply limit
        if ignore_refined:
            items = [
                i
                for i in items
                if _item_needs_refinement(
                    i, detector, registry, template_id, normalized_adapter, normalized_framework, normalized_persona
                )
            ]
            if limit is not None and len(items) > limit:
                items = items[:limit]
            if ignore_refined and (limit is not None or issue_id is not None):
                console.print(
                    f"[dim]Filtered to {len(items)} item(s) needing refinement"
                    + (f" (limit {limit})" if limit is not None else "")
                    + "[/dim]"
                )

        # Validate export/import flags
        if export_to_tmp and import_from_tmp:
            console.print("[bold red]✗[/bold red] --export-to-tmp and --import-from-tmp are mutually exclusive")
            raise typer.Exit(1)

        # Handle export mode
        if export_to_tmp:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            export_file = tmp_file or (Path(tempfile.gettempdir()) / f"specfact-backlog-refine-{timestamp}.md")

            console.print(f"[bold cyan]Exporting {len(items)} backlog item(s) to: {export_file}[/bold cyan]")

            # Export items to markdown file
            export_content = "# SpecFact Backlog Refinement Export\n\n"
            export_content += f"**Export Date**: {datetime.now().isoformat()}\n"
            export_content += f"**Adapter**: {adapter}\n"
            export_content += f"**Items**: {len(items)}\n\n"
            export_content += "---\n\n"

            for idx, item in enumerate(items, 1):
                export_content += f"## Item {idx}: {item.title}\n\n"
                export_content += f"**ID**: {item.id}\n"
                export_content += f"**URL**: {item.url}\n"
                if item.canonical_url:
                    export_content += f"**Canonical URL**: {item.canonical_url}\n"
                export_content += f"**State**: {item.state}\n"
                export_content += f"**Provider**: {item.provider}\n"

                # Include metrics
                if item.story_points is not None or item.business_value is not None or item.priority is not None:
                    export_content += "\n**Metrics**:\n"
                    if item.story_points is not None:
                        export_content += f"- Story Points: {item.story_points}\n"
                    if item.business_value is not None:
                        export_content += f"- Business Value: {item.business_value}\n"
                    if item.priority is not None:
                        export_content += f"- Priority: {item.priority} (1=highest)\n"
                    if item.value_points is not None:
                        export_content += f"- Value Points (SAFe): {item.value_points}\n"
                    if item.work_item_type:
                        export_content += f"- Work Item Type: {item.work_item_type}\n"

                # Include acceptance criteria
                if item.acceptance_criteria:
                    export_content += f"\n**Acceptance Criteria**:\n{item.acceptance_criteria}\n"

                # Include body
                export_content += f"\n**Body**:\n```markdown\n{item.body_markdown}\n```\n"

                export_content += "\n---\n\n"

            export_file.write_text(export_content, encoding="utf-8")
            console.print(f"[green]✓ Exported to: {export_file}[/green]")
            console.print("[dim]Process items with copilot, then use --import-from-tmp to import refined content[/dim]")
            return

        # Handle import mode
        if import_from_tmp:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            import_file = tmp_file or (Path(tempfile.gettempdir()) / f"specfact-backlog-refine-{timestamp}-refined.md")

            if not import_file.exists():
                console.print(f"[bold red]✗[/bold red] Import file not found: {import_file}")
                console.print(f"[dim]Expected file: {import_file}[/dim]")
                console.print("[dim]Or specify custom path with --tmp-file[/dim]")
                raise typer.Exit(1)

            console.print(f"[bold cyan]Importing refined content from: {import_file}[/bold cyan]")
            try:
                raw = import_file.read_text(encoding="utf-8")
                if is_debug_mode():
                    debug_log_operation("file_read", str(import_file), "success")
            except OSError as e:
                if is_debug_mode():
                    debug_log_operation("file_read", str(import_file), "error", error=str(e))
                raise
            parsed_by_id = _parse_refined_export_markdown(raw)
            if not parsed_by_id:
                console.print(
                    "[yellow]No valid item blocks found in import file (expected ## Item N: and **ID**:)[/yellow]"
                )
                raise typer.Exit(1)

            updated_items: list[BacklogItem] = []
            for item in items:
                if item.id not in parsed_by_id:
                    continue
                data = parsed_by_id[item.id]
                body = data.get("body_markdown", item.body_markdown or "")
                item.body_markdown = body if body is not None else (item.body_markdown or "")
                if "acceptance_criteria" in data:
                    item.acceptance_criteria = data["acceptance_criteria"]
                if data.get("title"):
                    item.title = data["title"]
                if "story_points" in data:
                    item.story_points = data["story_points"]
                if "business_value" in data:
                    item.business_value = data["business_value"]
                if "priority" in data:
                    item.priority = data["priority"]
                updated_items.append(item)

            if not write:
                console.print(f"[green]Would update {len(updated_items)} item(s)[/green]")
                console.print("[dim]Run with --write to apply changes to the backlog[/dim]")
                return

            writeback_kwargs = _build_adapter_kwargs(
                adapter,
                repo_owner=repo_owner,
                repo_name=repo_name,
                github_token=github_token,
                ado_org=ado_org,
                ado_project=ado_project,
                ado_team=ado_team,
                ado_token=ado_token,
            )
            adapter_instance = adapter_registry.get_adapter(adapter, **writeback_kwargs)
            if not isinstance(adapter_instance, BacklogAdapter):
                console.print("[bold red]✗[/bold red] Adapter does not support backlog updates")
                raise typer.Exit(1)

            for item in updated_items:
                update_fields_list = ["title", "body_markdown"]
                if item.acceptance_criteria:
                    update_fields_list.append("acceptance_criteria")
                if item.story_points is not None:
                    update_fields_list.append("story_points")
                if item.business_value is not None:
                    update_fields_list.append("business_value")
                if item.priority is not None:
                    update_fields_list.append("priority")
                adapter_instance.update_backlog_item(item, update_fields=update_fields_list)
                console.print(f"[green]✓ Updated backlog item: {item.url}[/green]")
            console.print(f"[green]✓ Updated {len(updated_items)} backlog item(s)[/green]")
            return

        # Apply limit if specified (when not ignore_refined; when ignore_refined we already filtered and sliced)
        if not ignore_refined and limit is not None and len(items) > limit:
            items = items[:limit]
            console.print(f"[yellow]Limited to {limit} items (found {len(items)} total)[/yellow]")
        else:
            console.print(f"[green]Found {len(items)} backlog items[/green]")

        # Process each item
        refined_count = 0
        skipped_count = 0
        cancelled = False

        # Process items without progress bar during refinement to avoid conflicts with interactive prompts
        for idx, item in enumerate(items, 1):
            # Check for cancellation
            if cancelled:
                break

            # Show simple status text instead of progress bar
            console.print(f"\n[bold cyan]Refining item {idx} of {len(items)}: {item.title}[/bold cyan]")

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
            # Use normalized values for case-insensitive template matching
            detection_result = detector.detect_template(
                item, provider=normalized_adapter, framework=normalized_framework, persona=normalized_persona
            )

            if detection_result.template_id:
                template_id_str = detection_result.template_id
                confidence_str = f"{detection_result.confidence:.2f}"
                console.print(f"[green]✓ Detected template: {template_id_str} (confidence: {confidence_str})[/green]")
                item.detected_template = detection_result.template_id
                item.template_confidence = detection_result.confidence
                item.template_missing_fields = detection_result.missing_fields

                # Check if item already has checkboxes in required sections (already refined)
                # Items with checkboxes (- [ ] or - [x]) in required sections are considered already refined
                target_template_for_check = (
                    registry.get_template(detection_result.template_id) if detection_result.template_id else None
                )
                if target_template_for_check:
                    import re

                    has_checkboxes = bool(
                        re.search(r"^[\s]*- \[[ x]\]", item.body_markdown, re.MULTILINE | re.IGNORECASE)
                    )
                    # Check if all required sections are present
                    all_sections_present = True
                    for section in target_template_for_check.required_sections:
                        # Look for section heading (## Section Name or ### Section Name)
                        section_pattern = rf"^#+\s+{re.escape(section)}\s*$"
                        if not re.search(section_pattern, item.body_markdown, re.MULTILINE | re.IGNORECASE):
                            all_sections_present = False
                            break
                    # If item has checkboxes and all required sections, it's already refined - skip it
                    if has_checkboxes and all_sections_present and not detection_result.missing_fields:
                        console.print(
                            "[green]Item already refined with checkboxes and all required sections - skipping[/green]"
                        )
                        skipped_count += 1
                        continue

                # High confidence AND no missing required fields - no refinement needed
                # Note: Even with high confidence, if required sections are missing, refinement is needed
                if template_id is None and detection_result.confidence >= 0.8 and not detection_result.missing_fields:
                    console.print(
                        "[green]High confidence match with all required sections - no refinement needed[/green]"
                    )
                    skipped_count += 1
                    continue
                if detection_result.missing_fields:
                    missing_str = ", ".join(detection_result.missing_fields)
                    console.print(f"[yellow]⚠ Missing required sections: {missing_str} - refinement needed[/yellow]")

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
                # Use normalized values for case-insensitive template matching
                target_template = registry.resolve_template(
                    provider=normalized_adapter, framework=normalized_framework, persona=normalized_persona
                )
                if target_template:
                    resolved_id = target_template.template_id
                    console.print(f"[yellow]No template detected, using resolved template: {resolved_id}[/yellow]")
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

            # In preview mode without --write, show full item details but skip interactive refinement
            if preview and not write:
                console.print("\n[bold]Preview Mode: Full Item Details[/bold]")
                console.print(f"[bold]Title:[/bold] {item.title}")
                console.print(f"[bold]URL:[/bold] {item.url}")
                if item.canonical_url:
                    console.print(f"[bold]Canonical URL:[/bold] {item.canonical_url}")
                console.print(f"[bold]State:[/bold] {item.state}")
                console.print(f"[bold]Provider:[/bold] {item.provider}")
                console.print(f"[bold]Assignee:[/bold] {', '.join(item.assignees) if item.assignees else 'Unassigned'}")

                # Show metrics if available
                if item.story_points is not None or item.business_value is not None or item.priority is not None:
                    console.print("\n[bold]Story Metrics:[/bold]")
                    if item.story_points is not None:
                        console.print(f"  - Story Points: {item.story_points}")
                    if item.business_value is not None:
                        console.print(f"  - Business Value: {item.business_value}")
                    if item.priority is not None:
                        console.print(f"  - Priority: {item.priority} (1=highest)")
                    if item.value_points is not None:
                        console.print(f"  - Value Points (SAFe): {item.value_points}")
                    if item.work_item_type:
                        console.print(f"  - Work Item Type: {item.work_item_type}")

                # Always show acceptance criteria if it's a required section, even if empty
                # This helps copilot understand what fields need to be added
                is_acceptance_criteria_required = (
                    target_template.required_sections and "Acceptance Criteria" in target_template.required_sections
                )
                if is_acceptance_criteria_required or item.acceptance_criteria:
                    console.print("\n[bold]Acceptance Criteria:[/bold]")
                    if item.acceptance_criteria:
                        console.print(Panel(item.acceptance_criteria))
                    else:
                        # Show empty state so copilot knows to add it
                        console.print(Panel("[dim](empty - required field)[/dim]", border_style="dim"))

                # Always show body (Description is typically required)
                console.print("\n[bold]Body:[/bold]")
                body_content = (
                    item.body_markdown[:1000] + "..." if len(item.body_markdown) > 1000 else item.body_markdown
                )
                if not body_content.strip():
                    # Show empty state so copilot knows to add it
                    console.print(Panel("[dim](empty - required field)[/dim]", border_style="dim"))
                else:
                    console.print(Panel(body_content))

                # Show template info
                console.print(
                    f"\n[bold]Target Template:[/bold] {target_template.name} (ID: {target_template.template_id})"
                )
                console.print(f"[bold]Template Description:[/bold] {target_template.description}")

                # Show what would be updated
                console.print(
                    "\n[yellow]⚠ Preview mode: Item needs refinement but interactive prompts are skipped[/yellow]"
                )
                console.print(
                    "[yellow]   Use [bold]--write[/bold] flag to enable interactive refinement and writeback[/yellow]"
                )
                console.print(
                    "[yellow]   Or use [bold]--export-to-tmp[/bold] to export items for copilot processing[/yellow]"
                )
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
            console.print("4. Paste the refined content below, then type 'END' on a new line when done\n")

            # Read multiline input from stdin
            # Support both interactive (paste + Ctrl+D) and non-interactive (EOF) modes
            # Note: When pasting multiline content, each line is read sequentially
            refined_content_lines: list[str] = []
            console.print("[bold]Paste refined content below (type 'END' on a new line when done):[/bold]")
            console.print("[dim]Commands: :skip (skip this item), :quit or :abort (cancel session)[/dim]")

            try:
                while True:
                    try:
                        line = input()
                        line_stripped = line.strip()
                        line_upper = line_stripped.upper()

                        # Check for sentinel values (case-insensitive)
                        if line_upper == "END":
                            break
                        if line_upper == ":SKIP":
                            console.print("[yellow]Skipping current item[/yellow]")
                            skipped_count += 1
                            refined_content_lines = []  # Clear content
                            break
                        if line_upper in (":QUIT", ":ABORT"):
                            console.print("[yellow]Cancelling refinement session[/yellow]")
                            cancelled = True
                            refined_content_lines = []  # Clear content
                            break

                        refined_content_lines.append(line)
                    except EOFError:
                        # Ctrl+D pressed or EOF reached (common when pasting multiline content)
                        break
            except KeyboardInterrupt:
                console.print("\n[yellow]Input cancelled - skipping[/yellow]")
                skipped_count += 1
                continue

            # Check if session was cancelled
            if cancelled:
                break

            refined_content = "\n".join(refined_content_lines).strip()

            if not refined_content:
                console.print("[yellow]No refined content provided - skipping[/yellow]")
                skipped_count += 1
                continue

            # Validate and score refined content (provider-aware)
            try:
                refinement_result = refiner.validate_and_score_refinement(
                    refined_content, item.body_markdown, target_template, item
                )

                # Print newline to separate validation results
                console.print()

                # Display validation result
                console.print("[bold]Refinement Validation Result:[/bold]")
                console.print(f"[green]Confidence: {refinement_result.confidence:.2f}[/green]")
                if refinement_result.has_todo_markers:
                    console.print("[yellow]⚠ Contains TODO markers[/yellow]")
                if refinement_result.has_notes_section:
                    console.print("[yellow]⚠ Contains NOTES section[/yellow]")

                # Display story metrics if available
                if item.story_points is not None or item.business_value is not None or item.priority is not None:
                    console.print("\n[bold]Story Metrics:[/bold]")
                    if item.story_points is not None:
                        console.print(f"  - Story Points: {item.story_points}")
                    if item.business_value is not None:
                        console.print(f"  - Business Value: {item.business_value}")
                    if item.priority is not None:
                        console.print(f"  - Priority: {item.priority} (1=highest)")
                    if item.value_points is not None:
                        console.print(f"  - Value Points (SAFe): {item.value_points}")
                    if item.work_item_type:
                        console.print(f"  - Work Item Type: {item.work_item_type}")

                # Display story splitting suggestion if needed
                if refinement_result.needs_splitting and refinement_result.splitting_suggestion:
                    console.print("\n[yellow]⚠ Story Splitting Recommendation:[/yellow]")
                    console.print(Panel(refinement_result.splitting_suggestion, title="Splitting Suggestion"))

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
                console.print("  - business_value: Preserved (if present in provider_fields)")
                console.print("  - priority: Preserved (if present in provider_fields)")
                console.print("  - acceptance_criteria: Preserved (if present in provider_fields)")
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

                        # Writeback to remote backlog using adapter
                        # Build adapter kwargs for writeback
                        writeback_kwargs = _build_adapter_kwargs(
                            adapter,
                            repo_owner=repo_owner,
                            repo_name=repo_name,
                            github_token=github_token,
                            ado_org=ado_org,
                            ado_project=ado_project,
                            ado_token=ado_token,
                        )

                        adapter_instance = adapter_registry.get_adapter(adapter, **writeback_kwargs)
                        if isinstance(adapter_instance, BacklogAdapter):
                            # Update all fields including new agile framework fields
                            update_fields_list = ["title", "body_markdown"]
                            if item.acceptance_criteria:
                                update_fields_list.append("acceptance_criteria")
                            if item.story_points is not None:
                                update_fields_list.append("story_points")
                            if item.business_value is not None:
                                update_fields_list.append("business_value")
                            if item.priority is not None:
                                update_fields_list.append("priority")
                            updated_item = adapter_instance.update_backlog_item(item, update_fields=update_fields_list)
                            console.print(f"[green]✓ Updated backlog item: {updated_item.url}[/green]")

                            # Add OpenSpec comment if requested
                            if openspec_comment:
                                # Extract OpenSpec change proposal ID from original body if present
                                original_body = item.body_markdown or ""
                                openspec_change_id = _extract_openspec_change_id(original_body)

                                # Generate OpenSpec change proposal reference
                                change_id = openspec_change_id or f"backlog-refine-{item.id}"
                                comment_text = (
                                    f"## OpenSpec Change Proposal Reference\n\n"
                                    f"This backlog item was refined using SpecFact CLI template-driven refinement.\n\n"
                                    f"- **Change ID**: `{change_id}`\n"
                                    f"- **Template**: `{item.detected_template or 'auto-detected'}`\n"
                                    f"- **Confidence**: `{item.template_confidence or 0.0:.2f}`\n"
                                    f"- **Refined**: {item.refinement_timestamp or 'N/A'}\n\n"
                                    f"*Note: Original body preserved. "
                                    f"This comment provides OpenSpec reference for cross-sync.*"
                                )
                                if adapter_instance.add_comment(updated_item, comment_text):
                                    console.print("[green]✓ Added OpenSpec reference comment[/green]")
                                else:
                                    console.print(
                                        "[yellow]⚠ Failed to add comment (adapter may not support comments)[/yellow]"
                                    )
                        else:
                            console.print("[yellow]⚠ Adapter does not support backlog updates[/yellow]")
                        refined_count += 1
                    else:
                        # Interactive prompt with clear separation
                        console.print()
                        accept = Confirm.ask("Accept refinement and write to backlog?", default=False)
                        if accept:
                            item.apply_refinement()

                            # Writeback to remote backlog using adapter
                            # Build adapter kwargs for writeback
                            writeback_kwargs = _build_adapter_kwargs(
                                adapter,
                                repo_owner=repo_owner,
                                repo_name=repo_name,
                                github_token=github_token,
                                ado_org=ado_org,
                                ado_project=ado_project,
                                ado_token=ado_token,
                            )

                            adapter_instance = adapter_registry.get_adapter(adapter, **writeback_kwargs)
                            if isinstance(adapter_instance, BacklogAdapter):
                                # Update all fields including new agile framework fields
                                update_fields_list = ["title", "body_markdown"]
                                if item.acceptance_criteria:
                                    update_fields_list.append("acceptance_criteria")
                                if item.story_points is not None:
                                    update_fields_list.append("story_points")
                                if item.business_value is not None:
                                    update_fields_list.append("business_value")
                                if item.priority is not None:
                                    update_fields_list.append("priority")
                                updated_item = adapter_instance.update_backlog_item(
                                    item, update_fields=update_fields_list
                                )
                                console.print(f"[green]✓ Updated backlog item: {updated_item.url}[/green]")

                                # Add OpenSpec comment if requested
                                if openspec_comment:
                                    # Extract OpenSpec change proposal ID from original body if present
                                    original_body = item.body_markdown or ""
                                    openspec_change_id = _extract_openspec_change_id(original_body)

                                    # Generate OpenSpec change proposal reference
                                    change_id = openspec_change_id or f"backlog-refine-{item.id}"
                                    comment_text = (
                                        f"## OpenSpec Change Proposal Reference\n\n"
                                        f"This backlog item was refined using SpecFact CLI template-driven refinement.\n\n"
                                        f"- **Change ID**: `{change_id}`\n"
                                        f"- **Template**: `{item.detected_template or 'auto-detected'}`\n"
                                        f"- **Confidence**: `{item.template_confidence or 0.0:.2f}`\n"
                                        f"- **Refined**: {item.refinement_timestamp or 'N/A'}\n\n"
                                        f"*Note: Original body preserved. "
                                        f"This comment provides OpenSpec reference for cross-sync.*"
                                    )
                                    if adapter_instance.add_comment(updated_item, comment_text):
                                        console.print("[green]✓ Added OpenSpec reference comment[/green]")
                                    else:
                                        console.print(
                                            "[yellow]⚠ Failed to add comment "
                                            "(adapter may not support comments)[/yellow]"
                                        )
                            else:
                                console.print("[yellow]⚠ Adapter does not support backlog updates[/yellow]")
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

        # OpenSpec bundle import (if requested)
        if (bundle or auto_bundle) and refined_count > 0:
            console.print("\n[bold]OpenSpec Bundle Import:[/bold]")
            try:
                # Determine bundle path
                bundle_path: Path | None = None
                if bundle:
                    bundle_path = Path(bundle)
                elif auto_bundle:
                    # Auto-detect bundle from current directory
                    current_dir = Path.cwd()
                    bundle_path = current_dir / ".specfact" / "bundle.yaml"
                    if not bundle_path.exists():
                        bundle_path = current_dir / "bundle.yaml"

                if bundle_path and bundle_path.exists():
                    console.print(
                        f"[green]Importing {refined_count} refined items to OpenSpec bundle: {bundle_path}[/green]"
                    )
                    # TODO: Implement actual import logic using import command functionality
                    console.print(
                        "[yellow]⚠ OpenSpec bundle import integration pending (use import command separately)[/yellow]"
                    )
                else:
                    console.print("[yellow]⚠ Bundle path not found. Skipping import.[/yellow]")
            except Exception as e:
                console.print(f"[yellow]⚠ Failed to import to OpenSpec bundle: {e}[/yellow]")

        # Summary
        console.print("\n[bold]Summary:[/bold]")
        if cancelled:
            console.print("[yellow]Session cancelled by user[/yellow]")
        if limit:
            console.print(f"[dim]Limit applied: {limit} items[/dim]")
        console.print(f"[green]Refined: {refined_count}[/green]")
        console.print(f"[yellow]Skipped: {skipped_count}[/yellow]")

        # Note: Writeback is handled per-item above when --write flag is set

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("map-fields")
@require(
    lambda ado_org, ado_project: isinstance(ado_org, str)
    and len(ado_org) > 0
    and isinstance(ado_project, str)
    and len(ado_project) > 0,
    "ADO org and project must be non-empty strings",
)
@beartype
def map_fields(
    ado_org: str = typer.Option(..., "--ado-org", help="Azure DevOps organization (required)"),
    ado_project: str = typer.Option(..., "--ado-project", help="Azure DevOps project (required)"),
    ado_token: str | None = typer.Option(
        None, "--ado-token", help="Azure DevOps PAT (optional, uses AZURE_DEVOPS_TOKEN env var if not provided)"
    ),
    ado_base_url: str | None = typer.Option(
        None, "--ado-base-url", help="Azure DevOps base URL (defaults to https://dev.azure.com)"
    ),
    reset: bool = typer.Option(
        False, "--reset", help="Reset custom field mapping to defaults (deletes ado_custom.yaml)"
    ),
) -> None:
    """
    Interactive command to map ADO fields to canonical field names.

    Fetches available fields from Azure DevOps API and guides you through
    mapping them to canonical field names (description, acceptance_criteria, etc.).
    Saves the mapping to .specfact/templates/backlog/field_mappings/ado_custom.yaml.

    Examples:
        specfact backlog map-fields --ado-org myorg --ado-project myproject
        specfact backlog map-fields --ado-org myorg --ado-project myproject --ado-token <token>
        specfact backlog map-fields --ado-org myorg --ado-project myproject --reset
    """
    import base64
    import re
    import sys

    import questionary  # type: ignore[reportMissingImports]
    import requests

    from specfact_cli.backlog.mappers.template_config import FieldMappingConfig
    from specfact_cli.utils.auth_tokens import get_token

    def _find_potential_match(canonical_field: str, available_fields: list[dict[str, Any]]) -> str | None:
        """
        Find a potential ADO field match for a canonical field using regex/fuzzy matching.

        Args:
            canonical_field: Canonical field name (e.g., "acceptance_criteria")
            available_fields: List of ADO field dicts with "referenceName" and "name"

        Returns:
            Reference name of best matching field, or None if no good match found
        """
        # Convert canonical field to search patterns
        # e.g., "acceptance_criteria" -> ["acceptance", "criteria"]
        field_parts = re.split(r"[_\s-]+", canonical_field.lower())

        best_match: tuple[str, int] | None = None
        best_score = 0

        for field in available_fields:
            ref_name = field.get("referenceName", "")
            name = field.get("name", ref_name)

            # Search in both reference name and display name
            search_text = f"{ref_name} {name}".lower()

            # Calculate match score
            score = 0
            matched_parts = 0

            for part in field_parts:
                # Exact match in reference name (highest priority)
                if part in ref_name.lower():
                    score += 10
                    matched_parts += 1
                # Exact match in display name
                elif part in name.lower():
                    score += 5
                    matched_parts += 1
                # Partial match (contains substring)
                elif part in search_text:
                    score += 2
                    matched_parts += 1

            # Bonus for matching all parts
            if matched_parts == len(field_parts):
                score += 5

            # Prefer Microsoft.VSTS.Common.* fields
            if ref_name.startswith("Microsoft.VSTS.Common."):
                score += 3

            if score > best_score and matched_parts > 0:
                best_score = score
                best_match = (ref_name, score)

        # Only return if we have a reasonable match (score >= 5)
        if best_match and best_score >= 5:
            return best_match[0]

        return None

    # Resolve token (explicit > env var > stored token)
    api_token: str | None = None
    auth_scheme = "basic"
    if ado_token:
        api_token = ado_token
        auth_scheme = "basic"
    elif os.environ.get("AZURE_DEVOPS_TOKEN"):
        api_token = os.environ.get("AZURE_DEVOPS_TOKEN")
        auth_scheme = "basic"
    elif stored_token := get_token("azure-devops", allow_expired=False):
        # Valid, non-expired token found
        api_token = stored_token.get("access_token")
        token_type = (stored_token.get("token_type") or "bearer").lower()
        auth_scheme = "bearer" if token_type == "bearer" else "basic"
    elif stored_token_expired := get_token("azure-devops", allow_expired=True):
        # Token exists but is expired - use it anyway for this command (user can refresh later)
        api_token = stored_token_expired.get("access_token")
        token_type = (stored_token_expired.get("token_type") or "bearer").lower()
        auth_scheme = "bearer" if token_type == "bearer" else "basic"
        console.print(
            "[yellow]⚠[/yellow] Using expired stored token. If authentication fails, refresh with: specfact auth azure-devops"
        )

    if not api_token:
        console.print("[red]Error:[/red] Azure DevOps token required")
        console.print("[yellow]Options:[/yellow]")
        console.print("  1. Use --ado-token option")
        console.print("  2. Set AZURE_DEVOPS_TOKEN environment variable")
        console.print("  3. Use: specfact auth azure-devops")
        raise typer.Exit(1)

    # Build base URL
    base_url = (ado_base_url or "https://dev.azure.com").rstrip("/")

    # Fetch fields from ADO API
    console.print("[cyan]Fetching fields from Azure DevOps...[/cyan]")
    fields_url = f"{base_url}/{ado_org}/{ado_project}/_apis/wit/fields?api-version=7.1"

    # Prepare authentication headers based on auth scheme
    headers: dict[str, str] = {}
    if auth_scheme == "bearer":
        headers["Authorization"] = f"Bearer {api_token}"
    else:
        # Basic auth for PAT tokens
        auth_header = base64.b64encode(f":{api_token}".encode()).decode()
        headers["Authorization"] = f"Basic {auth_header}"

    try:
        response = requests.get(fields_url, headers=headers, timeout=30)
        response.raise_for_status()
        fields_data = response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error:[/red] Failed to fetch fields from Azure DevOps: {e}")
        raise typer.Exit(1) from e

    # Extract fields and filter out system-only fields
    all_fields = fields_data.get("value", [])
    system_only_fields = {
        "System.Id",
        "System.Rev",
        "System.ChangedDate",
        "System.CreatedDate",
        "System.ChangedBy",
        "System.CreatedBy",
        "System.AreaId",
        "System.IterationId",
        "System.TeamProject",
        "System.NodeName",
        "System.AreaLevel1",
        "System.AreaLevel2",
        "System.AreaLevel3",
        "System.AreaLevel4",
        "System.AreaLevel5",
        "System.AreaLevel6",
        "System.AreaLevel7",
        "System.AreaLevel8",
        "System.AreaLevel9",
        "System.AreaLevel10",
        "System.IterationLevel1",
        "System.IterationLevel2",
        "System.IterationLevel3",
        "System.IterationLevel4",
        "System.IterationLevel5",
        "System.IterationLevel6",
        "System.IterationLevel7",
        "System.IterationLevel8",
        "System.IterationLevel9",
        "System.IterationLevel10",
    }

    # Filter relevant fields
    relevant_fields = [
        field
        for field in all_fields
        if field.get("referenceName") not in system_only_fields
        and not field.get("referenceName", "").startswith("System.History")
        and not field.get("referenceName", "").startswith("System.Watermark")
    ]

    # Sort fields by reference name
    relevant_fields.sort(key=lambda f: f.get("referenceName", ""))

    # Canonical fields to map
    canonical_fields = {
        "description": "Description",
        "acceptance_criteria": "Acceptance Criteria",
        "story_points": "Story Points",
        "business_value": "Business Value",
        "priority": "Priority",
        "work_item_type": "Work Item Type",
    }

    # Load default mappings from AdoFieldMapper
    from specfact_cli.backlog.mappers.ado_mapper import AdoFieldMapper

    default_mappings = AdoFieldMapper.DEFAULT_FIELD_MAPPINGS
    # Reverse default mappings: canonical -> list of ADO fields
    default_mappings_reversed: dict[str, list[str]] = {}
    for ado_field, canonical in default_mappings.items():
        if canonical not in default_mappings_reversed:
            default_mappings_reversed[canonical] = []
        default_mappings_reversed[canonical].append(ado_field)

    # Handle --reset flag
    current_dir = Path.cwd()
    custom_mapping_file = current_dir / ".specfact" / "templates" / "backlog" / "field_mappings" / "ado_custom.yaml"

    if reset:
        if custom_mapping_file.exists():
            custom_mapping_file.unlink()
            console.print(f"[green]✓[/green] Reset custom field mapping (deleted {custom_mapping_file})")
            console.print("[dim]Custom mappings removed. Default mappings will be used.[/dim]")
        else:
            console.print("[yellow]⚠[/yellow] No custom mapping file found. Nothing to reset.")
        return

    # Load existing mapping if it exists
    existing_mapping: dict[str, str] = {}
    existing_work_item_type_mappings: dict[str, str] = {}
    existing_config: FieldMappingConfig | None = None
    if custom_mapping_file.exists():
        try:
            existing_config = FieldMappingConfig.from_file(custom_mapping_file)
            existing_mapping = existing_config.field_mappings
            existing_work_item_type_mappings = existing_config.work_item_type_mappings or {}
            console.print(f"[green]✓[/green] Loaded existing mapping from {custom_mapping_file}")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Failed to load existing mapping: {e}")

    # Build combined mapping: existing > default (checking which defaults exist in fetched fields)
    combined_mapping: dict[str, str] = {}
    # Get list of available ADO field reference names
    available_ado_refs = {field.get("referenceName", "") for field in relevant_fields}

    # First add defaults, but only if they exist in the fetched ADO fields
    for canonical_field in canonical_fields:
        if canonical_field in default_mappings_reversed:
            # Find which default mappings actually exist in the fetched ADO fields
            # Prefer more common field names (Microsoft.VSTS.Common.* over System.*)
            default_options = default_mappings_reversed[canonical_field]
            existing_defaults = [ado_field for ado_field in default_options if ado_field in available_ado_refs]

            if existing_defaults:
                # Prefer Microsoft.VSTS.Common.* over System.* for better compatibility
                preferred = None
                for ado_field in existing_defaults:
                    if ado_field.startswith("Microsoft.VSTS.Common."):
                        preferred = ado_field
                        break
                # If no Microsoft.VSTS.Common.* found, use first existing
                if preferred is None:
                    preferred = existing_defaults[0]
                combined_mapping[preferred] = canonical_field
            else:
                # No default mapping exists - try to find a potential match using regex/fuzzy matching
                potential_match = _find_potential_match(canonical_field, relevant_fields)
                if potential_match:
                    combined_mapping[potential_match] = canonical_field
    # Then override with existing mappings
    combined_mapping.update(existing_mapping)

    # Interactive mapping
    console.print()
    console.print(Panel("[bold cyan]Interactive Field Mapping[/bold cyan]", border_style="cyan"))
    console.print("[dim]Use ↑↓ to navigate, ⏎ to select. Map ADO fields to canonical field names.[/dim]")
    console.print()

    new_mapping: dict[str, str] = {}

    # Build choice list with display names
    field_choices_display: list[str] = ["<no mapping>"]
    field_choices_refs: list[str] = ["<no mapping>"]
    for field in relevant_fields:
        ref_name = field.get("referenceName", "")
        name = field.get("name", ref_name)
        display = f"{ref_name} ({name})"
        field_choices_display.append(display)
        field_choices_refs.append(ref_name)

    for canonical_field, display_name in canonical_fields.items():
        # Find current mapping (existing > default)
        current_ado_fields = [
            ado_field for ado_field, canonical in combined_mapping.items() if canonical == canonical_field
        ]

        # Determine default selection
        default_selection = "<no mapping>"
        if current_ado_fields:
            # Find the current mapping in the choices list
            current_ref = current_ado_fields[0]
            if current_ref in field_choices_refs:
                default_selection = field_choices_display[field_choices_refs.index(current_ref)]
            else:
                # If current mapping not in available fields, use "<no mapping>"
                default_selection = "<no mapping>"

        # Use interactive selection menu with questionary
        console.print(f"[bold]{display_name}[/bold] (canonical: {canonical_field})")
        if current_ado_fields:
            console.print(f"[dim]Current: {', '.join(current_ado_fields)}[/dim]")
        else:
            console.print("[dim]Current: <no mapping>[/dim]")

        # Find default index
        default_index = 0
        if default_selection != "<no mapping>" and default_selection in field_choices_display:
            default_index = field_choices_display.index(default_selection)

        # Use questionary for interactive selection with arrow keys
        try:
            selected_display = questionary.select(
                f"Select ADO field for {display_name}",
                choices=field_choices_display,
                default=field_choices_display[default_index] if default_index < len(field_choices_display) else None,
                use_arrow_keys=True,
                use_jk_keys=False,
            ).ask()
            if selected_display is None:
                selected_display = "<no mapping>"
        except KeyboardInterrupt:
            console.print("\n[yellow]Selection cancelled.[/yellow]")
            sys.exit(0)

        # Convert display name back to reference name
        if selected_display and selected_display != "<no mapping>" and selected_display in field_choices_display:
            selected_ref = field_choices_refs[field_choices_display.index(selected_display)]
            new_mapping[selected_ref] = canonical_field

        console.print()

    # Validate mapping
    console.print("[cyan]Validating mapping...[/cyan]")
    duplicate_ado_fields = {}
    for ado_field, canonical in new_mapping.items():
        if ado_field in duplicate_ado_fields:
            duplicate_ado_fields[ado_field].append(canonical)
        else:
            # Check if this ADO field is already mapped to a different canonical field
            for other_ado, other_canonical in new_mapping.items():
                if other_ado == ado_field and other_canonical != canonical:
                    if ado_field not in duplicate_ado_fields:
                        duplicate_ado_fields[ado_field] = []
                    duplicate_ado_fields[ado_field].extend([canonical, other_canonical])

    if duplicate_ado_fields:
        console.print("[yellow]⚠[/yellow] Warning: Some ADO fields are mapped to multiple canonical fields:")
        for ado_field, canonicals in duplicate_ado_fields.items():
            console.print(f"  {ado_field}: {', '.join(set(canonicals))}")
        if not Confirm.ask("Continue anyway?", default=False):
            console.print("[yellow]Mapping cancelled.[/yellow]")
            raise typer.Exit(0)

    # Merge with existing mapping (new mapping takes precedence)
    final_mapping = existing_mapping.copy()
    final_mapping.update(new_mapping)

    # Preserve existing work_item_type_mappings if they exist
    # This prevents erasing custom work item type mappings when updating field mappings
    work_item_type_mappings = existing_work_item_type_mappings.copy() if existing_work_item_type_mappings else {}

    # Create FieldMappingConfig
    config = FieldMappingConfig(
        framework=existing_config.framework if existing_config else "default",
        field_mappings=final_mapping,
        work_item_type_mappings=work_item_type_mappings,
    )

    # Save to file
    custom_mapping_file.parent.mkdir(parents=True, exist_ok=True)
    with custom_mapping_file.open("w", encoding="utf-8") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)

    console.print()
    console.print(Panel("[bold green]✓ Mapping saved successfully[/bold green]", border_style="green"))
    console.print(f"[green]Location:[/green] {custom_mapping_file}")
    console.print()
    console.print("[dim]You can now use this mapping with specfact backlog refine.[/dim]")
