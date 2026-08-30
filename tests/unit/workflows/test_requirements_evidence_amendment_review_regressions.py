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


def test_exact_external_amendment_bootstraps_later_generic_cycle_selection() -> None:
    """A verified external green must remain usable for later same-PR review cycles."""
    command = _cycle_command()
    bootstrap = command.index("python scripts/requirements_amendment_bootstrap.py")
    cycle_function = command.index("try_cycle_base()")
    special_case = command[bootstrap:cycle_function]

    bootstrap_controls = (
        '--authority-output "$external_authority_file"',
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
