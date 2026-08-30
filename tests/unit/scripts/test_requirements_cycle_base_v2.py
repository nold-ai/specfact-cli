"""Post-red external authority regressions for amendment-cycle selection."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast


REPO_ROOT = Path(__file__).resolve().parents[3]
CYCLE_BASE_SCRIPT = REPO_ROOT / "scripts" / "requirements_cycle_base.py"
FIXTURE_MODULE = REPO_ROOT / "tests" / "unit" / "scripts" / "test_requirements_cycle_base.py"


class _TrustedCycle(Protocol):
    cycle_base: str


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _paths(module: ModuleType, root: Path, repository: Path) -> object:
    return module.CycleBasePaths(
        run=root / "metadata" / "run.json",
        artifacts=root / "metadata" / "artifacts.json",
        artifact_root=root / "artifact",
        repo_root=repository,
    )


def test_public_external_digest_cannot_authenticate_self_authored_candidate(tmp_path: Path) -> None:
    """A candidate's self-asserted copy of a public digest is not authority."""
    module = _load(CYCLE_BASE_SCRIPT, "requirements_cycle_base_v2_digest")
    fixtures = _load(FIXTURE_MODULE, "requirements_cycle_base_v2_fixtures_digest")
    authority_digest = f"sha256:{'d' * 64}"
    repository, base_ref, candidate_ref, final_ref = fixtures._initialize_history(
        tmp_path, self_authored_authority=True
    )
    fixtures._write_verified_artifact(tmp_path, candidate_ref, authority_digest=authority_digest)
    fixtures._write_run_metadata(tmp_path, candidate_ref, conclusion="success", pull_request=698)
    context = module.CycleBaseContext(
        base_ref,
        final_ref,
        "nold-ai/specfact-cli",
        698,
        "codex/692-computed-owner-red-proof-v2",
    )

    assert (
        module.validated_cycle_base(
            _paths(module, tmp_path, repository),
            context,
            external_authority_digest=authority_digest,
        )
        is None
    )


def _receipt(fixtures: ModuleType, repository: Path, root_green: str, red_ref: str) -> dict[str, object]:
    authority: dict[str, object] = {
        "repository": "nold-ai/specfact-cli",
        "change_id": "fix-release-promotion-security-gates",
        "issue": 692,
        "pull_request": 698,
        "head_branch": "codex/692-computed-owner-red-proof-v2",
        "cycle_base_commit": root_green,
        "cycle_base_tree": fixtures._git(repository, "rev-parse", f"{root_green}^{{tree}}"),
        "red_commit": red_ref,
        "red_tree": fixtures._git(repository, "rev-parse", f"{red_ref}^{{tree}}"),
        "prior_green_run_id": 11,
        "prior_green_artifact_id": 22,
        "prior_green_artifact_digest": f"sha256:{'a' * 64}",
        "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
        "signer_login": "owner",
    }
    digest = (
        "sha256:" + hashlib.sha256(json.dumps(authority, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    )
    return {
        **authority,
        "kind": "externally-approved-amendment-bootstrap",
        "comment_id": 5464938148,
        "cycle_base": root_green,
        "red_ref": red_ref,
        "authority_digest": digest,
    }


def _redigest(receipt: dict[str, object]) -> dict[str, object]:
    """Return a self-consistent forged receipt for one negative control."""
    payload = {
        key: value
        for key, value in receipt.items()
        if key not in {"kind", "comment_id", "cycle_base", "red_ref", "authority_digest"}
    }
    return {
        **receipt,
        "authority_digest": (
            "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        ),
    }


def _validated_receipt(
    module: ModuleType,
    paths: object,
    context: object,
    red_ref: str,
    receipt: dict[str, object],
) -> _TrustedCycle | None:
    """Validate one receipt using its independently supplied canonical digest."""
    return cast(
        _TrustedCycle | None,
        module.validated_cycle_base(
            paths,
            context,
            red_ref=red_ref,
            external_authority_digest=cast(str, receipt["authority_digest"]),
            external_authority_receipt=receipt,
        ),
    )


def test_exact_live_receipt_authenticates_bound_descendant_candidate(tmp_path: Path) -> None:
    """A descendant green is trusted only through its exact approved root receipt."""
    module = _load(CYCLE_BASE_SCRIPT, "requirements_cycle_base_v2_receipt")
    fixtures = _load(FIXTURE_MODULE, "requirements_cycle_base_v2_fixtures_receipt")
    repository, base_ref, root_green, approved_red = fixtures._initialize_history(
        tmp_path, self_authored_authority=True
    )
    receipt = _receipt(fixtures, repository, root_green, approved_red)
    authority_digest = cast(str, receipt["authority_digest"])
    implementation = repository / "src" / "implementation.py"
    implementation.parent.mkdir(exist_ok=True)
    implementation.write_text("VALUE = 1\n", encoding="utf-8")
    candidate_ref = fixtures._commit(repository, "externally reviewed implementation")
    current_test = repository / "tests" / "test_later_review.py"
    current_test.write_text("def test_later_review(): assert False\n", encoding="utf-8")
    current_red = fixtures._commit(repository, "later review red test")
    fixtures._write_verified_artifact(tmp_path, candidate_ref, authority_digest=authority_digest)
    report_path = tmp_path / "artifact" / "requirements-evidence.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["execution_proof"].update(
        cycle_base=root_green,
        prior_green_run_id=receipt["prior_green_run_id"],
        prior_green_artifact_id=receipt["prior_green_artifact_id"],
        prior_green_artifact_digest=receipt["prior_green_artifact_digest"],
    )
    report_path.write_text(json.dumps(report), encoding="utf-8")
    fixtures._write_run_metadata(tmp_path, candidate_ref, conclusion="success", pull_request=698)
    context = module.CycleBaseContext(
        base_ref,
        current_red,
        "nold-ai/specfact-cli",
        698,
        "codex/692-computed-owner-red-proof-v2",
    )
    paths = _paths(module, tmp_path, repository)

    trusted = _validated_receipt(module, paths, context, current_red, receipt)
    assert trusted is not None and trusted.cycle_base == candidate_ref

    tampered = {**receipt, "red_tree": "0" * 40}
    tampered = _redigest(tampered)
    assert _validated_receipt(module, paths, context, current_red, tampered) is None

    expired = _redigest(
        {
            **receipt,
            "expires_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat().replace("+00:00", "Z"),
        }
    )
    assert _validated_receipt(module, paths, context, current_red, expired) is None

    wrong_locator = _redigest({**receipt, "comment_id": 5464938149})
    assert _validated_receipt(module, paths, context, current_red, wrong_locator) is None

    report["execution_proof"]["prior_green_artifact_id"] = 23
    report_path.write_text(json.dumps(report), encoding="utf-8")
    assert _validated_receipt(module, paths, context, current_red, receipt) is None
