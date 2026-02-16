"""
Global extension registry for schema extensions declared by modules (arch-07).

Maps module name to list of SchemaExtension; enforces namespace collision detection at registration.
"""

from __future__ import annotations

from beartype import beartype

from specfact_cli.models.module_package import SchemaExtension


def _check_collision(
    module_name: str,
    extensions: list[SchemaExtension],
    registry: dict[str, list[SchemaExtension]],
) -> None:
    """Raise ValueError if any (target, field) is already registered by another module."""
    for ext in extensions:
        key = f"{module_name}.{ext.field}"
        for existing_module, existing_exts in registry.items():
            if existing_module == module_name:
                continue
            for e in existing_exts:
                if (e.target, e.field) == (ext.target, ext.field):
                    raise ValueError(
                        f"Extension field collision: {key} already declared by module {existing_module}"
                    )


class ExtensionRegistry:
    """Global registry of module-declared schema extensions (arch-07)."""

    _registry: dict[str, list[SchemaExtension]]

    def __init__(self) -> None:
        self._registry = {}

    @beartype
    def register(self, module_name: str, extensions: list[SchemaExtension]) -> None:
        """Register schema extensions for a module. Raises ValueError on namespace collision."""
        _check_collision(module_name, extensions, self._registry)
        self._registry.setdefault(module_name, []).extend(extensions)

    @beartype
    def get_extensions(self, module_name: str) -> list[SchemaExtension]:
        """Return list of schema extensions for the given module."""
        return list(self._registry.get(module_name, []))

    @beartype
    def list_all(self) -> dict[str, list[SchemaExtension]]:
        """Return copy of full registry (module_name -> list of SchemaExtension)."""
        return {k: list(v) for k, v in self._registry.items()}


def get_extension_registry() -> ExtensionRegistry:
    """Return the global extension registry singleton."""
    if not hasattr(get_extension_registry, "_instance"):
        get_extension_registry._instance = ExtensionRegistry()  # type: ignore[attr-defined]
    return get_extension_registry._instance  # type: ignore[attr-defined]
