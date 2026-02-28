"""Compatibility shim for legacy specfact_cli.modules.import_cmd.src.commands module."""

from importlib import import_module


_target = import_module("specfact_project.import_cmd.commands")
app = _target.app


def __getattr__(name: str):
    return getattr(_target, name)


__all__ = ["app"]
