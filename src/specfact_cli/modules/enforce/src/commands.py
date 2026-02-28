"""Compatibility shim for legacy specfact_cli.modules.enforce.src.commands module."""

from importlib import import_module


_target = import_module("specfact_govern.enforce.commands")
app = _target.app


def __getattr__(name: str):
    return getattr(_target, name)


__all__ = ["app"]
