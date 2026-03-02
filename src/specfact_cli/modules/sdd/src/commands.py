"""Compatibility alias for legacy specfact_cli.modules.sdd.src.commands module."""

import sys
from importlib import import_module

from specfact_cli.modules._bundle_import import bootstrap_local_bundle_sources


bootstrap_local_bundle_sources(__file__)
_target = import_module("specfact_spec.sdd.commands")

# Ensure monkeypatch/mock targets on this legacy import path affect the real
# command module used by Typer callbacks.
sys.modules[__name__] = _target
