"""Execute a verified Requirements proof plan without shell interpretation."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol, cast, runtime_checkable

from beartype import beartype
from icontract import ensure


MAX_SELECTORS = 100
SELECTOR_PATTERN = re.compile(r"(?!-)[A-Za-z0-9_./-]+\.py::[^\r\n\x00]+")
FORBIDDEN_SELECTOR_CHARACTERS = frozenset('\r\n\x00$&;|`<>*?(){}!\\"')
PROOF_ENVIRONMENT_KEYS = frozenset(
    {
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PATH",
        "SPECFACT_MODULES_REPO",
        "SPECFACT_MODULES_ROOTS",
        "TMPDIR",
        "VIRTUAL_ENV",
    }
)


@runtime_checkable
class CommandRunner(Protocol):
    """Typed subprocess seam for unit testing the no-shell invocation."""

    def __call__(self, request: ProofCommand) -> int: ...


@dataclass(frozen=True)
class ProofCommand:
    """Core-owned process inputs for one bounded pytest proof invocation."""

    arguments: list[str]
    cwd: Path
    env: dict[str, str]
    shell: bool
    timeout: int


def _validate_plan_state(plan: Mapping[str, object]) -> None:
    """Accept only the released plan report state that authorizes execution."""
    if (
        plan.get("schema_version") != "2"
        or plan.get("gate_decision") != "pass"
        or plan.get("observed_maturity") != "test-authored"
    ):
        raise ValueError("invalid proof plan state")


def _plan_cases(plan: Mapping[str, object]) -> list[Mapping[str, object]]:
    nested_plan = plan.get("plan")
    if not isinstance(nested_plan, Mapping):
        raise ValueError("proof plan must contain a plan object")
    nested_plan = cast(Mapping[str, object], nested_plan)
    cases = nested_plan.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("proof plan must contain nonempty cases")
    if any(not isinstance(case, Mapping) for case in cases):
        raise ValueError("proof plan contains an invalid case")
    return [cast(Mapping[str, object], case) for case in cases if isinstance(case, Mapping)]


def _contains_control_character(value: str) -> bool:
    """Reject terminal and other ASCII controls before invoking pytest."""
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _is_unsafe_node_id(node_id: str) -> bool:
    """Keep paths relative and reject options, controls, and shell metacharacters."""
    test_path, _, _ = node_id.partition("::")
    relative_path = PurePosixPath(test_path)
    return (
        relative_path.is_absolute()
        or ".." in relative_path.parts
        or node_id.startswith("-")
        or _contains_control_character(node_id)
        or any(character in node_id for character in FORBIDDEN_SELECTOR_CHARACTERS)
    )


def _validate_selector(selector: object, repo_root: Path) -> str:
    if not isinstance(selector, Mapping):
        raise ValueError("proof plan contains an invalid pytest selector")
    selector = cast(Mapping[str, object], selector)
    if selector.get("runner") != "pytest":
        raise ValueError("proof plan contains an unsupported runner")
    node_id = selector.get("node_id")
    if not isinstance(node_id, str) or not SELECTOR_PATTERN.fullmatch(node_id):
        raise ValueError("proof plan contains an invalid pytest selector")
    test_path, _, _ = node_id.partition("::")
    relative_path = PurePosixPath(test_path)
    if _is_unsafe_node_id(node_id):
        raise ValueError("proof plan contains an invalid pytest selector")
    resolved_path = (repo_root / relative_path).resolve()
    if not resolved_path.is_relative_to(repo_root.resolve()) or not resolved_path.is_file():
        raise ValueError("proof plan selector must name an existing repository test file")
    return node_id


@beartype
@ensure(lambda result: result and len(result) <= MAX_SELECTORS)
def selectors_from_plan(plan: dict[str, object], repo_root: Path) -> list[str]:
    """Return unique, repository-contained exact pytest selectors from a module plan."""
    _validate_plan_state(plan)
    selectors: list[str] = []
    for case in _plan_cases(plan):
        if case.get("method") != "test":
            continue
        selector = case.get("selector")
        if selector is None:
            raise ValueError("proof plan test case is missing a selector")
        selectors.append(_validate_selector(selector, repo_root))
    if not selectors:
        raise ValueError("proof plan contains no executable test selectors")
    if len(selectors) > MAX_SELECTORS:
        raise ValueError(f"proof plan exceeds the {MAX_SELECTORS} selector limit")
    if len(set(selectors)) != len(selectors):
        raise ValueError("proof plan contains a duplicate pytest selector")
    return selectors


def _run_command(request: ProofCommand) -> int:
    return subprocess.run(
        request.arguments,
        check=False,
        cwd=request.cwd,
        env=request.env,
        shell=request.shell,
        timeout=request.timeout,
    ).returncode


@beartype
@ensure(lambda result: isinstance(result, int))
def execute_plan(
    plan: dict[str, object], repo_root: Path, junit_path: Path, *, command_runner: CommandRunner = _run_command
) -> int:
    """Run exact selectors with a deterministic JUnit destination and no shell."""
    selectors = selectors_from_plan(plan, repo_root)
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    junit_path.unlink(missing_ok=True)
    arguments = [
        sys.executable,
        "-m",
        "pytest",
        "--junitxml",
        str(junit_path),
        "-p",
        "scripts.requirements_proof_pytest_plugin",
        "--",
        *selectors,
    ]
    environment = {key: value for key, value in os.environ.items() if key in PROOF_ENVIRONMENT_KEYS}
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return command_runner(ProofCommand(arguments, repo_root, environment, shell=False, timeout=600))


def _read_plan(plan_path: Path) -> dict[str, object]:
    try:
        payload = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read proof plan: {plan_path}") from error
    if not isinstance(payload, dict):
        raise ValueError("proof plan must contain a JSON object")
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True, help="Module-produced lifecycle plan report.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository containing selected tests.")
    parser.add_argument("--junit", type=Path, required=True, help="Fresh JUnit XML destination.")
    return parser


@beartype
@ensure(lambda result: isinstance(result, int))
def main(argv: Sequence[str] | None = None) -> int:
    """Validate the structured plan and return the selected pytest exit code."""
    arguments = _build_parser().parse_args(argv)
    try:
        return execute_plan(
            _read_plan(arguments.plan),
            arguments.repo_root.resolve(),
            arguments.junit.resolve(),
            command_runner=_run_command,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f"Requirements proof execution rejected: {error}") from error


if __name__ == "__main__":
    raise SystemExit(main())
