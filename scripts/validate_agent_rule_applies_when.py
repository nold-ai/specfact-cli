#!/usr/bin/env python3
"""Validate docs/agent-rules/*.md frontmatter applies_when against canonical task signals."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


# Keep in sync with docs/agent-rules/INDEX.md — Task signal definitions.
CANONICAL_TASK_SIGNALS: frozenset[str] = frozenset(
    {
        "session-bootstrap",
        "implementation",
        "openspec-change-selection",
        "branch-management",
        "github-public-work",
        "change-readiness",
        "finalization",
        "release",
        "documentation-update",
        "repository-orientation",
        "command-lookup",
        "detailed-reference",
        "verification",
    }
)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL | re.MULTILINE)


def _parse_frontmatter(text: str) -> dict[str, object] | None:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None
    try:
        loaded = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return loaded if isinstance(loaded, dict) else None


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    rules_dir = root / "docs" / "agent-rules"
    if not rules_dir.is_dir():
        sys.stderr.write("validate_agent_rule_applies_when: docs/agent-rules not found\n")
        return 2

    errors: list[str] = []
    for path in sorted(rules_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        data = _parse_frontmatter(text)
        if data is None:
            continue
        raw = data.get("applies_when")
        if raw is None:
            continue
        if isinstance(raw, str):
            signals = [raw]
        elif isinstance(raw, list):
            signals = [str(x) for x in raw if x is not None]
        else:
            errors.append(f"{path.name}: applies_when must be a list or string")
            continue
        for sig in signals:
            if sig not in CANONICAL_TASK_SIGNALS:
                errors.append(
                    f"{path.name}: unknown applies_when value {sig!r} "
                    f"(not in canonical set; update INDEX.md or fix frontmatter)"
                )

    if errors:
        sys.stderr.write(
            "validate_agent_rule_applies_when: invalid applies_when values "
            "(see docs/agent-rules/INDEX.md — Task signal definitions):\n"
        )
        for line in errors:
            sys.stderr.write(f"  {line}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
