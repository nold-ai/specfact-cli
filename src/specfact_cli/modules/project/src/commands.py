"""Compatibility shim for legacy specfact_cli.modules.project.src.commands module."""

from importlib import import_module


_target = import_module("specfact_project.project.commands")
app = _target.app


def __getattr__(name: str):
    return getattr(_target, name)


__all__ = ["app"]
