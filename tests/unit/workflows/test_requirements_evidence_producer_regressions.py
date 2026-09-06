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


def test_producer_repair_bootstrap_requires_external_red_authority() -> None:
    """The repair exception must bind an owner-authorized signed run and exact ancestry."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    required_fragments = (
        "issues: read",
        "bootstrap_comment_id=5431081643",
        "bootstrap_run_id=33013274590",
        'bootstrap_red_commit="04b6c02eb63f779309d8dced48085f3ef0efe029"',
        "requirements_bootstrap_authority.py",
        '--base-ref "$evidence_base_commit"',
        '--final-ref "$EVIDENCE_FINAL_REF"',
        "--issue 689",
        "EVIDENCE_HEAD_BRANCH: ${{ github.head_ref }}",
        "EVIDENCE_PULL_REQUEST: ${{ github.event.pull_request.number }}",
        '--pull-request "$EVIDENCE_PULL_REQUEST"',
        '--head-branch "$EVIDENCE_HEAD_BRANCH"',
        'write_failure_reports "One-time Requirements bootstrap authority rejected."',
    )

    assert all(fragment in workflow for fragment in required_fragments)
