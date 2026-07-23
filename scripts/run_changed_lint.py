#!/usr/bin/env python3
"""Run the local lint stack against the provided changed Python files only."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _normalize_targets(argv: list[str]) -> list[str]:
    targets: list[str] = []
    seen: set[str] = set()
    for raw in argv:
        if not raw:
            continue
        path = Path(raw)
        path = (REPO_ROOT / path).resolve() if not path.is_absolute() else path.resolve()
        try:
            relative = path.relative_to(REPO_ROOT)
        except ValueError:
            continue
        if not path.exists() or path.suffix not in {".py", ".pyi"}:
            continue
        rel_text = str(relative)
        if rel_text in seen:
            continue
        seen.add(rel_text)
        targets.append(rel_text)
    return targets


def _run(cmd: list[str]) -> int:
    completed = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    return int(completed.returncode)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    targets = _normalize_targets(args)
    if not targets:
        print("No changed Python files to lint.")
        return 0

    commands: list[list[str]] = [
        ["ruff", "format", "--check", *targets],
        [
            "bash",
            "tools/run_basedpyright.sh",
            "--project",
            "pyproject.toml",
            "--level",
            "error",
            "--pythonpath",
            sys.executable,
            *targets,
        ],
        ["ruff", "check", *targets],
    ]
    commands.append(["python", "scripts/verify_safe_project_writes.py"])

    for cmd in commands:
        exit_code = _run(cmd)
        if exit_code != 0:
            return exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
