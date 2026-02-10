"""Regression tests for side-effect free contracts package imports."""

from __future__ import annotations

import importlib
import sys


def test_crosshair_props_import_does_not_load_models_package() -> None:
    """Importing crosshair props should not eagerly import specfact_cli.models."""
    for module_name in list(sys.modules):
        if module_name == "specfact_cli.contracts" or module_name.startswith("specfact_cli.contracts."):
            sys.modules.pop(module_name, None)
        if module_name == "specfact_cli.models" or module_name.startswith("specfact_cli.models."):
            sys.modules.pop(module_name, None)

    module = importlib.import_module("specfact_cli.contracts.crosshair_props")

    assert module is not None
    assert "specfact_cli.models" not in sys.modules
