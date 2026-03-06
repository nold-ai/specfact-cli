"""Backward-compatible app shim for spec sdd command."""

from typing import TYPE_CHECKING, Any

from ._bundle_shim import load_bundle_app


if TYPE_CHECKING:
    app: Any


def __getattr__(name: str) -> Any:
    if name == "app":
        return load_bundle_app(__file__, "specfact_spec.sdd.commands")
    raise AttributeError(name)


__all__ = ["app"]
