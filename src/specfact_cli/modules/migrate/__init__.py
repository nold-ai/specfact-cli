"""Compatibility shim for legacy specfact_cli.modules.migrate imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_project.migrate")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.migrate is deprecated; use specfact_project.migrate instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
