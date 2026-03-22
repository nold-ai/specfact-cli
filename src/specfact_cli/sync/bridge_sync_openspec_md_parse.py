"""Parse OpenSpec proposal.md sections (split from bridge_sync for cyclomatic complexity)."""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require


def _append_block(buf: str, line: str) -> str:
    """Append a line to a section buffer matching legacy newline behavior."""
    if buf and not buf.endswith("\n"):
        buf += "\n"
    return buf + line + "\n"


def _source_tracking_follows(lines: list[str], line_idx: int) -> bool:
    remaining = lines[line_idx + 1 : line_idx + 5]
    return any("## Source Tracking" in ln for ln in remaining)


def _section_header_mode(stripped: str) -> str | None:
    if stripped == "## Why":
        return "why"
    if stripped == "## What Changes":
        return "what"
    if stripped == "## Impact":
        return "impact"
    if stripped == "## Source Tracking":
        return "source"
    return None


@require(lambda proposal_content: isinstance(proposal_content, str))
@ensure(lambda result: isinstance(result, tuple) and len(result) == 4 and all(isinstance(x, str) for x in result))
@beartype
def bridge_sync_parse_openspec_proposal_markdown(proposal_content: str) -> tuple[str, str, str, str]:
    """Parse title, rationale, description, and impact from proposal.md body."""
    title = ""
    description = ""
    rationale = ""
    impact = ""

    lines = proposal_content.split("\n")
    mode = "none"

    for line_idx, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped.startswith("# Change:"):
            title = line_stripped.replace("# Change:", "").strip()
            continue

        hdr = _section_header_mode(line_stripped)
        if hdr is not None:
            mode = hdr
            continue

        if mode == "source":
            continue

        if line_stripped == "---" and _source_tracking_follows(lines, line_idx):
            mode = "source"
            continue

        if mode == "why":
            rationale = _append_block(rationale, line)
        elif mode == "what":
            description = _append_block(description, line)
        elif mode == "impact":
            impact = _append_block(impact, line)

    return title, rationale, description, impact
