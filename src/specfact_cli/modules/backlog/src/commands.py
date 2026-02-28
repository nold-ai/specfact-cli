"""Compatibility shim for legacy specfact_cli.modules.backlog.src.commands module."""

from importlib import import_module


_target = import_module("specfact_backlog.backlog.commands")
app = _target.app


def __getattr__(name: str):
    return getattr(_target, name)


__all__ = ["app"]
