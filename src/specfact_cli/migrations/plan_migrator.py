"""
Plan bundle migration logic.

Handles migration from older plan bundle schema versions to current version.
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.generators.plan_generator import PlanGenerator
from specfact_cli.models.plan import PlanBundle
from specfact_cli.utils.structured_io import load_structured_file


# Current schema version
CURRENT_SCHEMA_VERSION = "1.1"

# Latest schema version (alias for semantic clarity when creating new bundles)
LATEST_SCHEMA_VERSION = CURRENT_SCHEMA_VERSION

# Schema version history
# Version 1.0: Initial schema (no summary metadata)
# Version 1.1: Added summary metadata to Metadata model


@beartype
def get_current_schema_version() -> str:
    """
    Get the current plan bundle schema version.

    Returns:
        Current schema version string (e.g., "1.1")
    """
    return CURRENT_SCHEMA_VERSION


@beartype
def get_latest_schema_version() -> str:
    """
    Get the latest schema version for new bundles.

    This is an alias for get_current_schema_version() but provides semantic
    clarity when creating new bundles that should use the latest schema.

    Returns:
        Latest schema version string (e.g., "1.1")
    """
    return LATEST_SCHEMA_VERSION


@beartype
@require(lambda plan_path: plan_path.exists(), "Plan path must exist")
@ensure(lambda result: result is not None, "Must return PlanBundle")
def load_plan_bundle(plan_path: Path) -> PlanBundle:
    """
    Load plan bundle from file, handling any schema version.

    Args:
        plan_path: Path to plan bundle YAML file

    Returns:
        PlanBundle instance (may be from older schema)
    """
    plan_data = load_structured_file(plan_path)

    # Provide defaults for missing required fields (for backward compatibility)
    # This allows loading older bundles that may be missing required fields
    if "product" not in plan_data or plan_data["product"] is None:
        # Provide default Product if missing
        plan_data["product"] = {"themes": [], "releases": []}

    return PlanBundle.model_validate(plan_data)


@beartype
@require(lambda bundle: isinstance(bundle, PlanBundle), "Must be PlanBundle instance")
@require(lambda from_version: isinstance(from_version, str), "From version must be string")
@require(lambda to_version: isinstance(to_version, str), "To version must be string")
@ensure(lambda result: isinstance(result, PlanBundle), "Must return PlanBundle")
def migrate_plan_bundle(bundle: PlanBundle, from_version: str, to_version: str) -> PlanBundle:
    """
    Migrate plan bundle from one schema version to another.

    Args:
        bundle: Plan bundle to migrate
        from_version: Source schema version (e.g., "1.0")
        to_version: Target schema version (e.g., "1.1")

    Returns:
        Migrated PlanBundle instance

    Raises:
        ValueError: If migration path is not supported
    """
    if from_version == to_version:
        return bundle

    # Build migration path
    migrations = []
    current_version = from_version

    # Define migration steps
    version_steps = {
        "1.0": "1.1",  # Add summary metadata
        # Future migrations can be added here:
        # "1.1": "1.2",  # Future schema changes
    }

    # Build migration chain
    while current_version != to_version:
        if current_version not in version_steps:
            raise ValueError(
                f"Cannot migrate from version {from_version} to {to_version}: no migration path from {current_version}"
            )
        next_version = version_steps[current_version]
        migrations.append((current_version, next_version))
        current_version = next_version

    # Apply migrations in sequence
    migrated_bundle = bundle
    for from_ver, to_ver in migrations:
        migrated_bundle = _apply_migration(migrated_bundle, from_ver, to_ver)
        migrated_bundle.version = to_ver

    return migrated_bundle


@beartype
@require(lambda bundle: isinstance(bundle, PlanBundle), "Must be PlanBundle instance")
@ensure(lambda result: isinstance(result, PlanBundle), "Must return PlanBundle")
def _apply_migration(bundle: PlanBundle, from_version: str, to_version: str) -> PlanBundle:
    """
    Apply a single migration step.

    Args:
        bundle: Plan bundle to migrate
        from_version: Source version
        to_version: Target version

    Returns:
        Migrated PlanBundle
    """
    if from_version == "1.0" and to_version == "1.1":
        # Migration 1.0 -> 1.1: Add summary metadata
        bundle.update_summary(include_hash=True)
        return bundle

    # Unknown migration
    raise ValueError(f"Unknown migration: {from_version} -> {to_version}")


class PlanMigrator:
    """
    Plan bundle migrator for upgrading schema versions.

    Handles detection of schema version and migration to current version.
    """

    @beartype
    @require(lambda plan_path: plan_path.exists(), "Plan path must exist")
    @ensure(lambda result: result is not None, "Must return PlanBundle")
    def load_and_migrate(self, plan_path: Path, dry_run: bool = False) -> tuple[PlanBundle, bool]:
        """
        Load plan bundle and migrate if needed.

        Args:
            plan_path: Path to plan bundle file
            dry_run: If True, don't save migrated bundle

        Returns:
            Tuple of (PlanBundle, was_migrated)
        """
        # Load bundle (may be from older schema)
        bundle = load_plan_bundle(plan_path)

        # Check if migration is needed
        current_version = get_current_schema_version()
        bundle_version = bundle.version

        if bundle_version == current_version:
            # Check if summary exists (backward compatibility check)
            if bundle.metadata is None or bundle.metadata.summary is None:
                # Missing summary, needs migration
                bundle = migrate_plan_bundle(bundle, bundle_version, current_version)
                was_migrated = True
            else:
                was_migrated = False
        else:
            # Version mismatch, migrate
            bundle = migrate_plan_bundle(bundle, bundle_version, current_version)
            was_migrated = True

        # Save migrated bundle if needed
        if was_migrated and not dry_run:
            generator = PlanGenerator()
            generator.generate(bundle, plan_path, update_summary=True)

        return bundle, was_migrated

    @beartype
    @require(lambda plan_path: plan_path.exists(), "Plan path must exist")
    def check_migration_needed(self, plan_path: Path) -> tuple[bool, str]:
        """
        Check if plan bundle needs migration.

        Args:
            plan_path: Path to plan bundle file

        Returns:
            Tuple of (needs_migration, reason)
        """
        try:
            plan_data = load_structured_file(plan_path)
            bundle_version = plan_data.get("version", "1.0")
            current_version = get_current_schema_version()

            if bundle_version != current_version:
                return True, f"Schema version mismatch: {bundle_version} -> {current_version}"

            # Check for missing summary metadata
            metadata = plan_data.get("metadata", {})
            summary = metadata.get("summary")
            if summary is None:
                return True, "Missing summary metadata (required for version 1.1+)"

            return False, "Up to date"
        except Exception as e:
            return True, f"Error checking migration: {e}"
