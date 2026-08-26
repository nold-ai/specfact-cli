"""Regression coverage for retained-red producer wiring and legacy evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"


def test_red_binder_receives_executor_junit_path() -> None:
    """The producer must bind the exact JUnit filename written by the executor."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    binding_start = workflow.index("--bind-red-proof artifacts/requirements-evidence/requirements-evidence.json")
    binding_end = workflow.index("--repo-root", binding_start)

    assert "--junit artifacts/requirements-evidence/requirements-proof.xml" in workflow[binding_start:binding_end]


def test_r07_legacy_ledger_digest_matches_approved_prefix() -> None:
    """The narrowly approved R07 prefix must remain bound to its current bytes."""
    ledger = REPO_ROOT / "openspec" / "changes" / "requirements-07-runtime-proof-delivery" / "TDD_EVIDENCE.md"
    prefix = b"".join(ledger.read_bytes().splitlines(keepends=True)[:1143])
    expected_digest = f"sha256:{hashlib.sha256(prefix).hexdigest()}"
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert f'legacy_tdd_ledger_digest="{expected_digest}"' in workflow
