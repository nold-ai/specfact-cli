"""Review regressions for repeatable Requirements amendment cycles."""

from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


def _cycle_command() -> str:
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    jobs = parsed["jobs"]
    evidence = jobs["requirements-evidence"]
    step = next(item for item in evidence["steps"] if item.get("name") == "Locate verified amendment cycle base")
    command = step["run"]
    assert isinstance(command, str)
    return command


def _retained_red_command() -> str:
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = parsed["jobs"]["requirements-evidence"]["steps"]
    step = next(item for item in steps if item.get("name") == "Locate retained red proof run")
    command = step["run"]
    assert isinstance(command, str)
    return command


def _amendment_selection_command() -> str:
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = parsed["jobs"]["requirements-evidence"]["steps"]
    step = next(item for item in steps if item.get("name") == "Select amendment OpenSpec change")
    command = step["run"]
    assert isinstance(command, str)
    return command


def _workflow_steps() -> list[dict[str, object]]:
    """Return the Requirements workflow steps for focused static assertions."""
    workflow = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
    parsed = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    return parsed["jobs"]["requirements-evidence"]["steps"]


def test_amendment_cycle_recovers_the_authenticated_red_source() -> None:
    """Later fixes validate the prior green against the retained red commit, not final HEAD."""
    command = _cycle_command()

    assert 'try_cycle_base "$current_head"' in command
    assert 'select(.conclusion == "failure")' in command
    assert 'try_cycle_base "$candidate_red_ref" "${proof_root}/red.json"' in command
    assert '--red-ref "$candidate_red_ref"' in command
    assert '--prior-red-proof "$red_proof"' in command
    assert '--final-ref "$current_head"' in command


def test_amendment_cycle_authenticates_proof_before_exporting_authority() -> None:
    """An untrusted failed run cannot select a cycle base for downstream evidence."""
    command = _cycle_command()
    verification = command.index('--prior-red-proof "$red_proof"')
    export = command.index('printf "source-ref=%s\\n" "$head_sha"')

    assert verification < export


def test_amendment_cycle_binds_one_preselected_active_change() -> None:
    """Cycle validators receive one exact active change ID before trusting red history."""
    selection = _amendment_selection_command()
    cycle = _cycle_command()
    retained = _retained_red_command()

    assert 'git diff --name-only -z "origin/${GITHUB_BASE_REF}...HEAD"' in selection
    assert '[[ "${#active_change_ids[@]}" -eq 1 ]]' in selection
    assert 'git ls-tree -d HEAD -- "openspec/changes/${change_id}"' in selection
    assert "printf 'change-id=%s\\n' \"$selected_change\"" in selection
    assert cycle.count('--change-id "$EVIDENCE_CHANGE_ID"') == 4
    assert '--change-id "$EVIDENCE_CHANGE_ID"' in retained


def test_amendment_workflow_supports_verified_cycle_selection() -> None:
    """The workflow binds a verified cycle source without replacing the PR base."""
    steps = _workflow_steps()
    cycle = next(item for item in steps if item.get("name") == "Locate verified amendment cycle base")
    evidence = next(item for item in steps if item.get("name") == "Run Requirements evidence gate")
    cycle_command = cycle["run"]
    evidence_command = evidence["run"]
    environment = evidence["env"]

    assert isinstance(cycle_command, str)
    assert isinstance(evidence_command, str)
    assert isinstance(environment, dict)
    assert 'git merge-base --is-ancestor "$head_sha" "$current_head"' in cycle_command
    assert '--pull-request "$EVIDENCE_PULL_REQUEST"' in cycle_command
    assert environment["EVIDENCE_CYCLE_BASE"] == "${{ steps.cycle-base.outputs.source-ref }}"
    assert 'cycle_base_ref="${EVIDENCE_CYCLE_BASE:-origin/${EVIDENCE_BASE_BRANCH}}"' in evidence_command
    assert '--base-ref "origin/${EVIDENCE_BASE_BRANCH}"' in evidence_command


def test_amendment_workflow_code_review_node_setup_has_no_persistent_cache() -> None:
    """The reviewed Node setup must not restore or save a persistent npm cache."""
    setup = next(item for item in _workflow_steps() if item.get("name") == "Set up reviewed Code Review Node runtime")
    inputs = setup.get("with", {})

    assert isinstance(inputs, dict)
    assert "cache" not in inputs
    assert "cache-dependency-path" not in inputs


def test_exact_external_amendment_bootstraps_later_generic_cycle_selection() -> None:
    """A verified external green must remain usable for later same-PR review cycles."""
    command = _cycle_command()
    bootstrap = command.index("python scripts/requirements_amendment_bootstrap.py")
    cycle_function = command.index("try_cycle_base()")
    special_case = command[bootstrap:cycle_function]

    bootstrap_controls = (
        '--authority-output "$external_authority_file"',
        '"repos/${GITHUB_REPOSITORY}/issues/692/comments?per_page=100"',
        '--producer-comments "${bootstrap_root}/producer-comments.json"',
        "python scripts/requirements_proof_provenance.py",
        '--bind-red-proof "${external_proof_root}/red.json"',
        '--cycle-authority "$external_authority_file"',
        '--output "${external_proof_root}/red.json"',
    )
    cycle_controls = (
        "external_authority_digest=",
        '--external-authority-digest "$external_authority_digest"',
        'external_proof_root="${RUNNER_TEMP}/external-prior-red-proof"',
        'cp "${external_proof_root}/red.json" "${proof_root}/red.json"',
        'cp "${external_proof_root}/red.xml" "${proof_root}/red.xml"',
        'if try_cycle_base "$current_head"; then',
    )
    assert all(control in special_case for control in bootstrap_controls)
    assert all(control in command for control in cycle_controls)
    assert command.index('if try_cycle_base "$current_head"; then') > cycle_function


def test_retained_red_lookup_omits_empty_cycle_authority() -> None:
    """Ordinary proof reuse must not turn an empty authority output into the repository path."""
    command = _retained_red_command()

    assert "cycle_authority_arguments=()" in command
    assert 'if [[ -n "$cycle_authority" ]]; then' in command
    assert '"${cycle_authority_arguments[@]}"' in command
    assert '--cycle-authority "${{ steps.cycle-base.outputs.authority }}"' not in command
