"""
Unit tests for ExtensionRegistry (arch-07 schema extension system).

Spec: schema-extension-system — namespace collision detection, registry populated at registration.
"""

from __future__ import annotations

import pytest

from specfact_cli.models.module_package import SchemaExtension
from specfact_cli.registry.extension_registry import ExtensionRegistry


class TestExtensionRegistry:
    """ExtensionRegistry register, collision detection, list_all."""

    def test_register_extensions_from_module(self) -> None:
        """Registry SHALL register extensions from a module."""
        registry = ExtensionRegistry()
        exts = [
            SchemaExtension(target="Feature", field="ado_work_item_id", type_hint="str", description="ADO ID"),
        ]
        registry.register("backlog", exts)
        assert registry.get_extensions("backlog") == exts

    def test_list_all_returns_module_to_extensions(self) -> None:
        """list_all() SHALL return dict module_name -> list of SchemaExtension."""
        registry = ExtensionRegistry()
        exts = [
            SchemaExtension(target="Feature", field="ado_id", type_hint="str", description="ADO work item ID"),
        ]
        registry.register("backlog", exts)
        all_ = registry.list_all()
        assert "backlog" in all_
        assert all_["backlog"] == exts

    def test_same_module_multiple_fields(self) -> None:
        """Same module declaring multiple fields SHALL register successfully."""
        registry = ExtensionRegistry()
        exts = [
            SchemaExtension(target="Feature", field="ado_work_item_id", type_hint="str", description="ADO ID"),
            SchemaExtension(target="Feature", field="jira_issue_key", type_hint="str", description="Jira key"),
        ]
        registry.register("backlog", exts)
        assert len(registry.get_extensions("backlog")) == 2

    def test_different_modules_unique_namespaces(self) -> None:
        """Different modules with unique namespaces SHALL both succeed."""
        registry = ExtensionRegistry()
        registry.register(
            "backlog",
            [SchemaExtension(target="Feature", field="ado_work_item_id", type_hint="str", description="")],
        )
        registry.register(
            "sync",
            [SchemaExtension(target="ProjectBundle", field="last_sync_timestamp", type_hint="str", description="")],
        )
        assert len(registry.get_extensions("backlog")) == 1
        assert len(registry.get_extensions("sync")) == 1
        assert len(registry.list_all()) == 2

    def test_collision_raises_or_logs(self) -> None:
        """Duplicate extension field (same module.field) from different module SHALL be rejected."""
        registry = ExtensionRegistry()
        registry.register(
            "module_a",
            [SchemaExtension(target="Feature", field="ado_work_item_id", type_hint="str", description="")],
        )
        with pytest.raises(ValueError, match="collision|already declared"):
            registry.register(
                "module_b",
                [SchemaExtension(target="Feature", field="ado_work_item_id", type_hint="str", description="")],
            )
