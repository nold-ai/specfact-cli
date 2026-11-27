"""A signed source can reuse evidence only from the protected producer."""

from pathlib import Path

import pytest

from tests.unit.scripts.test_requirements_promotion_reuse import (
    PREVIOUS_DEV_SHA,
    SOURCE_SHA,
    WORKFLOW_BLOB,
    WORKFLOW_PATH,
    _signed_topic_fixture,
    _validate_signed_topic,
)


@pytest.mark.parametrize(
    ("commit", "replacement"),
    [(SOURCE_SHA, "b" * 40), (PREVIOUS_DEV_SHA, "b" * 40), (SOURCE_SHA, "invalid")],
)
def test_signed_topic_rejects_untrusted_producer_workflow(tmp_path: Path, commit: str, replacement: str) -> None:
    fixture, commits = _signed_topic_fixture(tmp_path)
    fixture.git_outputs[("rev-parse", "--verify", f"{commit}:{WORKFLOW_PATH}")] = replacement
    fixture.git_outputs[("cat-file", "-t", replacement)] = "blob"

    with pytest.raises(ValueError, match="promotion-reuse-invalid"):
        _validate_signed_topic(fixture, commits)


def test_signed_topic_rejects_non_blob_producer(tmp_path: Path) -> None:
    fixture, commits = _signed_topic_fixture(tmp_path)
    fixture.git_outputs[("cat-file", "-t", WORKFLOW_BLOB)] = "tree"

    with pytest.raises(ValueError, match="promotion-reuse-invalid"):
        _validate_signed_topic(fixture, commits)
