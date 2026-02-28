"""Compatibility shim for legacy specfact_cli.modules.sync imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_project.sync")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.sync is deprecated; use specfact_project.sync instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
