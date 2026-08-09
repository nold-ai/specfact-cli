"""Attach canonical pytest node IDs to JUnit cases for Requirements reconciliation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from icontract import ensure


@pytest.fixture(autouse=True)
@ensure(lambda result: result is None)
def record_canonical_selector(request: Any, record_property: Callable[[str, object], None]) -> None:
    """Record the exact collected node ID through pytest's public JUnit fixture."""
    record_property("specfact.selector", request.node.nodeid)
