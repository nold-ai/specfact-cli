"""Focused red/green contracts for the #692 security patch."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

import pytest
import yaml
from _pytest.config import ExitCode


REPO_ROOT = Path(__file__).resolve().parents[3]

_CONFTEST_OUTCOME_FORGERY = """
import pytest

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed:
        report.outcome = "passed"
        report.longrepr = None

def pytest_sessionfinish(session):
    session.exitstatus = 0
""".lstrip()

_ISOLATED_PYTEST_BOOTSTRAP = """
import os
import sys

site_packages, repo_root, junit_path, disable_conftest, block_plugins = sys.argv[1:6]
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
sys.path.append(site_packages)
import pytest

class TrustedPluginPolicy:
    def pytest_configure(self, config):
        consider_module = config.pluginmanager.consider_module
        def reject_candidate_plugins(module):
            if "pytest_plugins" in module.__dict__:
                raise pytest.UsageError("selected Requirements tests cannot declare pytest_plugins")
            consider_module(module)
        config.pluginmanager.consider_module = reject_candidate_plugins

sys.path.append(repo_root)
arguments = ["--junitxml", junit_path]
if disable_conftest == "1":
    arguments.append("--noconftest")
arguments.extend(["--", "test_guard.py::test_guard"])
plugins = [TrustedPluginPolicy()] if block_plugins == "1" else []
raise SystemExit(pytest.main(arguments, plugins=plugins))
"""


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


def _assert_contains(text: str, fragments: tuple[str, ...]) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    assert not missing, missing


def _run_isolated_guard(
    tmp_path: Path, junit_name: str, *, disable_conftest: bool, block_plugins: bool = False
) -> subprocess.CompletedProcess[str]:
    junit_path = tmp_path / junit_name
    pytest_file = pytest.__file__
    assert pytest_file is not None
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            _ISOLATED_PYTEST_BOOTSTRAP,
            str(Path(pytest_file).resolve().parent.parent),
            str(tmp_path),
            str(junit_path),
            str(int(disable_conftest)),
            str(int(block_plugins)),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )


def _on_block(workflow: dict[str, Any]) -> dict[str, Any]:
    value = workflow.get("on", cast(dict[object, Any], workflow).get(True))
    assert isinstance(value, dict)
    return cast(dict[str, Any], value)


def _named_step(job: dict[str, Any], name: str) -> dict[str, Any]:
    steps = job.get("steps")
    assert isinstance(steps, list)
    for item in steps:
        if isinstance(item, dict):
            step = cast(dict[str, Any], item)
            if step.get("name") == name:
                return step
    raise AssertionError(name)


def _assert_fresh_review_job(jobs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return producer and review jobs after checking the isolated final context."""
    producer = cast(dict[str, Any], jobs["requirements-evidence-producer"])
    review = cast(dict[str, Any], jobs["requirements-evidence"])
    final = cast(dict[str, Any], jobs["requirements-evidence-final"])
    assert review["name"] == "Requirements evidence execution"
    assert final["name"] == "Requirements evidence"
    assert final["needs"] == "requirements-evidence"
    assert review["needs"] == "requirements-evidence-producer"
    assert review["if"] == "always()"
    return producer, review


def _assert_exact_review_checkout(review: dict[str, Any]) -> None:
    """Require a clean, credential-free checkout of the immutable PR head."""
    checkout = _named_step(review, "Checkout exact head for Code Review")
    assert checkout["uses"] == "actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10"
    assert checkout["with"]["ref"] == "${{ github.event.pull_request.head.sha || github.sha }}"  # type: ignore[index]
    assert checkout["with"]["clean"] is True  # type: ignore[index]
    assert checkout["with"]["persist-credentials"] is False  # type: ignore[index]
    verify_head = _named_step(review, "Verify exact head for Code Review")
    assert verify_head["env"]["EXPECTED_HEAD"] == "${{ github.event.pull_request.head.sha || github.sha }}"  # type: ignore[index]
    assert 'test "$(git rev-parse HEAD)" = "$EXPECTED_HEAD"' in str(verify_head.get("run", ""))


