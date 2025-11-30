"""
Unit tests for plan bundle migration.

Tests migration from older schema versions to current version.
"""

import pytest
import yaml

from specfact_cli.migrations.plan_migrator import (
    PlanMigrator,
    get_current_schema_version,
    load_plan_bundle,
    migrate_plan_bundle,
)
from specfact_cli.models.plan import Feature, PlanBundle, Product


class TestPlanMigrator:
    """Tests for PlanMigrator class."""

    def test_get_current_schema_version(self):
        """Test getting current schema version."""
        version = get_current_schema_version()
        assert isinstance(version, str)
        assert version == "1.1"  # Current version with summary metadata

    def test_load_plan_bundle(self, tmp_path):
        """Test loading plan bundle from file."""
        # Create a test plan bundle
        plan_path = tmp_path / "test.bundle.yaml"
        plan_data = {
            "version": "1.0",
            "product": {"themes": ["Theme1"]},
            "features": [],
        }
        with plan_path.open("w") as f:
            yaml.dump(plan_data, f)

        bundle = load_plan_bundle(plan_path)
        assert isinstance(bundle, PlanBundle)
        assert bundle.version == "1.0"

    def test_migrate_plan_bundle_1_0_to_1_1(self):
        """Test migration from schema 1.0 to 1.1 (add summary metadata)."""
        product = Product(themes=["Theme1"])
        features = [Feature(key="FEATURE-001", title="Feature 1", source_tracking=None, contract=None, protocol=None)]

        bundle = PlanBundle(
            version="1.0",
            product=product,
            features=features,
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        # Migrate
        migrated = migrate_plan_bundle(bundle, "1.0", "1.1")

        assert migrated.version == "1.1"
        assert migrated.metadata is not None
        assert migrated.metadata.summary is not None
        assert migrated.metadata.summary.features_count == 1
        assert migrated.metadata.summary.content_hash is not None

    def test_migrate_plan_bundle_same_version(self):
        """Test migration when versions are the same (no-op)."""
        product = Product(themes=["Theme1"])
        bundle = PlanBundle(
            version="1.1",
            product=product,
            features=[],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        migrated = migrate_plan_bundle(bundle, "1.1", "1.1")
        assert migrated.version == "1.1"
        assert migrated is bundle  # Should return same instance

    def test_migrate_plan_bundle_unknown_version(self):
        """Test migration with unknown version raises error."""
        product = Product(themes=["Theme1"])
        bundle = PlanBundle(
            version="2.0",
            product=product,
            features=[],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        with pytest.raises(ValueError, match="no migration path"):
            migrate_plan_bundle(bundle, "2.0", "1.1")

    def test_plan_migrator_check_migration_needed(self, tmp_path):
        """Test checking if migration is needed."""
        migrator = PlanMigrator()

        # Create plan bundle without summary (needs migration)
        plan_path = tmp_path / "test.bundle.yaml"
        plan_data = {
            "version": "1.0",
            "product": {"themes": ["Theme1"]},
            "features": [],
        }
        with plan_path.open("w") as f:
            yaml.dump(plan_data, f)

        needs_migration, reason = migrator.check_migration_needed(plan_path)
        assert needs_migration is True
        assert "Missing summary" in reason or "version" in reason.lower()

    def test_plan_migrator_check_migration_not_needed(self, tmp_path):
        """Test checking when migration is not needed."""
        migrator = PlanMigrator()

        # Create plan bundle with summary (up to date)
        product = Product(themes=["Theme1"])
        bundle = PlanBundle(
            version="1.1",
            product=product,
            features=[],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )
        bundle.update_summary(include_hash=True)

        plan_path = tmp_path / "test.bundle.yaml"
        from specfact_cli.generators.plan_generator import PlanGenerator

        generator = PlanGenerator()
        generator.generate(bundle, plan_path, update_summary=True)

        needs_migration, reason = migrator.check_migration_needed(plan_path)
        assert needs_migration is False
        assert "Up to date" in reason

    def test_plan_migrator_load_and_migrate(self, tmp_path):
        """Test loading and migrating a plan bundle."""
        migrator = PlanMigrator()

        # Create plan bundle without summary (needs migration)
        plan_path = tmp_path / "test.bundle.yaml"
        plan_data = {
            "version": "1.0",
            "product": {"themes": ["Theme1"]},
            "features": [{"key": "FEATURE-001", "title": "Feature 1"}],
        }
        with plan_path.open("w") as f:
            yaml.dump(plan_data, f)

        # Load and migrate (dry run)
        bundle, was_migrated = migrator.load_and_migrate(plan_path, dry_run=True)
        assert was_migrated is True
        assert bundle.metadata is not None
        assert bundle.metadata.summary is not None

        # Verify file wasn't changed (dry run)
        with plan_path.open() as f:
            plan_data_after = yaml.safe_load(f)
        assert plan_data_after.get("version") == "1.0"  # Not updated in dry run

        # Load and migrate (actual migration)
        bundle, was_migrated = migrator.load_and_migrate(plan_path, dry_run=False)
        assert was_migrated is True

        # Verify file was updated
        with plan_path.open() as f:
            plan_data_after = yaml.safe_load(f)
        assert plan_data_after.get("version") == "1.1"
        assert "summary" in plan_data_after.get("metadata", {})
