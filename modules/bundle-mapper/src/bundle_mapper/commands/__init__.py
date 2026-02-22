"""Command hooks and ModuleIOContract exports for bundle-mapper."""

from specfact_cli.contracts.module_interface import ModuleIOContract
from specfact_cli.modules import module_io_shim


_MODULE_IO_CONTRACT = ModuleIOContract
import_to_bundle = module_io_shim.import_to_bundle
export_from_bundle = module_io_shim.export_from_bundle
sync_with_bundle = module_io_shim.sync_with_bundle
validate_bundle = module_io_shim.validate_bundle
commands_interface = module_io_shim

__all__ = [
    "_MODULE_IO_CONTRACT",
    "commands_interface",
    "export_from_bundle",
    "import_to_bundle",
    "sync_with_bundle",
    "validate_bundle",
]
