"""Backlog-core command entrypoints."""

from specfact_cli.contracts.module_interface import ModuleIOContract
from specfact_cli.modules import module_io_shim

from .add import add
from .analyze_deps import analyze_deps, trace_impact
from .diff import diff
from .promote import promote
from .release_notes import generate_release_notes
from .sync import BacklogGraphToPlanBundle, compute_delta, sync
from .verify import verify_readiness


_MODULE_IO_CONTRACT = ModuleIOContract
import_to_bundle = module_io_shim.import_to_bundle
export_from_bundle = module_io_shim.export_from_bundle
sync_with_bundle = module_io_shim.sync_with_bundle
validate_bundle = module_io_shim.validate_bundle
commands_interface = module_io_shim

__all__ = [
    "BacklogGraphToPlanBundle",
    "add",
    "analyze_deps",
    "commands_interface",
    "compute_delta",
    "diff",
    "export_from_bundle",
    "generate_release_notes",
    "import_to_bundle",
    "promote",
    "sync",
    "sync_with_bundle",
    "trace_impact",
    "validate_bundle",
    "verify_readiness",
]
