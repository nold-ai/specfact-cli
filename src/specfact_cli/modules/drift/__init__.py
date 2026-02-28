"""Compatibility shim for legacy specfact_cli.modules.drift imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_codebase.drift")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.drift is deprecated; use specfact_codebase.drift instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
