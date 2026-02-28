"""Compatibility shim for legacy specfact_cli.modules.enforce imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_govern.enforce")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.enforce is deprecated; use specfact_govern.enforce instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
