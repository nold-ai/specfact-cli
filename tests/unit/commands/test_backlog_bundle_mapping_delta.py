from __future__ import annotations

from pathlib import Path

from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.modules.backlog.src import commands as backlog_commands


def _item(item_id: str, *, tags: list[str] | None = None) -> BacklogItem:
    return BacklogItem(
        id=item_id,
        provider="github",
        url=f"https://example.com/issues/{item_id}",
        title=f"Item {item_id}",
        body_markdown="Body",
        state="open",
        tags=tags or [],
        assignees=[],
    )


class _FakeMapping:
    def __init__(self, primary_bundle_id: str | None, confidence: float) -> None:
        self.primary_bundle_id = primary_bundle_id
        self.confidence = confidence
        self.candidates: list[tuple[str, float]] = []
        self.explained_reasoning = "test"


def test_route_bundle_mapping_auto_assign_high_confidence() -> None:
    called = {"prompted": False}

    def _prompt(_mapping: _FakeMapping, _bundles: list[str]) -> str | None:
        called["prompted"] = True
        return None

    selected = backlog_commands._route_bundle_mapping_decision(
        _FakeMapping("alpha", 0.91),
        available_bundle_ids=["alpha", "beta"],
        auto_assign_threshold=0.8,
        confirm_threshold=0.5,
        prompt_callback=_prompt,
    )
    assert selected == "alpha"
    assert called["prompted"] is False


def test_route_bundle_mapping_prompts_in_medium_band() -> None:
    def _prompt(_mapping: _FakeMapping, _bundles: list[str]) -> str | None:
        return "beta"

    selected = backlog_commands._route_bundle_mapping_decision(
        _FakeMapping("alpha", 0.62),
        available_bundle_ids=["alpha", "beta"],
        auto_assign_threshold=0.8,
        confirm_threshold=0.5,
        prompt_callback=_prompt,
    )
    assert selected == "beta"


def test_apply_bundle_mapping_runtime_persists_mapping_history(tmp_path: Path, monkeypatch) -> None:
    saved: list[tuple[str, str, Path | None]] = []

    class _FakeMapper:
        def __init__(self, available_bundle_ids, config_path=None, bundle_spec_keywords=None):
            self.available_bundle_ids = available_bundle_ids

        def compute_mapping(self, _item: BacklogItem) -> _FakeMapping:
            return _FakeMapping("core-platform", 0.95)

    def _fake_save(item: BacklogItem, bundle_id: str, config_path: Path | None = None) -> None:
        saved.append((item.id, bundle_id, config_path))

    def _fake_load(_config_path: Path | None = None) -> dict[str, float]:
        return {"auto_assign_threshold": 0.8, "confirm_threshold": 0.5}

    monkeypatch.setattr(
        backlog_commands,
        "_load_bundle_mapper_runtime_dependencies",
        lambda: (_FakeMapper, _fake_save, _fake_load, None),
    )

    mapped = backlog_commands._apply_bundle_mappings_for_items(
        items=[_item("42", tags=["bundle:core-platform"])],
        available_bundle_ids=["core-platform"],
        config_path=tmp_path / "config.yaml",
    )

    assert mapped == {"42": "core-platform"}
    assert saved == [("42", "core-platform", tmp_path / "config.yaml")]
