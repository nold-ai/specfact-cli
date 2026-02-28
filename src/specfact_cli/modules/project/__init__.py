"""Compatibility shim for legacy specfact_cli.modules.project imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_project.project")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.project is deprecated; use specfact_project.project instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
