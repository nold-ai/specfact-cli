"""Compatibility alias for legacy specfact_cli.modules.policy_engine.src.commands module."""

import sys
from importlib import import_module

from specfact_cli.modules import module_io_shim
from specfact_cli.modules._bundle_import import bootstrap_local_bundle_sources


bootstrap_local_bundle_sources(__file__)
_target = import_module("specfact_backlog.policy_engine.commands")
sys.modules[__name__] = _target

app = _target.app

import_to_bundle = module_io_shim.import_to_bundle
export_from_bundle = module_io_shim.export_from_bundle
sync_with_bundle = module_io_shim.sync_with_bundle
validate_bundle = module_io_shim.validate_bundle


__all__ = [
    "app",
    "export_from_bundle",
    "import_to_bundle",
    "sync_with_bundle",
    "validate_bundle",
]
