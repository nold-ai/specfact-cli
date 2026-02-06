"""
Command registry with lazy-loaded Typer apps.

Register command groups by name with a loader and metadata; resolve Typer only when requested.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

from beartype import beartype
from icontract import ensure, require
from typing_extensions import TypedDict

from specfact_cli.registry.metadata import CommandMetadata


# Loader: callable that returns typer.Typer (invoked on first get_typer(name))
Loader: TypeAlias = Callable[[], Any]  # noqa: UP040


class _Entry(TypedDict, total=False):
    """Internal entry: name, loader, metadata, optional cached typer."""

    name: str
    loader: Loader
    metadata: CommandMetadata
    typer: Any


class CommandRegistry:
    """
    Registry for CLI command groups (lazy load).

    Register by name with a loader and metadata; get_typer(name) invokes loader on first use.
    """

    _entries: list[_Entry] = []
    _typer_cache: dict[str, Any] = {}

    @classmethod
    def _ensure_bootstrapped(cls) -> None:
        """Re-register commands if registry was cleared during runtime/tests."""
        if cls._entries:
            return
        # Local import avoids circular import at module load time.
        from specfact_cli.registry.bootstrap import register_builtin_commands

        register_builtin_commands()

    @classmethod
    @beartype
    @require(lambda name: isinstance(name, str) and len(name) > 0, "Name must be non-empty string")
    @require(lambda metadata: isinstance(metadata, CommandMetadata), "Metadata must be CommandMetadata")
    @ensure(lambda result: result is None, "Must return None")
    def register(cls, name: str, loader: Loader, metadata: CommandMetadata) -> None:
        """Register a command. Does not invoke loader."""
        for e in cls._entries:
            if e.get("name") == name:
                e["loader"] = loader
                e["metadata"] = metadata
                cls._typer_cache.pop(name, None)
                return
        cls._entries.append({"name": name, "loader": loader, "metadata": metadata})

    @classmethod
    @beartype
    @require(lambda name: isinstance(name, str) and len(name) > 0, "Name must be non-empty string")
    def get_typer(cls, name: str) -> Any:
        """Return Typer app for name; invoke loader on first use and cache."""
        cls._ensure_bootstrapped()
        if name in cls._typer_cache:
            return cls._typer_cache[name]
        for e in cls._entries:
            if e.get("name") == name:
                loader = e.get("loader")
                if loader is None:
                    raise ValueError(f"Command '{name}' has no loader")
                app = loader()
                cls._typer_cache[name] = app
                return app
        registered = ", ".join(e.get("name", "") for e in cls._entries)
        raise ValueError(f"Command '{name}' not found. Registered commands: {registered or '(none)'}")

    @classmethod
    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def list_commands(cls) -> list[str]:
        """Return all registered command names in registration order."""
        cls._ensure_bootstrapped()
        return [e.get("name", "") for e in cls._entries if e.get("name")]

    @classmethod
    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def list_commands_for_help(cls) -> list[tuple[str, CommandMetadata]]:
        """Return (name, metadata) for help display; does not invoke loaders."""
        cls._ensure_bootstrapped()
        return [(e.get("name", ""), e["metadata"]) for e in cls._entries if e.get("name") and "metadata" in e]

    @classmethod
    def get_metadata(cls, name: str) -> CommandMetadata | None:
        """Return metadata for name without invoking loader."""
        cls._ensure_bootstrapped()
        for e in cls._entries:
            if e.get("name") == name:
                return e.get("metadata")
        return None

    @classmethod
    def _clear_for_testing(cls) -> None:
        """Reset registry state (for tests only)."""
        cls._entries = []
        cls._typer_cache = {}