def _assert_review_tool_and_artifact_order(review: dict[str, Any]) -> None:
    """Require frozen tools before the immutable proof artifact enters the runner."""
    install = str(_named_step(review, "Install frozen Code Review tools").get("run", ""))
    closure_proof = '"$TRUSTED_DELIVERY_VERIFIER"'
    assert '"${REQUIREMENTS_VERIFIER_ROOT}/bin/python" -I -S -c' in install
    assert install.index(closure_proof) < install.index("uv pip install")
    assert "python scripts/check_reproducible_delivery.py" not in install
    review_steps = cast(list[dict[str, Any]], review["steps"])
    step_names = [step.get("name") for step in review_steps]
    assert step_names.index("Install frozen Code Review tools") < step_names.index(
        "Restore Requirements evidence for Code Review"
    )
    restore = _named_step(review, "Restore Requirements evidence for Code Review")
    assert restore["env"]["ARTIFACT_ID"] == "${{ needs.requirements-evidence-producer.outputs.artifact-id }}"


def _assert_review_diff_is_fail_closed(review: dict[str, Any]) -> None:
    """Require checked tempfile transport for the immutable review diff."""
    review_command = str(_named_step(review, "Run Code Review with finalized Requirements context").get("run", ""))
    assert 'if ! git diff --name-only -z "${review_base_commit}..HEAD"' in review_command
    assert 'done < "$review_paths_file"' in review_command
    assert "done < <(git diff" not in review_command


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


def test_requirements_review_restarts_from_exact_head_after_proof() -> None:
    """Proof execution cannot share a runner or mutable tool state with review."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    jobs = cast(dict[str, Any], workflow["jobs"])
    producer, review = _assert_fresh_review_job(jobs)
    _named_step(producer, "Run Requirements evidence gate")
    _assert_exact_review_checkout(review)
    _assert_review_tool_and_artifact_order(review)
    _assert_review_diff_is_fail_closed(review)


def test_required_requirements_check_cannot_be_manually_dispatched() -> None:
    """Only PR provenance may emit the branch-protected Requirements context."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    assert set(_on_block(workflow)) == {"pull_request"}
    jobs = cast(dict[str, Any], workflow["jobs"])
    assert cast(dict[str, Any], jobs["requirements-evidence-final"])["name"] == "Requirements evidence"


def test_requirements_proof_step_has_no_github_token_ancestor() -> None:
    """Credentialed bootstrap retrieval is isolated from the step that runs tests."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    job = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["requirements-evidence-producer"])
    bootstrap = _named_step(job, "Prepare one-time Requirements bootstrap authority")
    proof = _named_step(job, "Run Requirements evidence gate")
    assert cast(dict[str, Any], bootstrap["env"])["GH_TOKEN"] == "${{ github.token }}"
    assert "GH_TOKEN" not in cast(dict[str, Any], proof.get("env", {}))
    proof_command = str(proof.get("run", ""))
    assert "gh api" not in proof_command
    assert "gh run download" not in proof_command


def test_fresh_consumer_reexecutes_trusted_plan() -> None:
    """Producer-authored JUnit cannot mint the fresh consumer's final verdict."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    review = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["requirements-evidence"])
    materialize = str(_named_step(review, "Materialize trusted Requirements core").get("run", ""))
    reconcile_step = _named_step(review, "Reconcile Requirements evidence on fresh runner")
    reconcile = str(reconcile_step.get("run", ""))

    _assert_contains(
        materialize,
        (
            "scripts/requirements_proof_executor.py",
            "scripts/requirements_proof_pytest_plugin.py",
            "TRUSTED_PROOF_EXECUTOR",
            "TRUSTED_PROOF_PLUGIN",
        ),
    )
    _assert_contains(
        reconcile,
        (
            'cmp --silent "$consumer_plan"',
            'consumer_junit="${RUNNER_TEMP}/requirements-proof-consumer.xml"',
            "importlib.util.spec_from_file_location(",
            "sys.modules[executor_spec.name] = trusted_executor",
            "trusted_executor.selectors_from_plan(",
            'os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"',
            "plugins=[trusted_plugin, trusted_plugin_policy]",
            '"--rootdir", repo_root',
            '--junit "$consumer_junit"',
        ),
    )
    forbidden_fragments = (
        "runpy.run_path(trusted_executor)",
        "--junit artifacts/requirements-evidence/requirements-proof.xml",
        'cmp --silent "$consumer_report"',
    )
    assert not any(fragment in reconcile for fragment in forbidden_fragments)
    assert reconcile.index("import pytest") < reconcile.index("sys.path.append(repo_root)")
    execution_order = tuple(
        reconcile.index(fragment)
        for fragment in ('cmp --silent "$consumer_plan"', "pytest.main(", "reconciliation_arguments=(")
    )
    assert execution_order == tuple(sorted(execution_order))
    assert reconcile_step["timeout-minutes"] == 12


