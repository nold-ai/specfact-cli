"""Compatibility shim for legacy specfact_cli.modules.policy_engine imports."""

import warnings
from importlib import import_module


_target = import_module("specfact_backlog.policy_engine")


def __getattr__(name: str):
    warnings.warn(
        "specfact_cli.modules.policy_engine is deprecated; use specfact_backlog.policy_engine instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(_target, name)


__all__ = ["app"]
