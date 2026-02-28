"""Compatibility shim for legacy specfact_cli.modules.contract imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_spec.contract")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.contract is deprecated; use specfact_spec.contract instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
