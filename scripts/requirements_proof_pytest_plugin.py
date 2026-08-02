"""Attach canonical pytest node IDs to JUnit cases for Requirements reconciliation."""

from __future__ import annotations

from typing import Any, cast

import pytest
from _pytest.junitxml import xml_key
from icontract import ensure


pytest_runtime = cast(Any, pytest)


class CanonicalSelectorPlugin:
    """Add the exact collected node ID without reconstructing it from JUnit labels."""

    junit_xml: Any | None = None
    reported_node_ids: set[str] = set()

    @ensure(lambda result: result is None)
    def pytest_sessionstart(self, session: Any) -> None:
        self.junit_xml = session.config.stash.get(xml_key, None)
        self.reported_node_ids = set()

    @pytest_runtime.hookimpl(tryfirst=True)
    @ensure(lambda result: result is None)
    def pytest_runtest_logreport(self, report: Any) -> None:
        if self.junit_xml is None or report.nodeid in self.reported_node_ids:
            return
        self.junit_xml.node_reporter(report).add_property("specfact.selector", report.nodeid)
        self.reported_node_ids.add(report.nodeid)


plugin = CanonicalSelectorPlugin()


@ensure(lambda result: result is None)
def pytest_configure(config: Any) -> None:
    """Register a stateful hook object after pytest configures the JUnit plugin."""
    config.pluginmanager.register(plugin, "specfact-canonical-selector")
