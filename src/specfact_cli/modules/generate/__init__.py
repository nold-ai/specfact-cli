"""Compatibility shim for legacy specfact_cli.modules.generate imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_spec.generate")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.generate is deprecated; use specfact_spec.generate instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
