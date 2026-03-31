"""Tests for clean-code-01-principle-gates.

Validates that specfact-cli instruction surfaces expose the 7-principle
clean-code charter consistently and that the review gate is configured
for the expanded clean-code categories under Phase A thresholds.

Spec scenarios from:
  openspec/changes/clean-code-01-principle-gates/specs/
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]

# Instruction surface paths
AGENTS_MD = REPO_ROOT / "AGENTS.md"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
CLEAN_CODE_MDC = REPO_ROOT / ".cursor" / "rules" / "clean-code-principles.mdc"
COPILOT_INSTRUCTIONS = REPO_ROOT / ".github" / "copilot-instructions.md"


# ---------------------------------------------------------------------------
# Spec: agent-instruction-clean-code-charter
# Scenario: Core instruction surfaces reference the charter consistently
# ---------------------------------------------------------------------------


def test_agents_md_references_clean_code_categories() -> None:
    """AGENTS.md must reference clean-code review categories so contributors
    know which categories the gate checks."""
    text = AGENTS_MD.read_text(encoding="utf-8")
    for category in ("naming", "kiss", "yagni", "dry", "solid"):
        assert category in text.lower(), (
            f"AGENTS.md missing clean-code category reference: {category!r}. "
            "Add a clean-code review section that lists all 5 expanded categories."
        )


def test_claude_md_references_clean_code_categories() -> None:
    """CLAUDE.md must reference clean-code review categories."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    for category in ("naming", "kiss", "yagni", "dry", "solid"):
        assert category in text.lower(), (
            f"CLAUDE.md missing clean-code category reference: {category!r}. "
            "Add a clean-code review section that lists all 5 expanded categories."
        )


def test_clean_code_mdc_references_seven_principles() -> None:
    """clean-code-principles.mdc must reference all 7 principles by canonical name."""
    text = CLEAN_CODE_MDC.read_text(encoding="utf-8")
    # 7 canonical principles
    for category in ("naming", "kiss", "yagni", "dry", "solid", "small", "self"):
        assert category in text.lower(), (
            f".cursor/rules/clean-code-principles.mdc missing principle: {category!r}. "
            "Update this file to reference the canonical 7-principle charter."
        )


def test_clean_code_mdc_references_canonical_skill() -> None:
    """clean-code-principles.mdc must reference the canonical charter source
    (skills/specfact-code-review/SKILL.md or the policy-pack name) so that
    generated alias surfaces do not duplicate the full charter text."""
    text = CLEAN_CODE_MDC.read_text(encoding="utf-8")
    assert "specfact-code-review" in text or "clean-code-principles" in text, (
        ".cursor/rules/clean-code-principles.mdc must point to the canonical charter source "
        "(e.g. 'specfact/clean-code-principles' policy-pack or 'skills/specfact-code-review/SKILL.md')."
    )


# ---------------------------------------------------------------------------
# Spec: agent-instruction-clean-code-charter
# Scenario: Generated IDE aliases stay lightweight
# ---------------------------------------------------------------------------


def test_copilot_instructions_exists_and_references_charter() -> None:
    """GITHUB copilot-instructions.md must exist and contain a clean-code alias
    reference without duplicating the full charter inline."""
    assert COPILOT_INSTRUCTIONS.exists(), (
        f"{COPILOT_INSTRUCTIONS} is missing. Create a lightweight alias file "
        "that references the canonical clean-code charter."
    )
    text = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    assert "clean-code" in text.lower() or "clean_code" in text.lower(), (
        ".github/copilot-instructions.md must contain a clean-code alias reference."
    )


def test_copilot_instructions_does_not_duplicate_full_charter() -> None:
    """copilot-instructions.md must be a short alias, not a full charter copy.
    If the file is longer than 80 lines it likely duplicates the charter verbatim."""
    if not COPILOT_INSTRUCTIONS.exists():
        pytest.skip("copilot-instructions.md not yet created")
    lines = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 80, (
        f".github/copilot-instructions.md is {len(lines)} lines — too long for an alias. "
        "Keep it concise and reference the canonical charter rather than duplicating it."
    )


# ---------------------------------------------------------------------------
# Spec: clean-code-compliance-gate
# Scenario: Repo review includes expanded clean-code categories
# ---------------------------------------------------------------------------


def test_agents_md_documents_clean_code_compliance_gate() -> None:
    """AGENTS.md must document that the SpecFact review gate checks clean-code
    categories so contributors know regressions will block merges."""
    text = AGENTS_MD.read_text(encoding="utf-8")
    assert "clean-code" in text.lower() or "clean_code" in text.lower(), (
        "AGENTS.md must document the clean-code compliance gate so contributors "
        "know the review gate enforces clean-code categories."
    )


def test_claude_md_documents_clean_code_compliance_gate() -> None:
    """CLAUDE.md must document that the review gate checks clean-code categories."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    assert "clean-code" in text.lower() or "clean_code" in text.lower(), (
        "CLAUDE.md must document the clean-code compliance gate."
    )


# ---------------------------------------------------------------------------
# Spec: clean-code-loc-nesting-check
# Scenario: Phase A thresholds are enforced first
# ---------------------------------------------------------------------------


def test_clean_code_mdc_documents_phase_a_loc_thresholds() -> None:
    """clean-code-principles.mdc must document the Phase A LOC thresholds
    (>80 warning, >120 error) so reviewers and tools know the active limits."""
    text = CLEAN_CODE_MDC.read_text(encoding="utf-8")
    assert "> 80 (warning)" in text and "> 120 (error)" in text, (
        ".cursor/rules/clean-code-principles.mdc must document Phase A LOC thresholds: "
        "'> 80 (warning)' and '> 120 (error)'. These are the active KISS metric limits."
    )


def test_clean_code_mdc_mentions_nesting_and_parameter_checks() -> None:
    """clean-code-principles.mdc must mention nesting-depth and parameter-count
    checks alongside the LOC thresholds (all three are Phase A KISS metrics)."""
    text = CLEAN_CODE_MDC.read_text(encoding="utf-8")
    assert "nesting" in text.lower(), ".cursor/rules/clean-code-principles.mdc must mention nesting-depth checks."
    assert "parameter" in text.lower(), ".cursor/rules/clean-code-principles.mdc must mention parameter-count checks."


# ---------------------------------------------------------------------------
# Spec: clean-code-loc-nesting-check
# Scenario: Phase B remains deferred until cleanup is complete
# ---------------------------------------------------------------------------


def test_clean_code_mdc_documents_phase_b_as_deferred() -> None:
    """clean-code-principles.mdc must note that Phase B thresholds (>40 / >80)
    are deferred so no tool silently promotes them to a hard gate."""
    text = CLEAN_CODE_MDC.read_text(encoding="utf-8")
    assert "phase b" in text.lower() or "phase-b" in text.lower(), (
        ".cursor/rules/clean-code-principles.mdc must document that Phase B thresholds "
        "(>40 / >80 LOC) are deferred — not yet active as a hard gate."
    )
