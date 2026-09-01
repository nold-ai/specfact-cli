"""Focused red/green contracts for the #692 security patch."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_script(name: str) -> Any:
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _workflow(path: str) -> dict[str, Any]:
    payload = yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _on_block(workflow: dict[str, Any]) -> dict[str, Any]:
    value = workflow.get("on", cast(dict[object, Any], workflow).get(True))
    assert isinstance(value, dict)
    return cast(dict[str, Any], value)


def _named_step(job: dict[str, Any], name: str) -> dict[str, Any]:
    steps = job.get("steps")
    assert isinstance(steps, list)
    step = next((item for item in steps if isinstance(item, dict) and item.get("name") == name), None)
    assert isinstance(step, dict), name
    return cast(dict[str, Any], step)


def test_shared_frozen_setup_disables_persistent_cache() -> None:
    """The shared setup action removes both uv cache restore and save."""
    action = (REPO_ROOT / ".github" / "actions" / "setup-frozen-python" / "action.yml").read_text(encoding="utf-8")
    assert "enable-cache: false" in action
    assert "enable-cache: true" not in action
    assert "uv sync --locked --all-extras" in action


def test_compatibility_fixture_is_schedule_only_and_verified_before_export() -> None:
    """Branch-selected workflow bytes cannot manually choose and execute a fixture."""
    workflow = _workflow(".github/workflows/pr-orchestrator.yml")
    assert "workflow_dispatch" not in _on_block(workflow)
    job = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["dependency-compatibility"])
    assert job.get("if") == "github.event_name == 'schedule'"
    read = _named_step(job, "Read immutable module fixture")
    verify = _named_step(job, "Verify immutable module fixture")
    steps = cast(list[dict[str, Any]], job["steps"])
    names = [str(step.get("name", "")) for step in steps]
    assert names.index("Verify immutable module fixture") < names.index("Export module bundles path")
    assert '"tree"' in str(read.get("run", ""))
    assert "HEAD^{tree}" in str(verify.get("run", ""))


def test_post_fixture_node_setup_has_no_persistent_npm_cache() -> None:
    """Code Review setup cannot restore or save npm state after fixture execution."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    job = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["requirements-evidence"])
    step = _named_step(job, "Set up reviewed Code Review Node runtime")
    inputs = step.get("with", {})
    assert isinstance(inputs, dict)
    assert "cache" not in inputs
    assert "cache-dependency-path" not in inputs


