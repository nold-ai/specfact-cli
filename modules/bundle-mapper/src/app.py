"""Module entrypoint for bundle-mapper protocol compliance."""

from __future__ import annotations

from typing import Any

import typer

from specfact_cli.modules.module_io_shim import export_from_bundle, import_to_bundle, sync_with_bundle, validate_bundle


class _BundleMapperIO:
    """Expose standard module lifecycle I/O operations."""

    def import_to_bundle(self, bundle: Any, payload: dict[str, Any]) -> Any:
        return import_to_bundle(bundle, payload)

    def export_from_bundle(self, bundle: Any) -> dict[str, Any]:
        return export_from_bundle(bundle)

    def sync_with_bundle(self, bundle: Any, external_state: dict[str, Any]) -> Any:
        return sync_with_bundle(bundle, external_state)

    def validate_bundle(self, bundle: Any) -> dict[str, Any]:
        return validate_bundle(bundle)


runtime_interface = _BundleMapperIO()
app = typer.Typer(help="Bundle mapper module")

__all__ = [
    "app",
    "export_from_bundle",
    "import_to_bundle",
    "runtime_interface",
    "sync_with_bundle",
    "validate_bundle",
]