def _assert_guard_result(
    result: subprocess.CompletedProcess[str], junit_path: Path, expected_returncode: int, expected_failures: str
) -> None:
    assert result.returncode == expected_returncode, result.stderr
    suite = ElementTree.parse(junit_path).find(".//testsuite")
    assert suite is not None
    assert suite.get("failures") == expected_failures


def _assert_conftest_outcome_forgery_is_blocked(tmp_path: Path) -> None:
    (tmp_path / "conftest.py").write_text(_CONFTEST_OUTCOME_FORGERY, encoding="utf-8")
    (tmp_path / "test_guard.py").write_text("def test_guard():\n    assert False\n", encoding="utf-8")

    forged_junit = tmp_path / "forged.xml"
    forged = _run_isolated_guard(tmp_path, forged_junit.name, disable_conftest=False)
    _assert_guard_result(forged, forged_junit, 0, "0")

    trusted_junit = tmp_path / "trusted.xml"
    trusted = _run_isolated_guard(tmp_path, trusted_junit.name, disable_conftest=True)
    _assert_guard_result(trusted, trusted_junit, 1, "1")


def _assert_declared_plugin_outcome_forgery_is_blocked(tmp_path: Path) -> None:
    (tmp_path / "forge_plugin.py").write_text(_CONFTEST_OUTCOME_FORGERY, encoding="utf-8")
    (tmp_path / "test_guard.py").write_text(
        'globals()["pytest_" + "plugins"] = ("forge_plugin",)\n\ndef test_guard():\n    assert False\n',
        encoding="utf-8",
    )
    plugin_forged_junit = tmp_path / "plugin-forged.xml"
    plugin_forged = _run_isolated_guard(tmp_path, plugin_forged_junit.name, disable_conftest=True)
    _assert_guard_result(plugin_forged, plugin_forged_junit, 0, "0")

    plugin_guarded = _run_isolated_guard(tmp_path, "plugin-guarded.xml", disable_conftest=True, block_plugins=True)
    assert plugin_guarded.returncode == ExitCode.USAGE_ERROR  # pyright: ignore[reportUnknownMemberType]
    assert "selected Requirements tests cannot declare pytest_plugins" in (
        plugin_guarded.stdout + plugin_guarded.stderr
    )


def _assert_consumer_pytest_isolation(workflow: dict[str, Any]) -> None:
    review = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["requirements-evidence"])
    reconcile = str(_named_step(review, "Reconcile Requirements evidence on fresh runner").get("run", ""))
    assert '"--noconftest"' in reconcile
    assert '"-c", os.devnull' in reconcile
    assert 'if "pytest_plugins" in module.__dict__' in reconcile
    assert "plugins=[trusted_plugin, trusted_plugin_policy]" in reconcile


def _assert_final_job_does_not_execute_candidate_tests(workflow: dict[str, Any]) -> None:
    final = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["requirements-evidence-final"])
    final_commands = "\n".join(str(step.get("run", "")) for step in cast(list[dict[str, Any]], final["steps"]))
    assert "pytest.main(" not in final_commands
    assert all(not str(step.get("uses", "")).startswith("./") for step in cast(list[dict[str, Any]], final["steps"]))
    assert "Reconcile final Requirements verdict on fresh runner" in {
        step.get("name") for step in cast(list[dict[str, Any]], final["steps"])
    }


def test_fresh_consumer_rejects_candidate_conftest_outcome_forgery(tmp_path: Path) -> None:
    """Candidate pytest hooks cannot turn a failing selector into trusted pass JUnit."""
    _assert_conftest_outcome_forgery_is_blocked(tmp_path)
    _assert_declared_plugin_outcome_forgery_is_blocked(tmp_path)
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    _assert_consumer_pytest_isolation(workflow)
    _assert_final_job_does_not_execute_candidate_tests(workflow)


