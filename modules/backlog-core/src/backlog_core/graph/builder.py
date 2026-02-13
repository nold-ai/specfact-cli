"""Template-driven provider-to-graph mapping utilities."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml
from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field

from backlog_core.graph.config_schema import BacklogConfigSchema, load_backlog_config_from_spec
from backlog_core.graph.models import BacklogGraph, BacklogItem, Dependency, DependencyType, ItemType


class BacklogConfigModel(BaseModel):
    """Optional configuration overrides for backlog graph mapping."""

    template: str | None = Field(default=None, description="Preferred template override")
    type_mapping: dict[str, str] = Field(default_factory=dict, description="Raw type -> normalized type mapping")
    dependency_rules: dict[str, str] = Field(
        default_factory=dict,
        description="Raw relationship type -> normalized dependency mapping",
    )
    status_mapping: dict[str, str] = Field(default_factory=dict, description="Raw status -> normalized status mapping")


@beartype
class BacklogGraphBuilder:
    """Build provider-agnostic backlog graphs from provider payloads."""

    @beartype
    @require(lambda provider: provider.strip() != "", "Provider must be non-empty")
    def __init__(
        self, provider: str, template_name: str | None = None, custom_config: dict[str, Any] | None = None
    ) -> None:
        self.provider = provider
        self.template_name = template_name or provider
        self._template = self._load_template(self.template_name)
        self._custom_config = self._load_custom_config(custom_config)
        self._items: dict[str, BacklogItem] = {}
        self._dependencies: list[Dependency] = []

    @beartype
    @require(lambda template_name: template_name.strip() != "", "Template name must be non-empty")
    @ensure(lambda result: isinstance(result, dict), "Template loader must return dict")
    def _load_template(self, template_name: str) -> dict[str, Any]:
        module_root = Path(__file__).resolve().parents[1]
        template_file = module_root / "resources" / "backlog-templates" / f"{template_name}.yaml"
        shared_template_file = (
            Path(__file__).resolve().parents[5]
            / "src"
            / "specfact_cli"
            / "resources"
            / "backlog-templates"
            / f"{template_name}.yaml"
        )

        for candidate in (template_file, shared_template_file):
            if candidate.exists():
                data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
        return {"type_mapping": {}, "dependency_rules": {}, "status_mapping": {}}

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Custom config must normalize to dict")
    def _load_custom_config(self, custom_config: dict[str, Any] | None) -> dict[str, Any]:
        merged = BacklogConfigModel().model_dump()

        spec_config = load_backlog_config_from_spec(Path(".specfact/spec.yaml"))
        if spec_config is not None:
            merged = self._merge_config(merged, self._flatten_config_payload(spec_config.model_dump()))

        if custom_config:
            project_bundle_metadata = custom_config.get("project_bundle_metadata")
            if isinstance(project_bundle_metadata, dict):
                metadata_backlog_config = project_bundle_metadata.get("backlog_config")
                if not isinstance(metadata_backlog_config, dict):
                    backlog_core = project_bundle_metadata.get("backlog_core")
                    if isinstance(backlog_core, dict):
                        metadata_backlog_config = backlog_core.get("backlog_config")
                if not isinstance(metadata_backlog_config, dict):
                    extensions = project_bundle_metadata.get("extensions")
                    if isinstance(extensions, dict):
                        backlog_core_extension = extensions.get("backlog_core")
                        if isinstance(backlog_core_extension, dict):
                            metadata_backlog_config = backlog_core_extension.get("backlog_config")
                if isinstance(metadata_backlog_config, dict):
                    merged = self._merge_config(merged, self._flatten_config_payload(metadata_backlog_config))
            merged = self._merge_config(merged, self._flatten_config_payload(custom_config))

        return merged

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Flattened config must be dict")
    def _flatten_config_payload(self, config_payload: dict[str, Any]) -> dict[str, Any]:
        if "dependencies" in config_payload or "providers" in config_payload:
            schema = BacklogConfigSchema.model_validate(config_payload)
            dependency_data = schema.dependencies.model_dump()
            return {
                "template": dependency_data.get("template"),
                "type_mapping": dependency_data.get("type_mapping", {}),
                "dependency_rules": dependency_data.get("dependency_rules", {}),
                "status_mapping": dependency_data.get("status_mapping", {}),
                "providers": {name: provider.model_dump() for name, provider in schema.providers.items()},
            }
        return BacklogConfigModel.model_validate(config_payload).model_dump()

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Merged config must be dict")
    def _merge_config(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key in ("template", "project_key"):
            value = override.get(key)
            if value is not None:
                merged[key] = value
        for key in ("type_mapping", "dependency_rules", "status_mapping", "providers"):
            merged[key] = {**merged.get(key, {}), **override.get(key, {})}
        return merged

    @beartype
    @require(lambda raw_items: isinstance(raw_items, list), "raw_items must be a list")
    def add_items(self, raw_items: list[dict[str, Any]]) -> BacklogGraphBuilder:
        for raw_item in raw_items:
            item_id = str(raw_item.get("id") or raw_item.get("key") or "")
            if not item_id:
                continue
            inferred_type, confidence = self._infer_type(raw_item)
            status_value = self._map_status(str(raw_item.get("status") or raw_item.get("state") or "unknown"))
            item = BacklogItem(
                id=item_id,
                key=str(raw_item.get("key") or item_id),
                title=str(raw_item.get("title") or raw_item.get("name") or item_id),
                type=inferred_type,
                status=status_value,
                description=(str(raw_item.get("description")) if raw_item.get("description") else None),
                priority=(str(raw_item.get("priority")) if raw_item.get("priority") else None),
                parent_id=(str(raw_item.get("parent_id")) if raw_item.get("parent_id") else None),
                raw_data=raw_item,
                inferred_type=inferred_type,
                confidence=confidence,
            )
            self._items[item.id] = item
        return self

    @beartype
    @ensure(lambda result: isinstance(result, tuple), "Type inference must return tuple")
    def _infer_type(self, raw_item: dict[str, Any]) -> tuple[ItemType, float]:
        raw_type = str(raw_item.get("type") or raw_item.get("work_item_type") or "custom").strip().lower()
        mapping = {
            **{k.lower(): v for k, v in self._template.get("type_mapping", {}).items()},
            **{k.lower(): v for k, v in self._custom_config.get("type_mapping", {}).items()},
        }
        mapped = mapping.get(raw_type, "custom")
        try:
            return ItemType(mapped), 0.9 if mapped != "custom" else 0.4
        except ValueError:
            return ItemType.CUSTOM, 0.1

    @beartype
    @ensure(lambda result: isinstance(result, str), "Mapped status must be a string")
    def _map_status(self, status: str) -> str:
        normalized = status.strip().lower()
        mapping = {
            **{k.lower(): v for k, v in self._template.get("status_mapping", {}).items()},
            **{k.lower(): v for k, v in self._custom_config.get("status_mapping", {}).items()},
        }
        return str(mapping.get(normalized, normalized or "unknown"))

    @beartype
    @require(lambda relationships: isinstance(relationships, list), "relationships must be a list")
    def add_dependencies(self, relationships: list[dict[str, Any]]) -> BacklogGraphBuilder:
        for relationship in relationships:
            source_id = str(relationship.get("source_id") or relationship.get("from") or "")
            target_id = str(relationship.get("target_id") or relationship.get("to") or "")
            if not source_id or not target_id:
                continue
            dep_type = self._infer_dependency_type(str(relationship.get("type") or relationship.get("relation") or ""))
            self._dependencies.append(
                Dependency(
                    source_id=source_id,
                    target_id=target_id,
                    type=dep_type,
                    metadata=relationship,
                    confidence=0.9 if dep_type is not DependencyType.CUSTOM else 0.4,
                )
            )
        return self

    @beartype
    @ensure(lambda result: isinstance(result, DependencyType), "Dependency type must be normalized")
    def _infer_dependency_type(self, raw_relationship_type: str) -> DependencyType:
        normalized = raw_relationship_type.strip().lower()
        mapping = {
            **{k.lower(): v for k, v in self._template.get("dependency_rules", {}).items()},
            **{k.lower(): v for k, v in self._custom_config.get("dependency_rules", {}).items()},
        }
        mapped = mapping.get(normalized)
        if mapped is None:
            return DependencyType.CUSTOM
        try:
            return DependencyType(mapped)
        except ValueError:
            return DependencyType.CUSTOM

    def _compute_transitive_closure(self) -> dict[str, list[str]]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for dep in self._dependencies:
            adjacency[dep.source_id].add(dep.target_id)

        closure: dict[str, list[str]] = {}
        for source in self._items:
            seen: set[str] = set()
            stack = list(adjacency.get(source, set()))
            while stack:
                node = stack.pop()
                if node in seen:
                    continue
                seen.add(node)
                stack.extend(adjacency.get(node, set()))
            if seen:
                closure[source] = sorted(seen)
        return closure

    def _detect_cycles(self) -> list[list[str]]:
        adjacency: dict[str, list[str]] = defaultdict(list)
        for dep in self._dependencies:
            adjacency[dep.source_id].append(dep.target_id)

        visited: set[str] = set()
        in_stack: set[str] = set()
        path: list[str] = []
        cycles: list[list[str]] = []

        def dfs(node: str) -> None:
            visited.add(node)
            in_stack.add(node)
            path.append(node)
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in in_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append([*path[cycle_start:], neighbor])
            path.pop()
            in_stack.remove(node)

        for node in self._items:
            if node not in visited:
                dfs(node)
        return cycles

    def _find_orphans(self) -> list[str]:
        targets = {dep.target_id for dep in self._dependencies}
        orphans: list[str] = []
        for item in self._items.values():
            if item.parent_id:
                continue
            if item.id not in targets:
                orphans.append(item.id)
        return sorted(set(orphans))

    @beartype
    @ensure(lambda result: isinstance(result, BacklogGraph), "Builder must return BacklogGraph")
    def build(self) -> BacklogGraph:
        return BacklogGraph(
            items=self._items,
            dependencies=self._dependencies,
            provider=self.provider,
            project_key=str(self._custom_config.get("project_key") or "unknown"),
            transitive_closure=self._compute_transitive_closure(),
            cycles_detected=self._detect_cycles(),
            orphans=self._find_orphans(),
        )
