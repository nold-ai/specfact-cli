"""
Project bundle data models for modular project structure.

This module defines Pydantic models for modular project bundles that replace
the monolithic plan bundle structure. Project bundles use a directory-based
structure with separated aspects (idea, business, product, features) and
support dual versioning (schema + project).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field

from specfact_cli.models.contract import ContractIndex
from specfact_cli.models.plan import (
    Business,
    Clarifications,
    Feature,
    Idea,
    PlanSummary,
    Product,
)


class BundleFormat(str, Enum):
    """Bundle format types."""

    MONOLITHIC = "monolithic"  # Single file with all aspects
    MODULAR = "modular"  # Directory-based with separated aspects
    UNKNOWN = "unknown"


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


class ProjectBundle(BaseModel):
    """Modular project bundle (replaces monolithic PlanBundle)."""

    manifest: BundleManifest = Field(..., description="Bundle manifest with metadata")
    bundle_name: str = Field(..., description="Project bundle name (directory name, e.g., 'legacy-api')")
    idea: Idea | None = None
    business: Business | None = None
    product: Product = Field(..., description="Product definition")
    features: dict[str, Feature] = Field(default_factory=dict, description="Feature dictionary (key -> Feature)")
    clarifications: Clarifications | None = None

    @classmethod
    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @ensure(lambda result: isinstance(result, ProjectBundle), "Must return ProjectBundle")
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

        # Count total artifacts to load for progress tracking
        features_dir = bundle_dir / "features"
        num_features = len(list(features_dir.glob("*.yaml")) if features_dir.exists() else [])
        # Base artifacts: manifest, product (required), idea, business, clarifications (optional)
        total_artifacts = (
            2
            + (1 if (bundle_dir / "idea.yaml").exists() else 0)
            + (1 if (bundle_dir / "business.yaml").exists() else 0)
            + (1 if (bundle_dir / "clarifications.yaml").exists() else 0)
            + num_features
        )

        current = 0

        # Load manifest first (required for feature index)
        if progress_callback:
            progress_callback(current + 1, total_artifacts, "bundle.manifest.yaml")
        manifest_data = load_structured_file(manifest_path)
        manifest = BundleManifest.model_validate(manifest_data)
        current += 1

        # Load all other artifacts in parallel (they're independent)
        idea: Idea | None = None
        business: Business | None = None
        product: Product | None = None  # Will be set from parallel loading (required)
        clarifications: Clarifications | None = None
        features: dict[str, Feature] = {}

        # Prepare tasks for parallel loading
        load_tasks: list[tuple[str, Path, Callable]] = []

        # Add aspect loading tasks
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

        # Add feature loading tasks (from manifest index)
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

        # Load artifacts in parallel using ThreadPoolExecutor
        # In test mode, use fewer workers to avoid resource contention
        if os.environ.get("TEST_MODE") == "true":
            max_workers = max(1, min(2, len(load_tasks)))  # Max 2 workers in test mode
        else:
            max_workers = min(os.cpu_count() or 4, 8, len(load_tasks))  # Cap at 8 workers
        completed_count = current

        def load_artifact(artifact_name: str, artifact_path: Path, validator: Callable) -> tuple[str, Any]:
            """Load a single artifact and return (name, validated_data)."""
            data = load_structured_file(artifact_path)
            validated = validator(data)
            return (artifact_name, validated)

        if load_tasks:
            executor = ThreadPoolExecutor(max_workers=max_workers)
            interrupted = False
            # In test mode, use wait=False to avoid hanging on shutdown
            wait_on_shutdown = os.environ.get("TEST_MODE") != "true"
            try:
                # Submit all tasks
                future_to_task = {
                    executor.submit(load_artifact, name, path, validator): (name, path, validator)
                    for name, path, validator in load_tasks
                }

                # Collect results as they complete
                try:
                    for future in as_completed(future_to_task):
                        try:
                            artifact_name, result = future.result()
                            completed_count += 1

                            if progress_callback:
                                progress_callback(completed_count, total_artifacts, artifact_name)

                            # Assign results to appropriate variables
                            if artifact_name == "idea.yaml":
                                idea = result  # type: ignore[assignment]  # Validated by validator
                            elif artifact_name == "business.yaml":
                                business = result  # type: ignore[assignment]  # Validated by validator
                            elif artifact_name == "product.yaml":
                                product = result  # type: ignore[assignment]  # Validated by validator, required field
                            elif artifact_name == "clarifications.yaml":
                                clarifications = result  # type: ignore[assignment]  # Validated by validator
                            elif (
                                artifact_name.startswith("features/") and isinstance(result, tuple) and len(result) == 2
                            ):
                                # Result is (key, Feature) tuple for features
                                key, feature = result
                                features[key] = feature
                        except KeyboardInterrupt:
                            interrupted = True
                            for f in future_to_task:
                                if not f.done():
                                    f.cancel()
                            break
                        except Exception as e:
                            # Log error but continue loading other artifacts
                            artifact_name = future_to_task[future][0]
                            raise ValueError(f"Failed to load {artifact_name}: {e}") from e
                except KeyboardInterrupt:
                    interrupted = True
                    for f in future_to_task:
                        if not f.done():
                            f.cancel()
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

        # Validate that required product was loaded
        if product is None:
            raise FileNotFoundError(f"Product file not found or failed to load: {bundle_dir / 'product.yaml'}")

        bundle_name = bundle_dir.name

        return cls(
            manifest=manifest,
            bundle_name=bundle_name,
            idea=idea,
            business=business,
            product=product,  # type: ignore[arg-type]  # Verified to be non-None above
            features=features,
            clarifications=clarifications,
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

        # Update manifest bundle metadata
        now = datetime.now(UTC).isoformat()
        if "created_at" not in self.manifest.bundle:
            self.manifest.bundle["created_at"] = now
        self.manifest.bundle["last_modified"] = now
        self.manifest.bundle["format"] = "directory-based"

        # Prepare tasks for parallel saving (all artifacts except manifest)
        save_tasks: list[tuple[str, Path, dict[str, Any]]] = []

        # Add aspect saving tasks
        if self.idea:
            save_tasks.append(("idea.yaml", bundle_dir / "idea.yaml", self.idea.model_dump()))

        if self.business:
            save_tasks.append(("business.yaml", bundle_dir / "business.yaml", self.business.model_dump()))

        save_tasks.append(("product.yaml", bundle_dir / "product.yaml", self.product.model_dump()))

        if self.clarifications:
            save_tasks.append(
                ("clarifications.yaml", bundle_dir / "clarifications.yaml", self.clarifications.model_dump())
            )

        # Prepare feature saving tasks
        features_dir = bundle_dir / "features"
        features_dir.mkdir(parents=True, exist_ok=True)

        # Ensure features is a dict with string keys and Feature values
        if not isinstance(self.features, dict):
            raise ValueError(f"Expected features to be dict, got {type(self.features)}")

        for key, feature in self.features.items():
            # Ensure key is a string, not a FeatureIndex or other object
            if not isinstance(key, str):
                raise ValueError(f"Expected feature key to be string, got {type(key)}: {key}")
            # Ensure feature is a Feature object, not a FeatureIndex
            if not isinstance(feature, Feature):
                raise ValueError(f"Expected feature to be Feature, got {type(feature)}: {feature}")

            feature_file = f"{key}.yaml"
            feature_path = features_dir / feature_file
            save_tasks.append((f"features/{feature_file}", feature_path, feature.model_dump()))

        # Save artifacts in parallel using ThreadPoolExecutor
        # In test mode, use fewer workers to avoid resource contention
        if os.environ.get("TEST_MODE") == "true":
            max_workers = max(1, min(2, len(save_tasks)))  # Max 2 workers in test mode
        else:
            max_workers = min(os.cpu_count() or 4, 8, len(save_tasks))  # Cap at 8 workers
        completed_count = 0
        checksums: dict[str, str] = {}  # Track checksums for manifest update
        feature_indices: list[FeatureIndex] = []  # Track feature indices

        def save_artifact(artifact_name: str, artifact_path: Path, data: dict[str, Any]) -> tuple[str, str]:
            """Save a single artifact and return (name, checksum)."""
            dump_structured_file(data, artifact_path)
            # Compute checksum after file is written (static method)
            checksum = ProjectBundle._compute_file_checksum(artifact_path)
            return (artifact_name, checksum)

        if save_tasks:
            executor = ThreadPoolExecutor(max_workers=max_workers)
            interrupted = False
            # In test mode, use wait=False to avoid hanging on shutdown
            wait_on_shutdown = os.environ.get("TEST_MODE") != "true"
            try:
                # Submit all tasks
                future_to_task = {
                    executor.submit(save_artifact, name, path, data): (name, path, data)
                    for name, path, data in save_tasks
                }

                # Collect results as they complete
                try:
                    for future in as_completed(future_to_task):
                        try:
                            artifact_name, checksum = future.result()
                            completed_count += 1
                            checksums[artifact_name] = checksum

                            if progress_callback:
                                progress_callback(completed_count, total_artifacts, artifact_name)

                            # Build feature indices for features
                            if artifact_name.startswith("features/"):
                                feature_file = artifact_name.split("/", 1)[1]
                                key = feature_file.replace(".yaml", "")
                                if key in self.features:
                                    feature = self.features[key]
                                    feature_index = FeatureIndex(
                                        key=key,
                                        title=feature.title,
                                        file=feature_file,
                                        status="active" if not feature.draft else "draft",
                                        stories_count=len(feature.stories),
                                        created_at=now,  # TODO: Preserve original created_at if exists
                                        updated_at=now,
                                        contract=feature.contract,  # Link contract from feature
                                        checksum=checksum,
                                    )
                                    feature_indices.append(feature_index)
                        except KeyboardInterrupt:
                            interrupted = True
                            for f in future_to_task:
                                if not f.done():
                                    f.cancel()
                            break
                        except Exception as e:
                            # Get artifact name from the future's task
                            artifact_name = future_to_task.get(future, ("unknown", None, None))[0]
                            error_msg = f"Failed to save {artifact_name}"
                            if str(e):
                                error_msg += f": {e}"
                            raise ValueError(error_msg) from e
                except KeyboardInterrupt:
                    interrupted = True
                    for f in future_to_task:
                        if not f.done():
                            f.cancel()
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

        # Update manifest with checksums and feature indices
        self.manifest.checksums.files.update(checksums)
        self.manifest.features = feature_indices

        # Save manifest (last, after all checksums are computed)
        if progress_callback:
            progress_callback(total_artifacts, total_artifacts, "bundle.manifest.yaml")
        manifest_path = bundle_dir / "bundle.manifest.yaml"
        dump_structured_file(self.manifest.model_dump(mode="json"), manifest_path)

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
    @require(lambda file_path: file_path.exists(), "File must exist")
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
