"""Compatibility shim for legacy specfact_cli.modules.sdd imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_spec.sdd")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.sdd is deprecated; use specfact_spec.sdd instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
