"""Typer app for policy-engine commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from beartype import beartype
from icontract import require
from rich.console import Console

from policy_engine.config import list_policy_templates, load_policy_config, load_policy_template
from policy_engine.engine.suggester import build_suggestions
from policy_engine.engine.validator import load_snapshot_items, render_markdown, validate_policies


policy_app = typer.Typer(name="policy", help="Policy validation and suggestion workflows.")
console = Console()
_TEMPLATE_CHOICES = tuple(list_policy_templates())


def _resolve_template_selection(template_name: str | None) -> str:
    if template_name is not None:
        return template_name.strip().lower()
    selected = typer.prompt(
        "Select policy template (scrum/kanban/safe/mixed)",
        default="scrum",
    )
    return selected.strip().lower()


@policy_app.command("init")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
def init_command(
    repo: Annotated[Path, typer.Option("--repo", help="Repository root path.")] = Path("."),
    template: Annotated[str | None, typer.Option("--template", help="Template: scrum, kanban, safe, mixed.")] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing .specfact/policy.yaml.")] = False,
) -> None:
    """Scaffold .specfact/policy.yaml from built-in templates."""
    selected = _resolve_template_selection(template)
    if selected not in _TEMPLATE_CHOICES:
        options = ", ".join(_TEMPLATE_CHOICES)
        console.print(f"[red]Unsupported template '{selected}'. Available: {options}[/red]")
        raise typer.Exit(2)

    template_content, template_error = load_policy_template(selected)
    if template_error:
        console.print(f"[red]{template_error}[/red]")
        raise typer.Exit(1)
    assert template_content is not None

    config_path = repo / ".specfact" / "policy.yaml"
    if config_path.exists() and not force:
        console.print(f"[red]Policy config already exists: {config_path}. Use --force to overwrite.[/red]")
        raise typer.Exit(1)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(template_content, encoding="utf-8")
    console.print(f"Created policy config from '{selected}' template: {config_path}")


@policy_app.command("validate")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
def validate_command(
    repo: Annotated[Path, typer.Option("--repo", help="Repository root path.")] = Path("."),
    snapshot: Annotated[Path | None, typer.Option("--snapshot", help="Optional snapshot JSON path.")] = None,
    output_format: Annotated[str, typer.Option("--format", help="Output format: json, markdown, or both.")] = "both",
) -> None:
    """Run deterministic policy validation and report hard failures."""
    config, config_error = load_policy_config(repo)
    if config_error:
        console.print(f"[red]{config_error}[/red]")
        raise typer.Exit(1)
    assert config is not None

    items, snapshot_error = load_snapshot_items(snapshot)
    if snapshot_error:
        console.print(f"[red]{snapshot_error}[/red]")
        raise typer.Exit(1)

    findings = validate_policies(config, items)
    payload = {
        "summary": {
            "total_findings": len(findings),
            "status": "failed" if findings else "passed",
            "deterministic": True,
            "network_required": False,
        },
        "failures": [finding.model_dump(mode="json") for finding in findings],
    }

    normalized_format = output_format.strip().lower()
    if normalized_format not in ("json", "markdown", "both"):
        console.print("[red]Invalid format. Use: json, markdown, or both.[/red]")
        raise typer.Exit(2)

    if normalized_format in ("markdown", "both"):
        console.print(render_markdown(findings))
    if normalized_format in ("json", "both"):
        console.print(json.dumps(payload, indent=2, sort_keys=True))

    if findings:
        raise typer.Exit(1)


@policy_app.command("suggest")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
def suggest_command(
    repo: Annotated[Path, typer.Option("--repo", help="Repository root path.")] = Path("."),
    snapshot: Annotated[Path | None, typer.Option("--snapshot", help="Optional snapshot JSON path.")] = None,
) -> None:
    """Generate confidence-scored patch-ready policy suggestions without writing files."""
    config, config_error = load_policy_config(repo)
    if config_error:
        console.print(f"[red]{config_error}[/red]")
        raise typer.Exit(1)
    assert config is not None

    items, snapshot_error = load_snapshot_items(snapshot)
    if snapshot_error:
        console.print(f"[red]{snapshot_error}[/red]")
        raise typer.Exit(1)

    findings = validate_policies(config, items)
    suggestions = build_suggestions(findings)
    payload = {
        "summary": {
            "suggestion_count": len(suggestions),
            "patch_ready": True,
            "auto_write": False,
        },
        "suggestions": suggestions,
    }
    console.print("# Policy Suggestions")
    console.print(json.dumps(payload, indent=2, sort_keys=True))
    console.print("No changes were written. Re-run with explicit apply workflow when available.")


# Backward-compatible module package loader expects an `app` attribute.
app = policy_app
