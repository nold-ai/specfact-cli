"""Compatibility shim for legacy specfact_cli.modules.repro imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_codebase.repro")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.repro is deprecated; use specfact_codebase.repro instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
