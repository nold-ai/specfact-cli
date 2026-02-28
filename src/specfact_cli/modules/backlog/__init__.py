"""Compatibility shim for legacy specfact_cli.modules.backlog imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_backlog.backlog")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.backlog is deprecated; use specfact_backlog.backlog instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
