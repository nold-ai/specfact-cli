"""Contract exports for protocol and validation integrations.

Keep this package import side-effect free so CrossHair can import
``specfact_cli.contracts.crosshair_props`` without loading heavy model/utils
packages that trigger subprocess-based initializers.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from specfact_cli.contracts import crosshair_props as crosshair_props
    from specfact_cli.models.validation import ValidationReport


__all__ = ["ValidationReport", "crosshair_props"]


def __getattr__(name: str) -> Any:
    """Lazily resolve exported symbols to avoid import-time side effects."""
    if name == "ValidationReport":
        from specfact_cli.models.validation import ValidationReport as _ValidationReport

        return _ValidationReport
    if name == "crosshair_props":
        return import_module(".crosshair_props", __name__)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
