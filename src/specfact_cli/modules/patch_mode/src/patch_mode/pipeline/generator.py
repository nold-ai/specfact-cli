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
        target_path = Path("patch_generated.txt")
    target_str = str(target_path)
    line_count = content.count("\n")
    if content and not content.endswith("\n"):
        line_count += 1
    header = f"--- /dev/null\n+++ b/{target_str}\n"
    if description:
        header = f"# {description}\n" + header
    lines = content.splitlines()
    hunk_header = f"@@ -0,0 +1,{line_count} @@\n"
    hunk_body = "".join(f"+{line}\n" for line in lines)
    return header + hunk_header + hunk_body
