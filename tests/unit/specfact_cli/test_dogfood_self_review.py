"""Dogfooding tests: specfact code review must pass on its own codebase.

These tests serve as the TDD gate for the code-review-zero-findings change.
They were written BEFORE the fixes and are expected to FAIL on the pre-fix
codebase, then PASS once all remediation phases are complete.

Spec scenarios from: openspec/changes/code-review-zero-findings/specs/
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest


# Repo root is three levels up from this test file
REPO_ROOT = Path(__file__).parent.parent.parent.parent
REVIEW_JSON_OUT = REPO_ROOT / "review-dogfood-test.json"


def _run_review() -> dict:
    """Run specfact code review --scope full and return the parsed JSON report."""
    result = subprocess.run(
        [
            "hatch",
            "run",
            "specfact",
            "code",
            "review",
            "run",
            "--scope",
            "full",
            "--json",
            "--out",
            str(REVIEW_JSON_OUT),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=300,
    )
    assert REVIEW_JSON_OUT.exists(), (
        f"Review report not written. stdout={result.stdout[-500:]}, stderr={result.stderr[-500:]}"
    )
    with REVIEW_JSON_OUT.open() as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def review_report() -> Generator[dict, None, None]:
    """Run the review once per module and share the result across all tests."""
    if os.environ.get("TEST_MODE") == "true":
        pytest.skip("Skipping live review run in TEST_MODE")
    report = _run_review()
    yield report
    # Cleanup temp output
    if REVIEW_JSON_OUT.exists():
        REVIEW_JSON_OUT.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 2.1 — overall verdict must be PASS
# ---------------------------------------------------------------------------


def test_review_overall_verdict_pass(review_report: dict) -> None:
    """specfact code review run --scope full must return overall_verdict: PASS."""
    verdict = review_report.get("overall_verdict")
    total = len(review_report.get("findings", []))
    assert verdict == "PASS", (
        f"overall_verdict={verdict!r}, total findings={total}. Expected PASS with 0 findings after remediation."
    )


# ---------------------------------------------------------------------------
# 2.2 — zero basedpyright reportUnknownMemberType findings
# ---------------------------------------------------------------------------


def test_zero_basedpyright_unknown_member_type(review_report: dict) -> None:
    """No reportUnknownMemberType findings in src/."""
    findings = review_report.get("findings", [])
    bad = [f for f in findings if f.get("rule") == "reportUnknownMemberType"]
    assert len(bad) == 0, (
        f"Found {len(bad)} reportUnknownMemberType findings. "
        "Add explicit type annotations to all untyped class members."
    )


# ---------------------------------------------------------------------------
# 2.3 — zero semgrep print-in-src findings
# ---------------------------------------------------------------------------


def test_zero_semgrep_print_in_src(review_report: dict) -> None:
    """No print-in-src semgrep findings in src/, scripts/, tools/."""
    findings = review_report.get("findings", [])
    bad = [f for f in findings if f.get("rule") == "print-in-src"]
    assert len(bad) == 0, (
        f"Found {len(bad)} print-in-src findings. Replace all print() calls with get_bridge_logger() or Rich Console."
    )


# ---------------------------------------------------------------------------
# 2.4 — zero MISSING_ICONTRACT findings
# ---------------------------------------------------------------------------


def test_zero_missing_icontract(review_report: dict) -> None:
    """No MISSING_ICONTRACT contract findings in src/."""
    findings = review_report.get("findings", [])
    bad = [f for f in findings if f.get("rule") == "MISSING_ICONTRACT"]
    assert len(bad) == 0, (
        f"Found {len(bad)} MISSING_ICONTRACT findings. Add @require/@ensure/@beartype to all flagged public functions."
    )


# ---------------------------------------------------------------------------
# 2.5 — zero CC>=16 radon findings
# ---------------------------------------------------------------------------


def test_zero_radon_cc_error_band(review_report: dict) -> None:
    """No cyclomatic complexity >= 16 findings in src/, scripts/, tools/."""
    findings = review_report.get("findings", [])
    bad = [
        f
        for f in findings
        if f.get("rule", "").startswith("CC") and f.get("category") == "clean_code" and int(f["rule"][2:]) >= 16
    ]
    assert len(bad) == 0, (
        f"Found {len(bad)} CC>=16 findings. Refactor high-complexity functions by extracting private helpers."
    )


# ---------------------------------------------------------------------------
# 2.5b — zero tool_error findings
# ---------------------------------------------------------------------------


def test_zero_tool_errors(review_report: dict) -> None:
    """No tool_error findings (e.g. pylint timeout, missing binary)."""
    findings = review_report.get("findings", [])
    bad = [f for f in findings if f.get("category") == "tool_error"]
    assert len(bad) == 0, f"Found {len(bad)} tool_error findings: " + "; ".join(f.get("message", "")[:120] for f in bad)
