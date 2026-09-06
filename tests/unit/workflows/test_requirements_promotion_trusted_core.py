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


def _assert_materialization_contract(command: str) -> None:
    """Require the immutable legacy bootstrap and normal base-relative path."""
    assert command.count("git archive ") == 2
    assert f'test "$base_commit" = "{LEGACY_BASE}"' in command
    assert f'review_source="{REVIEW_SOURCE}"' in command
    assert REVIEW_TREE in command
    assert REVIEW_INPUT_BLOB in command
    assert REVIEW_LOCK_BLOB in command
    assert BASE_TO_SOURCE_ANCESTRY in command
    assert SOURCE_TO_HEAD_ANCESTRY in command

    base_archive = _archive_block(command, "$base_commit")
    review_archive = _archive_block(command, "$review_source")
    for path in REVIEW_PATHS:
        assert path not in base_archive
        assert path in review_archive
        assert f'/{path}"' in command


def test_promotion_trusted_core_materializes_from_exact_main_base() -> None:
    """Both materializers must bind one exact source and reject missing ancestry."""
    for step_name in (
        "Materialize trusted Requirements core",
        "Materialize trusted final Requirements core",
    ):
        command = _step_command(step_name)
        _assert_materialization_contract(command)
        invalid_ancestry = command.replace(BASE_TO_SOURCE_ANCESTRY, "true", 1)
        try:
            _assert_materialization_contract(invalid_ancestry)
        except AssertionError:
            continue
        raise AssertionError(f"{step_name} accepted a missing base-to-source ancestry guard")
