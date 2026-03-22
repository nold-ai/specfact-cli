"""Module entrypoint for bundle-mapper protocol compliance."""

from __future__ import annotations

from typing import Any, cast

import typer
from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.validation import ValidationReport
from specfact_cli.modules.module_io_shim import export_from_bundle, import_to_bundle, sync_with_bundle, validate_bundle


class _BundleMapperIO:
    """Expose standard module lifecycle I/O operations."""

    @beartype
    @require(lambda config: isinstance(config, dict), "config must be a dictionary")
    def import_to_bundle(self, source: Any, config: dict[str, Any]) -> Any:
        return import_to_bundle(source, config)

    @beartype
    @require(lambda config: isinstance(config, dict), "config must be a dictionary")
    @ensure(lambda result: result is None, "export returns None")
    def export_from_bundle(self, bundle: Any, target: Any, config: dict[str, Any]) -> None:
        export_from_bundle(bundle, target, config)

    @beartype
    @require(lambda external_source: bool(cast(str, external_source).strip()), "external_source must be non-empty")
    @require(lambda config: isinstance(config, dict), "config must be a dictionary")
    def sync_with_bundle(self, bundle: Any, external_source: str, config: dict[str, Any]) -> Any:
        return sync_with_bundle(bundle, external_source, config)

    @beartype
    @require(lambda rules: isinstance(rules, dict), "rules must be a dictionary")
    def validate_bundle(self, bundle: Any, rules: dict[str, Any]) -> ValidationReport:
        return validate_bundle(bundle, rules)


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
