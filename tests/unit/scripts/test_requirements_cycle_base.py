"""Security boundary coverage for verified Requirements amendment cycles."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Protocol


REPO_ROOT = Path(__file__).resolve().parents[3]
CYCLE_BASE_SCRIPT = REPO_ROOT / "scripts" / "requirements_cycle_base.py"


class CycleBasePathsLike(Protocol):
    """Path surface consumed by negative authority helpers."""

    run: Path


class CycleBaseContextLike(Protocol):
    """Context surface preserved while replacing the final Git head."""

    base_ref: str
    final_ref: str
    repository: str
    pull_request: int
    head_branch: str
    change_id: str


def _load_cycle_base_module() -> ModuleType:
    assert CYCLE_BASE_SCRIPT.is_file(), "verified amendment-cycle authority is not implemented"
    loaded = sys.modules.get("requirements_cycle_base")
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location("requirements_cycle_base", CYCLE_BASE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(repo_root: Path, *arguments: str) -> str:
    result = _load_cycle_base_module()._git(repo_root, *arguments)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _commit(repo_root: Path, message: str) -> str:
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "--no-gpg-sign", "-m", message)
    return _git(repo_root, "rev-parse", "HEAD")


def _initialize_history(root: Path, *, self_authored_authority: bool = False) -> tuple[Path, str, str, str]:
    repository = root / "repository"
    repository.mkdir()
    _git(repository, "-c", "init.templateDir=", "init")
    _git(repository, "config", "core.hooksPath", "/dev/null")
    _git(repository, "config", "user.email", "requirements@example.test")
    _git(repository, "config", "user.name", "Requirements proof")
    (repository / "README.md").write_text("# base\n", encoding="utf-8")
    base_ref = _commit(repository, "base")
    delivery_path = (
        repository / "scripts" / "requirements_proof_provenance.py"
        if self_authored_authority
        else repository / "src" / "runtime.py"
    )
    delivery_path.parent.mkdir()
    delivery_path.write_text("VALUE = 1\n", encoding="utf-8")
    cycle_ref = _commit(repository, "verified implementation")
    (repository / "tests").mkdir()
    (repository / "tests" / "test_review.py").write_text("def test_review(): assert False\n", encoding="utf-8")
    final_ref = _commit(repository, "review red test")
    return repository, base_ref, cycle_ref, final_ref


def _write_verified_artifact(root: Path, cycle_ref: str, *, authority_digest: str | None = None) -> None:
    artifact_root = root / "artifact"
    artifact_root.mkdir()
    mapping_digest = f"sha256:{'a' * 64}"
    plan_digest = f"sha256:{'b' * 64}"
    report = {
        "schema_version": "2",
        "verdict": "passed",
        "gate_decision": "pass",
        "observed_maturity": "verified",
        "mapping_digest": mapping_digest,
        "plan_digest": plan_digest,
        "execution_proof": {
            "run_stage": "final",
            "source_ref": cycle_ref,
            **({"cycle_authority_digest": authority_digest} if authority_digest is not None else {}),
        },
    }
    (artifact_root / "requirements-evidence.json").write_text(json.dumps(report), encoding="utf-8")
    plan = {"plan": {"mapping_digest": mapping_digest, "plan_digest": plan_digest}}
    (artifact_root / "requirements-evidence-plan.json").write_text(json.dumps(plan), encoding="utf-8")


def _write_run_metadata(root: Path, cycle_ref: str, *, conclusion: str, pull_request: int) -> None:
    metadata_root = root / "metadata"
    metadata_root.mkdir()
    run = {
        "id": 42,
        "head_sha": cycle_ref,
        "head_branch": "codex/692-computed-owner-red-proof-v2",
        "event": "pull_request",
        "status": "completed",
        "conclusion": conclusion,
        "name": "Requirements Evidence",
        "repository": {"full_name": "nold-ai/specfact-cli"},
        "pull_requests": [{"number": pull_request}],
    }
    (metadata_root / "run.json").write_text(json.dumps(run), encoding="utf-8")
    artifacts = {
        "artifacts": [
            {
                "id": 84,
                "name": "requirements-evidence",
                "expired": False,
                "digest": f"sha256:{'c' * 64}",
                "workflow_run": {"id": 42, "head_sha": cycle_ref},
            }
        ]
    }
    (metadata_root / "artifacts.json").write_text(json.dumps(artifacts), encoding="utf-8")


def _write_fixture(root: Path, *, conclusion: str = "success", pull_request: int = 698) -> tuple[Path, str, str]:
    repository, base_ref, cycle_ref, final_ref = _initialize_history(root)
    _write_verified_artifact(root, cycle_ref)
    _write_run_metadata(root, cycle_ref, conclusion=conclusion, pull_request=pull_request)
    return repository, base_ref, final_ref


def _assert_untrusted_metadata_rejected(
    module: ModuleType, paths: CycleBasePathsLike, context: CycleBaseContextLike
) -> None:
    run_path = paths.run
    run = json.loads(run_path.read_text(encoding="utf-8"))
    for field, invalid in (("conclusion", "failure"), ("head_branch", "foreign")):
        run_path.write_text(json.dumps({**run, field: invalid}), encoding="utf-8")
        assert module.validated_cycle_base(paths, context) is None
    run_path.write_text(json.dumps({**run, "pull_requests": [{"number": 697}]}), encoding="utf-8")
    assert module.validated_cycle_base(paths, context) is None
    run_path.write_text(json.dumps(run), encoding="utf-8")


def _assert_parallel_merge_rejected(
    module: ModuleType,
    paths: CycleBasePathsLike,
    context: CycleBaseContextLike,
    repository: Path,
) -> None:
    run = json.loads(paths.run.read_text(encoding="utf-8"))
    cycle_ref = run["head_sha"]
    _git(repository, "checkout", "--detach", cycle_ref)
    (repository / "src" / "parallel.py").write_text("VALUE = 2\n", encoding="utf-8")
    parallel_ref = _commit(repository, "parallel production")
    _git(repository, "checkout", "--detach", context.final_ref)
    merge = module._git(
        repository,
        "merge",
        "--no-ff",
        "--no-gpg-sign",
        "-m",
        "merge parallel production",
        parallel_ref,
    )
    assert merge.returncode == 0, merge.stderr
    merged_context = module.CycleBaseContext(
        base_ref=context.base_ref,
        final_ref=_git(repository, "rev-parse", "HEAD"),
        repository=context.repository,
        pull_request=context.pull_request,
        head_branch=context.head_branch,
        change_id=context.change_id,
    )
    assert module.validated_cycle_base(paths, merged_context) is None


def test_cycle_base_accepts_only_matching_verified_pull_request_history(tmp_path: Path) -> None:
    """Only an exact successful same-PR final artifact may narrow red history."""
    module = _load_cycle_base_module()
    repository, base_ref, final_ref = _write_fixture(tmp_path)
    paths = module.CycleBasePaths(
        run=tmp_path / "metadata" / "run.json",
        artifacts=tmp_path / "metadata" / "artifacts.json",
        artifact_root=tmp_path / "artifact",
        repo_root=repository,
    )
    context = module.CycleBaseContext(
        base_ref=base_ref,
        final_ref=final_ref,
        repository="nold-ai/specfact-cli",
        pull_request=698,
        head_branch="codex/692-computed-owner-red-proof-v2",
        change_id="fix-release-promotion-security-gates",
    )

    cycle_ref = json.loads(paths.run.read_text(encoding="utf-8"))["head_sha"]
    trusted_cycle = module.validated_cycle_base(paths, context)
    assert trusted_cycle is not None
    assert trusted_cycle.cycle_base == cycle_ref
    _assert_untrusted_metadata_rejected(module, paths, context)
    _assert_parallel_merge_rejected(module, paths, context, repository)


def test_cycle_base_accepts_self_authored_green_only_with_matching_external_authority_digest(tmp_path: Path) -> None:
    """A public external digest alone cannot bypass producer self-authorship."""
    module = _load_cycle_base_module()
    authority_digest = f"sha256:{'d' * 64}"
    repository, base_ref, cycle_ref, final_ref = _initialize_history(tmp_path, self_authored_authority=True)
    _write_verified_artifact(tmp_path, cycle_ref, authority_digest=authority_digest)
    _write_run_metadata(tmp_path, cycle_ref, conclusion="success", pull_request=698)
    paths = module.CycleBasePaths(
        run=tmp_path / "metadata" / "run.json",
        artifacts=tmp_path / "metadata" / "artifacts.json",
        artifact_root=tmp_path / "artifact",
        repo_root=repository,
    )
    context = module.CycleBaseContext(
        base_ref=base_ref,
        final_ref=final_ref,
        repository="nold-ai/specfact-cli",
        pull_request=698,
        head_branch="codex/692-computed-owner-red-proof-v2",
        change_id="fix-release-promotion-security-gates",
    )

    assert module.validated_cycle_base(paths, context) is None
    trusted = module.validated_cycle_base(paths, context, external_authority_digest=authority_digest)
    assert trusted is None
    assert (
        module.validated_cycle_base(
            paths,
            context,
            external_authority_digest=f"sha256:{'e' * 64}",
        )
        is None
    )
    authority_path = tmp_path / "authority.json"
    assert (
        module.main(
            [
                "--run",
                str(paths.run),
                "--artifacts",
                str(paths.artifacts),
                "--artifact-root",
                str(paths.artifact_root),
                "--repo-root",
                str(paths.repo_root),
                "--base-ref",
                base_ref,
                "--final-ref",
                final_ref,
                "--external-authority-digest",
                authority_digest,
                "--repository",
                context.repository,
                "--change-id",
                context.change_id,
                "--pull-request",
                str(context.pull_request),
                "--head-branch",
                context.head_branch,
                "--output",
                str(authority_path),
            ]
        )
        == 1
    )
    assert not authority_path.exists()
