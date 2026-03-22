# pyright: reportUnknownMemberType=false
"""Unit tests for BundleMapper engine."""

from __future__ import annotations

from pathlib import Path

import yaml
from bundle_mapper.mapper.engine import BundleMapper
from bundle_mapper.models.bundle_mapping import BundleMapping

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
    mapper: BundleMapper = BundleMapper(available_bundle_ids=["backend-services"])
    item = _item(tags=["bundle:backend-services"])
    m: BundleMapping = mapper.compute_mapping(item)
    assert m.primary_bundle_id == "backend-services"
    assert m.confidence >= 0.8


def test_explicit_label_invalid_bundle_ignored() -> None:
    mapper: BundleMapper = BundleMapper(available_bundle_ids=["backend-services"])
    item = _item(tags=["bundle:nonexistent"])
    m: BundleMapping = mapper.compute_mapping(item)
    assert m.primary_bundle_id is None
    assert m.confidence == 0.0


def test_no_signals_returns_none_zero_confidence() -> None:
    mapper: BundleMapper = BundleMapper(available_bundle_ids=[])
    item = _item(tags=[], title="Generic task")
    m: BundleMapping = mapper.compute_mapping(item)
    assert m.primary_bundle_id is None
    assert m.confidence == 0.0


def test_confidence_in_bounds() -> None:
    mapper: BundleMapper = BundleMapper(available_bundle_ids=["b"])
    item = _item(tags=["bundle:b"])
    m: BundleMapping = mapper.compute_mapping(item)
    assert 0.0 <= m.confidence <= 1.0


def test_weighted_calculation_explicit_dominates() -> None:
    mapper: BundleMapper = BundleMapper(available_bundle_ids=["backend"])
    item = _item(tags=["bundle:backend"])
    m: BundleMapping = mapper.compute_mapping(item)
    assert m.primary_bundle_id == "backend"
    assert m.confidence >= 0.8


def test_historical_mapping_ignores_stale_bundle_ids(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    key = "area=backend;assignee=alice;tags=bug,login"
    config_path.write_text(
        yaml.safe_dump(
            {
                "backlog": {
                    "bundle_mapping": {
                        "history": {
                            key: {
                                "counts": {
                                    "removed-bundle": 50,
                                    "backend-services": 2,
                                }
                            }
                        }
                    }
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    mapper: BundleMapper = BundleMapper(available_bundle_ids=["backend-services"], config_path=config_path)
    item = _item(assignees=["alice"], area="backend", tags=["bug", "login"])
    mapping: BundleMapping = mapper.compute_mapping(item)

    assert mapping.primary_bundle_id == "backend-services"


def test_conflicting_content_signal_does_not_increase_primary_confidence() -> None:
    mapper: BundleMapper = BundleMapper(
        available_bundle_ids=["alpha", "beta"],
        bundle_spec_keywords={"beta": {"beta"}},
    )
    item = _item(
        tags=["bundle:alpha"],
        title="beta",
    )

    mapping: BundleMapping = mapper.compute_mapping(item)

    assert mapping.primary_bundle_id == "alpha"
    assert mapping.confidence == 0.8
