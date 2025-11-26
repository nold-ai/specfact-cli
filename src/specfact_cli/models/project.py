"""
Project bundle data models for modular project structure.

This module defines Pydantic models for modular project bundles that replace
the monolithic plan bundle structure. Project bundles use a directory-based
structure with separated aspects (idea, business, product, features) and
support dual versioning (schema + project).
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field

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
    def load_from_directory(cls, bundle_dir: Path) -> ProjectBundle:
        """
        Load project bundle from directory structure.

        Args:
            bundle_dir: Path to project bundle directory (e.g., .specfact/projects/legacy-api/)

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

        # Load manifest
        manifest_data = load_structured_file(manifest_path)
        manifest = BundleManifest.model_validate(manifest_data)

        # Load aspects
        idea = None
        idea_path = bundle_dir / "idea.yaml"
        if idea_path.exists():
            idea_data = load_structured_file(idea_path)
            idea = Idea.model_validate(idea_data)

        business = None
        business_path = bundle_dir / "business.yaml"
        if business_path.exists():
            business_data = load_structured_file(business_path)
            business = Business.model_validate(business_data)

        product_path = bundle_dir / "product.yaml"
        if not product_path.exists():
            raise FileNotFoundError(f"Product file not found: {product_path}")
        product_data = load_structured_file(product_path)
        product = Product.model_validate(product_data)

        clarifications = None
        clarifications_path = bundle_dir / "clarifications.yaml"
        if clarifications_path.exists():
            clarifications_data = load_structured_file(clarifications_path)
            clarifications = Clarifications.model_validate(clarifications_data)

        # Load features (lazy loading - only load from index initially)
        features: dict[str, Feature] = {}
        features_dir = bundle_dir / "features"
        if features_dir.exists():
            # Load features from index in manifest
            for feature_index in manifest.features:
                feature_path = features_dir / feature_index.file
                if feature_path.exists():
                    feature_data = load_structured_file(feature_path)
                    feature = Feature.model_validate(feature_data)
                    features[feature_index.key] = feature

        bundle_name = bundle_dir.name

        return cls(
            manifest=manifest,
            bundle_name=bundle_name,
            idea=idea,
            business=business,
            product=product,
            features=features,
            clarifications=clarifications,
        )

    @beartype
    @require(lambda self, bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @ensure(lambda result: result is None, "Must return None")
    def save_to_directory(self, bundle_dir: Path) -> None:
        """
        Save project bundle to directory structure.

        Args:
            bundle_dir: Path to project bundle directory (e.g., .specfact/projects/legacy-api/)

        Raises:
            ValueError: If bundle structure is invalid
        """

        from specfact_cli.utils.structured_io import dump_structured_file

        # Ensure directory exists
        bundle_dir.mkdir(parents=True, exist_ok=True)

        # Update manifest bundle metadata
        now = datetime.now(UTC).isoformat()
        if "created_at" not in self.manifest.bundle:
            self.manifest.bundle["created_at"] = now
        self.manifest.bundle["last_modified"] = now
        self.manifest.bundle["format"] = "directory-based"

        # Save aspects
        if self.idea:
            idea_path = bundle_dir / "idea.yaml"
            dump_structured_file(self.idea.model_dump(), idea_path)
            # Update checksum
            self.manifest.checksums.files["idea.yaml"] = self._compute_file_checksum(idea_path)

        if self.business:
            business_path = bundle_dir / "business.yaml"
            dump_structured_file(self.business.model_dump(), business_path)
            self.manifest.checksums.files["business.yaml"] = self._compute_file_checksum(business_path)

        product_path = bundle_dir / "product.yaml"
        dump_structured_file(self.product.model_dump(), product_path)
        self.manifest.checksums.files["product.yaml"] = self._compute_file_checksum(product_path)

        if self.clarifications:
            clarifications_path = bundle_dir / "clarifications.yaml"
            dump_structured_file(self.clarifications.model_dump(), clarifications_path)
            self.manifest.checksums.files["clarifications.yaml"] = self._compute_file_checksum(clarifications_path)

        # Save features
        features_dir = bundle_dir / "features"
        features_dir.mkdir(parents=True, exist_ok=True)

        # Update feature index in manifest
        feature_indices: list[FeatureIndex] = []
        for key, feature in self.features.items():
            feature_file = f"{key}.yaml"
            feature_path = features_dir / feature_file

            dump_structured_file(feature.model_dump(), feature_path)
            checksum = self._compute_file_checksum(feature_path)

            # Find or create feature index
            feature_index = FeatureIndex(
                key=key,
                title=feature.title,
                file=feature_file,
                status="active" if not feature.draft else "draft",
                stories_count=len(feature.stories),
                created_at=now,  # TODO: Preserve original created_at if exists
                updated_at=now,
                contract=None,  # Contract will be linked separately if needed
                checksum=checksum,
            )
            feature_indices.append(feature_index)

            # Update checksum in manifest
            self.manifest.checksums.files[f"features/{feature_file}"] = checksum

        self.manifest.features = feature_indices

        # Save manifest (last, after all checksums are computed)
        manifest_path = bundle_dir / "bundle.manifest.yaml"
        dump_structured_file(self.manifest.model_dump(), manifest_path)

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
            bundle_dict = {
                "idea": self.idea.model_dump() if self.idea else None,
                "business": self.business.model_dump() if self.business else None,
                "product": self.product.model_dump(),
                "features": [f.model_dump() for f in self.features.values()],
                "clarifications": self.clarifications.model_dump() if self.clarifications else None,
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
