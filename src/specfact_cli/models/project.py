"""
Project bundle data models for modular project structure.

This module defines Pydantic models for modular project bundles that replace
the monolithic plan bundle structure. Project bundles use a directory-based
structure with separated aspects (idea, business, product, features) and
support dual versioning (schema + project).
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field, StrictStr, model_validator

from specfact_cli.models.change import ChangeArchive, ChangeProposal, ChangeTracking, FeatureDelta
from specfact_cli.models.contract import ContractIndex
from specfact_cli.models.plan import (
    Business,
    Clarifications,
    Feature,
    Idea,
    PlanSummary,
    Product,
)
from specfact_cli.utils.icontract_helpers import (
    require_bundle_dir_exists,
    require_extension_key_nonempty,
    require_file_path_exists,
    require_namespace_stripped_nonempty,
)


_EXT_MODULE_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
_EXT_FIELD_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class BundleFormat(StrEnum):
    """Bundle format types."""

    MONOLITHIC = "monolithic"  # Single file with all aspects
    MODULAR = "modular"  # Directory-based with separated aspects
    UNKNOWN = "unknown"


def _is_schema_v1_1(manifest: BundleManifest) -> bool:
    """
    Check if bundle manifest uses schema version 1.1 or later.

    Args:
        manifest: Bundle manifest to check

    Returns:
        True if schema version is 1.1 or later, False otherwise
    """
    try:
        schema_version = manifest.versions.schema_version
        # Compare as strings, but handle numeric comparison for future versions
        # For future versions (1.2, 2.0, etc.), we'd need more sophisticated parsing
        # For now, only 1.1 is supported
        return schema_version == "1.1"
    except (AttributeError, KeyError):
        return False


class BundleVersions(BaseModel):
    """Dual versioning system: schema (format) + project (contracts)."""

    schema_version: str = Field("1.0", alias="schema", description="Bundle format version (breaks loader)")
    project: str = Field("0.1.0", description="Project contract version (SemVer, breaks semantics)")

    model_config = {"populate_by_name": True}  # Allow both field name and alias


class SchemaMetadata(BaseModel):
    """Schema version metadata."""

    compatible_loaders: list[str] = Field(
        default_factory=lambda: ["0.7.0+"], description="CLI versions supporting this schema"
    )
    upgrade_path: str | None = Field(None, description="URL to migration guide")


class ProjectMetadata(BaseModel):
    """Project version metadata (SemVer)."""

    stability: str = Field("alpha", description="Stability level: alpha | beta | stable")
    breaking_changes: list[dict[str, str]] = Field(default_factory=list, description="Breaking change history")
    version_history: list[dict[str, str]] = Field(default_factory=list, description="Version change log")
    extensions: dict[str, Any] = Field(default_factory=dict, description="Module-scoped metadata extensions")

    @beartype
    @require(require_namespace_stripped_nonempty, "Extension namespace must be non-empty")
    @require(require_extension_key_nonempty, "Extension key must be non-empty")
    def set_extension(self, namespace: str, key: str, value: Any) -> None:
        """Set a module-scoped extension value."""
        namespace_data = self.extensions.get(namespace)
        if not isinstance(namespace_data, dict):
            namespace_data = {}
            self.extensions[namespace] = namespace_data
        bucket = cast(dict[str, Any], namespace_data)
        bucket[key] = value

    @beartype
    @require(require_namespace_stripped_nonempty, "Extension namespace must be non-empty")
    @require(require_extension_key_nonempty, "Extension key must be non-empty")
    def get_extension(self, namespace: str, key: str, default: Any = None) -> Any:
        """Get a module-scoped extension value."""
        namespace_data = self.extensions.get(namespace)
        if not isinstance(namespace_data, dict):
            return default
        return cast(dict[str, Any], namespace_data).get(key, default)


class BundleChecksums(BaseModel):
    """Checksums for integrity validation."""

    algorithm: str = Field("sha256", description="Hash algorithm")
    files: dict[str, str] = Field(default_factory=dict, description="File path -> checksum mapping")


class SectionLock(BaseModel):
    """Section ownership and lock information."""

    section: str = Field(..., description="Section pattern (e.g., 'idea,business,features.*.stories')")
    owner: str = Field(..., description="Persona owner (e.g., 'product-owner', 'architect')")
    locked_at: str = Field(..., description="Lock timestamp")
    locked_by: str = Field(..., description="User email who locked")


class PersonaMapping(BaseModel):
    """Persona-to-section ownership mapping."""

    owns: list[str] = Field(..., description="Section patterns owned by persona")
    exports_to: str = Field(..., description="Spec-Kit file pattern (e.g., 'specs/*/spec.md')")


class FeatureIndex(BaseModel):
    """Feature index entry for fast lookup."""

    key: str = Field(..., description="Feature key (FEATURE-001)")
    title: str = Field(..., description="Feature title")
    file: str = Field(..., description="Feature file name (FEATURE-001.yaml)")
    status: str = Field("active", description="Feature status")
    stories_count: int = Field(0, description="Number of stories")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    contract: str | None = Field(None, description="Contract file path (optional)")
    checksum: str | None = Field(None, description="Feature file checksum")


class ProtocolIndex(BaseModel):
    """Protocol index entry for fast lookup."""

    name: str = Field(..., description="Protocol name (e.g., 'auth')")
    file: str = Field(..., description="Protocol file name (e.g., 'auth.protocol.yaml')")
    checksum: str | None = Field(None, description="Protocol file checksum")


class BundleManifest(BaseModel):
    """Bundle manifest (entry point) with dual versioning, checksums, locks."""

    versions: BundleVersions = Field(
        default_factory=lambda: BundleVersions(schema="1.0", project="0.1.0"), description="Schema + project versions"
    )

    bundle: dict[str, str] = Field(
        default_factory=dict, description="Bundle metadata (format, created_at, last_modified)"
    )

    schema_metadata: SchemaMetadata | None = Field(None, description="Schema version metadata")
    project_metadata: ProjectMetadata | None = Field(None, description="Project version metadata")

    checksums: BundleChecksums = Field(
        default_factory=lambda: BundleChecksums(algorithm="sha256"), description="File integrity checksums"
    )
    locks: list[SectionLock] = Field(default_factory=list, description="Section ownership locks")

    personas: dict[str, PersonaMapping] = Field(default_factory=dict, description="Persona-to-section mappings")

    features: list[FeatureIndex] = Field(
        default_factory=list, description="Feature index (key, title, file, contract, checksum)"
    )
    protocols: list[ProtocolIndex] = Field(default_factory=list, description="Protocol index (name, file, checksum)")
    contracts: list[ContractIndex] = Field(
        default_factory=list,
        description="Contract index (feature_key, contract_file, status, checksum, endpoints_count, coverage)",
    )
    # NEW in v1.1 (optional, backward compatible)
    change_tracking: ChangeTracking | None = Field(
        default=None,
        description="Change tracking (tool-agnostic capability, used by OpenSpec and potentially others) (v1.1+)",
    )
    change_archive: list[ChangeArchive] = Field(
        default_factory=list,
        description="Archive of completed changes (tool-agnostic) (v1.1+)",
    )


class _BundleLoadSlots:
    """Mutable holder for parallel bundle load results."""

    def __init__(self) -> None:
        self.idea: Idea | None = None
        self.business: Business | None = None
        self.product: Product | None = None
        self.clarifications: Clarifications | None = None
        self.features: dict[str, Feature] = {}


def _count_bundle_load_artifacts(bundle_dir: Path, num_features: int) -> int:
    return (
        2
        + (1 if (bundle_dir / "idea.yaml").exists() else 0)
        + (1 if (bundle_dir / "business.yaml").exists() else 0)
        + (1 if (bundle_dir / "clarifications.yaml").exists() else 0)
        + num_features
    )


def _bundle_load_max_workers(num_tasks: int) -> int:
    if os.environ.get("TEST_MODE") == "true":
        return max(1, min(2, num_tasks))
    cpu_count = os.cpu_count() or 4
    return min(cpu_count, 8, num_tasks)


def _merge_bundle_load_result(artifact_name: str, result: Any, slots: _BundleLoadSlots) -> None:
    if artifact_name == "idea.yaml":
        slots.idea = result  # type: ignore[assignment]
        return
    if artifact_name == "business.yaml":
        slots.business = result  # type: ignore[assignment]
        return
    if artifact_name == "product.yaml":
        slots.product = result  # type: ignore[assignment]
        return
    if artifact_name == "clarifications.yaml":
        slots.clarifications = result  # type: ignore[assignment]
        return
    if artifact_name.startswith("features/") and isinstance(result, tuple) and len(result) == 2:
        key, feature = result
        slots.features[key] = feature  # type: ignore[assignment]


def _load_bundle_artifact_file(
    artifact_name: str, artifact_path: Path, validator: Callable[..., Any], load_structured_file: Callable[..., Any]
) -> tuple[str, Any]:
    data = load_structured_file(artifact_path)
    validated = validator(data)
    return (artifact_name, validated)


def _cancel_executor_futures(future_to_task: dict[Any, Any]) -> None:
    for f in future_to_task:
        if not f.done():
            f.cancel()


def _try_load_bundle_change_tracking(bundle_dir: Path, manifest: BundleManifest) -> ChangeTracking | None:
    if not _is_schema_v1_1(manifest):
        return None
    change_tracking: ChangeTracking | None = None
    try:
        from specfact_cli.adapters.registry import AdapterRegistry
        from specfact_cli.models.bridge import BridgeConfig
        from specfact_cli.utils.structure import SpecFactStructure
        from specfact_cli.utils.structured_io import load_structured_file

        repo_root = bundle_dir.parent.parent
        bridge_config_path = repo_root / SpecFactStructure.CONFIG / "bridge.yaml"
        if bridge_config_path.exists():
            bridge_config_data = load_structured_file(bridge_config_path)
            bridge_config = BridgeConfig.model_validate(bridge_config_data)
            if bridge_config.adapter:
                adapter = AdapterRegistry.get_adapter(bridge_config.adapter.value)
                change_tracking = adapter.load_change_tracking(bundle_dir, bridge_config)
    except (ImportError, AttributeError, FileNotFoundError, ValueError, KeyError):
        pass
    if change_tracking is None and manifest.change_tracking is not None:
        return manifest.change_tracking
    return change_tracking


def _bundle_save_max_workers(num_features: int, num_tasks: int) -> int:
    if os.environ.get("TEST_MODE") == "true":
        return max(1, min(2, num_tasks))
    cpu_count = os.cpu_count() or 4
    if num_features > 1000:
        return min(cpu_count, 4, num_tasks)
    return min(cpu_count, 8, num_tasks)


def _write_bundle_artifact_disk(
    artifact_name: str,
    artifact_path: Path,
    data: dict[str, Any] | Feature,
) -> tuple[str, str]:
    import hashlib

    from specfact_cli.utils.structured_io import StructuredFormat, _get_yaml_instance

    dump_data = data.model_dump() if isinstance(data, Feature) else data
    hash_obj = hashlib.sha256()
    path = Path(artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = StructuredFormat.from_path(path)

    if fmt == StructuredFormat.JSON:
        import json

        content = json.dumps(dump_data, indent=2).encode("utf-8")
        hash_obj.update(content)
        path.write_bytes(content)
    else:
        yaml_instance = _get_yaml_instance()
        quoted_data = yaml_instance._quote_boolean_like_strings(dump_data)
        yaml_content = yaml_instance.dump_string(quoted_data)
        yaml_bytes = yaml_content.encode("utf-8")
        hash_obj.update(yaml_bytes)
        path.write_bytes(yaml_bytes)

    checksum = hash_obj.hexdigest()
    del dump_data
    return (artifact_name, checksum)


def _assign_feature_index_from_save(
    bundle: ProjectBundle,
    artifact_name: str,
    checksum: str,
    now: str,
    feature_key_to_save_index: dict[str, int],
    feature_indices: list[FeatureIndex | None],
) -> None:
    if not artifact_name.startswith("features/"):
        return
    feature_file = artifact_name.split("/", 1)[1]
    key = feature_file.replace(".yaml", "")
    if key not in feature_key_to_save_index:
        return
    save_idx = feature_key_to_save_index[key]
    feature = bundle.features[key]
    feature_indices[save_idx] = FeatureIndex(
        key=key,
        title=feature.title,
        file=feature_file,
        status="active" if not feature.draft else "draft",
        stories_count=len(feature.stories),
        created_at=now,
        updated_at=now,
        contract=feature.contract,
        checksum=checksum,
    )


def _build_bundle_load_tasks(bundle_dir: Path, manifest: BundleManifest) -> list[tuple[str, Path, Callable[..., Any]]]:
    features_dir = bundle_dir / "features"
    load_tasks: list[tuple[str, Path, Callable[..., Any]]] = []
    idea_path = bundle_dir / "idea.yaml"
    if idea_path.exists():
        load_tasks.append(("idea.yaml", idea_path, lambda data: Idea.model_validate(data)))
    business_path = bundle_dir / "business.yaml"
    if business_path.exists():
        load_tasks.append(("business.yaml", business_path, lambda data: Business.model_validate(data)))
    product_path = bundle_dir / "product.yaml"
    if not product_path.exists():
        raise FileNotFoundError(f"Product file not found: {product_path}")
    load_tasks.append(("product.yaml", product_path, lambda data: Product.model_validate(data)))
    clarifications_path = bundle_dir / "clarifications.yaml"
    if clarifications_path.exists():
        load_tasks.append(
            ("clarifications.yaml", clarifications_path, lambda data: Clarifications.model_validate(data))
        )
    if features_dir.exists():
        for feature_index in manifest.features:
            feature_path = features_dir / feature_index.file
            if feature_path.exists():
                load_tasks.append(
                    (
                        f"features/{feature_index.file}",
                        feature_path,
                        lambda data, key=feature_index.key: (key, Feature.model_validate(data)),
                    )
                )
    return load_tasks


def _run_bundle_parallel_load(
    load_tasks: list[tuple[str, Path, Callable[..., Any]]],
    total_artifacts: int,
    start_count: int,
    progress_callback: Callable[[int, int, str], None] | None,
    load_structured_file: Callable[..., Any],
    slots: _BundleLoadSlots,
) -> None:
    max_workers = _bundle_load_max_workers(len(load_tasks))
    completed_count = start_count
    executor = ThreadPoolExecutor(max_workers=max_workers)
    interrupted = False
    wait_on_shutdown = os.environ.get("TEST_MODE") != "true"
    try:
        future_to_task = {
            executor.submit(_load_bundle_artifact_file, name, path, validator, load_structured_file): (
                name,
                path,
                validator,
            )
            for name, path, validator in load_tasks
        }

        try:
            for future in as_completed(future_to_task):
                try:
                    artifact_name, result = future.result()
                    completed_count += 1

                    if progress_callback:
                        progress_callback(completed_count, total_artifacts, artifact_name)

                    _merge_bundle_load_result(artifact_name, result, slots)
                except KeyboardInterrupt:
                    interrupted = True
                    _cancel_executor_futures(future_to_task)
                    break
                except Exception as e:
                    artifact_name_err = future_to_task[future][0]
                    raise ValueError(f"Failed to load {artifact_name_err}: {e}") from e
        except KeyboardInterrupt:
            interrupted = True
            _cancel_executor_futures(future_to_task)
        if interrupted:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        interrupted = True
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        if not interrupted:
            executor.shutdown(wait=wait_on_shutdown)
        else:
            executor.shutdown(wait=False)


class ProjectBundle(BaseModel):
    """Modular project bundle (replaces monolithic PlanBundle).

    The ``schema_version`` field tracks module IO compatibility independently
    from manifest schema evolution to support forward-compatible module loading.
    """

    manifest: BundleManifest = Field(..., description="Bundle manifest with metadata")
    bundle_name: str = Field(..., description="Project bundle name (directory name, e.g., 'legacy-api')")
    schema_version: StrictStr = Field(
        default="1",
        description="ProjectBundle IO schema version used by module contracts for compatibility checks.",
    )
    idea: Idea | None = None
    business: Business | None = None
    product: Product = Field(..., description="Product definition")
    features: dict[str, Feature] = Field(default_factory=dict, description="Feature dictionary (key -> Feature)")
    clarifications: Clarifications | None = None
    # NEW in v1.1 (optional, backward compatible)
    change_tracking: ChangeTracking | None = Field(
        default=None,
        description="Change tracking (tool-agnostic capability, used by OpenSpec and potentially others) (v1.1+)",
    )
    extensions: dict[str, Any] = Field(
        default_factory=dict,
        description="Module-scoped extension data (namespace-prefixed keys, e.g. sync.last_sync_timestamp)",
    )

    @beartype
    @require(lambda self, module_name: bool(_EXT_MODULE_RE.match(module_name)), "Invalid module name format")
    @require(lambda self, field: bool(_EXT_FIELD_RE.match(field)), "Invalid field name format")
    def get_extension(self, module_name: str, field: str, default: Any = None) -> Any:
        """Return extension value at module.field or default."""
        if "." in module_name:
            raise ValueError("Invalid module name format")
        return self.extensions.get(f"{module_name}.{field}", default)

    @beartype
    @require(lambda self, module_name: bool(_EXT_MODULE_RE.match(module_name)), "Invalid module name format")
    @require(lambda self, field: bool(_EXT_FIELD_RE.match(field)), "Invalid field name format")
    @ensure(
        lambda self, module_name, field: f"{module_name}.{field}" in cast(ProjectBundle, self).extensions,
    )
    def set_extension(self, module_name: str, field: str, value: Any) -> None:
        """Store extension value at module.field."""
        if "." in module_name:
            raise ValueError("Invalid module name format")
        self.extensions[f"{module_name}.{field}"] = value

    @model_validator(mode="before")
    @classmethod
    def _normalize_nested_models(cls, data: Any) -> Any:
        """Normalize nested model instances from alternate module identities."""
        if not isinstance(data, dict):
            return data

        normalized: dict[str, Any] = dict(data)
        for key in ("manifest", "idea", "business", "product", "clarifications", "change_tracking"):
            value = normalized.get(key)
            if value is not None and isinstance(value, BaseModel):
                normalized[key] = value.model_dump(mode="python")

        features = normalized.get("features")
        if isinstance(features, dict):
            normalized["features"] = {
                feature_key: feature.model_dump(mode="python") if isinstance(feature, BaseModel) else feature
                for feature_key, feature in features.items()
            }

        return normalized

    @classmethod
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(require_bundle_dir_exists, "Bundle directory must exist")
    @ensure(lambda cls, result: isinstance(result, cls), "Must return ProjectBundle instance")
    def load_from_directory(
        cls, bundle_dir: Path, progress_callback: Callable[[int, int, str], None] | None = None
    ) -> ProjectBundle:
        """
        Load project bundle from directory structure.

        Args:
            bundle_dir: Path to project bundle directory (e.g., .specfact/projects/legacy-api/)
            progress_callback: Optional callback function(current: int, total: int, artifact: str) for progress updates

        Returns:
            ProjectBundle instance loaded from directory

        Raises:
            FileNotFoundError: If bundle.manifest.yaml is missing
            ValueError: If manifest is invalid
        """
        from specfact_cli.utils.structured_io import load_structured_file

        manifest_path = bundle_dir / "bundle.manifest.yaml"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Bundle manifest not found: {manifest_path}")

        features_dir = bundle_dir / "features"
        num_features = len(list(features_dir.glob("*.yaml")) if features_dir.exists() else [])
        total_artifacts = _count_bundle_load_artifacts(bundle_dir, num_features)

        current = 0

        if progress_callback:
            progress_callback(current + 1, total_artifacts, "bundle.manifest.yaml")
        manifest_data = load_structured_file(manifest_path)
        extensions_data = manifest_data.get("extensions", {}) if isinstance(manifest_data, dict) else {}
        if not isinstance(extensions_data, dict):
            raise ValueError("ProjectBundle extensions must be a mapping")
        manifest = BundleManifest.model_validate(manifest_data)
        current += 1

        slots = _BundleLoadSlots()

        load_tasks = _build_bundle_load_tasks(bundle_dir, manifest)
        if load_tasks:
            _run_bundle_parallel_load(
                load_tasks, total_artifacts, current, progress_callback, load_structured_file, slots
            )

        if slots.product is None:
            raise FileNotFoundError(f"Product file not found or failed to load: {bundle_dir / 'product.yaml'}")

        bundle_name = bundle_dir.name
        change_tracking = _try_load_bundle_change_tracking(bundle_dir, manifest)

        return cls(
            manifest=manifest,
            bundle_name=bundle_name,
            idea=slots.idea,
            business=slots.business,
            product=slots.product,  # type: ignore[arg-type]
            features=slots.features,
            clarifications=slots.clarifications,
            change_tracking=change_tracking,
            extensions=dict(extensions_data),
        )

    @beartype
    @require(lambda self, bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @ensure(lambda result: result is None, "Must return None")
    def save_to_directory(
        self, bundle_dir: Path, progress_callback: Callable[[int, int, str], None] | None = None
    ) -> None:
        """
        Save project bundle to directory structure.

        Args:
            bundle_dir: Path to project bundle directory (e.g., .specfact/projects/legacy-api/)
            progress_callback: Optional callback function(current: int, total: int, artifact: str) for progress updates

        Raises:
            ValueError: If bundle structure is invalid
        """

        from specfact_cli.utils.structured_io import dump_structured_file

        # Ensure directory exists
        bundle_dir.mkdir(parents=True, exist_ok=True)

        # Count total artifacts to save for progress tracking
        num_features = len(self.features)
        total_artifacts = (
            1  # manifest (always saved last)
            + (1 if self.idea else 0)
            + (1 if self.business else 0)
            + 1  # product (always saved)
            + (1 if self.clarifications else 0)
            + num_features
        )

        # Sync change tracking into manifest for persistence (v1.1+)
        # Preserve manifest.change_tracking if it's set but self.change_tracking is None
        # This allows setting change_tracking via manifest directly
        if self.change_tracking is not None:
            self.manifest.change_tracking = self.change_tracking
        elif self.manifest.change_tracking is None:
            # Only set to None if both are None (don't overwrite existing manifest.change_tracking)
            pass

        # Update manifest bundle metadata
        now = datetime.now(UTC).isoformat()
        if "created_at" not in self.manifest.bundle:
            self.manifest.bundle["created_at"] = now
        self.manifest.bundle["last_modified"] = now
        self.manifest.bundle["format"] = "directory-based"

        save_tasks = _build_bundle_save_tasks(self, bundle_dir)
        max_workers = _bundle_save_max_workers(num_features, len(save_tasks))
        feature_indices: list[FeatureIndex | None] = [None] * num_features
        feature_key_to_save_index = {key: idx for idx, key in enumerate(self.features)}
        checksums = _run_bundle_parallel_save(
            _BundleParallelSaveParams(
                bundle=self,
                save_tasks=save_tasks,
                total_artifacts=total_artifacts,
                max_workers=max_workers,
                progress_callback=progress_callback,
                now=now,
                feature_key_to_save_index=feature_key_to_save_index,
                feature_indices=feature_indices,
            ),
        )

        # Update manifest with checksums and feature indices
        self.manifest.checksums.files.update(checksums)
        # Filter out None placeholders (shouldn't happen, but safety check)
        self.manifest.features = [idx for idx in feature_indices if idx is not None]

        # Save manifest (last, after all checksums are computed)
        if progress_callback:
            progress_callback(total_artifacts, total_artifacts, "bundle.manifest.yaml")
        manifest_path = bundle_dir / "bundle.manifest.yaml"
        manifest_data = self.manifest.model_dump(mode="json")
        if self.extensions:
            manifest_data["extensions"] = self.extensions
        if num_features > 1000:
            import json

            manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        else:
            dump_structured_file(manifest_data, manifest_path)

    @beartype
    @require(lambda self, key: isinstance(key, str) and len(key) > 0, "Feature key must be non-empty string")
    @ensure(lambda result: result is None or isinstance(result, Feature), "Must return Feature or None")
    def get_feature(self, key: str) -> Feature | None:
        """
        Get feature by key (lazy load if needed).

        Args:
            key: Feature key (e.g., 'FEATURE-001')

        Returns:
            Feature if found, None otherwise
        """
        return self.features.get(key)

    @beartype
    @require(lambda self, feature: isinstance(feature, Feature), "Feature must be Feature instance")
    @ensure(lambda result: result is None, "Must return None")
    def add_feature(self, feature: Feature) -> None:
        """
        Add feature (save to file, update registry).

        Args:
            feature: Feature to add
        """
        self.features[feature.key] = feature
        # Note: Actual file save happens in save_to_directory()

    @beartype
    @require(lambda self, key: isinstance(key, str) and len(key) > 0, "Feature key must be non-empty string")
    @require(lambda self, feature: isinstance(feature, Feature), "Feature must be Feature instance")
    @ensure(lambda result: result is None, "Must return None")
    def update_feature(self, key: str, feature: Feature) -> None:
        """
        Update feature (save to file, update registry).

        Args:
            key: Feature key to update
            feature: Updated feature (must match key)
        """
        if key != feature.key:
            raise ValueError(f"Feature key mismatch: {key} != {feature.key}")
        self.features[key] = feature
        # Note: Actual file save happens in save_to_directory()

    @beartype
    @require(lambda self, include_hash: isinstance(include_hash, bool), "include_hash must be bool")
    @ensure(lambda result: isinstance(result, PlanSummary), "Must return PlanSummary")
    def compute_summary(self, include_hash: bool = False) -> PlanSummary:
        """
        Compute summary from all aspects (for compatibility).

        Args:
            include_hash: Whether to compute content hash

        Returns:
            PlanSummary with counts and optional hash
        """
        import hashlib
        import json

        features_count = len(self.features)
        stories_count = sum(len(f.stories) for f in self.features.values())
        themes_count = len(self.product.themes) if self.product.themes else 0
        releases_count = len(self.product.releases) if self.product.releases else 0

        content_hash = None
        if include_hash:
            # Compute hash of all aspects combined
            # NOTE: Exclude clarifications from hash - they are review metadata, not plan content
            # This ensures hash stability across review sessions (clarifications change but plan doesn't)
            # IMPORTANT: Sort features by key to ensure deterministic hash regardless of dict insertion order
            sorted_features = sorted(self.features.items(), key=lambda x: x[0])
            bundle_dict = {
                "idea": self.idea.model_dump() if self.idea else None,
                "business": self.business.model_dump() if self.business else None,
                "product": self.product.model_dump(),
                "features": [f.model_dump() for _, f in sorted_features],
                # Exclude clarifications - they are review metadata, not part of the plan content
            }
            bundle_json = json.dumps(bundle_dict, sort_keys=True, default=str)
            content_hash = hashlib.sha256(bundle_json.encode("utf-8")).hexdigest()

        return PlanSummary(
            features_count=features_count,
            stories_count=stories_count,
            themes_count=themes_count,
            releases_count=releases_count,
            content_hash=content_hash,
            computed_at=datetime.now(UTC).isoformat(),
        )

    @staticmethod
    @beartype
    @require(lambda file_path: isinstance(file_path, Path), "File path must be Path")
    @require(require_file_path_exists, "File must exist")
    @ensure(lambda result: isinstance(result, str) and len(result) == 64, "Must return SHA256 hex digest")
    def _compute_file_checksum(file_path: Path) -> str:
        """
        Compute SHA256 checksum of a file.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hex digest
        """
        import hashlib

        hash_obj = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def get_active_changes(self) -> list[ChangeProposal]:
        """
        Get all active (non-archived) change proposals.

        Returns:
            List of ChangeProposal objects with status "proposed" or "in-progress"
        """
        if not self.change_tracking:
            return []
        return [
            proposal
            for proposal in self.change_tracking.proposals.values()
            if proposal.status in ["proposed", "in-progress"]
        ]

    @beartype
    @require(lambda change_name: isinstance(change_name, str) and len(change_name) > 0, "Change name must be non-empty")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def get_feature_deltas(self, change_name: str) -> list[FeatureDelta]:
        """
        Get feature deltas for a specific change.

        Args:
            change_name: Change identifier

        Returns:
            List of FeatureDelta objects for the specified change, or empty list if not found
        """
        if not self.change_tracking:
            return []
        return self.change_tracking.feature_deltas.get(change_name, [])


@dataclass(slots=True)
class _BundleParallelSaveParams:
    bundle: ProjectBundle
    save_tasks: list[tuple[str, Path, dict[str, Any] | Feature]]
    total_artifacts: int
    max_workers: int
    progress_callback: Callable[[int, int, str], None] | None
    now: str
    feature_key_to_save_index: dict[str, int]
    feature_indices: list[FeatureIndex | None]


def _build_bundle_save_tasks(
    bundle: ProjectBundle,
    bundle_dir: Path,
) -> list[tuple[str, Path, dict[str, Any] | Feature]]:
    save_tasks: list[tuple[str, Path, dict[str, Any] | Feature]] = []
    if bundle.idea:
        save_tasks.append(("idea.yaml", bundle_dir / "idea.yaml", bundle.idea.model_dump()))
    if bundle.business:
        save_tasks.append(("business.yaml", bundle_dir / "business.yaml", bundle.business.model_dump()))
    save_tasks.append(("product.yaml", bundle_dir / "product.yaml", bundle.product.model_dump()))
    if bundle.clarifications:
        save_tasks.append(
            ("clarifications.yaml", bundle_dir / "clarifications.yaml", bundle.clarifications.model_dump())
        )
    features_dir = bundle_dir / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    if not isinstance(bundle.features, dict):
        raise ValueError(f"Expected features to be dict, got {type(bundle.features)}")
    for key, feature in bundle.features.items():
        if not isinstance(key, str):
            raise ValueError(f"Expected feature key to be string, got {type(key)}: {key}")
        if not isinstance(feature, Feature):
            raise ValueError(f"Expected feature to be Feature, got {type(feature)}: {feature}")
        feature_file = f"{key}.yaml"
        feature_path = features_dir / feature_file
        save_tasks.append((f"features/{feature_file}", feature_path, feature))
    return save_tasks


def _run_bundle_parallel_save(params: _BundleParallelSaveParams) -> dict[str, str]:
    completed_count = 0
    checksums: dict[str, str] = {}
    if not params.save_tasks:
        return checksums
    executor = ThreadPoolExecutor(max_workers=params.max_workers)
    interrupted = False
    wait_on_shutdown = os.environ.get("TEST_MODE") != "true"
    try:
        future_to_task = {
            executor.submit(_write_bundle_artifact_disk, name, path, data): (name, path, data)
            for name, path, data in params.save_tasks
        }

        try:
            for future in as_completed(future_to_task):
                try:
                    artifact_name, checksum = future.result()
                    completed_count += 1
                    checksums[artifact_name] = checksum

                    if params.progress_callback:
                        params.progress_callback(completed_count, params.total_artifacts, artifact_name)

                    _assign_feature_index_from_save(
                        params.bundle,
                        artifact_name,
                        checksum,
                        params.now,
                        params.feature_key_to_save_index,
                        params.feature_indices,
                    )
                except KeyboardInterrupt:
                    interrupted = True
                    _cancel_executor_futures(future_to_task)
                    break
                except Exception as e:
                    artifact_name_err = future_to_task.get(future, ("unknown", None, None))[0]
                    error_msg = f"Failed to save {artifact_name_err}"
                    if str(e):
                        error_msg += f": {e}"
                    raise ValueError(error_msg) from e
        except KeyboardInterrupt:
            interrupted = True
            _cancel_executor_futures(future_to_task)
        if interrupted:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        interrupted = True
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        if not interrupted:
            executor.shutdown(wait=wait_on_shutdown)
        else:
            executor.shutdown(wait=False)

    return checksums
