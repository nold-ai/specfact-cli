"""Typer app for policy-engine commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from beartype import beartype
from icontract import require
from rich.console import Console

from policy_engine.config import load_policy_config
from policy_engine.engine.suggester import build_suggestions
from policy_engine.engine.validator import load_snapshot_items, render_markdown, validate_policies


policy_app = typer.Typer(name="policy", help="Policy validation and suggestion workflows.")
console = Console()


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
