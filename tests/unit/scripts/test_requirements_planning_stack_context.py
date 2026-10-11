"""Exercise planning boundaries through the real CLI and immutable Git objects."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest


REPOSITORY = "nold-ai/specfact-cli"
REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT_SOURCE = "openspec/changes/root-security/"
PLANNING_PATH = "openspec/changes/deferred-feature/proposal.md"
CHECK_ROUTE = "/repos/" + REPOSITORY + "/commits/{root}/check-runs?filter=all&per_page=100&page=1"
WORKFLOWS = (
    ("Requirements evidence", "Requirements Evidence", 323253915, "requirements-evidence.yml", 1101, 2101),
    (
        "Trusted Requirements Authority",
        "Trusted Requirements Authority",
        348163848,
        "trusted-requirements-authority.yml",
        1102,
        2102,
    ),
)


@dataclass
class StackCase:
    """Owned synthetic repository and independently supplied GitHub responses."""

    repo: Path
    baseline: str
    root: str
    child: str
    event: dict[str, Any]
    routes: dict[str, Any]


def _git(repo: Path, *arguments: str) -> str:
    """Run Git only inside the caller-isolated fixture repository."""
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout.strip()


def _commit(repo: Path, path: str, content: str) -> str:
    """Create an unsigned synthetic fixture commit, never a publication commit."""
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    _git(repo, "add", "--", path)
    _git(repo, "-c", "commit.gpgsign=false", "commit", "-m", "fixture")
    return _git(repo, "rev-parse", "HEAD")


def _run_record(root: str, workflow: tuple[str, str, int, str, int, int]) -> dict[str, Any]:
    """Supply immutable run identity separately from check metadata."""
    _, run_name, workflow_id, workflow_path, run_id, _ = workflow
    repository = {"id": 1085706003, "full_name": REPOSITORY}
    return {
        "id": run_id,
        "run_attempt": 1,
        "name": run_name,
        "workflow_id": workflow_id,
        "path": ".github/workflows/" + workflow_path,
        "event": "pull_request",
        "head_sha": root,
        "head_branch": "dependency-root",
        "status": "completed",
        "conclusion": "success",
        "repository": repository,
        "head_repository": repository,
        "check_suite_id": run_id + 10000,
        "pull_requests": [{"number": 744, "head": {"sha": "f" * 40}}],
    }


def _check_record(root: str, workflow: tuple[str, str, int, str, int, int]) -> dict[str, Any]:
    """Keep check issuer, exact SHA and run/job binding explicit."""
    check_name, _, _, _, run_id, check_id = workflow
    return {
        "id": check_id,
        "name": check_name,
        "head_sha": root,
        "app": {"id": 15368, "slug": "github-actions"},
        "status": "completed",
        "conclusion": "success",
        "details_url": f"https://github.com/{REPOSITORY}/actions/runs/{run_id}/job/{check_id}",
        "check_suite": {"id": run_id + 10000},
    }


def _proof_routes(root: str) -> dict[str, Any]:
    """Model GitHub-owned checks and runs without candidate evidence labels."""
    checks = [_check_record(root, workflow) for workflow in WORKFLOWS]
    routes = {f"/repos/{REPOSITORY}/actions/runs/{workflow[4]}": _run_record(root, workflow) for workflow in WORKFLOWS}
    routes[f"/repos/{REPOSITORY}/commits/{root}"] = {
        "sha": root,
        "commit": {"verification": {"verified": True}},
    }
    routes[CHECK_ROUTE.format(root=root)] = {"total_count": len(checks), "check_runs": checks}
    return routes


def _case(repo: Path, baseline: str, root: str, child: str) -> StackCase:
    """Bind the existing native ancestry fixture to actual commit objects."""
    text = (REPO_ROOT / "tests/fixtures/native_stack_context.json").read_text()
    for original, replacement in (("a" * 40, baseline), ("b" * 40, root), ("c" * 40, child)):
        text = text.replace(original, replacement)
    payload = json.loads(text)
    routes = payload["routes"]
    routes.update(_proof_routes(root))
    return StackCase(repo, baseline, root, child, payload["event"], routes)


@pytest.fixture
def planning_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> StackCase:
    """Own every Git mutation and ignore inherited worktree/configuration selectors."""
    for name in tuple(os.environ):
        if name.startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    repo = tmp_path / "owned-repository"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=fixture")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    baseline = _commit(repo, ".github/workflows/requirements-evidence.yml", "protected proof workflow\n")
    _commit(repo, "src/runtime.py", "baseline\n")
    baseline = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "src/runtime.py", "security fix\n")
    root = _commit(repo, ROOT_SOURCE + "specs/security/spec.md", "security contract\n")
    child = _commit(repo, PLANNING_PATH, "deferred planning\n")
    monkeypatch.chdir(repo)
    return _case(repo, baseline, root, child)


def _resolve(case: StackCase, monkeypatch: pytest.MonkeyPatch) -> tuple[int, dict[str, Any]]:
    """Execute the public isolated CLI with a caller-owned GitHub response executable."""
    executable_dir = case.repo / "github-fixture-bin"
    executable_dir.mkdir(exist_ok=True)
    (executable_dir / "api-routes.json").write_text(json.dumps(case.routes))
    github = executable_dir / "gh"
    github.write_text(
        f"#!{sys.executable}\n"
        "import json, sys\nfrom pathlib import Path\n"
        "routes = json.loads(Path(sys.argv[0]).with_name('api-routes.json').read_text())\n"
        "print(json.dumps(routes[sys.argv[-1]]))\n"
    )
    github.chmod(0o755)
    event = case.repo / "event.json"
    output = case.repo / "context.json"
    output.unlink(missing_ok=True)
    event.write_text(json.dumps(case.event))
    environment = os.environ.copy()
    environment["PATH"] = str(executable_dir) + os.pathsep + environment.get("PATH", "")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            str(REPO_ROOT / "scripts/requirements_stack_context.py"),
            "--event",
            str(event),
            "--output",
            str(output),
        ],
        cwd=case.repo,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, json.loads(output.read_text()) if output.exists() else {}


def _planning_context(case: StackCase, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Require separate planning selection while preserving validator and native ancestry."""
    result, context = _resolve(case, monkeypatch)
    assert result == 0
    assert context.get("planning_base_commit") == case.root
    assert context["proof_base_commit"] == case.baseline
    assert context["proof_head_commit"] == case.root
    assert context["head_commit"] == case.child
    return context


