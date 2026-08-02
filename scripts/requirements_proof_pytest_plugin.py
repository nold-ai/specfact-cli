"""Attach canonical pytest node IDs to JUnit cases for Requirements reconciliation."""

from __future__ import annotations

from typing import Any

import pytest
from _pytest.junitxml import xml_key


class CanonicalSelectorPlugin:
    """Add the exact collected node ID without reconstructing it from JUnit labels."""

    junit_xml: Any | None = None

    def pytest_sessionstart(self, session: Any) -> None:
        self.junit_xml = session.config.stash.get(xml_key, None)

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logreport(self, report: Any) -> None:
        if report.when != "call" or self.junit_xml is None:
            return
        self.junit_xml.node_reporter(report).add_property("specfact.selector", report.nodeid)


plugin = CanonicalSelectorPlugin()


def pytest_configure(config: Any) -> None:
    """Register a stateful hook object after pytest configures the JUnit plugin."""
    config.pluginmanager.register(plugin, "specfact-canonical-selector")