def test_requirements_archive_uses_one_immutable_merge_base() -> None:
    """Archive selection and blob identity share the exact same base commit."""
    workflow = _workflow(".github/workflows/requirements-evidence.yml")
    job = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])["requirements-evidence-producer"])
    command = str(_named_step(job, "Run Requirements evidence gate").get("run", ""))
    assert 'evidence_base_commit="${PLANNING_BASE_COMMIT:-${PROOF_BASE_COMMIT:-}}"' in command
    assert '"${evidence_base_commit}..HEAD"' in command
    assert 'git ls-tree -r -z --name-only "$evidence_base_commit"' in command
    assert 'git ls-tree "$evidence_base_commit"' in command
    assert '"origin/${EVIDENCE_BASE_BRANCH}...HEAD"' not in command


def test_every_code_review_lock_install_has_exact_closure_proof() -> None:
    """Hash identity alone never authorizes an extra package in the review lock."""
    for workflow_path, job_name in (
        (".github/workflows/pr-orchestrator.yml", "license-check"),
        (".github/workflows/requirements-evidence.yml", "requirements-evidence"),
    ):
        workflow = _workflow(workflow_path)
        job = cast(dict[str, Any], cast(dict[str, Any], workflow["jobs"])[job_name])
        install = str(
            _named_step(
                job,
                "Install frozen Code Review tools"
                if job_name == "requirements-evidence"
                else "Install frozen Code Review license scope",
            ).get("run", "")
        )
        closure_proof = (
            '"$TRUSTED_DELIVERY_VERIFIER"'
            if job_name == "requirements-evidence"
            else "python scripts/check_reproducible_delivery.py"
        )
        assert install.index(closure_proof) < install.index("uv pip install")


def _assert_native_provider_binding(release: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider_path = REPO_ROOT / ".github/actions/setup-frozen-python/provision_semgrep.py"
    spec = importlib.util.spec_from_file_location("_release_native_semgrep_provider", provider_path)
    assert spec is not None and spec.loader is not None
    provider = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, provider)
    spec.loader.exec_module(provider)
    assert provider.POLICY_FILE == REPO_ROOT / "ci/security-tool-minimum-versions.json"
    verify_installation = provider._verify_installation
    observed: list[tuple[Path, tuple[Any, ...]]] = []

    def observe_verification(destination: Path, members: tuple[Any, ...]) -> None:
        observed.append((destination, members))
        verify_installation(destination, members)

    monkeypatch.setattr(provider, "_verify_installation", observe_verification)
    for platform, artifact in release["platforms"].items():
        monkeypatch.setattr(provider, "_platform_key", lambda platform=platform: platform)
        observed.clear()
        with pytest.raises(ValueError, match=r"^Native installation file set differs from selection$"):
            provider.provision_semgrep(tmp_path)
        assert len(observed) == 1
        destination, members = observed[0]
        assert destination == tmp_path
        replacements = artifact.get("curl_fix", artifact.get("pcre2_fix", {})).get("members", [])
        replaced = {member["installed_path"] for member in replacements}
        removed = set(artifact.get("curl_fix", {}).get("remove", []))
        expected = [
            *[member for member in artifact["members"] if member["installed_path"] not in replaced | removed],
            *release["notices"],
            *artifact.get("notices", []),
            *replacements,
        ]
        assert [(member.destination, member.size, member.digest) for member in members] == [
            (member["installed_path"], member["size"], member["sha256"]) for member in expected
        ]

    action = _workflow(".github/actions/setup-frozen-python/action.yml")
    provision = _named_step(action["runs"], "Provision frozen native Semgrep")
    assert (
        '"$project_python" .github/actions/setup-frozen-python/provision_semgrep.py '
        '"$RUNNER_TEMP/specfact-native-semgrep" >> "$GITHUB_PATH"'
    ) in provision["run"]


