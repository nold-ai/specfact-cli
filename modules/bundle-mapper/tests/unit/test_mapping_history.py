"""Unit tests for mapping history persistence."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from bundle_mapper.mapper.history import (
    item_key,
    item_keys_similar,
    load_bundle_mapping_config,
    save_user_confirmed_mapping,
)

from specfact_cli.models.backlog_item import BacklogItem


def _item(
    assignees: list[str] | None = None,
    area: str | None = None,
    tags: list[str] | None = None,
) -> BacklogItem:
    return BacklogItem(
        id="1",
        provider="github",
        url="https://x/1",
        title="T",
        state="open",
        assignees=assignees or [],
        area=area,
        tags=tags or [],
    )


def test_item_key() -> None:
    item = _item(assignees=["alice"], area="backend", tags=["bug"])
    k = item_key(item)
    assert "alice" in k
    assert "backend" in k


def test_item_keys_similar_two_components() -> None:
    k1 = "area=be|assignee=alice|tags=a"
    k2 = "area=be|assignee=alice|tags=b"
    assert item_keys_similar(k1, k2) is True


def test_item_keys_similar_empty_fields_not_counted() -> None:
    """Items with only empty area/assignee/tags must not be considered similar."""
    k1 = "area=|assignee=|tags="
    k2 = "area=|assignee=|tags="
    assert item_keys_similar(k1, k2) is False


def test_save_user_confirmed_mapping_increments_history() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.yaml"
        item = _item(assignees=["bob"], area="api")
        save_user_confirmed_mapping(item, "backend-services", config_path=config_path)
        save_user_confirmed_mapping(item, "backend-services", config_path=config_path)
        cfg = load_bundle_mapping_config(config_path=config_path)
        history = cfg.get("history", {})
        assert len(history) >= 1
        for entry in history.values():
            counts = entry.get("counts", {})
            if "backend-services" in counts:
                assert counts["backend-services"] == 2
                break
        else:
            pytest.fail("Expected backend-services in history counts")
