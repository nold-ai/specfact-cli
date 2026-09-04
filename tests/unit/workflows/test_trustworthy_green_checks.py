"""Workflow and hook policy tests for trustworthy green checks."""

# pyright: reportUnknownMemberType=false

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any, cast

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT = REPO_ROOT / "pyproject.toml"
PR_ORCHESTRATOR = REPO_ROOT / ".github" / "workflows" / "pr-orchestrator.yml"
REQUIREMENTS_EVIDENCE = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
DOCS_REVIEW = REPO_ROOT / ".github" / "workflows" / "docs-review.yml"
SPECFACT_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "specfact.yml"
SIGN_MODULES = REPO_ROOT / ".github" / "workflows" / "sign-modules.yml"
PUBLISH_MODULES = REPO_ROOT / ".github" / "workflows" / "publish-modules.yml"
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"
DEPENDABOT_CONFIG = REPO_ROOT / ".github" / "dependabot.yml"
CODERABBIT_CONFIG = REPO_ROOT / ".coderabbit.yaml"
LEGACY_ACTIONLINT_RUNNER = REPO_ROOT / "scripts" / "run_actionlint.sh"
MODULE_FIXTURE_LOCK = REPO_ROOT / "ci" / "module-fixture.lock.json"
UV_LOCK = REPO_ROOT / "uv.lock"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"Expected mapping at {path}"
    return cast(dict[str, Any], data)


def _workflow_on_block(workflow: dict[str, Any]) -> dict[str, Any]:
    """Return the Actions trigger block, accounting for YAML 1.1 `on` coercion."""
    on_block = workflow.get("on")
    if on_block is None:
        on_block = cast(dict[object, Any], workflow).get(True)
    assert isinstance(on_block, dict), "Workflow must define event mappings"
    return cast(dict[str, Any], on_block)


def _load_jobs() -> dict[str, dict[str, Any]]:
    workflow = _load_yaml(PR_ORCHESTRATOR)
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "Expected jobs mapping in pr-orchestrator workflow"
    typed_jobs: dict[str, dict[str, Any]] = {}
    for job_name, job_value in jobs.items():
        assert isinstance(job_name, str), "Job names must be strings"
        assert isinstance(job_value, dict), f"Expected mapping for job {job_name}"
        typed_jobs[job_name] = cast(dict[str, Any], job_value)
    return typed_jobs


def _load_hooks() -> list[dict[str, Any]]:
    config = _load_yaml(PRE_COMMIT_CONFIG)
    repos = config.get("repos")
    assert isinstance(repos, list) and repos, "Expected repos list in .pre-commit-config.yaml"
    local_repo = next(
        (r for r in repos if isinstance(r, dict) and r.get("repo") == "local"),
        None,
    )
    assert isinstance(local_repo, dict), "Expected a 'repo: local' entry in .pre-commit-config.yaml"
    hooks = local_repo.get("hooks")
    assert isinstance(hooks, list), "Expected hooks list in .pre-commit-config.yaml"
    typed_hooks: list[dict[str, Any]] = []
    for hook in hooks:
        assert isinstance(hook, dict), "Each hook must be a mapping"
        typed_hooks.append(cast(dict[str, Any], hook))
    return typed_hooks


def _load_job_steps(job_name: str) -> list[dict[str, Any]]:
    jobs = _load_jobs()
    job = jobs.get(job_name)
    assert job is not None, f"Expected {job_name!r} job in pr-orchestrator"
    steps = job.get("steps")
    assert isinstance(steps, list), f"Expected steps list in {job_name!r} job"
    return [cast(dict[str, Any], step) for step in steps if isinstance(step, dict)]


def _find_named_step(job_name: str, step_name: str) -> dict[str, Any]:
    step = next((step for step in _load_job_steps(job_name) if step.get("name") == step_name), None)
    assert step is not None, f"Expected {step_name!r} step in {job_name!r} job"
    return step


def _find_requirements_final_step(step_name: str) -> dict[str, Any]:
    workflow = _load_yaml(REQUIREMENTS_EVIDENCE)
    jobs = cast(dict[str, dict[str, Any]], workflow["jobs"])
    final_steps = cast(list[dict[str, Any]], jobs["requirements-evidence-final"]["steps"])
    step = next((item for item in final_steps if item.get("name") == step_name), None)
    assert step is not None, f"Expected {step_name!r} step in final Requirements job"
    return step


def _normalized_condition(value: object) -> str:
    assert isinstance(value, str), "Expected workflow condition to be a string"
    return " ".join(value.replace('"', "'").split())


def _assert_condition_contains(value: object, expected: str, *, context: str) -> None:
    normalized = _normalized_condition(value)
    assert expected in normalized, f"{context}; got {value!r}"


def _assert_unsets_github_base_ref_before(step: dict[str, Any], command_fragment: str) -> None:
    run_clause = step.get("run")
    assert isinstance(run_clause, str), "Test step must define a shell run block"
    lines = [line.strip() for line in run_clause.splitlines()]
    assert lines.count("unset GITHUB_BASE_REF") == 1
    unset_index = lines.index("unset GITHUB_BASE_REF")
    command_index = next(
        (index for index, line in enumerate(lines) if command_fragment in line),
        None,
    )
    assert command_index is not None, f"Expected test launcher containing {command_fragment!r}"
    assert unset_index < command_index, "GITHUB_BASE_REF must be unset before the test launcher"


def test_pr_orchestrator_pypi_version_check_gated_on_version_sources() -> None:
    """PyPI-ahead must not run on every code PR; gate matches pre-commit staged version files."""
    pypi_step = _find_named_step("tests", "Verify local version is ahead of PyPI")
    _assert_condition_contains(
        pypi_step.get("if"),
        "version_sources_changed == 'true'",
        context="PyPI-ahead step must be gated on version_sources_changed == 'true'",
    )

    run_clause = pypi_step.get("run") or ""
    assert "skip-when-version-unchanged-vs" in str(run_clause), (
        "PyPI-ahead step must invoke check_local_version_ahead_of_pypi.py with --skip-when-version-unchanged-vs"
    )
    assert "github.event.pull_request.base.sha" in str(run_clause), (
        "PyPI-ahead step must compare against the PR base SHA"
    )

    jobs = _load_jobs()
    changes_job = jobs.get("changes")
    assert isinstance(changes_job, dict), "Expected 'changes' job in pr-orchestrator"
    outputs = changes_job.get("outputs")
    assert isinstance(outputs, dict) and "version_sources_changed" in outputs, (
        "'changes' job must export 'version_sources_changed' output for downstream gating"
    )


