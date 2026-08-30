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
        "bootstrap_issue=689",
        "requirements_bootstrap_authority.py",
        '--base-ref "origin/${EVIDENCE_BASE_BRANCH}"',
        '--final-ref "$EVIDENCE_FINAL_REF"',
        '--issue "$bootstrap_issue"',
        "EVIDENCE_HEAD_BRANCH: ${{ github.head_ref }}",
        "EVIDENCE_PULL_REQUEST: ${{ github.event.pull_request.number }}",
        '--pull-request "$EVIDENCE_PULL_REQUEST"',
        '--head-branch "$EVIDENCE_HEAD_BRANCH"',
        'write_failure_reports "One-time Requirements bootstrap authority rejected."',
    )

    assert all(fragment in workflow for fragment in required_fragments)


def test_release_security_bootstrap_binds_approved_external_red_authority() -> None:
    """The #692 exception must bind its exact approved ledger, run, and authority comment."""
    ledger = REPO_ROOT / "openspec" / "changes" / "fix-release-promotion-security-gates" / "TDD_EVIDENCE.md"
    prefix = b"".join(ledger.read_bytes().splitlines(keepends=True)[:279])
    expected_digest = f"sha256:{hashlib.sha256(prefix).hexdigest()}"
    workflow = WORKFLOW.read_text(encoding="utf-8")
    required_fragments = (
        'selected_change" == "fix-release-promotion-security-gates"',
        "legacy_tdd_line_count=279",
        f'legacy_tdd_ledger_digest="{expected_digest}"',
        'legacy_tdd_mapping_digest="sha256:31daf300f1bfeb2a6b5903567128bb100df8016dd23c3a8f5e6a8dcbfb31a202"',
        'legacy_tdd_plan_digest="sha256:01c1e0730d499e95b8164593059ffdc33ce11462da10b29f7d318257699d1975"',
        "bootstrap_comment_id=5448719352",
        "bootstrap_run_id=33124192051",
        'bootstrap_red_commit="2f5cb18c66b133a09a24234c982d2366f3de07d4"',
        "bootstrap_issue=692",
        '--issue "$bootstrap_issue"',
    )

    assert expected_digest == "sha256:1e2d64027e7e80d26e51431aad70d561dc495191915adee4e193352d80552c6f"
    assert all(fragment in workflow for fragment in required_fragments)
