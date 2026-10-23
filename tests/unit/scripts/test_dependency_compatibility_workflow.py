from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
SECURITY_TESTS = "tests/unit/security/"
FROZEN_RELEASE_SELECTORS = (
    SECURITY_TESTS + "test_release_dependency_selection.py::test_reviewed_tooling_versions_match_frozen_export",
    SECURITY_TESTS
    + "test_release_promotion_security_gates.py::test_frozen_graph_uses_official_semgrep_with_bounded_mcp_exception",
    SECURITY_TESTS + "test_frozen_dependency_artifacts.py::test_frozen_certifi_bundle_excludes_compromised_root",
    SECURITY_TESTS + "test_frozen_dependency_artifacts.py::test_artifact_download_rejects_wrong_sha256",
    SECURITY_TESTS + "test_frozen_jwt_compatibility.py::test_inspection_preserves_options_and_expiry_on_reuse",
    SECURITY_TESTS
    + "test_frozen_gitpython_compatibility.py::test_submodule_update_rejects_outside_checkout_before_clone",
    SECURITY_TESTS + "test_frozen_gitpython_compatibility.py::test_submodule_creation_validates_checkout_before_clone",
)


def _workflow_jobs() -> dict[str, dict[str, Any]]:
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/pr-orchestrator.yml").read_text(encoding="utf-8"))
    return cast(dict[str, dict[str, Any]], workflow["jobs"])


def _resolver_command() -> str:
    steps = cast(list[dict[str, Any]], _workflow_jobs()["dependency-compatibility"]["steps"])
    return str(
        next(step["run"] for step in steps if step.get("name") == "Exercise latest and lower-bound resolver lanes")
    )


def test_resolver_filters_are_shared_by_both_advisory_lanes() -> None:
    job = _workflow_jobs()["dependency-compatibility"]
    assert job["if"] == "github.event_name == 'schedule'"
    assert job["continue-on-error"] is True
    commands = [shlex.split(line) for line in _resolver_command().splitlines()]
    pytest_command = ["python", "-m", "pytest", "-q", "${compatibility_deselections[@]}", "tests/unit"]
    resolver_start = commands.index(["uv", "lock", "--upgrade"])
    assert commands[resolver_start:] == [
        ["uv", "lock", "--upgrade"],
        ["uv", "sync", "--locked", "--all-extras"],
        pytest_command,
        ["uv", "lock", "--resolution", "lowest-direct"],
        ["uv", "sync", "--locked", "--all-extras", "--resolution", "lowest-direct"],
        pytest_command,
    ]


def test_frozen_release_filters_do_not_leak_into_blocking_jobs() -> None:
    for name, job in _workflow_jobs().items():
        if name == "dependency-compatibility":
            continue
        source = yaml.safe_dump(job)
        assert "compatibility_deselections" not in source, name
        assert all(f"--deselect={selector}" not in source for selector in FROZEN_RELEASE_SELECTORS), name


def _collect_release_tests(deselections: list[str]) -> set[str]:
    test_files = sorted({selector.split("::")[0] for selector in FROZEN_RELEASE_SELECTORS})
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "--override-ini",
            "addopts=",
            "-q",
            "-p",
            "no:cacheprovider",
            *deselections,
            *test_files,
            "tests/unit/scripts/test_security_audit_gate.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return {line for line in result.stdout.splitlines() if line.startswith("tests/") and "::" in line}


def test_resolver_selection_excludes_only_frozen_release_cases() -> None:
    match = re.search(r"compatibility_deselections=\((.*?)\)", _resolver_command(), re.DOTALL)
    assert match is not None
    deselections = shlex.split(match.group(1))
    assert all(argument.startswith("--deselect=") for argument in deselections)
    baseline = _collect_release_tests([])
    selected = _collect_release_tests(deselections)
    frozen_cases = {node for node in baseline if node.split("[")[0] in FROZEN_RELEASE_SELECTORS}
    assert {node.split("[")[0] for node in frozen_cases} == set(FROZEN_RELEASE_SELECTORS)
    ordinary_cases = baseline - frozen_cases
    assert ordinary_cases
    assert selected == ordinary_cases, (
        f"Frozen cases still selected: {sorted(selected & frozen_cases)}; "
        f"ordinary cases lost: {sorted(ordinary_cases - selected)}"
    )
