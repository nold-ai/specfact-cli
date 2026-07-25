#!/usr/bin/env python3
"""Refresh the committed frozen dependency inputs after reviewed metadata changes."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from beartype import beartype
from icontract import ensure


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCKED_EXPORT = REPO_ROOT / "requirements" / "ci" / "locked.txt"
UV_COMMAND_TIMEOUT_SECONDS = 120


@beartype
@ensure(lambda result: result is None, "must return None")  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
def validate_locked_export_path(output_path: Path, repository_root: Path = REPO_ROOT) -> None:
    """Reject output paths that would traverse a repository-controlled symlink."""
    try:
        relative_path = output_path.relative_to(repository_root)
    except ValueError as error:
        raise OSError(f"locked export path escapes the repository: {output_path}") from error

    parent = repository_root
    for part in relative_path.parts[:-1]:
        parent = parent / part
        if parent.is_symlink():
            raise OSError(f"locked export parent must not be a symlink: {parent}")
        if parent.exists():
            if not parent.is_dir():
                raise OSError(f"locked export parent is not a directory: {parent}")
            continue
        parent.mkdir()
    if output_path.is_symlink():
        raise OSError(f"locked export path must not be a symlink: {output_path}")
    if output_path.exists() and not output_path.is_file():
        raise OSError(f"locked export path is not a regular file: {output_path}")


@beartype
@ensure(lambda result: result is None, "must return None")  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
def run(command: list[str]) -> None:
    """Run one checked-in refresh command from the repository root."""
    subprocess.run(command, cwd=REPO_ROOT, check=True, timeout=UV_COMMAND_TIMEOUT_SECONDS)


@beartype
@ensure(lambda result: result in {0, 1}, "must return a shell-compatible status")  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
def main() -> int:
    """Regenerate the lock and hash-protected CI export, then verify both."""
    temporary_export: Path | None = None
    try:
        validate_locked_export_path(LOCKED_EXPORT)
        descriptor, temporary_export_name = tempfile.mkstemp(
            prefix=".locked-export-",
            suffix=".txt",
            dir=LOCKED_EXPORT.parent,
        )
        os.close(descriptor)
        temporary_export = Path(temporary_export_name)
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
                str(temporary_export.relative_to(REPO_ROOT)),
            ]
        )
        os.replace(temporary_export, LOCKED_EXPORT)
        temporary_export = None
        run([sys.executable, "scripts/check_reproducible_delivery.py"])
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        sys.stderr.write(f"frozen delivery refresh failed: {error}\n")
        return 1
    finally:
        if temporary_export is not None:
            temporary_export.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
