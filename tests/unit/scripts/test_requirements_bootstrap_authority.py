"""Security boundary coverage for the one-time Requirements bootstrap authority."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
AUTHORITY_SCRIPT = REPO_ROOT / "scripts" / "requirements_bootstrap_authority.py"


def _load_authority_module() -> Any:
    spec = importlib.util.spec_from_file_location("requirements_bootstrap_authority", AUTHORITY_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Requirements bootstrap authority validator must be importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(repo_root: Path, *arguments: str) -> str:
    result = subprocess.run(["git", *arguments], cwd=repo_root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _commit(repo_root: Path, message: str) -> str:
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "--no-gpg-sign", "-m", message)
    return _git(repo_root, "rev-parse", "HEAD")


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _repository_history(tmp_path: Path, *, governed_red_path: bool = False) -> tuple[Path, str, str, str]:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "requirements@example.test")
    _git(repo_root, "config", "user.name", "Requirements proof")
    (repo_root / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(repo_root, "chore: base")
    test_path = repo_root / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    if governed_red_path:
        governed_path = repo_root / "src" / "smuggled.py"
        governed_path.parent.mkdir()
        governed_path.write_text("VALUE = 1\n", encoding="utf-8")
    red_ref = _commit(repo_root, "test: red")
    (repo_root / "src").mkdir(exist_ok=True)
    (repo_root / "src" / "proof.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(repo_root, "fix: green")
    return repo_root, base_ref, red_ref, final_ref


def _write_red_artifact(artifact_root: Path, red_ref: str) -> tuple[dict[str, object], Path, Path, bytes]:
    """Write the three exact files retained by the failing workflow run."""
    junit = b"<testsuite><testcase><failure/></testcase></testsuite>"
    report = {
        "gate_decision": "pass",
        "mapping_digest": f"sha256:{'a' * 64}",
        "observed_maturity": "red",
        "plan_digest": f"sha256:{'b' * 64}",
        "execution_proof": {
            "junit_digest": f"sha256:{hashlib.sha256(junit).hexdigest()}",
            "run_stage": "red",
            "source_ref": red_ref,
        },
    }
    report_path = artifact_root / "requirements-evidence.json"
    plan_path = artifact_root / "requirements-evidence-plan.json"
    _write_json(report_path, report)
    (artifact_root / "requirements-proof.xml").write_bytes(junit)
    _write_json(plan_path, {"plan": {"mapping_digest": report["mapping_digest"], "plan_digest": report["plan_digest"]}})
    return report, report_path, plan_path, junit


def _red_artifact(tmp_path: Path, base_ref: str, red_ref: str) -> tuple[Path, dict[str, object]]:
    artifact_root = tmp_path / "artifact"
    artifact_root.mkdir()
    report, report_path, plan_path, junit = _write_red_artifact(artifact_root, red_ref)
    authority = {
        "artifact_digest": f"sha256:{'c' * 64}",
        "artifact_id": 22,
        "base_commit": base_ref,
        "change_id": "fix-retained-red-proof-provenance",
        "expires_at": "2099-01-01T00:00:00Z",
        "head_branch": "bugfix/689-retained-red-proof-provenance",
        "issue": 689,
        "junit_digest": f"sha256:{hashlib.sha256(junit).hexdigest()}",
        "mapping_digest": report["mapping_digest"],
        "plan_digest": report["plan_digest"],
        "plan_report_digest": f"sha256:{hashlib.sha256(plan_path.read_bytes()).hexdigest()}",
        "pull_request": 690,
        "red_commit": red_ref,
        "report_digest": f"sha256:{hashlib.sha256(report_path.read_bytes()).hexdigest()}",
        "repository": "nold-ai/specfact-cli",
        "run_id": 11,
        "signer_login": "djm81",
    }
    return artifact_root, authority


def _write_comment_and_commit_metadata(tmp_path: Path, authority: dict[str, object]) -> tuple[Path, Path]:
    comment_path = tmp_path / "comment.json"
    commit_path = tmp_path / "commit.json"
    _write_json(
        comment_path,
        {
            "author_association": "OWNER",
            "body": f"SPECFACT_REQUIREMENTS_BOOTSTRAP_AUTHORITY_V1\n{json.dumps(authority, sort_keys=True, separators=(',', ':'))}",
            "created_at": "2026-08-26T00:00:00Z",
            "html_url": "https://github.com/nold-ai/specfact-cli/issues/689#issuecomment-33",
            "id": 33,
            "issue_url": "https://api.github.com/repos/nold-ai/specfact-cli/issues/689",
            "updated_at": "2026-08-26T00:00:00Z",
            "user": {"login": "djm81"},
        },
    )
    _write_json(
        commit_path,
        {
            "author": {"login": "djm81"},
            "commit": {"verification": {"reason": "valid", "verified": True}},
            "sha": authority["red_commit"],
        },
    )
    return comment_path, commit_path


def _write_run_and_artifact_metadata(tmp_path: Path, authority: dict[str, object]) -> tuple[Path, Path]:
    run_path = tmp_path / "run.json"
    artifacts_path = tmp_path / "artifacts.json"
    _write_json(
        run_path,
        {
            "conclusion": "failure",
            "event": "pull_request",
            "head_branch": authority["head_branch"],
            "head_sha": authority["red_commit"],
            "id": 11,
            "name": "Requirements Evidence",
            "repository": {"full_name": authority["repository"]},
            "status": "completed",
        },
    )
    _write_json(
        artifacts_path,
        {
            "artifacts": [
                {
                    "digest": authority["artifact_digest"],
                    "expired": False,
                    "id": 22,
                    "name": "requirements-evidence",
                    "workflow_run": {"head_sha": authority["red_commit"], "id": 11},
                }
            ]
        },
    )
    return run_path, artifacts_path


def _external_metadata(tmp_path: Path, authority: dict[str, object]) -> dict[str, Path]:
    comment_path, commit_path = _write_comment_and_commit_metadata(tmp_path, authority)
    run_path, artifacts_path = _write_run_and_artifact_metadata(tmp_path, authority)
    return {
        "artifacts_path": artifacts_path,
        "comment_path": comment_path,
        "commit_path": commit_path,
        "run_path": run_path,
    }


def _authority_fixture(tmp_path: Path, *, governed_red_path: bool = False) -> dict[str, object]:
    repo_root, base_ref, red_ref, final_ref = _repository_history(tmp_path, governed_red_path=governed_red_path)
    artifact_root, authority = _red_artifact(tmp_path, base_ref, red_ref)
    return {
        **_external_metadata(tmp_path, authority),
        "artifact_root": artifact_root,
        "base_ref": base_ref,
        "final_ref": final_ref,
        "repo_root": repo_root,
    }


def _validate(module: Any, fixture: dict[str, object], *, final_ref: str | None = None) -> bool:
    paths = module.AuthorityPaths(
        comment=fixture["comment_path"],
        commit=fixture["commit_path"],
        run=fixture["run_path"],
        artifacts=fixture["artifacts_path"],
        artifact_root=fixture["artifact_root"],
        repo_root=fixture["repo_root"],
    )
    context = module.AuthorityContext(
        comment_id=33,
        base_ref=cast(str, fixture["base_ref"]),
        final_ref=final_ref or cast(str, fixture["final_ref"]),
        repository="nold-ai/specfact-cli",
        change_id="fix-retained-red-proof-provenance",
        issue=689,
        pull_request=690,
        head_branch="bugfix/689-retained-red-proof-provenance",
    )
    return cast(
        bool,
        module.validate_bootstrap_authority(paths, context),
    )


def _mutate_authority(fixture: dict[str, object], **updates: object) -> None:
    comment_path = cast(Path, fixture["comment_path"])
    comment = json.loads(comment_path.read_text(encoding="utf-8"))
    header, separator, encoded_authority = comment["body"].partition("\n")
    assert separator
    authority = json.loads(encoded_authority)
    authority.update(updates)
    comment["body"] = f"{header}\n{json.dumps(authority, sort_keys=True, separators=(',', ':'))}"
    _write_json(comment_path, comment)


def _history_is_valid(module: Any, repo_root: Path, base_ref: str, red_ref: str, final_ref: str) -> bool:
    """Exercise only the Git-history boundary with otherwise well-formed identities."""
    placeholder = repo_root / "unused"
    paths = module.AuthorityPaths(
        comment=placeholder,
        commit=placeholder,
        run=placeholder,
        artifacts=placeholder,
        artifact_root=placeholder,
        repo_root=repo_root,
    )
    context = module.AuthorityContext(
        comment_id=33,
        base_ref=base_ref,
        final_ref=final_ref,
        repository="nold-ai/specfact-cli",
        change_id="fix-retained-red-proof-provenance",
        issue=689,
        pull_request=690,
        head_branch="bugfix/689-retained-red-proof-provenance",
    )
    return cast(bool, module._valid_history({"base_commit": base_ref, "red_commit": red_ref}, paths, context))


def test_bootstrap_authority_accepts_exact_owner_bound_red_history(tmp_path: Path) -> None:
    """Every external and local identity must agree for the one-time bootstrap."""
    module = _load_authority_module()
    fixture = _authority_fixture(tmp_path)

    assert _validate(module, fixture)


def test_bootstrap_authority_accepts_exact_collaborator_bound_red_history(tmp_path: Path) -> None:
    """Private organization membership may surface as COLLABORATOR to Actions."""
    module = _load_authority_module()
    fixture = _authority_fixture(tmp_path)
    comment_path = cast(Path, fixture["comment_path"])
    comment = json.loads(comment_path.read_text(encoding="utf-8"))
    comment["author_association"] = "COLLABORATOR"
    _write_json(comment_path, comment)

    assert _validate(module, fixture)


def test_bootstrap_authority_rejects_same_evidence_without_authorized_red_ancestor(tmp_path: Path) -> None:
    """Replaying the same ledger and plan on unrelated history must fail closed."""
    module = _load_authority_module()
    fixture = _authority_fixture(tmp_path)
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    _git(unrelated, "init")
    _git(unrelated, "config", "user.email", "requirements@example.test")
    _git(unrelated, "config", "user.name", "Requirements proof")
    (unrelated / "README.md").write_text("# unrelated\n", encoding="utf-8")
    unrelated_ref = _commit(unrelated, "chore: unrelated")

    assert not _validate(module, fixture, final_ref=unrelated_ref)


def test_bootstrap_authority_rejects_unverified_red_commit(tmp_path: Path) -> None:
    """An unsigned red commit cannot authorize the one-time bootstrap."""
    module = _load_authority_module()
    fixture = _authority_fixture(tmp_path)
    commit_path = cast(Path, fixture["commit_path"])
    commit = json.loads(commit_path.read_text(encoding="utf-8"))
    commit["commit"]["verification"] = {"reason": "unsigned", "verified": False}
    _write_json(commit_path, commit)

    assert not _validate(module, fixture)


def test_bootstrap_authority_rejects_nonfailing_red_run(tmp_path: Path) -> None:
    """Only a completed failing red run can authorize green delivery."""
    module = _load_authority_module()
    fixture = _authority_fixture(tmp_path)
    run_path = cast(Path, fixture["run_path"])
    run = json.loads(run_path.read_text(encoding="utf-8"))
    run["conclusion"] = "success"
    _write_json(run_path, run)

    assert not _validate(module, fixture)


def test_bootstrap_authority_rejects_expired_authority(tmp_path: Path) -> None:
    """Expired one-time authority must fail closed."""
    module = _load_authority_module()
    fixture = _authority_fixture(tmp_path)
    _mutate_authority(fixture, expires_at="2026-01-01T00:00:00Z")

    assert not _validate(module, fixture)


def test_bootstrap_authority_rejects_tampered_red_report(tmp_path: Path) -> None:
    """A red report that no longer matches its authority digest must fail closed."""
    module = _load_authority_module()
    fixture = _authority_fixture(tmp_path)
    report_path = cast(Path, fixture["artifact_root"]) / "requirements-evidence.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["gate_decision"] = "tampered"
    _write_json(report_path, report)

    assert not _validate(module, fixture)


def test_bootstrap_authority_rejects_governed_path_in_red_history(tmp_path: Path) -> None:
    """Production code committed between base and red must fail closed."""
    module = _load_authority_module()
    fixture = _authority_fixture(tmp_path, governed_red_path=True)

    assert not _validate(module, fixture)


def test_bootstrap_authority_rejects_merge_commit_in_red_history(tmp_path: Path) -> None:
    """A merge cannot hide production bytes that exist only in its resolution tree."""
    module = _load_authority_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "requirements@example.test")
    _git(repo_root, "config", "user.name", "Requirements proof")
    (repo_root / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(repo_root, "chore: base")

    _git(repo_root, "switch", "-c", "red-tests")
    test_path = repo_root / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    _commit(repo_root, "test: red")

    _git(repo_root, "switch", "master")
    (repo_root / "README.md").write_text("# proof\n\nmain line\n", encoding="utf-8")
    _commit(repo_root, "docs: advance main")
    _git(repo_root, "merge", "--no-ff", "--no-commit", "red-tests")
    governed_path = repo_root / "src" / "merge_resolution.py"
    governed_path.parent.mkdir()
    governed_path.write_text("VALUE = 1\n", encoding="utf-8")
    red_ref = _commit(repo_root, "test: merge red evidence")
    (repo_root / "README.md").write_text("# proof\n\nfinal line\n", encoding="utf-8")
    final_ref = _commit(repo_root, "docs: final")

    assert not _history_is_valid(module, repo_root, base_ref, red_ref, final_ref)


def test_bootstrap_authority_rejects_tabbed_governed_path(tmp_path: Path) -> None:
    """Git quoting cannot conceal a governed path containing a tab."""
    module = _load_authority_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "requirements@example.test")
    _git(repo_root, "config", "user.name", "Requirements proof")
    (repo_root / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(repo_root, "chore: base")
    governed_path = repo_root / "src" / "tab\tpath.py"
    governed_path.parent.mkdir()
    governed_path.write_text("VALUE = 1\n", encoding="utf-8")
    red_ref = _commit(repo_root, "test: tabbed governed path")
    (repo_root / "README.md").write_text("# proof\n\nfinal line\n", encoding="utf-8")
    final_ref = _commit(repo_root, "docs: final")

    assert not _history_is_valid(module, repo_root, base_ref, red_ref, final_ref)


def test_bootstrap_authority_rejects_invalid_base_oid_before_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Untrusted base authority must be rejected before reaching Git arguments."""
    module = _load_authority_module()
    fixture = _authority_fixture(tmp_path)
    _mutate_authority(fixture, base_commit="--all")

    def reject_git(*_arguments: object, **_keywords: object) -> None:
        raise AssertionError("invalid authority reached git")

    monkeypatch.setattr(module, "_git", reject_git)
    assert not _validate(module, fixture)


def test_bootstrap_authority_rejects_malformed_red_commit_without_traceback(tmp_path: Path) -> None:
    """Non-string authority identities must return false instead of raising."""
    module = _load_authority_module()
    fixture = _authority_fixture(tmp_path)
    _mutate_authority(fixture, red_commit={"unexpected": "object"})

    assert not _validate(module, fixture)
