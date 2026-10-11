"""A stale stack root cannot reuse proof from obsolete protected controls."""

from __future__ import annotations

import pytest

from tests.unit.scripts.test_requirements_planning_stack_context import (
    StackCase,
    _case,
    _commit,
    _git,
    _resolve,
    planning_case as planning_case,
)


@pytest.mark.parametrize(
    "control_path",
    (
        ".github/workflows/requirements-evidence.yml",
        ".github/workflows/trusted-requirements-authority.yml",
        ".github/actions/setup-frozen-python/action.yml",
    ),
)
def test_current_protected_controls_block_stale_root_reuse(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
    control_path: str,
) -> None:
    """Exact successful old-root checks cannot substitute for current control bytes."""
    _git(planning_case.repo, "checkout", "--detach", planning_case.baseline)
    protected = _commit(planning_case.repo, control_path, "updated protected security control\n")
    stale = _case(planning_case.repo, protected, planning_case.root, planning_case.child)
    result, context = _resolve(stale, monkeypatch)
    assert result == 0
    assert context["proof_base_commit"] == planning_case.baseline
    assert "planning_base_commit" not in context
    assert "inherited_proof" not in context


def test_unrelated_protected_update_preserves_authenticated_planning(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A newer protected docs commit does not invalidate identical proof controls."""
    _git(planning_case.repo, "checkout", "--detach", planning_case.baseline)
    protected = _commit(planning_case.repo, "docs/protected-note.md", "updated protected documentation\n")
    unchanged = _case(planning_case.repo, protected, planning_case.root, planning_case.child)
    result, context = _resolve(unchanged, monkeypatch)
    assert result == 0
    assert context["proof_base_commit"] == planning_case.baseline
    assert context.get("planning_base_commit") == planning_case.root


def test_root_modified_authority_workflow_keeps_full_proof(
    planning_case: StackCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A successful root-authored authority workflow cannot authorize inherited proof."""
    _git(planning_case.repo, "checkout", "--detach", planning_case.root)
    root = _commit(
        planning_case.repo, ".github/workflows/trusted-requirements-authority.yml", "candidate authority success\n"
    )
    child = _commit(planning_case.repo, "openspec/changes/deferred-feature/proposal.md", "deferred proposal\n")
    changed = _case(planning_case.repo, planning_case.baseline, root, child)
    result, context = _resolve(changed, monkeypatch)
    assert result == 0
    assert "planning_base_commit" not in context
    assert "inherited_proof" not in context
