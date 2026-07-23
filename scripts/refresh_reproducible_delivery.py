#!/usr/bin/env python3
"""Refresh the committed frozen dependency inputs after reviewed metadata changes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from beartype import beartype
from icontract import ensure


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCKED_EXPORT = REPO_ROOT / "requirements" / "ci" / "locked.txt"


@beartype
@ensure(lambda result: result is None, "must return None")
def run(command: list[str]) -> None:
    """Run one checked-in refresh command from the repository root."""
    subprocess.run(command, cwd=REPO_ROOT, check=True)


@beartype
@ensure(lambda result: result in {0, 1}, "must return a shell-compatible status")
def main() -> int:
    """Regenerate the lock and hash-protected CI export, then verify both."""
    LOCKED_EXPORT.parent.mkdir(parents=True, exist_ok=True)
    try:
        run(["uv", "lock"])
        run(
            [
                "uv",
                "export",
                "--locked",
                "--all-extras",
                "--no-emit-project",
                "--format",
                "requirements-txt",
                "--no-annotate",
                "--output-file",
                "requirements/ci/locked.txt",
            ]
        )
        run([sys.executable, "scripts/check_reproducible_delivery.py"])
    except (OSError, subprocess.CalledProcessError) as error:
        sys.stderr.write(f"frozen delivery refresh failed: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