_EXPECTED_NATIVE_ARTIFACTS = {
    "macos-arm64": (
        51257278,
        "0ce3064175a44236dd9fd35603627e3f56139ac61e13ca967bae2b76b2cec9bf",
        "1a5cb45e24673f3f5a6276943efc917ffd427db53e0e0537d1c880d3b9d10bb3",
    ),
    "linux-x86_64": (
        72254465,
        "d847abb8fb6fdde77d9e30a6bc869dbfcb68eff4142dcd77897c52635a7600d9",
        "440018d25dc528a902a1174f6d6b74676a5e9fa79e7d2cdd7404158a5c94aa55",
    ),
    "windows-x86_64": (
        59524393,
        "3c86b2961b4663d1338fb965de038c7869571661971b78e18e9346ab57e1e20a",
        "d630d1f1f3178f17680cd438704d2d6dd8669248225c1a904aed1cd746970da2",
    ),
}


def test_frozen_python_graph_excludes_expired_scanner_dependencies() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = [
        *project["project"]["dependencies"],
        *(item for group in project["project"]["optional-dependencies"].values() for item in group),
        *project["tool"]["hatch"]["envs"]["default"]["dependencies"],
    ]
    assert not any(re.match(r"^(?:semgrep|mcp|specfact-semgrep)(?:\b|[<>=!~;\[])", item) for item in dependencies)
    locked = (REPO_ROOT / "requirements/ci/locked.txt").read_text(encoding="utf-8")
    assert not re.search(r"^(?:semgrep|mcp|specfact-semgrep)==", locked, re.MULTILINE)
    assert re.search(r"^opentelemetry-api==1\.45\.1[ \t]", locked, re.MULTILINE)
    lock = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    packages = [
        (package["name"], package["version"], package["source"])
        for package in lock["package"]
        if package["name"] in {"semgrep", "mcp", "opentelemetry-api", "specfact-semgrep"}
    ]
    assert sorted(packages) == [("opentelemetry-api", "1.45.1", {"registry": "https://pypi.org/simple"})]


def test_native_policy_retains_security_floor_and_empty_registers() -> None:
    policy = json.loads((REPO_ROOT / "ci/security-tool-minimum-versions.json").read_text(encoding="utf-8"))
    assert policy["minimum_versions"] == {"mcp": "1.28.1", "semgrep": "1.175.0"}
    for register in ("dependency-trust-exceptions.json", "vulnerability-audit-exceptions.json"):
        assert json.loads((REPO_ROOT / "ci" / register).read_text(encoding="utf-8"))["exceptions"] == []
    release = policy["native_semgrep"]
    assert release["version"] == "1.184.0"
    assert set(release["platforms"]) == set(_EXPECTED_NATIVE_ARTIFACTS)


@pytest.mark.parametrize("platform", _EXPECTED_NATIVE_ARTIFACTS)
def test_native_platform_artifact_retains_original_bytes(platform: str) -> None:
    release = json.loads((REPO_ROOT / "ci/security-tool-minimum-versions.json").read_text())["native_semgrep"]
    size, digest, engine_digest = _EXPECTED_NATIVE_ARTIFACTS[platform]
    artifact = release["platforms"][platform]
    origin = urlsplit(cast(str, artifact["url"]))
    assert (origin.scheme, origin.netloc, origin.query, origin.fragment) == (
        "https",
        "files.pythonhosted.org",
        "",
        "",
    )
    assert origin.path.rsplit("/", 1)[-1].startswith("semgrep-1.184.0-")
    assert origin.path.endswith(".whl")
    assert (artifact["size"], artifact["sha256"]) == (size, digest)
    engine = "osemgrep.exe" if platform == "windows-x86_64" else "osemgrep"
    assert [member["sha256"] for member in artifact["members"] if member["installed_path"] == engine] == [engine_digest]


def test_linux_curl_correction_is_exact() -> None:
    release = json.loads((REPO_ROOT / "ci/security-tool-minimum-versions.json").read_text())["native_semgrep"]
    curl = release["platforms"]["linux-x86_64"]["curl_fix"]
    assert (curl["package"], curl["version"], curl["url"], curl["size"], curl["sha256"]) == (
        "libcurl-minimal",
        "7.76.1-40.el9_8.9",
        "https://repo.almalinux.org/almalinux/9/BaseOS/x86_64/os/Packages/libcurl-minimal-7.76.1-40.el9_8.9.x86_64.rpm",
        231361,
        "d971ebea1a637cfaf7afac8416c2f0e4afc64f0d8b89314279e55b061f080921",
    )
    assert [(member["installed_path"], member["size"], member["sha256"]) for member in curl["members"]] == [
        ("libs/libcurl.so.4", 517040, "6a0d187667a03530e0a67766fa28d62ebbfb5632b923b2a8af07be8071890cbe"),
        ("LICENSE.libcurl", 1088, "6fd1a1c008b5ef4c4741dd188c3f8af6944c14c25afa881eb064f98fb98358e7"),
    ]


