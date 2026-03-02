"""Module IO contract tests for backlog module."""

from __future__ import annotations

import inspect

import pytest

pytest.importorskip("specfact_cli.modules.backlog.src.commands")
from specfact_cli.modules.backlog.src import commands as module_commands


REQUIRED_METHODS = [
    "import_to_bundle",
    "export_from_bundle",
    "sync_with_bundle",
    "validate_bundle",
]


def test_module_implements_protocol() -> None:
    for method_name in REQUIRED_METHODS:
        assert hasattr(module_commands, method_name)


def test_import_to_bundle_signature() -> None:
    signature = inspect.signature(module_commands.import_to_bundle)
    assert set(signature.parameters.keys()) == {"source", "config"}


def test_export_from_bundle_signature() -> None:
    signature = inspect.signature(module_commands.export_from_bundle)
    assert set(signature.parameters.keys()) == {"bundle", "target", "config"}


def test_methods_have_contracts() -> None:
    for method_name in REQUIRED_METHODS:
        method = getattr(module_commands, method_name)
        assert hasattr(method, "__wrapped__")
        assert hasattr(method, "__preconditions__")
        assert hasattr(method, "__postconditions__")
