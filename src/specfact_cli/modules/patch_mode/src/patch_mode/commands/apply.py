"""Patch apply command: local apply and --write with confirmation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Annotated

import typer
from beartype import beartype
from icontract import require

from specfact_cli.common import get_bridge_logger
from specfact_cli.modules.patch_mode.src.patch_mode.pipeline.applier import (
    apply_patch_local,
    apply_patch_write,
    preflight_check,
)
from specfact_cli.modules.patch_mode.src.patch_mode.pipeline.idempotency import check_idempotent, mark_applied
from specfact_cli.runtime import get_configured_console


app = typer.Typer(help="Preview and apply patches (local or upstream with --write).")
console = get_configured_console()
logger = get_bridge_logger(__name__)


@beartype
@require(lambda patch_file: patch_file.exists(), "Patch file must exist")
def _apply_local(patch_file: Path, dry_run: bool) -> None:
    """Apply patch locally with preflight; no upstream write."""
    if not preflight_check(patch_file):
        console.print("[red]Preflight check failed: patch file empty or unreadable.[/red]")
        raise SystemExit(1)
    if dry_run:
        console.print(f"[dim]Dry run: would apply {patch_file}[/dim]")
        return
    ok = apply_patch_local(patch_file, dry_run=False)
    if not ok:
        console.print("[red]Apply failed.[/red]")
        raise SystemExit(1)
    console.print(f"[green]Applied patch locally: {patch_file}[/green]")


@beartype
@require(lambda patch_file: patch_file.exists(), "Patch file must exist")
def _apply_write(patch_file: Path, confirmed: bool) -> None:
    """Update upstream only with explicit confirmation; idempotent."""
    if not confirmed:
        console.print("[yellow]Write skipped: use --yes to confirm upstream write.[/yellow]")
        raise SystemExit(0)
    key = hashlib.sha256(patch_file.read_bytes()).hexdigest()
    if check_idempotent(key):
        console.print("[dim]Already applied (idempotent); skipping write.[/dim]")
        return
    ok = apply_patch_write(patch_file, confirmed=True)
    if not ok:
        console.print("[red]Write failed.[/red]")
        raise SystemExit(1)
    mark_applied(key)
    console.print(f"[green]Wrote patch upstream: {patch_file}[/green]")


@app.command("apply")
@beartype
def apply_cmd(
    patch_file: Annotated[
        Path,
        typer.Argument(..., help="Path to patch file", exists=True),
    ],
    write: bool = typer.Option(False, "--write", help="Write to upstream (requires --yes)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm upstream write"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preflight only, do not apply"),
) -> None:
    """Apply patch locally or write upstream with confirmation."""
    path = Path(patch_file) if not isinstance(patch_file, Path) else patch_file
    if write:
        _apply_write(path, confirmed=yes)
    else:
        _apply_local(path, dry_run=dry_run)
