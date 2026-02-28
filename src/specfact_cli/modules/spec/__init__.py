"""Compatibility shim for legacy specfact_cli.modules.spec imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_spec.spec")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.spec is deprecated; use specfact_spec.spec instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