def test_macos_pcre2_correction_is_exact() -> None:
    release = json.loads((REPO_ROOT / "ci/security-tool-minimum-versions.json").read_text())["native_semgrep"]
    pcre2 = release["platforms"]["macos-arm64"]["pcre2_fix"]
    assert release["platforms"]["macos-arm64"]["observed_macos_minimum"] == "15.0"
    assert (pcre2["package"], pcre2["version"], pcre2["url"], pcre2["size"], pcre2["sha256"]) == (
        "pcre2",
        "10.49",
        "https://ghcr.io/v2/homebrew/core/pcre2/blobs/sha256:0ec47d18c50f5770db2b3f07b5b85644284cc6ee8e07e23b11d2727e95932b77",
        2465167,
        "0ec47d18c50f5770db2b3f07b5b85644284cc6ee8e07e23b11d2727e95932b77",
    )
    assert [(member["installed_path"], member["size"], member["sha256"]) for member in pcre2["members"]] == [
        ("libs/libpcre2-8.0.dylib", 573984, "56bc0ef73d8b270e074b163795abeb02b3809d83b68c50ee8d29b148d0b2e5d4"),
        ("LICENSE.pcre2", 4011, "197d8a73ffee0d6b09adba2f9c677b5f5aede24edf89258a68e48248d010d811"),
    ]


def test_current_native_provider_binding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    release = json.loads((REPO_ROOT / "ci/security-tool-minimum-versions.json").read_text())["native_semgrep"]
    _assert_native_provider_binding(release, tmp_path, monkeypatch)


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


def test_repository_license_exceptions_match_their_actual_environments() -> None:
    """The root and isolated review scopes accept only their intended rows."""
    checker = _load_script("check_license_compliance")
    allowlist = checker._load_allowlist()
    assert allowlist["pygments"][0]["scope"] == "dev-only"
    assert allowlist["pylint"][0]["scope"] == "code-review-only"


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

    exit_code = module.execute_plan(
        plan,
        tmp_path,
        tmp_path / "proof.xml",
        command_runner=lambda command: captured.append(command) or 0,
    )
    assert exit_code == 0
    command = captured[0]
    bootstrap = getattr(module, "PROOF_PYTEST_BOOTSTRAP", "")
    assert command.arguments[1:4] == ["-P", "-c", bootstrap]
    assert bootstrap.index("import pytest") < bootstrap.index("sys.path.append(repo_root)")


def test_invalid_utf8_authority_refuses_with_stable_error(tmp_path: Path) -> None:
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

    authority_validation = subprocess.run(arguments, capture_output=True, text=True, check=False)

    assert authority_validation.returncode == 1
    assert authority_validation.stderr.strip() == "bootstrap-authority-invalid:authority-metadata"


def test_doc_owner_rg_terminates_options(monkeypatch: Any, tmp_path: Path) -> None:
    """A dash-prefixed Markdown path is data, not an ripgrep option."""
    module = _load_script("check_doc_frontmatter")
    observed: list[list[str]] = []

    def run_rg(arguments: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        observed.append(arguments)
        return subprocess.CompletedProcess(arguments, 1, "", "")

    monkeypatch.setattr(module.subprocess, "run", run_rg)
    assert module._missing_owner_via_rg([tmp_path / "--files"]) == []
    assert observed[0][-2:] == ["--", str(tmp_path / "--files")]


def test_patch_release_uses_next_version_in_all_sources() -> None:
    """The security baseline consumes only the next semver patch."""
    expected = "0.55.12"
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == expected
    for path in ("setup.py", "src/__init__.py", "src/specfact_cli/__init__.py"):
        assert expected in (REPO_ROOT / path).read_text(encoding="utf-8")