def test_pr_orchestrator_version_sync_uses_base_sha_on_clean_ci_checkout() -> None:
    """Version-source synchronization must compare PR/push changes, not only the staged index."""
    version_step = _find_named_step("tests", "Verify version strings are synchronized")
    run_clause = str(version_step.get("run") or "")
    assert "--changed-vs" in run_clause, "Version-source sync step must pass --changed-vs in CI"
    assert "github.event.pull_request.base.sha" in run_clause, (
        "Version-source sync step must compare against the PR base SHA"
    )
    assert "github.event.before" in run_clause, (
        "Version-source sync step must compare against the push 'before' SHA when applicable"
    )


def test_primary_test_process_does_not_inherit_github_base_ref() -> None:
    """The primary pytest launcher must not inherit pull-request routing state."""
    step = _find_named_step("tests", "Run full test suite (direct smart-test-full)")
    _assert_unsets_github_base_ref_before(step, "python tools/smart_test_coverage.py")


def test_compatibility_test_process_does_not_inherit_github_base_ref() -> None:
    """The Python 3.11 pytest launcher must not inherit pull-request routing state."""
    step = _find_named_step("compat-py311", "Run Python 3.11 compatibility tests")
    assert step.get("shell") == "bash", "Compatibility test isolation requires an explicit Bash shell"
    _assert_unsets_github_base_ref_before(step, "python -m pytest")


def test_only_test_processes_override_github_base_ref() -> None:
    """Only the two test run blocks may remove GitHub's authentic base reference."""
    workflow = _load_yaml(PR_ORCHESTRATOR)
    workflow_environment = workflow.get("env")
    assert not (isinstance(workflow_environment, dict) and "GITHUB_BASE_REF" in workflow_environment), (
        "Workflow-level GITHUB_BASE_REF overrides are forbidden"
    )

    clearers: set[tuple[str, str]] = set()
    for job_name, job in _load_jobs().items():
        job_environment = job.get("env")
        assert not (isinstance(job_environment, dict) and "GITHUB_BASE_REF" in job_environment), (
            f"Job {job_name!r} must retain GitHub's authentic base reference"
        )
        for step in _load_job_steps(job_name):
            step_environment = step.get("env")
            assert not (isinstance(step_environment, dict) and "GITHUB_BASE_REF" in step_environment), (
                "Reserved GitHub variables cannot be overridden through workflow env"
            )
            run_clause = step.get("run")
            if isinstance(run_clause, str) and "unset GITHUB_BASE_REF" in {
                line.strip() for line in run_clause.splitlines()
            }:
                clearers.add((job_name, str(step.get("name", ""))))

    assert clearers == {
        ("tests", "Run full test suite (direct smart-test-full)"),
        ("compat-py311", "Run Python 3.11 compatibility tests"),
    }


def test_pr_orchestrator_required_checks_trigger_on_every_pr_head_commit() -> None:
    """Required checks must not disappear behind workflow-level path filters."""
    workflow = _load_yaml(PR_ORCHESTRATOR)
    on_block = _workflow_on_block(workflow)
    pull_request = on_block.get("pull_request")
    push = on_block.get("push")
    assert isinstance(pull_request, dict), "pull_request trigger must be a mapping"
    assert isinstance(push, dict), "push trigger must be a mapping"
    assert "paths-ignore" not in pull_request, "Required PR workflows must still emit statuses on docs-only commits"
    assert "paths-ignore" not in push, "Required push workflows must still emit statuses on docs-only commits"


def test_pr_orchestrator_required_jobs_fail_closed() -> None:
    """Required jobs should not hide tool failures behind warn-only shell patterns."""
    required_jobs = {
        "verify-module-signatures",
        "tests",
        "compat-py311",
        "contract-first-ci",
        "cli-validation",
        "quality-gates",
        "independent-static-analysis",
        "package-runtime-matrix",
        "type-checking",
        "linting",
        "workflow-lint",
    }
    jobs = _load_jobs()
    for job_name in required_jobs:
        job = jobs.get(job_name)
        assert job is not None, f"Expected required job {job_name!r} in pr-orchestrator"
        assert job.get("continue-on-error") is not True, f"Required job {job_name!r} must fail closed"
        steps = job.get("steps")
        assert isinstance(steps, list), f"Expected steps list for job {job_name!r}"
        for step in steps:
            if not isinstance(step, dict):
                continue
            run = step.get("run")
            if not isinstance(run, str):
                continue
            assert "|| echo" not in run, f"Required job {job_name!r} still swallows failure with `|| echo`"
            assert "continue-on-error" not in run, f"Required job {job_name!r} must not emulate continue-on-error"


