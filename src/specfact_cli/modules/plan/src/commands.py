"""Compatibility alias for legacy specfact_cli.modules.plan.src.commands module."""

import sys
from importlib import import_module


_target = import_module("specfact_project.plan.commands")

# Ensure monkeypatch/mock targets on this legacy import path affect the real
# command module used by Typer callbacks.
sys.modules[__name__] = _target
