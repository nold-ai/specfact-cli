"""Attach canonical pytest node IDs to JUnit cases for Requirements reconciliation."""

from __future__ import annotations

import platform
from collections.abc import Callable
from typing import Any

import pytest
from icontract import ensure


@pytest.fixture(autouse=True)
@ensure(lambda result: result is None)
def record_canonical_selector(request: Any, record_property: Callable[[str, object], None]) -> None:
    """Record the exact selector and proof process through pytest's public JUnit fixture."""
    record_property("specfact.selector", request.node.nodeid)
    record_property("specfact.runner", "pytest")
    record_property("specfact.python", platform.python_version())
    record_property("specfact.pytest", pytest.__version__)
