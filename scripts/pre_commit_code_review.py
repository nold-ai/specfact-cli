"""Run specfact code review as a staged-file pre-commit gate.

Writes a machine-readable JSON report to ``.specfact/code-review.json`` (gitignored)
so IDEs and Copilot can read findings. Exit code is ``0`` when there are no
severity=error findings (warning-only score ``FAIL`` from the nested CLI does not block).

CrossHair: skip (importlib/subprocess side effects; not amenable to full symbolic execution)
"""

# This helper shells out to the CLI and is intentionally side-effecting.

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from subprocess import TimeoutExpired

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


PYTHON_SUFFIXES = {".py", ".pyi"}

# Default matches dogfood / OpenSpec: machine-readable report under ignored ``.specfact/``.
REVIEW_JSON_OUT = ".specfact/code-review.json"


class ReviewFinding(BaseModel):
    """Minimal validated review finding for summary rendering."""

    model_config = ConfigDict(extra="ignore")

    severity: str = Field(default="other")

    @field_validator("severity", mode="before")
    @classmethod
    def _normalize_severity(cls, value: object) -> str:
        if not isinstance(value, str):
            return "other"
        key = value.lower().strip()
        if key in ("error", "err"):
            return "error"
        if key in ("warning", "warn"):
            return "warning"
        if key in ("advisory", "advise"):
            return "advisory"
        if key == "info":
            return "info"
        return "other"


class CodeReviewReport(BaseModel):
    """Minimal validated review report for summary rendering."""

    model_config = ConfigDict(extra="ignore")

    findings: list[ReviewFinding]
    overall_verdict: str | None = None


CodeReviewReport.model_rebuild()


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


@beartype
def discover_specfact_modules_repo() -> Path | None:
    """Return a sibling ``specfact-cli-modules`` checkout if present (local dev / worktrees).

    CI sets ``SPECFACT_MODULES_REPO`` explicitly. For local commits, walking upward from
    the repository root finds ``../specfact-cli-modules`` layouts used beside this repo.

    This path is only used so the nested ``code review`` process can prepend bundle ``src``
    trees to ``sys.path`` (see ``specfact_cli.modules._bundle_import``). It does **not**
    install, upgrade, or uninstall marketplace modules in the user's install scope.
    """
    root = _repo_root()
    here: Path = root
    for _ in range(12):
        candidate = here / "specfact-cli-modules"
        marker = candidate / "packages" / "specfact-codebase"
        if candidate.is_dir() and marker.is_dir():
            return candidate.resolve()
        if here == here.parent:
            break
        here = here.parent
    return None


@beartype
def build_review_subprocess_env() -> dict[str, str]:
    """Build ``env`` for the nested ``code review`` subprocess only.

    Copies the current process environment and, when ``SPECFACT_MODULES_REPO`` is unset,
    may add it from a discovered sibling checkout so bundle commands can load local
    sources. The parent process environment is **not** mutated, so user-scoped module
    installs and shell exports are left unchanged.
    """
    env: dict[str, str] = dict(os.environ)
    if env.get("SPECFACT_MODULES_REPO", "").strip():
        return env
    discovered = discover_specfact_modules_repo()
    if discovered is not None:
        env["SPECFACT_MODULES_REPO"] = str(discovered)
    return env


def _report_path(repo_root: Path) -> Path:
    """Absolute path to the machine-readable review report."""
    return repo_root / REVIEW_JSON_OUT


def _count_findings_by_severity(findings: list[ReviewFinding]) -> dict[str, int]:
    """Bucket validated review findings by normalized severity."""
    buckets = {"error": 0, "warning": 0, "advisory": 0, "info": 0, "other": 0}
    for finding in findings:
        buckets[finding.severity] += 1
    return buckets


def _load_review_report(report_path: Path) -> CodeReviewReport | None:
    """Load and validate the review JSON report."""
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"Code review: could not read {REVIEW_JSON_OUT}: {exc}\n")
        return None
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Code review: invalid JSON in {REVIEW_JSON_OUT}: {exc}\n")
        return None

    if not isinstance(data, dict):
        sys.stderr.write(
            f"Code review: expected a JSON object at top level in {REVIEW_JSON_OUT} (got {type(data).__name__}).\n",
        )
        return None

    try:
        return CodeReviewReport.model_validate(data)
    except ValidationError as exc:
        sys.stderr.write(f"Code review: invalid review report in {REVIEW_JSON_OUT}: {exc}\n")
        return None


