"""Unit tests for BundleMapper engine."""

from __future__ import annotations

from bundle_mapper.mapper.engine import BundleMapper

from specfact_cli.models.backlog_item import BacklogItem


def _item(
    id_: str = "1",
    title: str = "Fix login",
    tags: list[str] | None = None,
    assignees: list[str] | None = None,
    area: str | None = None,
    body: str = "",
) -> BacklogItem:
    return BacklogItem(
        id=id_,
        provider="github",
        url="https://github.com/r/1",
        title=title,
        body_markdown=body,
        state="open",
        tags=tags or [],
        assignees=assignees or [],
        area=area,
    )


def test_explicit_label_valid_bundle() -> None:
    mapper = BundleMapper(available_bundle_ids=["backend-services"])
    item = _item(tags=["bundle:backend-services"])
    m = mapper.compute_mapping(item)
    assert m.primary_bundle_id == "backend-services"
    assert m.confidence >= 0.8


def test_explicit_label_invalid_bundle_ignored() -> None:
    mapper = BundleMapper(available_bundle_ids=["backend-services"])
    item = _item(tags=["bundle:nonexistent"])
    m = mapper.compute_mapping(item)
    assert m.primary_bundle_id is None
    assert m.confidence == 0.0


def test_no_signals_returns_none_zero_confidence() -> None:
    mapper = BundleMapper(available_bundle_ids=[])
    item = _item(tags=[], title="Generic task")
    m = mapper.compute_mapping(item)
    assert m.primary_bundle_id is None
    assert m.confidence == 0.0


def test_confidence_in_bounds() -> None:
    mapper = BundleMapper(available_bundle_ids=["b"])
    item = _item(tags=["bundle:b"])
    m = mapper.compute_mapping(item)
    assert 0.0 <= m.confidence <= 1.0


def test_weighted_calculation_explicit_dominates() -> None:
    mapper = BundleMapper(available_bundle_ids=["backend"])
    item = _item(tags=["bundle:backend"])
    m = mapper.compute_mapping(item)
    assert m.primary_bundle_id == "backend"
    assert m.confidence >= 0.8
