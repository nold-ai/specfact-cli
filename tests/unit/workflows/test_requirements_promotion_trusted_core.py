"""Regression tests for main-relative Requirements promotion inputs."""

from pathlib import Path
from typing import Any, cast

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "requirements-evidence.yml"
LEGACY_BASE = "b1e517e60e669eaba15a18ecfa83ef5a9df65276"
REVIEW_SOURCE = "3ea3d9b4492ade6ec5683fac83c5b5090b0cb547"
REVIEW_TREE = "4d61f0420952b5c3913aa7c771a154c2913a9e14"
REVIEW_INPUT_BLOB = "6f0f16ba49e10d6b4f4132c112e3b4c5855e850f"
REVIEW_LOCK_BLOB = "bf0033c19cada1b656beb818e43366828ce6fabb"
BASE_TO_SOURCE_ANCESTRY = 'git merge-base --is-ancestor "$base_commit" "$review_source"'
SOURCE_TO_HEAD_ANCESTRY = 'git merge-base --is-ancestor "$review_source" HEAD'
BASE_RELATIVE_REVIEW_SOURCE = 'review_source="$base_commit"'
INPUT_PRESENT_DEFAULT = "review_input_present=false"
LOCK_PRESENT_DEFAULT = "review_lock_present=false"
INPUT_PRESENT_PROBE = 'if git cat-file -e "${base_commit}:requirements/code-review/requirements.in"'
LOCK_PRESENT_PROBE = 'if git cat-file -e "${base_commit}:requirements/code-review/locked.txt"'
PAIR_DISPATCH = 'case "${review_input_present}:${review_lock_present}" in'
PRESENT_PAIR_CASE = "true:true)"
ABSENT_PAIR_CASE = "false:false)"
MIXED_INPUT_ONLY_CASE = "true:false)"
MIXED_LOCK_ONLY_CASE = "false:true)"
INVALID_PAIR_CASE = "*)"
REVIEW_PATHS = (
    "requirements/code-review/requirements.in",
    "requirements/code-review/locked.txt",
)


def _step_command(name: str) -> str:
    """Return one named workflow step command."""
    parsed = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    jobs = cast(dict[str, Any], parsed["jobs"])
    for job in jobs.values():
        for step in job.get("steps", []):
            if step.get("name") == name:
                return cast(str, step["run"])
    raise AssertionError(f"Missing workflow step: {name}")


def _archive_block(command: str, source: str) -> str:
    """Return one archive argument block for an exact source expression."""
    marker = f'git archive "{source}" --'
    assert marker in command
    return command.split(marker, maxsplit=1)[1].split("| tar -x -C", maxsplit=1)[0]


def _assert_bootstrap_identities(command: str) -> None:
    """Require both source archives and every immutable bootstrap identity."""
    assert command.count("git archive ") == 2
    assert BASE_RELATIVE_REVIEW_SOURCE in command
    assert INPUT_PRESENT_DEFAULT in command
    assert LOCK_PRESENT_DEFAULT in command
    assert INPUT_PRESENT_PROBE in command
    assert LOCK_PRESENT_PROBE in command
    assert PAIR_DISPATCH in command
    assert f'test "$base_commit" = "{LEGACY_BASE}"' in command
    assert f'review_source="{REVIEW_SOURCE}"' in command
    assert REVIEW_TREE in command
    assert REVIEW_INPUT_BLOB in command
    assert REVIEW_LOCK_BLOB in command
    assert BASE_TO_SOURCE_ANCESTRY in command
    assert SOURCE_TO_HEAD_ANCESTRY in command


def _assert_bootstrap_order(command: str) -> None:
    """Require the base-relative default and fail-closed exception ordering."""
    assert command.index(BASE_RELATIVE_REVIEW_SOURCE) < command.index(INPUT_PRESENT_DEFAULT)
    assert command.index(INPUT_PRESENT_DEFAULT) < command.index(INPUT_PRESENT_PROBE)
    assert command.index(LOCK_PRESENT_DEFAULT) < command.index(LOCK_PRESENT_PROBE)
    assert command.index(LOCK_PRESENT_PROBE) < command.index(PAIR_DISPATCH)


def _case_block(command: str, label: str, next_label: str) -> str:
    """Return one exact state-dispatch branch body."""
    return command.split(label, maxsplit=1)[1].split(next_label, maxsplit=1)[0]


def _assert_pair_state_contract(command: str) -> None:
    """Require complete pairs to proceed and both mixed permutations to reject."""
    present_block = _case_block(command, PRESENT_PAIR_CASE, ABSENT_PAIR_CASE)
    absent_block = _case_block(command, ABSENT_PAIR_CASE, MIXED_INPUT_ONLY_CASE)
    input_only_block = _case_block(command, MIXED_INPUT_ONLY_CASE, MIXED_LOCK_ONLY_CASE)
    lock_only_block = _case_block(command, MIXED_LOCK_ONLY_CASE, INVALID_PAIR_CASE)
    invalid_block = command.split(INVALID_PAIR_CASE, maxsplit=1)[1].split("esac", maxsplit=1)[0]
    assert 'review_source="' not in present_block
    assert f'test "$base_commit" = "{LEGACY_BASE}"' in absent_block
    assert f'review_source="{REVIEW_SOURCE}"' in absent_block
    assert "exit 1" in input_only_block
    assert "exit 1" in lock_only_block
    assert "exit 1" in invalid_block


def _assert_archive_sources(command: str) -> None:
    """Require only Code Review inputs to come from the review source."""
    base_archive = _archive_block(command, "$base_commit")
    review_archive = _archive_block(command, "$review_source")
    for path in REVIEW_PATHS:
        assert path not in base_archive
        assert path in review_archive
        assert f'/{path}"' in command


def _assert_materialization_contract(command: str) -> None:
    """Require the immutable legacy bootstrap and normal base-relative path."""
    _assert_bootstrap_identities(command)
    _assert_bootstrap_order(command)
    _assert_pair_state_contract(command)
    _assert_archive_sources(command)


def test_promotion_trusted_core_materializes_from_exact_main_base() -> None:
    """Both materializers must bind the exact exception and its base-relative sunset."""
    for step_name in (
        "Materialize trusted Requirements core",
        "Materialize trusted final Requirements core",
    ):
        command = _step_command(step_name)
        _assert_materialization_contract(command)
        for required_contract, invalid_replacement in (
            (BASE_TO_SOURCE_ANCESTRY, "true"),
            (BASE_RELATIVE_REVIEW_SOURCE, 'review_source="HEAD"'),
            (MIXED_INPUT_ONLY_CASE, "true:false|false:true)"),
            (MIXED_LOCK_ONLY_CASE, "unreachable:false)"),
        ):
            invalid_command = command.replace(required_contract, invalid_replacement, 1)
            try:
                _assert_materialization_contract(invalid_command)
            except AssertionError:
                continue
            raise AssertionError(f"{step_name} accepted an invalid bootstrap relationship")
