"""Focused post-red review regressions for Requirements proof provenance."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_provenance.py"


def _load_provenance_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("requirements_proof_provenance_review_v2", PROVENANCE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_red_history_uses_a_positive_test_and_change_artifact_allowlist() -> None:
    """Files outside tests and the linked OpenSpec change are production by default."""
    module = _load_provenance_module()
    change_id = "fix-release-promotion-security-gates"
    unknown = (
        "implementation.py",
        "lib/implementation.py",
        "modules/new/module.py",
        "docs/_ext/implementation.py",
        f"openspec/changes/{change_id}/runtime.py",
    )
    allowed = (
        "tests/unit/test_review.py",
        "test/test_review.py",
        f"openspec/changes/{change_id}/TDD_EVIDENCE.md",
    )

    assert all(module._has_governed_production_path([path], change_id) for path in unknown)
    assert all(not module._has_governed_production_path([path], change_id) for path in allowed)
    assert not module._has_governed_production_path(
        ["openspec/changes/next-security-fix/specs/requirements/spec.md"],
        "next-security-fix",
    )
    assert module._has_governed_production_path(
        ["openspec/changes/next-security-fix/TDD_EVIDENCE.md"],
        None,
    )
    assert module._has_governed_production_path(
        ["openspec/changes/next-security-fix/TDD_EVIDENCE.md"],
        "../next-security-fix",
    )
    assert module._has_governed_production_path(
        [
            "openspec/changes/first-fix/TDD_EVIDENCE.md",
            "openspec/changes/second-fix/TDD_EVIDENCE.md",
        ],
        "first-fix",
    )


def test_direct_external_authority_revalidates_post_red_producer_history(tmp_path: Path) -> None:
    """The direct external receipt cannot skip the shared post-red history predicate."""
    module = _load_provenance_module()
    receipt = {
        "cycle_base": "a" * 40,
        "authority_digest": f"sha256:{'b' * 64}",
        "prior_green_run_id": 1,
        "prior_green_artifact_id": 2,
        "prior_green_artifact_digest": f"sha256:{'c' * 64}",
    }
    paths = SimpleNamespace(
        red_run=tmp_path / "red-run.json",
        red_artifacts=tmp_path / "red-artifacts.json",
        red_root=tmp_path / "red",
        green_run=tmp_path / "green-run.json",
        green_artifacts=tmp_path / "green-artifacts.json",
        green_root=tmp_path / "green",
        comment=tmp_path / "comment.json",
        proof=tmp_path / "proof.json",
        receipt=tmp_path / "receipt.json",
    )
    observed = {"history": 0}

    class FakeCycleModule:
        CycleBasePaths = SimpleNamespace
        CycleBaseContext = SimpleNamespace

        @staticmethod
        def _external_receipt_history_matches(*_arguments: object) -> bool:
            observed["history"] += 1
            return False

    module.__dict__["_external_hint_matches"] = lambda *_arguments: True
    module.__dict__["_fetch_external_amendment"] = lambda *_arguments: paths
    module.__dict__["_external_validator_command"] = lambda *_arguments: ["true"]
    module.__dict__["_read_red_proof"] = lambda *_arguments: receipt
    module.__dict__["_cycle_module"] = lambda: FakeCycleModule
    context = module.CycleAuthorityContext(
        tmp_path,
        "d" * 40,
        "e" * 40,
        "f" * 40,
        "nold-ai/specfact-cli",
        698,
        "codex/692-computed-owner-red-proof-v2",
        "fix-release-promotion-security-gates",
    )

    with patch.object(module.subprocess, "run", return_value=SimpleNamespace(returncode=0)):
        try:
            module._trusted_external_amendment(context, receipt, tmp_path)
        except ValueError as error:
            assert str(error) == "prior-red-proof-invalid"
        else:
            raise AssertionError("direct external authority skipped the post-red history predicate")
    assert observed["history"] == 1
