"""ModuleIOContract shim for policy-engine."""

from __future__ import annotations

from specfact_cli.modules import module_io_shim

from .policy_engine.main import app


# Expose standard ModuleIOContract operations for protocol compliance discovery.
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
