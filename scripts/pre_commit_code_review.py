"""Run specfact code review as a staged-file pre-commit gate.

Writes a machine-readable JSON report to ``.specfact/code-review.json`` (gitignored)
so IDEs and Copilot can read findings; exit code still reflects the governed CI verdict.
"""

# CrossHair: ignore
# This helper shells out to the CLI and is intentionally side-effecting.

from __future__ import annotations

import importlib
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from subprocess import TimeoutExpired

from icontract import ensure, require


PYTHON_SUFFIXES = {".py", ".pyi"}

# Default matches dogfood / OpenSpec: machine-readable report under ignored ``.specfact/``.
REVIEW_JSON_OUT = ".specfact/code-review.json"


@require(lambda paths: paths is not None)
@ensure(lambda result: len(result) == len(set(result)))
@ensure(lambda result: all(Path(path).suffix.lower() in PYTHON_SUFFIXES for path in result))
def filter_review_files(paths: Sequence[str]) -> list[str]:
    """Return only staged Python source files relevant to code review."""
    seen: set[str] = set()
    filtered: list[str] = []
    for path in paths:
        if Path(path).suffix.lower() not in PYTHON_SUFFIXES:
            continue
        if path in seen:
            continue
        seen.add(path)
        filtered.append(path)
    return filtered


@require(lambda files: files is not None)
@ensure(lambda result: result[:5] == [sys.executable, "-m", "specfact_cli.cli", "code", "review"])
@ensure(lambda result: "--json" in result and "--out" in result)
@ensure(lambda result: REVIEW_JSON_OUT in result)
def build_review_command(files: Sequence[str]) -> list[str]:
    """Build ``code review run --json --out …`` so findings are written for tooling."""
    return [
        sys.executable,
        "-m",
        "specfact_cli.cli",
        "code",
        "review",
        "run",
        "--json",
        "--out",
        REVIEW_JSON_OUT,
        *files,
    ]


def _repo_root() -> Path:
    """Repository root (parent of ``scripts/``)."""
    return Path(__file__).resolve().parents[1]


def ensure_runtime_available() -> tuple[bool, str | None]:
    """Verify the current Python environment can import SpecFact CLI."""
    try:
        importlib.import_module("specfact_cli.cli")
    except ModuleNotFoundError:
        return False, 'Install dev dependencies with `pip install -e ".[dev]"` or run `hatch env create`.'
    return True, None


@ensure(lambda result: isinstance(result, int))
def main(argv: Sequence[str] | None = None) -> int:
    """Run the code review gate; write JSON under ``.specfact/`` and return CLI exit code."""
    files = filter_review_files(list(argv or []))
    if not files:
        sys.stdout.write("No staged Python files to review; skipping code review gate.\n")
        return 0

    available, guidance = ensure_runtime_available()
    if not available:
        sys.stdout.write(f"Unable to run the code review gate. {guidance}\n")
        return 1

    cmd = build_review_command(files)
    try:
        result = subprocess.run(
            cmd,
            check=False,
            text=True,
            capture_output=True,
            cwd=str(_repo_root()),
            timeout=300,
        )
    except TimeoutExpired:
        joined_cmd = " ".join(cmd)
        sys.stderr.write(f"Code review gate timed out after 300s (command: {joined_cmd!r}, files: {files!r}).\n")
        return 1
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
