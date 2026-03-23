# pyright: reportUnknownMemberType=false
"""Unit tests for BundleMapping model."""

from __future__ import annotations

import pytest
from bundle_mapper.models.bundle_mapping import BundleMapping


def test_bundle_mapping_defaults() -> None:
    m: BundleMapping = BundleMapping()
    assert m.primary_bundle_id is None
    assert m.confidence == 0.0
    assert m.candidates == []
    assert m.explained_reasoning == ""


def test_bundle_mapping_with_values() -> None:
    m: BundleMapping = BundleMapping(
        primary_bundle_id="backend",
        confidence=0.9,
        candidates=[("api", 0.5)],
        explained_reasoning="Explicit label",
    )
    assert m.primary_bundle_id == "backend"
    assert m.confidence == 0.9


def test_bundle_mapping_confidence_bounds() -> None:
    BundleMapping(confidence=0.0)
    BundleMapping(confidence=1.0)
    with pytest.raises(ValueError):
        BundleMapping(confidence=-0.1)
    with pytest.raises(ValueError):
        BundleMapping(confidence=1.1)
