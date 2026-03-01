"""Compatibility shim for legacy specfact_cli.modules.sdd imports."""

import warnings
from importlib import import_module


_target = None


def __getattr__(name: str):
    global _target
    if _target is None:
        _target = import_module("specfact_spec.sdd")
    warnings.warn(
        "specfact_cli.modules.sdd is deprecated; use specfact_spec.sdd instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
