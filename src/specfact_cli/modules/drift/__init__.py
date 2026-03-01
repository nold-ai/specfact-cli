"""Compatibility shim for legacy specfact_cli.modules.drift imports."""

import warnings
from importlib import import_module


_target = None


def __getattr__(name: str):
    global _target
    if _target is None:
        _target = import_module("specfact_codebase.drift")
    warnings.warn(
        "specfact_cli.modules.drift is deprecated; use specfact_codebase.drift instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