def test_frozen_graph_uses_fixed_semgrep_mcp_pair_without_waiver() -> None:
    """All authoritative dependency surfaces select the reviewed fixed line."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev = cast(list[str], project["project"]["optional-dependencies"]["dev"])
    scanning = cast(list[str], project["project"]["optional-dependencies"]["scanning"])
    assert "semgrep>=1.175.0" in dev
    assert "semgrep>=1.175.0" in scanning

    locked = (REPO_ROOT / "requirements" / "ci" / "locked.txt").read_text(encoding="utf-8")
    assert "semgrep==1.175.0" in locked
    assert "mcp==1.29.0" in locked
    policy = json.loads((REPO_ROOT / "ci" / "security-tool-minimum-versions.json").read_text(encoding="utf-8"))
    assert policy["minimum_versions"] == {"mcp": "1.28.1", "semgrep": "1.175.0"}
    exceptions = json.loads((REPO_ROOT / "ci" / "vulnerability-audit-exceptions.json").read_text(encoding="utf-8"))
    assert all(record.get("package") != "mcp" for record in exceptions["exceptions"])


def test_code_review_lock_is_bound_before_installation(tmp_path: Path) -> None:
    """A stale Code Review input binding fails the standard-library trust gate."""
    input_path = tmp_path / "requirements.in"
    input_path.write_text("pylint==4.0.7\n", encoding="utf-8")
    lock_path = tmp_path / "locked.txt"
    lock_path.write_text(
        f"# input-sha256: {'0' * 64}\npylint==4.0.7 \\\n    --hash=sha256:{'a' * 64}\n",
        encoding="utf-8",
    )
    checker = _load_script("check_dependency_trust_exceptions")

    errors = checker.validate_frozen_dependency_policy(
        code_review_input_path=input_path,
        code_review_lock_path=lock_path,
    )

    assert "Code Review lock input SHA-256 binding does not match requirements.in" in errors


def test_code_review_only_license_exception_does_not_leak() -> None:
    """Only the named isolated interpreter scope may consume the Pylint exception."""
    checker = _load_script("check_license_compliance")
    package = {"Name": "pylint", "Version": "4.0.7", "License": "GPL-2.0-or-later"}
    allowlist = {
        "pylint": [
            {
                "package": "pylint",
                "version": "4.0.7",
                "license": "GPL-2.0-or-later",
                "reason": "isolated review fixture",
                "scope": "code-review-only",
            }
        ]
    }

    assert checker._evaluate_env_package(package, allowlist) == 1
    assert checker._evaluate_env_package(package, allowlist, allowlist_scope="code-review-only") == 0


def test_archive_selection_checks_exact_moves_and_git_failures() -> None:
    """Archive absence is accepted only after successful exact Git enumeration."""
    pre_commit = (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")
    workflow = (REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml").read_text(encoding="utf-8")
    for source in (pre_commit, workflow):
        assert "--find-renames=100%" in source
        assert "R100" in source
        assert "git ls-tree" in source
    assert "if ! git ls-files --cached" in pre_commit
    assert "if ! git ls-tree HEAD" in pre_commit
    assert "if ! git ls-tree -r -z --name-only" in workflow
    assert 'if ! destination_entry="$(git ls-tree HEAD' in workflow


def test_proof_executor_imports_installed_pytest_before_repository_root(tmp_path: Path) -> None:
    """A candidate root-level pytest.py cannot shadow the installed package."""
    module = _load_script("requirements_proof_executor")
    selected = tmp_path / "tests" / "test_proof.py"
    selected.parent.mkdir()
    selected.write_text("def test_selected() -> None: pass\n", encoding="utf-8")
    (tmp_path / "pytest.py").write_text("raise RuntimeError('shadowed')\n", encoding="utf-8")
    plan = {
        "schema_version": "2",
        "gate_decision": "pass",
        "observed_maturity": "test-authored",
        "plan": {
            "cases": [
                {
                    "method": "test",
                    "node_id": "tests/test_proof.py::test_selected",
                    "selector": {"runner": "pytest", "node_id": "tests/test_proof.py::test_selected"},
                }
            ]
        },
    }
    captured: list[Any] = []

    assert (
        module.execute_plan(
            plan,
            tmp_path,
            tmp_path / "proof.xml",
            command_runner=lambda command: captured.append(command) or 0,
        )
        == 0
    )
    command = captured[0]
    bootstrap = getattr(module, "PROOF_PYTEST_BOOTSTRAP", "")
    assert command.arguments[1:4] == ["-P", "-c", bootstrap]
    assert bootstrap.index("import pytest") < bootstrap.index("sys.path.append(repo_root)")


def test_invalid_utf8_authority_is_stable_metadata_failure(tmp_path: Path) -> None:
    """Malformed external bytes fail closed without exposing parser details."""
    comment = tmp_path / "comment.json"
    comment.write_bytes(b"\xff")
    artifact_root = tmp_path / "artifact"
    artifact_root.mkdir()
    arguments = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "requirements_bootstrap_authority.py"),
        "--comment",
        str(comment),
        "--commit",
        str(tmp_path / "commit.json"),
        "--run",
        str(tmp_path / "run.json"),
        "--artifacts",
        str(tmp_path / "artifacts.json"),
        "--artifact-root",
        str(artifact_root),
        "--repo-root",
        str(tmp_path),
        "--comment-id",
        "1",
        "--base-ref",
        "a" * 40,
        "--final-ref",
        "b" * 40,
        "--repository",
        "nold-ai/specfact-cli",
        "--change-id",
        "fix-release-promotion-security-gates",
        "--issue",
        "692",
        "--pull-request",
        "1",
        "--head-branch",
        "bugfix/692-security-patch-clean-replay",
    ]

    result = subprocess.run(arguments, capture_output=True, text=True, check=False)

    assert result.returncode == 1
    assert result.stderr.strip() == "bootstrap-authority-invalid:authority-metadata"


def test_doc_owner_rg_terminates_options(monkeypatch: Any, tmp_path: Path) -> None:
    """A dash-prefixed Markdown path is data, not an ripgrep option."""
    module = _load_script("check_doc_frontmatter")
    observed: list[list[str]] = []

    def run(arguments: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        observed.append(arguments)
        return subprocess.CompletedProcess(arguments, 1, "", "")

    monkeypatch.setattr(module.subprocess, "run", run)
    assert module._missing_owner_via_rg([tmp_path / "--files"]) == []
    assert observed[0][-2:] == ["--", str(tmp_path / "--files")]


def test_patch_release_uses_next_version_in_all_sources() -> None:
    """The security baseline consumes only the next semver patch."""
    expected = "0.55.4"
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == expected
    for path in ("setup.py", "src/__init__.py", "src/specfact_cli/__init__.py"):
        assert expected in (REPO_ROOT / path).read_text(encoding="utf-8")
