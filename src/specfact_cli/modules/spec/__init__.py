"""Compatibility shim for legacy specfact_cli.modules.spec imports."""

import warnings
from importlib import import_module


_target = None


def __getattr__(name: str):
    global _target
    if _target is None:
        _target = import_module("specfact_spec.spec")
    warnings.warn(
        "specfact_cli.modules.spec is deprecated; use specfact_spec.spec instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