def test_verified_planning_child_preserves_protected_trust_and_maturities(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A signed, independently verified runtime root permits only post-root planned evidence."""
    context = _planning_context(planning_case, monkeypatch)
    proof = context["inherited_proof"]
    assert proof["head_commit"] == planning_case.root
    assert {record["check_id"] for record in proof["checks"]} == {2101, 2102}
    assert {record["run_attempt"] for record in proof["checks"]} == {1}
    assert [member["pull_request"] for member in context["members"]] == [744, 727]


def test_runtime_and_inherited_source_changes_keep_complete_proof(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Eligible planning cannot launder a subsequent executable or inherited-source edit."""
    _planning_context(planning_case, monkeypatch)
    paths = [
        "src/runtime.py",
        "tests/test_runtime.py",
        "scripts/check.py",
        "ci/lock.json",
        ".github/workflows/requirements-evidence.yml",
        "requirements/ci/locked.txt",
        "pyproject.toml",
        "openspec/config.yaml",
        "openspec/specs/security/spec.md",
        ROOT_SOURCE + "requirements-evidence.yaml",
        ROOT_SOURCE + "proposal.md",
    ]
    for path in paths:
        _git(planning_case.repo, "checkout", "--detach", planning_case.child)
        head = _commit(planning_case.repo, path, "changed boundary\n")
        changed = _case(planning_case.repo, planning_case.baseline, planning_case.root, head)
        result, context = _resolve(changed, monkeypatch)
        assert result == 0, path
        assert "planning_base_commit" not in context, path
        assert context["proof_base_commit"] == planning_case.baseline


def test_forged_or_stale_root_checks_fail_before_evidence(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stack membership does not replace exact root check, run, signature or app identities."""
    route = CHECK_ROUTE.format(root=planning_case.root)
    for key, replacement in (
        ("conclusion", "failure"),
        ("status", "in_progress"),
        ("head_sha", "f" * 40),
        ("app", {"id": 99, "slug": "other"}),
        ("details_url", "https://example.invalid/actions/runs/1101/job/2101"),
    ):
        case = copy.deepcopy(planning_case)
        case.routes[route]["check_runs"][0][key] = replacement
        result, context = _resolve(case, monkeypatch)
        assert result != 0, key
        assert not context
    for key, replacement in (
        ("workflow_id", 99),
        ("path", ".github/workflows/other.yml"),
        ("head_sha", "f" * 40),
        ("head_branch", "foreign"),
        ("event", "workflow_dispatch"),
        ("repository", {"id": 99}),
        ("check_suite_id", 99),
        ("run_attempt", 0),
        ("pull_requests", [{"number": 999}]),
    ):
        case = copy.deepcopy(planning_case)
        case.routes[f"/repos/{REPOSITORY}/actions/runs/1101"][key] = replacement
        assert _resolve(case, monkeypatch)[0] != 0, key
    case = copy.deepcopy(planning_case)
    case.routes[f"/repos/{REPOSITORY}/commits/{case.root}"]["commit"]["verification"]["verified"] = False
    assert _resolve(case, monkeypatch)[0] != 0
    case = copy.deepcopy(planning_case)
    case.routes[route]["check_runs"] = []
    case.routes[route]["total_count"] = 0
    assert _resolve(case, monkeypatch)[0] != 0


def _stage_non_regular_change(case: StackCase, mode: str) -> None:
    """Stage one real mode, payload or inherited-source mutation."""
    target = case.repo / PLANNING_PATH
    if mode == "executable":
        target.chmod(0o755)
        _git(case.repo, "update-index", "--chmod=+x", PLANNING_PATH)
        return
    if mode == "symlink":
        target.unlink()
        target.symlink_to("../../../../src/runtime.py")
        _git(case.repo, "add", "--", PLANNING_PATH)
        return
    if mode == "payload":
        payload = case.repo / "openspec/changes/deferred-feature/payload.bin"
        payload.write_bytes(b"\x00\x01")
        _git(case.repo, "add", "--", str(payload.relative_to(case.repo)))
        return
    if mode == "source-deletion":
        _git(case.repo, "rm", "--", ROOT_SOURCE + "specs/security/spec.md")
        return
    if mode != "source-move":
        raise ValueError(mode)
    _git(
        case.repo,
        "mv",
        "--",
        ROOT_SOURCE + "specs/security/spec.md",
        "openspec/changes/deferred-feature/moved.md",
    )


def test_non_regular_planning_paths_keep_complete_proof(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenSpec naming cannot authorize executable, symlink or opaque payload bytes."""
    _planning_context(planning_case, monkeypatch)
    for mode in ("executable", "symlink", "payload", "source-deletion", "source-move"):
        _git(planning_case.repo, "checkout", "--detach", planning_case.child)
        _stage_non_regular_change(planning_case, mode)
        _git(planning_case.repo, "-c", "commit.gpgsign=false", "commit", "-m", "fixture boundary")
        changed = _case(
            planning_case.repo,
            planning_case.baseline,
            planning_case.root,
            _git(planning_case.repo, "rev-parse", "HEAD"),
        )
        result, context = _resolve(changed, monkeypatch)
        assert result == 0, mode
        assert "planning_base_commit" not in context, mode


def test_latest_failed_root_check_cannot_reuse_older_success(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A newer failed check must win even if an older successful check remains listed."""
    route = CHECK_ROUTE.format(root=planning_case.root)
    latest = copy.deepcopy(planning_case.routes[route]["check_runs"][0])
    latest.update(id=3101, conclusion="failure")
    planning_case.routes[route]["check_runs"].append(latest)
    planning_case.routes[route]["total_count"] += 1
    assert _resolve(planning_case, monkeypatch)[0] != 0


def test_root_modified_proof_workflow_cannot_authorize_planning(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Successful candidate-modified proof CI is not protected inherited proof."""
    _git(planning_case.repo, "checkout", "--detach", planning_case.root)
    root = _commit(planning_case.repo, ".github/workflows/requirements-evidence.yml", "candidate success\n")
    head = _commit(planning_case.repo, PLANNING_PATH, "deferred proposal\n")
    changed = _case(planning_case.repo, planning_case.baseline, root, head)
    result, context = _resolve(changed, monkeypatch)
    assert result == 0
    assert "planning_base_commit" not in context


def _step_script(job: dict[str, Any], key: str, value: str) -> str:
    """Select a named workflow step's script for trust-boundary assertions."""
    for step in job["steps"]:
        if step.get(key) == value:
            return cast(str, step["run"])
    raise AssertionError(value)


def test_all_consumers_separate_planning_selection_from_protected_verifier_trust() -> None:
    """All consumers agree without moving the validator trust base."""
    import yaml

    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/requirements-evidence.yml").read_text())
    selections = {
        "requirements-evidence-producer": "Run Requirements evidence gate",
        "requirements-evidence": "Reconcile Requirements evidence on fresh runner",
        "requirements-evidence-final": "Reconcile final Requirements verdict on fresh runner",
    }
    for job_name, selection_name in selections.items():
        job = workflow["jobs"][job_name]
        authentication = _step_script(job, "id", "stack-context")
        selection = _step_script(job, "name", selection_name)
        assert "PLANNING_BASE_COMMIT" in authentication, job_name
        assert "scripts/requirements_planning_context.py" in authentication, job_name
        assert 'policy_ref="origin/dev"' in authentication, job_name
        assert "PLANNING_BASE_COMMIT" in selection, job_name
        assert '--base-ref "$evidence_base_commit"' in selection, job_name
    materialization = _step_script(
        workflow["jobs"]["requirements-evidence-final"], "name", "Materialize trusted final Requirements core"
    )
    assert 'base_commit="$PROOF_BASE_COMMIT"' in materialization
    assert "PLANNING_BASE_COMMIT" not in materialization
    assert "FINAL_BASE_COMMIT=%s" in materialization


def test_root_proof_checks_on_later_api_pages_are_authenticated(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Complete pagination finds required checks and rejects duplicated or truncated pages."""
    route = CHECK_ROUTE.format(root=planning_case.root)
    required = planning_case.routes[route]["check_runs"]
    unrelated = [{"id": 4000 + index, "name": "Other check"} for index in range(100)]
    planning_case.routes[route] = {"total_count": 102, "check_runs": unrelated}
    second_page = route.removesuffix("page=1") + "page=2"
    planning_case.routes[second_page] = {"total_count": 102, "check_runs": required}
    _planning_context(planning_case, monkeypatch)
    duplicate = copy.deepcopy(planning_case)
    duplicate.routes[second_page]["check_runs"].append(copy.deepcopy(unrelated[0]))
    for page in (route, second_page):
        duplicate.routes[page]["total_count"] = 103
    assert {record["name"] for record in duplicate.routes[second_page]["check_runs"]} >= {
        "Requirements evidence",
        "Trusted Requirements Authority",
    }
    assert _resolve(duplicate, monkeypatch)[0] != 0
    truncated = copy.deepcopy(planning_case)
    truncated.routes[route]["check_runs"] = unrelated[:50]
    assert _resolve(truncated, monkeypatch)[0] != 0


def test_direct_protected_root_never_receives_planning_override(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Direct protected-base and promotion heads retain their original proof boundary."""
    parent_route = "/repos/nold-ai/specfact-cli/pulls?state=open&head=nold-ai%3Adependency-root&per_page=100"
    root_pull = planning_case.routes[parent_route][0]
    planning_case.routes["/repos/nold-ai/specfact-cli/pulls/744"] = root_pull
    planning_case.event["pull_request"] = root_pull
    result, context = _resolve(planning_case, monkeypatch)
    assert result == 0
    assert context["head_commit"] == planning_case.root
    assert context["proof_base_commit"] == planning_case.baseline
    assert "planning_base_commit" not in context


def test_existing_planning_document_type_change_retains_full_proof(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A real Git type-change entry falls back to complete proof rather than parsing as planning."""
    _git(planning_case.repo, "checkout", "--detach", planning_case.baseline)
    baseline = _commit(planning_case.repo, PLANNING_PATH, "existing planning\n")
    _commit(planning_case.repo, "src/runtime.py", "security fix\n")
    root = _commit(planning_case.repo, ROOT_SOURCE + "specs/security/spec.md", "security contract\n")
    target = planning_case.repo / PLANNING_PATH
    target.unlink()
    target.symlink_to("../../../../src/runtime.py")
    _git(planning_case.repo, "add", "--", PLANNING_PATH)
    _git(planning_case.repo, "-c", "commit.gpgsign=false", "commit", "-m", "fixture type change")
    case = _case(planning_case.repo, baseline, root, _git(planning_case.repo, "rev-parse", "HEAD"))
    result, context = _resolve(case, monkeypatch)
    assert result == 0
    assert "planning_base_commit" not in context
    assert context["proof_base_commit"] == baseline


def test_non_ascii_paths_retain_complete_proof(planning_case: StackCase, monkeypatch: pytest.MonkeyPatch) -> None:
    """A legitimate filename outside the planning allowlist must retain full proof."""
    for path in ("docs/café.md", "openspec/changes/deferred-feature/café.md"):
        _git(planning_case.repo, "checkout", "--detach", planning_case.child)
        case = copy.deepcopy(planning_case)
        case.child = _commit(case.repo, path, "unsupported planning filename\n")
        case = _case(case.repo, case.baseline, case.root, case.child)
        result, context = _resolve(case, monkeypatch)
        assert result == 0
        assert "planning_base_commit" not in context
        assert context["proof_base_commit"] == case.baseline
