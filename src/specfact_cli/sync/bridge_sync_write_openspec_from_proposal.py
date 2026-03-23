"""Write OpenSpec change files from imported ChangeProposal (split from bridge_sync for CC)."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

from icontract import ensure, require

from specfact_cli.runtime import get_configured_console


console = get_configured_console()


class _OpenspecWriter(Protocol):
    bridge_config: Any

    def _get_openspec_changes_dir(self) -> Path | None: ...

    def _format_proposal_title(self, title: str) -> str: ...

    def _extract_what_changes_content(self, description: str) -> str: ...

    def _format_what_changes_section(self, description: str) -> str: ...

    def _determine_affected_specs(self, proposal: Any) -> list[str]: ...

    def _extract_dependencies_section(self, description: str) -> str: ...

    def _generate_tasks_from_proposal(self, proposal: Any) -> str: ...

    def _extract_requirement_from_proposal(self, proposal: Any, spec_id: str) -> str: ...

    def _save_openspec_change_proposal(self, proposal: dict[str, Any]) -> None: ...


def _append_refinement_metadata_lines(
    proposal_lines: list[str],
    proposal: Any,
) -> None:
    if proposal.source_tracking.template_id:
        proposal_lines.append(f"- **Template ID**: {proposal.source_tracking.template_id}")
    if proposal.source_tracking.refinement_confidence is not None:
        proposal_lines.append(f"- **Refinement Confidence**: {proposal.source_tracking.refinement_confidence:.2f}")
    if proposal.source_tracking.refinement_timestamp:
        proposal_lines.append(
            f"- **Refinement Timestamp**: {proposal.source_tracking.refinement_timestamp.isoformat()}"
        )
    if proposal.source_tracking.refinement_ai_model:
        proposal_lines.append(f"- **Refinement AI Model**: {proposal.source_tracking.refinement_ai_model}")
    if proposal.source_tracking.template_id or proposal.source_tracking.refinement_confidence is not None:
        proposal_lines.append("")


def _append_backlog_source_tracking_lines(
    proposal_lines: list[str],
    proposal: Any,
    source_metadata: dict[str, Any],
) -> None:
    backlog_entries = source_metadata.get("backlog_entries", [])
    if not backlog_entries:
        return
    for entry in backlog_entries:
        if not isinstance(entry, dict):
            continue
        entry_d2: dict[str, Any] = cast(dict[str, Any], entry)
        source_repo = entry_d2.get("source_repo", "")
        source_id = entry_d2.get("source_id", "")
        source_url = entry_d2.get("source_url", "")
        source_type = entry_d2.get("source_type", "unknown")
        if source_repo:
            proposal_lines.append(f"<!-- source_repo: {source_repo} -->")
        source_type_capitalization = {
            "github": "GitHub",
            "ado": "ADO",
            "linear": "Linear",
            "jira": "Jira",
            "unknown": "Unknown",
        }
        source_type_display = source_type_capitalization.get(str(source_type).lower(), "Unknown")
        if source_id:
            proposal_lines.append(f"- **{source_type_display} Issue**: #{source_id}")
        if source_url:
            proposal_lines.append(f"- **Issue URL**: <{source_url}>")
        proposal_lines.append(f"- **Last Synced Status**: {proposal.status}")
        proposal_lines.append("")


def _write_spec_delta_file(
    bridge: _OpenspecWriter,
    change_id: str,
    spec_id: str,
    proposal: Any,
    specs_dir: Path,
    warnings: list[str],
    logger: logging.Logger,
) -> None:
    spec_dir = specs_dir / spec_id
    spec_dir.mkdir(exist_ok=True)
    spec_lines: list[str] = []
    spec_lines.append(f"# {spec_id} Specification")
    spec_lines.append("")
    spec_lines.append("## Purpose")
    spec_lines.append("")
    spec_lines.append("TBD - created by importing backlog item")
    spec_lines.append("")
    spec_lines.append("## Requirements")
    spec_lines.append("")
    requirement_text = bridge._extract_requirement_from_proposal(proposal, spec_id)
    if requirement_text:
        change_type = "MODIFIED"
        desc_lower = (proposal.description or "").lower()
        if any(keyword in desc_lower for keyword in ["new", "add", "introduce", "create", "implement"]):
            if any(keyword in desc_lower for keyword in ["extend", "modify", "update", "fix", "improve"]):
                change_type = "MODIFIED"
            else:
                change_type = "ADDED"
        spec_lines.append(f"## {change_type} Requirements")
        spec_lines.append("")
        spec_lines.append(requirement_text)
    else:
        spec_lines.append("## MODIFIED Requirements")
        spec_lines.append("")
        spec_lines.append("### Requirement: [Requirement name from proposal]")
        spec_lines.append("")
        spec_lines.append("The system SHALL [requirement description]")
        spec_lines.append("")
        spec_lines.append("#### Scenario: [Scenario name]")
        spec_lines.append("")
        spec_lines.append("- **WHEN** [condition]")
        spec_lines.append("- **THEN** [expected result]")
        spec_lines.append("")
    spec_file = spec_dir / "spec.md"
    if spec_file.exists():
        warning = f"Spec delta already exists for change '{change_id}' ({spec_id}), leaving it untouched."
        warnings.append(warning)
        logger.info(warning)
    else:
        spec_file.write_text("\n".join(spec_lines), encoding="utf-8")
        logger.info(f"Created spec delta: {spec_file}")


def _resolve_change_directory(
    bridge: _OpenspecWriter,
    proposal: Any,
    openspec_changes_dir: Path,
    logger: logging.Logger,
) -> tuple[str, Path]:
    change_id = proposal.name
    if change_id == "unknown" or not change_id:
        title_clean = bridge._format_proposal_title(proposal.title)
        change_id = re.sub(r"[^a-z0-9]+", "-", title_clean.lower()).strip("-")
        if not change_id:
            change_id = "imported-change"

    change_dir = openspec_changes_dir / change_id
    if change_dir.exists() and change_dir.is_dir() and (change_dir / "proposal.md").exists():
        logger.info(f"Updating existing OpenSpec change: {change_id}")
        return change_id, change_dir

    counter = 1
    original_change_id = change_id
    while change_dir.exists() and change_dir.is_dir():
        change_id = f"{original_change_id}-{counter}"
        change_dir = openspec_changes_dir / change_id
        counter += 1
    return change_id, change_dir


def _maybe_apply_refinement_fields(
    proposal: Any,
    template_id: str | None,
    refinement_confidence: float | None,
) -> None:
    if not proposal.source_tracking or (template_id is None and refinement_confidence is None):
        return
    if template_id is not None:
        proposal.source_tracking.template_id = template_id
    if refinement_confidence is not None:
        proposal.source_tracking.refinement_confidence = refinement_confidence
        proposal.source_tracking.refinement_timestamp = datetime.now(UTC)


def _build_proposal_markdown_lines(
    bridge: _OpenspecWriter,
    proposal: Any,
    template_id: str | None,
    refinement_confidence: float | None,
) -> tuple[list[str], list[str]]:
    """Return proposal markdown lines and affected spec ids."""
    _maybe_apply_refinement_fields(proposal, template_id, refinement_confidence)
    proposal_lines: list[str] = []
    proposal_lines.append(f"# Change: {bridge._format_proposal_title(proposal.title)}")
    proposal_lines.append("")
    proposal_lines.append("## Why")
    proposal_lines.append("")
    proposal_lines.append(proposal.rationale or "No rationale provided.")
    proposal_lines.append("")
    proposal_lines.append("## What Changes")
    proposal_lines.append("")
    description = proposal.description or "No description provided."
    what_changes_content = bridge._extract_what_changes_content(description)
    formatted_description = bridge._format_what_changes_section(what_changes_content)
    proposal_lines.append(formatted_description)
    proposal_lines.append("")
    affected_specs = bridge._determine_affected_specs(proposal)
    proposal_lines.append("## Impact")
    proposal_lines.append("")
    proposal_lines.append(f"- **Affected specs**: {', '.join(f'`{s}`' for s in affected_specs)}")
    proposal_lines.append("- **Affected code**: See implementation tasks")
    proposal_lines.append("- **Integration points**: See spec deltas")
    proposal_lines.append("")
    dependencies_section = bridge._extract_dependencies_section(proposal.description or "")
    if dependencies_section:
        proposal_lines.append("---")
        proposal_lines.append("")
        proposal_lines.append("## Dependencies")
        proposal_lines.append("")
        proposal_lines.append(dependencies_section)
        proposal_lines.append("")
    if proposal.source_tracking:
        proposal_lines.append("---")
        proposal_lines.append("")
        proposal_lines.append("## Source Tracking")
        proposal_lines.append("")
        source_metadata = proposal.source_tracking.source_metadata or {}
        if proposal.source_tracking.template_id or proposal.source_tracking.refinement_confidence is not None:
            _append_refinement_metadata_lines(proposal_lines, proposal)
        if isinstance(source_metadata, dict):
            source_metadata_d: dict[str, Any] = cast(dict[str, Any], source_metadata)
            _append_backlog_source_tracking_lines(proposal_lines, proposal, source_metadata_d)
    return proposal_lines, affected_specs


@require(lambda bridge, proposal, bridge_config: bridge is not None)
@ensure(lambda result: isinstance(result, list))
def bridge_sync_write_openspec_change_from_proposal(
    bridge: _OpenspecWriter,
    proposal: Any,
    bridge_config: Any,
    template_id: str | None = None,
    refinement_confidence: float | None = None,
) -> list[str]:
    """Write OpenSpec change files from imported ChangeProposal."""
    _ = bridge_config
    warnings: list[str] = []
    logger = logging.getLogger(__name__)

    openspec_changes_dir = bridge._get_openspec_changes_dir()
    if not openspec_changes_dir:
        warning = "OpenSpec changes directory not found. Skipping file creation."
        warnings.append(warning)
        logger.warning(warning)
        console.print(f"[yellow]⚠[/yellow] {warning}")
        return warnings

    change_id, change_dir = _resolve_change_directory(bridge, proposal, openspec_changes_dir, logger)

    try:
        change_dir.mkdir(parents=True, exist_ok=True)
        proposal_lines, affected_specs = _build_proposal_markdown_lines(
            bridge, proposal, template_id, refinement_confidence
        )
        proposal_file = change_dir / "proposal.md"
        proposal_file.write_text("\n".join(proposal_lines), encoding="utf-8")
        logger.info(f"Created proposal.md: {proposal_file}")
        tasks_file = change_dir / "tasks.md"
        if tasks_file.exists():
            warning = f"tasks.md already exists for change '{change_id}', leaving it untouched."
            warnings.append(warning)
            logger.info(warning)
        else:
            tasks_content = bridge._generate_tasks_from_proposal(proposal)
            tasks_file.write_text(tasks_content, encoding="utf-8")
            logger.info(f"Created tasks.md: {tasks_file}")
        specs_dir = change_dir / "specs"
        specs_dir.mkdir(exist_ok=True)
        for spec_id in affected_specs:
            _write_spec_delta_file(
                bridge,
                change_id,
                spec_id,
                proposal,
                specs_dir,
                warnings,
                logger,
            )
        console.print(f"[green]✓[/green] Created OpenSpec change: {change_id} at {change_dir}")
    except Exception as e:
        warning = f"Failed to create OpenSpec files for change '{change_id}': {e}"
        warnings.append(warning)
        logger.warning(warning, exc_info=True)

    return warnings
