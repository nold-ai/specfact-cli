#!/usr/bin/env python3
"""Verify frozen CI delivery inputs without mutating the worktree."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

from beartype import beartype
from icontract import ensure


REPO_ROOT = Path(__file__).resolve().parents[1]
UV_LOCK = REPO_ROOT / "uv.lock"
MODULE_FIXTURE_LOCK = REPO_ROOT / "ci" / "module-fixture.lock.json"
LOCKED_EXPORT = REPO_ROOT / "requirements" / "ci" / "locked.txt"
CODE_REVIEW_REQUIREMENTS_INPUT = REPO_ROOT / "requirements" / "code-review" / "requirements.in"
CODE_REVIEW_LOCKED_EXPORT = REPO_ROOT / "requirements" / "code-review" / "locked.txt"
COMMIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
UV_COMMAND_TIMEOUT_SECONDS = 120


class ModuleFixtureLock(TypedDict):
    """Validated schema for the reviewed companion-module fixture."""

    repository: str
    commit: str


@beartype
@ensure(lambda result: result is None, "must return None")  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
def verify_module_fixture() -> None:
    """Ensure blocking companion-module validation uses an immutable commit."""
    if not MODULE_FIXTURE_LOCK.is_file():
        raise ValueError(f"Missing module fixture lock: {MODULE_FIXTURE_LOCK}")
    fixture_payload = json.loads(MODULE_FIXTURE_LOCK.read_text(encoding="utf-8"))
    if not isinstance(fixture_payload, dict):
        raise ValueError("Module fixture lock must contain a JSON object")
    fixture = cast(dict[str, object], fixture_payload)
    repository = fixture.get("repository")
    commit = fixture.get("commit")
    if not isinstance(repository, str) or repository != "nold-ai/specfact-cli-modules":
        raise ValueError("Module fixture lock must target nold-ai/specfact-cli-modules")
    if not isinstance(commit, str) or COMMIT_SHA_PATTERN.fullmatch(commit) is None:
        raise ValueError("Module fixture lock commit must be a full immutable SHA")
    validated: ModuleFixtureLock = {"repository": repository, "commit": commit}
    if not validated["commit"]:
        raise ValueError("Module fixture lock commit must not be empty")


@beartype
@ensure(lambda result: result is None, "must return None")  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
def verify_uv_lock() -> None:
    """Ask uv to verify that the lock still matches project metadata."""
    if not UV_LOCK.is_file():
        raise ValueError(f"Missing committed lock: {UV_LOCK}")
    completed = subprocess.run(
        ["uv", "lock", "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=UV_COMMAND_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ValueError(f"uv.lock is stale: {detail}")


@beartype
@ensure(lambda result: result is None, "must return None")  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
def verify_locked_export() -> None:
    """Ensure the pip-compatible CI export is committed and hash-protected."""
    if not LOCKED_EXPORT.is_file():
        raise ValueError(f"Missing locked CI export: {LOCKED_EXPORT}")
    contents = LOCKED_EXPORT.read_text(encoding="utf-8")
    if "--hash=sha256:" not in contents:
        raise ValueError("Locked CI export must contain distribution hashes")
    if "-e " in contents or "--editable" in contents:
        raise ValueError("Locked CI export must not contain editable requirements")
    completed = subprocess.run(
        [
            "uv",
            "export",
            "--locked",
            "--all-extras",
            "--no-emit-project",
            "--format",
            "requirements-txt",
            "--no-annotate",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=UV_COMMAND_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ValueError(f"Could not render locked CI export: {detail}")
    rendered = _without_generated_header(completed.stdout)
    committed = _without_generated_header(contents)
    if rendered != committed:
        raise ValueError("Locked CI export differs from uv.lock; run refresh-frozen-delivery")


@beartype
@ensure(lambda result: result is None, "must return None")  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
def verify_code_review_lock() -> None:
    """Ensure the isolated Code Review lock is the current compiled input."""
    if not CODE_REVIEW_REQUIREMENTS_INPUT.is_file():
        raise ValueError(f"Missing Code Review requirements input: {CODE_REVIEW_REQUIREMENTS_INPUT}")
    if not CODE_REVIEW_LOCKED_EXPORT.is_file():
        raise ValueError(f"Missing Code Review lock: {CODE_REVIEW_LOCKED_EXPORT}")
    contents = CODE_REVIEW_LOCKED_EXPORT.read_text(encoding="utf-8")
    if "--hash=sha256:" not in contents:
        raise ValueError("Code Review lock must contain distribution hashes")
    completed = subprocess.run(
        [
            "uv",
            "pip",
            "compile",
            str(CODE_REVIEW_REQUIREMENTS_INPUT.relative_to(REPO_ROOT)),
            "--python-version",
            "3.12",
            "--generate-hashes",
            "--no-annotate",
            "--output-file",
            "-",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=UV_COMMAND_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ValueError(f"Could not compile Code Review requirements: {detail}")
    if _without_generated_header(completed.stdout) != _without_generated_header(contents):
        raise ValueError("Code Review lock differs from requirements.in; regenerate the isolated lock")


@beartype
def _without_generated_header(contents: str) -> str:
    """Strip uv's descriptive header before comparing generated requirement bodies."""
    return "\n".join(line for line in contents.splitlines() if not line.startswith("#")).strip()


@beartype
@ensure(lambda result: result in {0, 1}, "must return a shell-compatible status")  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
def main(argv: list[str] | None = None) -> int:
    """Run frozen-delivery verification and return a shell-compatible status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        verify_uv_lock()
        verify_locked_export()
        verify_code_review_lock()
        verify_module_fixture()
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        sys.stderr.write(f"reproducible delivery check failed: {error}\n")
        return 1
    sys.stdout.write("reproducible delivery inputs are valid\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
