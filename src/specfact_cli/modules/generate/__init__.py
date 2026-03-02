"""Compatibility shim for legacy specfact_cli.modules.generate imports."""

import warnings
from importlib import import_module


_target = None


def __getattr__(name: str):
    global _target
    if _target is None:
        _target = import_module("specfact_spec.generate")
    warnings.warn(
        "specfact_cli.modules.generate is deprecated; use specfact_spec.generate instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
