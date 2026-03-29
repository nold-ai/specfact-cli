"""Run specfact code review as a staged-file pre-commit gate.

Writes a machine-readable JSON report to ``.specfact/code-review.json`` (gitignored)
so IDEs and Copilot can read findings; exit code still reflects the governed CI verdict.

CrossHair: skip (importlib/subprocess side effects; not amenable to full symbolic execution)
"""

# This helper shells out to the CLI and is intentionally side-effecting.

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from subprocess import TimeoutExpired
from typing import Any, cast

from beartype import beartype
from icontract import ensure, require


PYTHON_SUFFIXES = {".py", ".pyi"}

# Default matches dogfood / OpenSpec: machine-readable report under ignored ``.specfact/``.
REVIEW_JSON_OUT = ".specfact/code-review.json"


@beartype
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


@beartype
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


def _count_findings_by_severity(findings: list[object]) -> dict[str, int]:
    """Bucket review findings by severity (unknown severities go to ``other``)."""
    buckets = {"error": 0, "warning": 0, "advisory": 0, "info": 0, "other": 0}
    for item in findings:
        if not isinstance(item, dict):
            buckets["other"] += 1
            continue
        row = cast(dict[str, Any], item)
        raw = row.get("severity")
        if not isinstance(raw, str):
            buckets["other"] += 1
            continue
        key = raw.lower().strip()
        if key in ("error", "err"):
            buckets["error"] += 1
        elif key in ("warning", "warn"):
            buckets["warning"] += 1
        elif key in ("advisory", "advise"):
            buckets["advisory"] += 1
        elif key == "info":
            buckets["info"] += 1
        else:
            buckets["other"] += 1
    return buckets


def _print_review_findings_summary(repo_root: Path) -> None:
    """Parse ``REVIEW_JSON_OUT`` and print a one-line findings count (errors / warnings / etc.)."""
    report_path = repo_root / REVIEW_JSON_OUT
    if not report_path.is_file():
        sys.stderr.write(f"Code review: no report file at {REVIEW_JSON_OUT} (could not print findings summary).\n")
        return
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"Code review: could not read {REVIEW_JSON_OUT}: {exc}\n")
        return
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Code review: invalid JSON in {REVIEW_JSON_OUT}: {exc}\n")
        return

    findings_raw = data.get("findings")
    if not isinstance(findings_raw, list):
        sys.stderr.write(f"Code review: report has no findings list in {REVIEW_JSON_OUT}.\n")
        return

    counts = _count_findings_by_severity(findings_raw)
    total = len(findings_raw)
    verdict = data.get("overall_verdict", "?")
    parts = [
        f"errors={counts['error']}",
        f"warnings={counts['warning']}",
        f"advisory={counts['advisory']}",
    ]
    if counts["info"]:
        parts.append(f"info={counts['info']}")
    if counts["other"]:
        parts.append(f"other={counts['other']}")
    summary = ", ".join(parts)
    # stderr keeps the summary separate from nested `specfact code review run` stdout; enable hook
    # `verbose: true` in .pre-commit-config.yaml so pre-commit prints hook output when the hook passes.
    sys.stderr.write(f"Code review summary: {total} finding(s) ({summary}); overall_verdict={verdict!r}.\n")
    abs_report = report_path.resolve()
    sys.stderr.write(f"Code review report file: {REVIEW_JSON_OUT}\n")
    sys.stderr.write(f"  absolute path: {abs_report}\n")
    sys.stderr.write("Copy-paste for Copilot or Cursor:\n")
    sys.stderr.write(
        f"  Read `{REVIEW_JSON_OUT}` and fix every finding (errors first), using file and line from each entry.\n"
    )
    sys.stderr.write(f"  @workspace Open `{REVIEW_JSON_OUT}` and remediate each item in `findings`.\n")


@beartype
@ensure(lambda result: isinstance(result, tuple) and len(result) == 2)
@ensure(lambda result: isinstance(result[0], bool) and (result[1] is None or isinstance(result[1], str)))
def ensure_runtime_available() -> tuple[bool, str | None]:
    """Verify the current Python environment can import SpecFact CLI."""
    try:
        importlib.import_module("specfact_cli.cli")
    except ModuleNotFoundError:
        return False, 'Install dev dependencies with `pip install -e ".[dev]"` or run `hatch env create`.'
    return True, None


@beartype
@require(lambda argv: argv is None or isinstance(argv, (list, tuple)))
@ensure(lambda result: isinstance(result, int))
def main(argv: Sequence[str] | None = None) -> int:
    """Run the code review gate; write JSON under ``.specfact/`` and return CLI exit code."""
    paths_arg = [] if argv is None else list(argv)
    files = filter_review_files(paths_arg)
    try:
        files[0]
    except IndexError:
        sys.stdout.write("No staged Python files to review; skipping code review gate.\n")
        return 0

    available, guidance = ensure_runtime_available()
    if available is False:
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
    # Do not echo nested `specfact code review run` stdout/stderr (verbose tool banners); full report
    # is in REVIEW_JSON_OUT; we print a short summary on stderr below.
    _print_review_findings_summary(_repo_root())
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
