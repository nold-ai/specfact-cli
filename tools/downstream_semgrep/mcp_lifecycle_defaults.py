from __future__ import annotations

import inspect
import unittest
from collections.abc import Callable
from typing import Protocol, cast

from icontract import ensure


class _ManagerDefaults(Protocol):
    max_sessions: int
    session_idle_timeout: float | None


@ensure(lambda result: result is None)
def assert_fixed_defaults(test: unittest.TestCase, manager_factory: Callable[..., object], app: object) -> None:
    """:raises AssertionError: The constructor signature or defaults violate the required policy."""
    parameters = inspect.signature(manager_factory).parameters
    test.assertIn("session_idle_timeout", parameters)
    test.assertIn("max_sessions", parameters)
    manager = cast(_ManagerDefaults, manager_factory(app, json_response=True))
    test.assertEqual(manager.session_idle_timeout, 1800)
    test.assertEqual(manager.max_sessions, 10000)