def test_pr_orchestrator_release_skip_requires_parity_proof() -> None:
    """Release fast-path skips must be gated by parity proof, not only branch names."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    assert 'echo "skip_expensive_tests_dev_to_main=true" >> "$GITHUB_OUTPUT"' not in raw
    assert "git merge-base" in raw or "git rev-parse" in raw, "Expected commit-parity proof in release skip logic"
    jobs = _load_jobs()
    changes = jobs.get("changes")
    assert changes is not None, "Expected changes job in pr-orchestrator"
    outputs = changes.get("outputs")
    assert isinstance(outputs, dict), "Expected outputs mapping for changes job"
    assert "skip_expensive_tests_dev_to_main" in outputs, "Release skip decision should remain explicit"
    normalized_conditions = [
        _normalized_condition(step.get("if")) for step in _load_job_steps("tests") if isinstance(step.get("if"), str)
    ]
    assert any(
        "needs.changes.outputs.skip_expensive_tests_dev_to_main" in cond and "== 'true'" in cond
        for cond in normalized_conditions
    ), "Expected a condition checking skip_expensive_tests_dev_to_main == 'true'"
    assert any(
        "needs.changes.outputs.skip_expensive_tests_dev_to_main" in cond and "!= 'true'" in cond
        for cond in normalized_conditions
    ), "Expected a condition checking skip_expensive_tests_dev_to_main != 'true'"


def test_pr_orchestrator_quality_gates_are_blocking() -> None:
    """Coverage quality gates must block below the configured threshold."""
    jobs = _load_jobs()
    quality_gate = jobs.get("quality-gates")
    assert quality_gate is not None, "Expected quality-gates job in pr-orchestrator"
    name = quality_gate.get("name")
    assert isinstance(name, str)
    assert name == "Quality Gates"
    run_blocks = "\n".join(str(step.get("run", "")) for step in _load_job_steps("quality-gates"))
    assert "advisory" not in run_blocks.lower()
    assert "fail_under" in run_blocks or "COVERAGE_FAIL_UNDER" in run_blocks
    assert "print(configured_fail_under)" in run_blocks
    assert "max(configured_fail_under, 80.0)" not in run_blocks
    assert "set -o pipefail" in run_blocks
    assert "exit 1" in run_blocks


def test_pr_orchestrator_read_only_checkouts_do_not_persist_credentials() -> None:
    """Read-only PR orchestration checkouts must not leave git credentials behind."""
    for job_name, _job in _load_jobs().items():
        for step in _load_job_steps(job_name):
            uses = step.get("uses")
            if not (isinstance(uses, str) and uses.startswith("actions/checkout@")):
                continue
            with_block = step.get("with")
            assert isinstance(with_block, dict), f"{job_name} checkout must define inputs"
            assert with_block.get("persist-credentials") is False, (
                f"{job_name} checkout must set persist-credentials: false"
            )


def test_pr_orchestrator_has_independent_static_analysis_gate() -> None:
    """Semgrep/Bandit must run as a blocking job independent from dogfood self-review."""
    jobs = _load_jobs()
    job = jobs.get("independent-static-analysis")
    assert job is not None, "Expected independent-static-analysis job in pr-orchestrator"
    assert job.get("name") == "Independent Static Analysis"
    assert job.get("continue-on-error") is not True


def test_pr_orchestrator_static_analysis_uses_external_tools_only() -> None:
    """Independent SAST must not rely on dogfood review output."""
    raw = "\n".join(str(step.get("run", "")) for step in _load_job_steps("independent-static-analysis"))
    assert "semgrep scan" in raw.lower()
    assert "scripts/semgrep_sast_gate.py" in raw.lower()
    assert "tools/semgrep/sast-baseline.json" in raw
    assert "--config auto" not in raw.lower()
    assert "bandit" in raw.lower()
    assert "semgrep-full" not in raw.lower()
    assert "specfact code review" not in raw
    assert ".specfact/code-review.json" not in raw


def test_semgrep_sast_hatch_script_uses_dedicated_checked_in_sast_config() -> None:
    """Semgrep SAST must not run the full development rule directory."""
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    scripts = pyproject["tool"]["hatch"]["envs"]["default"]["scripts"]
    command = scripts["semgrep-sast"]
    assert isinstance(command, str)
    assert "--config auto" not in command.lower()
    assert "--config tools/semgrep/sast.yml" in command.lower()
    assert "--config tools/semgrep {" not in command.lower()


def test_pr_orchestrator_package_runtime_matrix_uses_built_wheel() -> None:
    """PR runtime validation must exercise the built artifact, not editable installs."""
    jobs = _load_jobs()
    job = jobs.get("package-runtime-matrix")
    assert job is not None, "Expected package-runtime-matrix job in pr-orchestrator"
    assert job.get("name") == "Package Runtime Matrix"
    strategy = job.get("strategy")
    assert isinstance(strategy, dict), "package-runtime-matrix must define a launcher strategy"
    matrix = strategy.get("matrix")
    assert isinstance(matrix, dict), "package-runtime-matrix strategy must include matrix"
    launchers = matrix.get("launcher")
    assert isinstance(launchers, list)
    for expected in ("uv-source", "pip-wheel", "pipx", "uv-run"):
        assert expected in launchers


def test_pr_orchestrator_package_runtime_matrix_commands_are_black_box() -> None:
    """Package runtime commands must validate the wheel-backed CLI surface."""
    raw = "\n".join(str(step.get("run", "")) for step in _load_job_steps("package-runtime-matrix"))
    assert "uv build" in raw
    assert "find dist -maxdepth 1 -name '*.whl'" in raw
    assert "pip install -e" not in raw
    assert "uvx --from" not in raw
    assert "specfact --help" in raw
    assert "run_specfact_cli --help" in raw
    assert "module list" in raw
    upload_step = _find_named_step("package-runtime-matrix", "Upload package-runtime matrix logs")
    assert "${{ matrix.python-version }}" in str(upload_step.get("with") or "")


def test_pr_orchestrator_pipx_runtime_install_uses_the_frozen_lock() -> None:
    """pipx must install dependencies from the reviewed uv lock before the wheel."""
    raw = "\n".join(str(step.get("run", "")) for step in _load_job_steps("package-runtime-matrix"))
    assert "PIPX_DEFAULT_BACKEND=pip" in raw
    assert 'PIPX_LOCK="$RUNNER_TEMP/pylock.specfact-deps.toml"' in raw
    assert 'uv export --locked --format pylock.toml --no-emit-project --output-file "$PIPX_LOCK"' in raw
    assert 'pipx install --python "$pythonLocation/bin/python" --lock "$PIPX_LOCK" "$WHEEL"' in raw
    assert "pipx runpip specfact-cli" not in raw


def test_frozen_setup_uses_a_portable_virtual_environment_path() -> None:
    """Shared setup must expose the locked virtual environment on Windows and POSIX runners."""
    action = REPO_ROOT / ".github" / "actions" / "setup-frozen-python" / "action.yml"
    content = action.read_text(encoding="utf-8")

    assert '"$RUNNER_OS" = "Windows"' in content
    assert ".venv/Scripts" in content
    assert ".venv/bin" in content


def test_pr_orchestrator_pins_third_party_actions_to_shas() -> None:
    """Required PR workflow actions should use immutable refs, not mutable version tags."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    action_refs = re.findall(r"uses:\s+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[^\s#]+)", raw)
    mutable_refs = [ref for ref in action_refs if re.search(r"@[0-9a-f]{40}$", ref) is None]
    assert mutable_refs == []


def test_pr_orchestrator_avoids_action_runtime_annotations() -> None:
    """Workflow annotations should not hide behind known noisy Action runtime warnings."""
    workflow = _load_yaml(PR_ORCHESTRATOR)
    env = workflow.get("env")
    assert isinstance(env, dict)
    assert env.get("FORCE_JAVASCRIPT_ACTIONS_TO_NODE24") == "true"
    setup_go = next(step for step in _load_job_steps("workflow-lint") if step.get("name") == "Set up Go for actionlint")
    with_block = setup_go.get("with")
    assert isinstance(with_block, dict)
    assert with_block.get("cache") is False


def test_pr_orchestrator_release_fast_path_keeps_release_safety_checks() -> None:
    """dev -> main parity skips duplicate expensive checks, not release-safety gates."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    assert "skip_expensive_tests_dev_to_main" in raw
    assert "skip_tests_dev_to_main" not in raw
    package_runtime_condition = str(_load_jobs()["package-runtime-matrix"].get("if", ""))
    assert "skip_expensive_tests_dev_to_main" not in package_runtime_condition
    signature_condition = str(_load_jobs()["verify-module-signatures"].get("if", ""))
    assert "skip_expensive_tests_dev_to_main" not in signature_condition


def test_pr_orchestrator_requires_strict_module_signatures_at_main_boundary() -> None:
    """Direct-to-main PRs and main pushes must not inherit the relaxed dev PR policy."""
    step = _find_named_step(
        "verify-module-signatures",
        "Verify bundled module manifests (dev PR relaxed; main boundary strict)",
    )
    env = step.get("env")
    assert isinstance(env, dict)
    assert env.get("EVENT_NAME") == "${{ github.event_name }}"
    assert env.get("PR_BASE_REF") == "${{ github.event.pull_request.base.ref }}"
    assert env.get("BEFORE_SHA") == "${{ github.event.before }}"
    assert env.get("REF_NAME") == "${{ github.ref_name }}"


def test_pr_orchestrator_signature_step_keeps_main_boundary_commands() -> None:
    """Main-boundary signature verification must run the strict command path."""
    step = _find_named_step(
        "verify-module-signatures",
        "Verify bundled module manifests (dev PR relaxed; main boundary strict)",
    )
    run_clause = str(step.get("run") or "")
    assert "${{ github." not in run_clause
    assert '[ "${PR_BASE_REF}" = "main" ]' in run_clause
    assert 'python scripts/verify-modules-signature.py "${VERIFY_MODULES_STRICT[@]}"' in run_clause
    assert 'python scripts/verify-modules-signature.py "${VERIFY_MODULES_PR[@]}"' in run_clause
    assert '[ "${REF_NAME}" = "main" ]' in run_clause
    assert 'python scripts/verify-modules-signature.py "${VERIFY_MODULES_PUSH_ORCHESTRATOR[@]}"' in run_clause


def test_pr_orchestrator_has_staged_cross_platform_smoke() -> None:
    """macOS smoke blocks runtime PRs while Windows starts as scheduled/manual evidence."""
    jobs = _load_jobs()
    macos = jobs.get("runtime-smoke-macos")
    windows = jobs.get("runtime-smoke-windows")
    assert macos is not None, "Expected runtime-smoke-macos job"
    assert windows is not None, "Expected runtime-smoke-windows job"
    assert macos.get("runs-on") == "macos-latest"
    assert windows.get("runs-on") == "windows-latest"
    assert "workflow_dispatch" in str(windows.get("if", "")) or "schedule" in str(windows.get("if", ""))


def test_pr_orchestrator_has_advisory_mutation_baseline() -> None:
    """Mutation testing starts as scheduled/manual evidence, not a PR blocker."""
    jobs = _load_jobs()
    mutation = jobs.get("mutation-baseline")
    assert mutation is not None, "Expected mutation-baseline job"
    assert mutation.get("name") == "Mutation Baseline (Advisory)"
    assert "pull_request" not in str(mutation.get("if", ""))
    raw = "\n".join(str(step.get("run", "")) for step in _load_job_steps("mutation-baseline"))
    assert "mutation" in raw.lower()
    assert "dependency_resolver" in raw


def test_pr_orchestrator_contract_first_job_uses_frozen_contract_test() -> None:
    """Contract-first CI should run scoped frozen checks, leaving the full suite to smart-test-full."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    assert "python tools/contract_first_smart_test.py contracts" in raw
    assert "python tools/contract_first_smart_test.py exploration --crosshair-fast" in raw
    assert "hatch run contract-test" not in raw
    assert "hatch run specfact repro --verbose --crosshair-required --budget 120" not in raw


def test_pr_orchestrator_has_single_full_suite_owner() -> None:
    """PR validation must not run equivalent full pytest suites through multiple aliases."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    full_suite_runs = re.findall(
        r"(?:python tools/smart_test_coverage\.py run --level full|hatch run test|hatch run contract-test(?!-))", raw
    )
    assert full_suite_runs == ["python tools/smart_test_coverage.py run --level full"]


def test_core_ci_uses_immutable_modules_fixture() -> None:
    """Blocking core CI must use a reviewed modules commit rather than a moving branch."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    assert MODULE_FIXTURE_LOCK.is_file(), "Blocking module validation needs a versioned immutable fixture lock"
    fixture = json.loads(MODULE_FIXTURE_LOCK.read_text(encoding="utf-8"))
    assert fixture["repository"] == "nold-ai/specfact-cli-modules"
    assert re.fullmatch(r"[0-9a-f]{40}", fixture["commit"]), "Fixture refs must be immutable full commit SHAs"
    assert "ci/module-fixture.lock.json" in raw
    assert "git ls-remote --exit-code --heads https://github.com/nold-ai/specfact-cli-modules.git" not in raw
    assert "ref: ${{ steps.modules-ref.outputs.ref }}" not in raw
    assert "git -C specfact-cli-modules rev-parse HEAD" in raw


def test_requirements_final_verifier_archives_trusted_module_fixture_lock() -> None:
    """The final trusted delivery check must receive its base-sourced fixture lock."""
    materialize = _find_requirements_final_step("Materialize trusted final Requirements core")
    run_clause = cast(str, materialize["run"])
    assert "ci/module-fixture.lock.json" in run_clause
    assert 'test -f "$trusted_root/ci/module-fixture.lock.json"' in run_clause


def test_requirements_final_review_keeps_verified_node_in_restricted_path() -> None:
    """The final BasedPyright review must use the exact setup-node runtime."""
    setup = _find_requirements_final_step("Set up reviewed Code Review Node runtime for final verdict")
    install = cast(str, _find_requirements_final_step("Install frozen Code Review tools for final verdict")["run"])
    review = cast(str, _find_requirements_final_step("Run Code Review with trusted final Requirements context")["run"])
    assert setup["uses"] == "actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e"
    assert cast(dict[str, str], setup["with"])["node-version"] == "24.16.0"
    assert 'node_path="$(command -v node)"' in install
    assert '[[ "$node_path" =~ ^/[A-Za-z0-9._/-]+/node$ && -x "$node_path" ]]' in install
    assert 'test "$("$node_path" --version)" = "v24.16.0"' in install
    assert '[[ "$node_bin" == /* && -d "$node_bin" ]]' in install
    assert "FINAL_NODE_BIN=" in install
    assert "${FINAL_NODE_BIN}" in review
    assert 'test "$("${FINAL_NODE_BIN}/node" --version)" = "v24.16.0"' in review
    assert review.index("${FINAL_NODE_BIN}") < review.index("${FINAL_BASEDPYRIGHT_ROOT}/node_modules/.bin")


def test_requirements_final_review_prefers_full_verifier_python() -> None:
    """BasedPyright must inspect code with the frozen full verifier environment."""
    review = cast(str, _find_requirements_final_step("Run Code Review with trusted final Requirements context")["run"])
    path_clause = next(line for line in review.splitlines() if line.startswith("PATH="))
    assert path_clause.index("${FINAL_VERIFIER_ROOT}/bin") < path_clause.index(
        "${RUNNER_TEMP}/final-code-review-tools/bin"
    )


def test_requirements_final_review_persists_failure_before_enforcement() -> None:
    """A failing final review must retain its report without weakening the verdict."""
    workflow = _load_yaml(REQUIREMENTS_EVIDENCE)
    jobs = cast(dict[str, dict[str, Any]], workflow["jobs"])
    steps = cast(list[dict[str, Any]], jobs["requirements-evidence-final"]["steps"])
    review = _find_requirements_final_step("Run Code Review with trusted final Requirements context")
    upload = _find_requirements_final_step("Upload final Code Review evidence artifact")
    enforce = _find_requirements_final_step("Enforce final Code Review verdict")

    assert review["id"] == "run-final-code-review"
    assert review["continue-on-error"] is True
    assert upload["if"] == "always()"
    assert upload["uses"] == "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
    upload_options = cast(dict[str, str], upload["with"])
    assert upload_options["path"] == "${{ runner.temp }}/final-code-review.json"
    assert upload_options["if-no-files-found"] == "error"
    assert enforce["if"] == "steps.run-final-code-review.outcome == 'failure'"
    assert enforce["run"] == "exit 1"
    assert steps.index(review) < steps.index(upload) < steps.index(enforce)


def test_license_gate_runs_for_every_frozen_dependency_graph_change() -> None:
    """Transitive lock/export refreshes must receive the license policy gate."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    assert "license_inputs:" in raw
    assert "uv.lock" in raw
    assert "requirements/ci/locked.txt" in raw


def test_pr_orchestrator_uses_frozen_resolution_for_blocking_jobs() -> None:
    """Blocking CI must install declared dependencies from the committed lock."""
    assert UV_LOCK.is_file(), "A committed uv.lock is required for reproducible CI"
    for job_id in ("tests", "package-runtime-matrix", "type-checking", "package-validation", "reproducible-delivery"):
        steps = _load_job_steps(job_id)
        assert any(step.get("uses") == "./.github/actions/setup-frozen-python" for step in steps), job_id
        job_runs = "\n".join(str(step.get("run", "")) for step in steps)
        assert 'pip install -e ".[dev]"' not in job_runs


def test_reproducible_delivery_sbom_evidence_has_no_generator_dependency() -> None:
    """The delivery trust boundary must not execute an unreviewed SBOM package."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    assert "cyclonedx-py" not in raw
    assert "scripts/render_locked_sbom.py" in raw


def test_advisory_dependency_compatibility_lane_cannot_block_delivery() -> None:
    """Resolver drift evidence is scheduled/advisory rather than release input."""
    job = _load_jobs()["dependency-compatibility"]
    assert job.get("continue-on-error") is True
    assert "schedule" in str(job.get("if", ""))
    steps = _load_job_steps("dependency-compatibility")
    raw = "\n".join(str(step.get("run", "")) for step in steps)
    assert "uv lock --upgrade" in raw
    assert "uv sync --locked --all-extras --resolution lowest-direct" in raw
    assert any(step.get("name") == "Checkout module bundles repo" for step in steps)
    assert "SPECFACT_MODULES_REPO=${GITHUB_WORKSPACE}/specfact-cli-modules" in raw
    assert "--deselect=tests/unit/scripts/test_dependency_trust_review.py" in raw
    assert "--deselect=tests/unit/scripts/test_reproducible_delivery.py" in raw


def test_package_runtime_matrix_proves_all_declared_python_versions() -> None:
    """Locked built-wheel smoke must cover every supported Python interpreter."""
    job = _load_jobs()["package-runtime-matrix"]
    strategy = job.get("strategy")
    assert isinstance(strategy, dict)
    matrix = strategy.get("matrix")
    assert isinstance(matrix, dict)
    assert matrix.get("python-version") == ["3.11", "3.12", "3.13"]
    raw = "\n".join(str(step.get("run", "")) for step in _load_job_steps("package-runtime-matrix"))
    assert "--no-deps" in raw


def test_type_checking_explicitly_selects_pyproject_and_uploads_json() -> None:
    """CI must not rely on basedpyright configuration auto-discovery."""
    assert not (REPO_ROOT / "pyrightconfig.json").exists()
    basedpyright = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["basedpyright"]
    assert basedpyright["include"] == ["src", "tests", "tools", "scripts"]
    assert basedpyright["extraPaths"] == ["src"]
    assert basedpyright["typeCheckingMode"] == "standard"
    assert "**/node_modules/**" in basedpyright["exclude"]
    assert basedpyright["strict"] == [
        "scripts/check_dependency_trust_exceptions.py",
        "scripts/check_reproducible_delivery.py",
        "scripts/refresh_reproducible_delivery.py",
        "scripts/security_audit_gate.py",
    ]
    run_clause = str(_find_named_step("type-checking", "Run type checking").get("run") or "")
    assert "--project pyproject.toml" in run_clause
    assert "--outputjson" in run_clause
    upload_step = _find_named_step("type-checking", "Upload type-check logs")
    assert "json" in str(upload_step.get("with") or "").lower()


def test_type_runner_uses_pinned_node_and_committed_npm_lock() -> None:
    """BasedPyright must not acquire an executable Node runtime from PyPI."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    type_steps = _load_job_steps("type-checking")
    type_step_text = "\n".join(str(step.get("run", "")) for step in type_steps)
    assert "actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e" in raw
    assert "node-version: " in raw
    assert "npm ci --ignore-scripts --prefix tools/basedpyright" in type_step_text
    assert (REPO_ROOT / "tools" / "basedpyright" / "package-lock.json").is_file()
    pyproject_text = PYPROJECT.read_text(encoding="utf-8")
    assert '"basedpyright' not in pyproject_text
    assert "nodejs-wheel-binaries" not in UV_LOCK.read_text(encoding="utf-8")


def test_blocking_lint_has_no_pylint_or_dill_dependency() -> None:
    """Ruff replaces Pylint in CI so Dill is absent from the frozen Python graph."""
    raw = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dependencies = list(pyproject["project"].get("dependencies", []))
    for group in pyproject["project"].get("optional-dependencies", {}).values():
        dependencies.extend(group)
    lock_text = UV_LOCK.read_text(encoding="utf-8")
    assert not any(requirement.lower().startswith("pylint") for requirement in dependencies)
    assert "pylint src tests tools" not in raw
    assert 'name = "pylint"' not in lock_text
    assert 'name = "dill"' not in lock_text


def _assert_immutable_modules_fixture(raw: str) -> None:
    """Assert the shared immutable module-fixture safeguards for workflow text."""
    assert "ci/module-fixture.lock.json" in raw
    assert 'repository="$(python -c' in raw
    assert 'test "$repository" = "nold-ai/specfact-cli-modules"' in raw
    assert "steps.modules-fixture.outputs.repository" in raw
    assert "ref: ${{ steps.modules-fixture.outputs.commit }}" in raw
    assert "git -C specfact-cli-modules rev-parse HEAD" in raw
    assert "./.github/actions/setup-frozen-python" in raw
    assert "pip install" not in raw
    assert "git ls-remote --exit-code --heads https://github.com/nold-ai/specfact-cli-modules.git" not in raw


def test_docs_review_uses_immutable_modules_fixture_and_frozen_environment() -> None:
    """Docs command validation must not silently drift with branch or resolver state."""
    raw = DOCS_REVIEW.read_text(encoding="utf-8")
    _assert_immutable_modules_fixture(raw)
    assert "hatch run" not in raw


def test_specfact_contract_workflow_uses_immutable_modules_fixture_and_frozen_environment() -> None:
    """Standalone contract validation must not drift with branch or resolver state."""
    raw = SPECFACT_WORKFLOW.read_text(encoding="utf-8")
    _assert_immutable_modules_fixture(raw)
    assert "pip install -e" not in raw
    assert "SPECFACT_MODULES_REPO=${GITHUB_WORKSPACE}/specfact-cli-modules" in raw
    assert "SPECFACT_MODULES_ROOTS=${GITHUB_WORKSPACE}/specfact-cli-modules/packages" in raw
    assert "ref: ${{ (github.ref == 'refs/heads/main' || github.head_ref == 'main') && 'main' || 'dev' }}" not in raw


def test_module_signature_check_name_is_canonical_across_workflows() -> None:
    """Orchestrator and dedicated signature workflows should emit the same required check name."""
    orchestrator_jobs = _load_jobs()
    sign_modules = _load_yaml(SIGN_MODULES)
    sign_jobs = sign_modules.get("jobs")
    assert isinstance(sign_jobs, dict), "Expected jobs mapping in sign-modules workflow"
    orchestrator_name = orchestrator_jobs["verify-module-signatures"].get("name")
    sign_job = sign_jobs.get("verify")
    assert isinstance(sign_job, dict), "Expected verify job in sign-modules workflow"
    dedicated_name = sign_job.get("name")
    assert orchestrator_name == dedicated_name == "Verify Module Signatures"


def test_module_signing_remediation_commits_rerun_ci() -> None:
    """GitHub remediation commits must not suppress the checks that prove signatures are fixed."""
    sign_modules_raw = SIGN_MODULES.read_text(encoding="utf-8")
    approval_raw = (REPO_ROOT / ".github" / "workflows" / "sign-modules-on-approval.yml").read_text(encoding="utf-8")
    for raw in (sign_modules_raw, approval_raw):
        signing_commit_lines = [
            line for line in raw.splitlines() if "git commit -m" in line and "chore(modules):" in line
        ]
        assert signing_commit_lines, "Expected module-signing remediation commit lines"
        assert all("[skip ci]" not in line for line in signing_commit_lines)


def test_publish_modules_entry_summary_avoids_escaped_fstring_expression() -> None:
    """Bundled publishing must not use a python -c f-string with shell-escaped quotes."""
    raw = PUBLISH_MODULES.read_text(encoding="utf-8")
    assert "PY_ENTRY_SUMMARY=" not in raw
    assert "python - \"${FRAGMENT}\" <<'PY'" in raw
    assert "data['id']" in raw
    assert "data['latest_version']" in raw


def test_publish_modules_bundled_snapshot_targets_core_repository() -> None:
    """Bundled snapshot entries for core modules must not inherit the marketplace URL base."""
    raw = PUBLISH_MODULES.read_text(encoding="utf-8")
    expected_base = "BUNDLED_REGISTRY_DOWNLOAD_BASE_URL: https://github.com/nold-ai/specfact-cli/releases/download"
    assert raw.count(expected_base) == 2
    assert (
        "BUNDLED_REGISTRY_DOWNLOAD_BASE_URL: https://github.com/nold-ai/specfact-cli-modules/releases/download"
        not in raw
    )

    publish_blocks = [block for block in raw.split("\n\n") if "scripts/publish-module.py" in block]
    assert publish_blocks, "Expected publish-modules workflow to package module artifacts"
    for block in publish_blocks:
        assert "--download-base-url" in block, "Bundled publish calls must set the snapshot URL base"
        assert "${BUNDLED_REGISTRY_DOWNLOAD_BASE_URL}" in block
        if "--index-fragment" in block:
            assert "--download-base-url" in block, "Registry fragments must set the bundled snapshot URL base"
            assert "${BUNDLED_REGISTRY_DOWNLOAD_BASE_URL}" in block


def _assert_module_release_identity(raw: str) -> None:
    assert 'RELEASE_TAG="${MODULE_SLUG}-v${MODULE_VERSION}"' in raw
    assert 'RELEASE_TAG="${{ steps.entry.outputs.module_slug }}-v${{ steps.entry.outputs.module_version }}"' in raw
    assert '--download-base-url "${BUNDLED_REGISTRY_DOWNLOAD_BASE_URL}/${RELEASE_TAG}"' in raw
    assert raw.count('git merge-base --is-ancestor "${SOURCE_SHA}"') >= 2


def _assert_module_release_retry_safety(raw: str) -> None:
    assert raw.count('gh release create "${RELEASE_TAG}"') >= 2
    assert raw.count('gh release download "${RELEASE_TAG}"') >= 2
    assert "scripts/sign-modules.py" not in raw
    assert "SPECFACT_MODULE_PRIVATE_SIGN_KEY" not in raw
    assert raw.count('git diff --exit-code -- "${MODULE_PATH}"') >= 1
    assert raw.count('git diff --exit-code -- "${MODULE_DIR}"') >= 1
    assert raw.count("--verify-tag") >= 2
    assert '--target "${SOURCE_SHA}"' not in raw
    assert 'git push origin "${SOURCE_SHA}:refs/tags/${RELEASE_TAG}"' in raw
    assert "Release creation did not succeed; verifying an existing immutable release." in raw


def _assert_module_release_precedes_snapshot(raw: str) -> None:
    for publication_block in raw.split("python scripts/update-registry-index.py")[:-1]:
        assert publication_block.rfind('gh release download "${RELEASE_TAG}"') > publication_block.rfind(
            'gh release create "${RELEASE_TAG}"'
        )
        assert publication_block.rfind('sha256sum "${DOWNLOADED_ASSET}"') > publication_block.rfind(
            'gh release download "${RELEASE_TAG}"'
        )


def _publish_module_steps_by_name() -> dict[str, dict[str, Any]]:
    workflow = _load_yaml(PUBLISH_MODULES)
    jobs = cast(dict[str, Any], workflow["jobs"])
    publish = cast(dict[str, Any], jobs["publish"])
    steps = cast(list[dict[str, Any]], publish["steps"])
    return {str(step.get("name", "")): step for step in steps}


def _assert_publication_source_is_authenticated_first(steps_by_name: dict[str, dict[str, Any]]) -> None:
    step_names = list(steps_by_name)
    assert "Authenticate protected source" in step_names
    authentication_index = step_names.index("Authenticate protected source")
    protected_steps = ("Set up Python", "Install dependencies", "Verify checked-in module manifests (strict policy)")
    assert all(authentication_index < step_names.index(step) for step in protected_steps)


def _assert_candidate_publication_values_are_environment_bound(steps_by_name: dict[str, dict[str, Any]]) -> None:
    run_scripts = "\n".join(str(step.get("run", "")) for step in steps_by_name.values())
    candidate_expressions = (
        "${{ github.event.inputs.module_path }}",
        "${{ steps.resolve.outputs.module_path }}",
        "${{ steps.entry.outputs.module_id }}",
        "${{ steps.entry.outputs.module_slug }}",
        "${{ steps.entry.outputs.module_version }}",
    )
    assert "Resolve module path (manual)" not in steps_by_name
    assert all(expression not in run_scripts for expression in candidate_expressions)


def _assert_one_validated_module_path_is_reused(steps_by_name: dict[str, dict[str, Any]]) -> None:
    resolver = steps_by_name["Resolve and validate module path"]
    resolver_env = cast(dict[str, str], resolver["env"])
    assert resolver_env["INPUT_MODULE_PATH"] == "${{ github.event.inputs.module_path }}"
    assert resolver_env["TAG_MODULE_PATH"] == "${{ steps.resolve.outputs.module_path }}"
    resolver_script = str(resolver["run"])
    assert all(
        boundary in resolver_script
        for boundary in ("resolve(strict=True)", "allowed_roots", "module-package.yaml", "is_symlink()")
    )
    for consumer_name in ("Read module metadata", "Package module"):
        consumer = steps_by_name[consumer_name]
        consumer_env = cast(dict[str, str], consumer["env"])
        assert consumer_env["MODULE_PATH"] == "${{ steps.module.outputs.module_path }}"
        assert '"${MODULE_PATH}"' in str(consumer["run"])


def test_publish_modules_verifies_release_asset_before_snapshot_update() -> None:
    """Bundled metadata may advance only after a protected, tag-qualified asset is verified."""
    raw = PUBLISH_MODULES.read_text(encoding="utf-8")
    _assert_module_release_identity(raw)
    _assert_module_release_retry_safety(raw)
    _assert_module_release_precedes_snapshot(raw)
    publish_steps = _publish_module_steps_by_name()
    _assert_publication_source_is_authenticated_first(publish_steps)
    _assert_candidate_publication_values_are_environment_bound(publish_steps)
    _assert_one_validated_module_path_is_reused(publish_steps)


CANONICAL_VERSION_SOURCE_REGEX = r"^(pyproject\.toml|setup\.py|src/__init__\.py|src/specfact_cli/__init__\.py)$"


def _assert_pre_commit_verify_and_version_hooks(by_id: dict[str, dict[str, Any]]) -> None:
    verify_hook = by_id["verify-module-signatures"]
    assert verify_hook.get("always_run") is True
    assert verify_hook.get("language") == "script"
    verify_entry = str(verify_hook.get("entry", ""))
    assert "pre-commit-verify-modules" in verify_entry
    assert "pre-commit-verify-modules.sh" in verify_entry or "pre-commit-verify-modules-signature.sh" in verify_entry
    verify_script = REPO_ROOT / "scripts" / "pre-commit-verify-modules.sh"
    assert verify_script.is_file()
    legacy_verify = REPO_ROOT / "scripts" / "pre-commit-verify-modules-signature.sh"
    assert legacy_verify.is_file()
    verify_body = verify_script.read_text(encoding="utf-8")
    assert "module-verify-policy.sh" in verify_body
    assert "exec hatch run verify-modules-signature" in verify_body
    assert "exec hatch run verify-modules-signature-pr" in verify_body
    assert "check-version-sources" in by_id
    assert "check-local-version-ahead-of-pypi" in by_id


def _assert_pypi_version_hook(by_id: dict[str, dict[str, Any]]) -> None:
    pypi_hook = by_id["check-local-version-ahead-of-pypi"]
    files_pattern = pypi_hook.get("files")
    assert files_pattern == CANONICAL_VERSION_SOURCE_REGEX, (
        "PyPI-ahead pre-commit hook 'files:' scope must match the canonical version-source set "
        f"({CANONICAL_VERSION_SOURCE_REGEX!r}); got {files_pattern!r}"
    )
    entry = str(pypi_hook.get("entry", ""))
    assert "hatch run python scripts/check_local_version_ahead_of_pypi.py" in entry


def test_pr_orchestrator_package_validation_waits_for_dependency_gates() -> None:
    jobs = _load_jobs()
    package_validation = jobs.get("package-validation")
    assert package_validation is not None, "Expected package-validation job in pr-orchestrator"
    needs = package_validation.get("needs")
    assert isinstance(needs, list), "Expected package-validation needs list"
    assert "license-check" in needs
    assert "security-audit" in needs
    assert "dependency-trust" in needs


def test_license_gate_audits_the_frozen_code_review_environment() -> None:
    """Isolated review tools remain inside the blocking GPL/AGPL policy boundary."""
    workflow = PR_ORCHESTRATOR.read_text(encoding="utf-8")
    assert "requirements/code-review/requirements.in" in workflow
    assert "requirements/code-review/locked.txt" in workflow
    steps = _load_job_steps("license-check")
    commands = "\n".join(str(step.get("run", "")) for step in steps)
    assert "uv pip install" in commands
    assert "requirements/code-review/locked.txt" in commands
    assert "--code-review-python" in commands
    assert "--additional-python" not in commands


def test_dependency_trust_is_a_standalone_ci_and_pre_commit_gate() -> None:
    """Known alerted releases must be blocked locally and by a visible CI status."""
    jobs = _load_jobs()
    dependency_trust = jobs.get("dependency-trust")
    assert dependency_trust is not None
    assert dependency_trust.get("name") == "Dependency Trust Gate"
    assert "if" not in dependency_trust
    steps = _load_job_steps("dependency-trust")
    assert any(step.get("uses") == "./.github/actions/setup-frozen-python" for step in steps)
    commands = "\n".join(str(step.get("run", "")) for step in steps)
    assert "scripts/check_dependency_trust_exceptions.py" in commands
    assert "scripts/check_reproducible_delivery.py" in commands

    hooks = _load_hooks()
    by_id = {str(hook["id"]): hook for hook in hooks}
    trust_hook = by_id["dependency-trust-gate"]
    assert trust_hook.get("pass_filenames") is False
    assert trust_hook.get("entry") == "hatch run python scripts/check_dependency_trust_exceptions.py"
    assert "uv\\.lock" in str(trust_hook.get("files", ""))


def test_frozen_cve_audit_is_a_standalone_ci_and_pre_commit_gate() -> None:
    """The advisory database must audit every committed frozen requirements graph."""
    steps = _load_job_steps("security-audit")
    commands = "\n".join(str(step.get("run", "")) for step in steps)
    assert "scripts/security_audit_gate.py" in commands
    assert "--requirement requirements/code-review/locked.txt" in commands

    hooks = _load_hooks()
    by_id = {str(hook["id"]): hook for hook in hooks}
    cve_hook = by_id["frozen-cve-audit"]
    assert cve_hook.get("pass_filenames") is False
    assert cve_hook.get("entry") == "hatch run security-audit"
    assert "requirements/ci/locked" in str(cve_hook.get("files", ""))
    assert "requirements/code-review/" in str(cve_hook.get("files", ""))
    assert "vulnerability-audit-exceptions" in str(cve_hook.get("files", ""))
    hatch_scripts = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["hatch"]["envs"]["default"]["scripts"]
    assert "--requirement requirements/code-review/locked.txt" in hatch_scripts["security-audit"]


def _assert_docs_dependabot_monitoring() -> None:
    dependabot = _load_yaml(DEPENDABOT_CONFIG)
    updates = dependabot.get("updates")
    assert isinstance(updates, list)
    assert any(
        isinstance(item, dict) and item.get("package-ecosystem") == "bundler" and item.get("directory") == "/docs"
        for item in updates
    )


def _docs_review_security_step() -> dict[str, Any]:
    workflow = _load_yaml(DOCS_REVIEW)
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    docs_review = jobs.get("docs-review")
    assert isinstance(docs_review, dict)
    steps = docs_review.get("steps")
    assert isinstance(steps, list)
    security_step = next(
        (
            step
            for step in steps
            if isinstance(step, dict) and step.get("name") == "Validate docs dependency security floor"
        ),
        None,
    )
    assert isinstance(security_step, dict)
    return security_step


def _assert_docs_lock_pre_commit_gate() -> None:
    hooks = {str(hook["id"]): hook for hook in _load_hooks()}
    docs_lock_hook = hooks["docs-gem-lock-security"]
    assert "test_docs_json_gem_uses_the_patched_security_floor" in str(docs_lock_hook.get("entry", ""))
    assert "docs/Gemfile" in str(docs_lock_hook.get("files", ""))


def test_docs_ruby_lock_has_dependabot_and_security_floor_gates() -> None:
    """The docs lock must receive update PRs and enforce known security floors."""
    _assert_docs_dependabot_monitoring()
    security_step = _docs_review_security_step()
    assert "test_docs_json_gem_uses_the_patched_security_floor" in str(security_step.get("run", ""))
    _assert_docs_lock_pre_commit_gate()


def test_semgrep_mcp_server_is_not_invoked_by_project_automation() -> None:
    """The Semgrep SAST integration must not activate its separately exposed MCP server."""
    invocation_surfaces = (
        PYPROJECT,
        REPO_ROOT / ".github",
        PRE_COMMIT_CONFIG,
        REPO_ROOT / "scripts",
        REPO_ROOT / "src",
    )
    for surface in invocation_surfaces:
        if surface.is_file():
            contents = surface.read_text(encoding="utf-8")
        else:
            contents = "\n".join(
                path.read_text(encoding="utf-8", errors="ignore")
                for path in surface.rglob("*")
                if path.is_file() and path.suffix in {".py", ".sh", ".toml", ".yml", ".yaml"}
            )
        assert "semgrep mcp" not in contents.lower(), f"{surface} must not start Semgrep's MCP server"


def test_frozen_setup_checks_dependency_trust_before_synchronizing() -> None:
    """Every shared frozen setup rejects unsafe lock input before installation."""
    action = REPO_ROOT / ".github" / "actions" / "setup-frozen-python" / "action.yml"
    content = action.read_text(encoding="utf-8")

    assert content.index("python scripts/check_dependency_trust_exceptions.py") < content.index(
        "uv sync --locked --all-extras"
    )


def _assert_pre_commit_cli_quality_block_hooks(by_id: dict[str, dict[str, Any]]) -> None:
    hook_ids = (
        "cli-block1-format",
        "cli-block1-yaml",
        "cli-block1-markdown-fix",
        "cli-block1-markdown-lint",
        "cli-block1-workflows",
        "cli-block1-lint",
        "cli-block2",
    )
    for hid in hook_ids:
        assert hid in by_id
        entry = by_id[hid].get("entry", "")
        assert "pre-commit-quality-checks.sh" in str(entry), f"{hid} must invoke quality-checks script"
    assert by_id["cli-block1-format"].get("always_run") is not True
    assert by_id["cli-block1-format"].get("files")
    assert by_id["cli-block2"].get("always_run") is True
    assert "check-doc-frontmatter" in by_id


def test_pre_commit_config_matches_modular_quality_layout() -> None:
    """Local hooks should mirror specfact-cli-modules: fail_fast, verify, block1 stages, block2."""
    config = _load_yaml(PRE_COMMIT_CONFIG)
    assert config.get("fail_fast") is True
    hooks = _load_hooks()
    by_id: dict[str, dict[str, Any]] = {}
    for h in hooks:
        hid = h.get("id")
        if isinstance(hid, str):
            by_id[hid] = h
    _assert_pre_commit_verify_and_version_hooks(by_id)
    _assert_pypi_version_hook(by_id)
    _assert_pre_commit_cli_quality_block_hooks(by_id)


def test_coderabbit_auto_review_covers_dev_and_main() -> None:
    """Automatic review coverage should be consistent for both protected integration branches."""
    config = _load_yaml(CODERABBIT_CONFIG)
    reviews = config.get("reviews")
    assert isinstance(reviews, dict), "Expected reviews block in .coderabbit.yaml"
    auto_review = reviews.get("auto_review")
    assert isinstance(auto_review, dict), "Expected auto_review block in .coderabbit.yaml"
    base_branches = auto_review.get("base_branches")
    assert isinstance(base_branches, list), "Expected base_branches list in .coderabbit.yaml"
    assert "^dev$" in base_branches
    assert "^main$" in base_branches


def test_legacy_actionlint_runner_does_not_mask_docker_failures() -> None:
    """The legacy actionlint wrapper must fail cleanly when Docker is unusable."""
    raw = LEGACY_ACTIONLINT_RUNNER.read_text(encoding="utf-8")
    lines = raw.splitlines()
    assert any("docker run --rm" in line for line in lines), "Expected docker run invocation"
    assert "docker info >/dev/null 2>&1" in raw, "Expected docker daemon reachability check"
    assert "tools/bin" not in raw, "Should not download binaries into repo tree"
    assert "go install github.com/rhysd/actionlint/cmd/actionlint@" in raw, "Expected global install guidance"
    # Both execution paths (local binary and docker) must propagate exit codes
    assert raw.count("exit $?") >= 2, "Expected exit code propagation for both local and docker paths"