def _print_review_findings_summary(repo_root: Path) -> bool:
    """Parse ``REVIEW_JSON_OUT`` and print a one-line findings count (errors / warnings / etc.)."""
    report_path = _report_path(repo_root)
    if not report_path.is_file():
        sys.stderr.write(f"Code review: no report file at {REVIEW_JSON_OUT} (could not print findings summary).\n")
        return False
    report = _load_review_report(report_path)
    if report is None:
        return False

    counts = _count_findings_by_severity(report.findings)
    total = len(report.findings)
    verdict = report.overall_verdict or "?"
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
        f"  Read `{REVIEW_JSON_OUT}` for details; this hook blocks only on severity=error (warnings are advisory).\n"
    )
    sys.stderr.write(f"  @workspace Open `{REVIEW_JSON_OUT}` and remediate each item in `findings`.\n")
    return True


@beartype
@ensure(lambda result: isinstance(result, tuple) and len(result) == 2)
@ensure(lambda result: isinstance(result[0], bool) and (result[1] is None or isinstance(result[1], str)))
def ensure_runtime_available() -> tuple[bool, str | None]:
    """Verify the current Python environment can import SpecFact CLI."""
    try:
        importlib.import_module("specfact_cli.cli")
    except ModuleNotFoundError as exc:
        if exc.name in ("specfact_cli", "specfact_cli.cli"):
            return False, 'Install dev dependencies with `pip install -e ".[dev]"` or run `hatch env create`.'
        raise
    return True, None


def _prepare_report_path(repo_root: Path) -> Path:
    """Create the review-report directory and clear any stale report file."""
    report_path = _report_path(repo_root)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if report_path.is_file():
        report_path.unlink()
    return report_path


def _run_review_subprocess(
    cmd: Sequence[str],
    repo_root: Path,
    files: Sequence[str],
    env: dict[str, str],
) -> subprocess.CompletedProcess[str] | None:
    """Run the nested SpecFact review command and handle timeout reporting."""
    try:
        return subprocess.run(
            list(cmd),
            check=False,
            text=True,
            capture_output=True,
            cwd=str(repo_root),
            env=env,
            timeout=300,
        )
    except TimeoutExpired:
        joined_cmd = " ".join(cmd)
        sys.stderr.write(f"Code review gate timed out after 300s (command: {joined_cmd!r}, files: {list(files)!r}).\n")
        return None


def _emit_completed_output(result: subprocess.CompletedProcess[str]) -> None:
    """Forward captured subprocess output to stderr when the JSON report is missing."""
    if result.stdout:
        sys.stderr.write(result.stdout if result.stdout.endswith("\n") else result.stdout + "\n")
    if result.stderr:
        sys.stderr.write(result.stderr if result.stderr.endswith("\n") else result.stderr + "\n")


def _missing_report_exit_code(
    report_path: Path,
    result: subprocess.CompletedProcess[str],
) -> int:
    """Return the gate exit code when the nested review run failed to create its JSON report."""
    _emit_completed_output(result)
    sys.stderr.write(
        f"Code review: expected review report at {report_path.relative_to(_repo_root())} but it was not created.\n"
    )
    return result.returncode if result.returncode != 0 else 1


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

    review_env = build_review_subprocess_env()

    repo_root = _repo_root()
    cmd = build_review_command(files)
    report_path = _prepare_report_path(repo_root)
    result = _run_review_subprocess(cmd, repo_root, files, review_env)
    if result is None:
        return 1
    if not report_path.is_file():
        return _missing_report_exit_code(report_path, result)
    # Do not echo nested `specfact code review run` stdout/stderr (verbose tool banners); full report
    # is in REVIEW_JSON_OUT; we print a short summary on stderr below.
    if not _print_review_findings_summary(repo_root):
        return 1
    report = _load_review_report(report_path)
    if report is None:
        return 1
    counts = _count_findings_by_severity(report.findings)
    # Many warning-only findings across a large staged set can drive score below the PASS threshold
    # while the report summary still states "0 blocking". Pre-commit blocks commits only on
    # severity=error findings; advisory cleanup stays in `.specfact/code-review.json`.
    if counts["error"] == 0:
        return 0
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
