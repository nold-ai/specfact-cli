"""Run the released Requirements evidence command from a verified local fixture."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from beartype import beartype
from icontract import ensure


APPROVED_REPOSITORY = "nold-ai/specfact-cli-modules"
APPROVED_COMMIT = "2438372f8e34c96d4e474afa4c66c92a9cee7979"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
CommandRunner = Callable[[list[str], dict[str, str]], int]
GitRunner = Callable[[list[str]], str]


@dataclass(frozen=True)
class EvidenceRequest:
    """Immutable inputs delegated to the released public evidence command."""

    repo_root: Path
    selection: tuple[str, str | None]
    output_path: Path
    summary_path: Path
    required_maturity: str = "planned"


def _read_fixture_lock(repo_root: Path) -> dict[str, object]:
    """Load the checked-in immutable module fixture declaration."""
    lock_path = repo_root / "ci" / "module-fixture.lock.json"
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read module fixture lock: {lock_path}") from error
    if not isinstance(payload, dict):
        raise ValueError("Module fixture lock must contain a JSON object")
    return payload


def _git_head(arguments: list[str]) -> str:
    """Resolve a fixture checkout's immutable Git revision."""
    return subprocess.run(arguments, check=True, capture_output=True, text=True).stdout.strip()


def _reset_report_paths(request: EvidenceRequest) -> None:
    """Remove prior evidence so each invocation owns its resulting reports."""
    for report_path in (request.output_path, request.summary_path):
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.unlink(missing_ok=True)


def _write_failure_reports(request: EvidenceRequest, message: str) -> None:
    """Write minimal diagnostics without replacing module-owned reports."""
    try:
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        request.summary_path.parent.mkdir(parents=True, exist_ok=True)
        if not request.output_path.exists():
            request.output_path.write_text(
                json.dumps({"schema_version": 1, "verdict": "failed", "diagnostic": message}) + "\n",
                encoding="utf-8",
            )
        if not request.summary_path.exists():
            request.summary_path.write_text(
                f"## Requirements evidence unavailable\n\n- Diagnostic: {message}\n",
                encoding="utf-8",
            )
    except OSError:
        # Report writes are best-effort and must not mask the primary failure.
        pass


@beartype
@ensure(lambda result: result is None)
def verify_fixture(fixture: Mapping[str, object], fixture_root: Path, *, git_runner: GitRunner = _git_head) -> None:
    """Reject any fixture other than the checked-in released module commit."""
    repository = fixture.get("repository")
    commit = fixture.get("commit")
    if repository != APPROVED_REPOSITORY:
        raise ValueError(f"Module fixture must target {APPROVED_REPOSITORY}")
    if not isinstance(commit, str) or SHA_PATTERN.fullmatch(commit) is None:
        raise ValueError("Module fixture commit must be a full immutable SHA")
    if commit != APPROVED_COMMIT:
        raise ValueError("Module fixture must use approved release commit")
    if not fixture_root.is_dir():
        raise ValueError(f"Pinned module fixture is unavailable: {fixture_root}")
    try:
        actual = git_runner(["git", "-C", str(fixture_root), "rev-parse", "HEAD"])
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(f"Cannot verify pinned module fixture: {fixture_root}") from error
    if actual.strip() != commit:
        raise ValueError("Pinned module fixture HEAD does not match ci/module-fixture.lock.json")
    try:
        dirty = git_runner(["git", "-C", str(fixture_root), "status", "--porcelain", "--untracked-files=all"])
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(f"Cannot verify pinned module fixture: {fixture_root}") from error
    if dirty.strip():
        raise ValueError("Pinned module fixture must be clean")


def _run_command(arguments: list[str], environment: dict[str, str]) -> int:
    """Execute the module-owned public command without interpreting its verdict."""
    return subprocess.run(arguments, env=environment, check=False).returncode


@beartype
@ensure(lambda result: isinstance(result, int))
def run_evidence_command(
    request: EvidenceRequest, fixture_root: Path, *, command_runner: CommandRunner = _run_command
) -> int:
    """Delegate evidence semantics to the fixture's public command unchanged."""
    selection_flag, selection_value = request.selection
    arguments = [
        "hatch",
        "run",
        "specfact",
        "requirements",
        "evidence",
        "--repo-root",
        str(request.repo_root.resolve()),
        "--output",
        str(request.output_path),
        "--summary",
        str(request.summary_path),
        "--required-maturity",
        request.required_maturity,
        selection_flag,
    ]
    if selection_value is not None:
        arguments.append(selection_value)
    environment = dict(os.environ)
    environment["SPECFACT_MODULES_REPO"] = str(fixture_root.resolve())
    environment["SPECFACT_MODULES_ROOTS"] = str((fixture_root / "packages").resolve())
    environment.pop("SPECFACT_CLI_MODULES_REPO", None)
    try:
        exit_code = command_runner(arguments, environment)
    except (OSError, subprocess.SubprocessError) as error:
        _write_failure_reports(request, f"Released evidence command could not start: {error}")
        return 1
    if exit_code != 0:
        _write_failure_reports(request, f"Released evidence command exited with status {exit_code}.")
    return exit_code


def _fixture_root_from_environment(arguments: argparse.Namespace) -> Path:
    configured = arguments.fixture_root or os.environ.get("SPECFACT_MODULES_REPO", "")
    if not configured:
        raise ValueError(
            "Pinned module fixture is unavailable. Set SPECFACT_MODULES_REPO to a checkout at the locked commit."
        )
    return Path(configured).expanduser().resolve()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--base-ref", help="Git ref used for pull-request diff selection.")
    selection.add_argument("--staged", action="store_true", help="Evaluate the current Git index snapshot.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root to inspect.")
    parser.add_argument("--fixture-root", help="Verified local checkout of the pinned modules fixture.")
    parser.add_argument("--output", type=Path, required=True, help="Destination JSON evidence report.")
    parser.add_argument("--summary", type=Path, required=True, help="Destination Markdown evidence report.")
    return parser


def _selection(arguments: argparse.Namespace) -> tuple[str, str | None]:
    return ("--base-ref", arguments.base_ref) if arguments.base_ref else ("--staged", None)


@beartype
@ensure(lambda result: result in {0, 1, 2})
def main(argv: Sequence[str] | None = None) -> int:
    """Verify the fixture, then return the released command's exact exit code."""
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    request = EvidenceRequest(
        repo_root=arguments.repo_root.resolve(),
        selection=_selection(arguments),
        output_path=arguments.output,
        summary_path=arguments.summary,
    )
    try:
        _reset_report_paths(request)
        fixture_root = _fixture_root_from_environment(arguments)
        verify_fixture(_read_fixture_lock(request.repo_root), fixture_root)
        return run_evidence_command(request, fixture_root)
    except (OSError, ValueError) as error:
        _write_failure_reports(request, str(error))
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
