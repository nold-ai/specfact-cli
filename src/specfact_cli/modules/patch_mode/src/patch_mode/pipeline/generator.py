"""Generate unified diffs for backlog body, OpenSpec, config updates."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda content: isinstance(content, str), "Content must be string")
@require(lambda description: description is None or isinstance(description, str), "Description must be None or string")
@ensure(lambda result: isinstance(result, str), "Result must be string")
def generate_unified_diff(
    content: str,
    target_path: Path | None = None,
    description: str | None = None,
) -> str:
    """Produce a unified diff string from content (generate-only; no apply/write)."""
    if target_path is None:
        target_path = Path("/dev/null")
    header = f"--- {target_path}\n+++ {target_path}\n"
    if description:
        header = f"# {description}\n" + header
    lines = content.splitlines(keepends=True)
    if not lines and content:
        lines = [content]
    hunk = "".join(f"+{line}" if not line.startswith("+") else line for line in lines)
    return header + hunk
