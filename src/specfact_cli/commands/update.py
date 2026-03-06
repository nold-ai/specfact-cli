"""Backward-compatible app shim. Implementation moved to modules/upgrade/."""

from importlib import import_module
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    app: Any


def __getattr__(name: str) -> Any:
    if name == "app":
        return import_module("..modules.upgrade.src.commands", __package__).app
    raise AttributeError(name)


__all__ = ["app"]
