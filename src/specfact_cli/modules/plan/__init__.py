"""Compatibility shim for legacy specfact_cli.modules.plan imports."""

import warnings
from importlib import import_module


_target = None


def __getattr__(name: str):
    global _target
    if _target is None:
        _target = import_module("specfact_project.plan")
    warnings.warn(
        "specfact_cli.modules.plan is deprecated; use specfact_project.plan instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
