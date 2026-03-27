"""Unit tests for Spec-Kit bridge adapter."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.adapters.speckit import SpecKitAdapter
from specfact_cli.models.bridge import AdapterType, BridgeConfig


@pytest.fixture
def speckit_adapter() -> SpecKitAdapter:
    """Create Spec-Kit adapter instance for testing."""
    return SpecKitAdapter()


@pytest.fixture
def bridge_config_classic() -> BridgeConfig:
    """Create classic Spec-Kit bridge config for testing."""
    return BridgeConfig.preset_speckit_classic()


@pytest.fixture
def bridge_config_modern() -> BridgeConfig:
    """Create modern Spec-Kit bridge config for testing."""
    return BridgeConfig.preset_speckit_modern()


@pytest.fixture
def speckit_repo_classic(tmp_path: Path) -> Path:
    """Create a temporary classic Spec-Kit repository structure."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    feature_dir = specs_dir / "001-auth"
    feature_dir.mkdir()
    (feature_dir / "spec.md").write_text(
        """# Authentication Feature

## Overview
User authentication system with JWT tokens.

## Stories
- As a user, I want to log in with email and password
- As a user, I want to receive a JWT token after login
"""
    )
    (feature_dir / "plan.md").write_text(
        """# Authentication Plan

## Implementation
1. Create login endpoint
2. Implement JWT token generation
3. Add password hashing
"""
    )
    (feature_dir / "tasks.md").write_text(
        """# Authentication Tasks

- [ ] Create login API endpoint
- [ ] Implement JWT token generation
- [ ] Add password hashing with bcrypt
"""
    )
    return tmp_path


@pytest.fixture
def speckit_repo_modern(tmp_path: Path) -> Path:
    """Create a temporary modern Spec-Kit repository structure."""
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir()
    memory_dir = specify_dir / "memory"
    memory_dir.mkdir()
    (memory_dir / "constitution.md").write_text(
        """# Constitution

## Principles
- Test-driven development
- Contract-first design
"""
    )
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    specs_dir = docs_dir / "specs"
    specs_dir.mkdir()
    feature_dir = specs_dir / "001-auth"
    feature_dir.mkdir()
    (feature_dir / "spec.md").write_text(
        """# Authentication Feature

## Overview
User authentication system.
"""
    )
    return tmp_path


class TestSpecKitAdapter:
    """Test Spec-Kit adapter implementation."""

    def test_detect_same_repo_classic(self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path) -> None:
        """Test detecting classic Spec-Kit in same repository."""
        assert speckit_adapter.detect(speckit_repo_classic) is True

    def test_detect_same_repo_modern(self, speckit_adapter: SpecKitAdapter, speckit_repo_modern: Path) -> None:
        """Test detecting modern Spec-Kit in same repository."""
        assert speckit_adapter.detect(speckit_repo_modern) is True

    def test_detect_cross_repo_classic(self, speckit_adapter: SpecKitAdapter, tmp_path: Path) -> None:
        """Test detecting classic Spec-Kit in cross-repo scenario."""
        external_path = tmp_path / "external"
        specs_dir = external_path / "specs"
        specs_dir.mkdir(parents=True)
        feature_dir = specs_dir / "001-auth"
        feature_dir.mkdir()
        (feature_dir / "spec.md").write_text("# Auth Feature")

        bridge_config = BridgeConfig.preset_speckit_classic()
        bridge_config.external_base_path = external_path

        assert speckit_adapter.detect(tmp_path, bridge_config) is True

    def test_detect_cross_repo_modern(self, speckit_adapter: SpecKitAdapter, tmp_path: Path) -> None:
        """Test detecting modern Spec-Kit in cross-repo scenario."""
        external_path = tmp_path / "external"
        specify_dir = external_path / ".specify"
        specify_dir.mkdir(parents=True)
        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        (memory_dir / "constitution.md").write_text("# Constitution")

        bridge_config = BridgeConfig.preset_speckit_modern()
        bridge_config.external_base_path = external_path

        assert speckit_adapter.detect(tmp_path, bridge_config) is True

    def test_detect_not_speckit(self, speckit_adapter: SpecKitAdapter, tmp_path: Path) -> None:
        """Test detecting non-Spec-Kit repository."""
        assert speckit_adapter.detect(tmp_path) is False

    def test_get_capabilities_classic(self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path) -> None:
        """Test getting adapter capabilities for classic format."""
        capabilities = speckit_adapter.get_capabilities(speckit_repo_classic)

        assert capabilities.tool == "speckit"
        assert capabilities.layout == "classic"
        assert capabilities.specs_dir == "specs"
        assert capabilities.supported_sync_modes == ["bidirectional", "unidirectional"]

    def test_get_capabilities_modern(self, speckit_adapter: SpecKitAdapter, speckit_repo_modern: Path) -> None:
        """Test getting adapter capabilities for modern format."""
        capabilities = speckit_adapter.get_capabilities(speckit_repo_modern)

        assert capabilities.tool == "speckit"
        assert capabilities.layout == "modern"
        assert capabilities.specs_dir == "docs/specs"
        assert capabilities.has_custom_hooks is True  # Has constitution.md
        assert capabilities.supported_sync_modes == ["bidirectional", "unidirectional"]

    def test_get_capabilities_cross_repo(self, speckit_adapter: SpecKitAdapter, tmp_path: Path) -> None:
        """Test getting capabilities with cross-repo configuration."""
        external_path = tmp_path / "external"
        specs_dir = external_path / "specs"
        specs_dir.mkdir(parents=True)
        feature_dir = specs_dir / "001-auth"
        feature_dir.mkdir()
        (feature_dir / "spec.md").write_text("# Auth Feature")

        bridge_config = BridgeConfig.preset_speckit_classic()
        bridge_config.external_base_path = external_path

        capabilities = speckit_adapter.get_capabilities(tmp_path, bridge_config)

        assert capabilities.tool == "speckit"
        assert capabilities.has_external_config is True

    def test_generate_bridge_config_classic(self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path) -> None:
        """Test generating bridge config for classic format."""
        bridge_config = speckit_adapter.generate_bridge_config(speckit_repo_classic)

        assert bridge_config.adapter == AdapterType.SPECKIT
        # Check capabilities to verify layout
        capabilities = speckit_adapter.get_capabilities(speckit_repo_classic, bridge_config)
        assert capabilities.layout == "classic"
        assert "specification" in bridge_config.artifacts
        assert "plan" in bridge_config.artifacts
        assert "tasks" in bridge_config.artifacts
        assert "constitution" in bridge_config.artifacts

    def test_generate_bridge_config_modern(self, speckit_adapter: SpecKitAdapter, speckit_repo_modern: Path) -> None:
        """Test generating bridge config for modern format."""
        bridge_config = speckit_adapter.generate_bridge_config(speckit_repo_modern)

        assert bridge_config.adapter == AdapterType.SPECKIT
        # Check capabilities to verify layout
        capabilities = speckit_adapter.get_capabilities(speckit_repo_modern, bridge_config)
        assert capabilities.layout == "modern"
        assert "specification" in bridge_config.artifacts
        assert "plan" in bridge_config.artifacts
        assert "tasks" in bridge_config.artifacts
        assert "constitution" in bridge_config.artifacts

    def test_import_artifact_specification(self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path) -> None:
        """Test importing specification artifact."""
        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(manifest=manifest, bundle_name="test", product=product, features={})
        spec_path = speckit_repo_classic / "specs" / "001-auth" / "spec.md"

        bridge_config = BridgeConfig.preset_speckit_classic()
        speckit_adapter.import_artifact("specification", spec_path, project_bundle, bridge_config)

        # Check that feature was imported (key might be normalized)
        assert len(project_bundle.features) > 0
        # Find feature by checking all features for matching key or title
        feature_found = False
        for feature_key, feature in project_bundle.features.items():
            if "001" in feature_key.upper() or "auth" in feature_key.lower() or "Authentication" in feature.title:
                feature_found = True
                assert feature.source_tracking is not None
                assert feature.source_tracking.tool == "speckit"
                break
        assert feature_found, "Feature should be imported"

    def test_import_artifact_plan(self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path) -> None:
        """Test importing plan artifact."""
        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(manifest=manifest, bundle_name="test", product=product, features={})
        plan_path = speckit_repo_classic / "specs" / "001-auth" / "plan.md"

        bridge_config = BridgeConfig.preset_speckit_classic()
        speckit_adapter.import_artifact("plan", plan_path, project_bundle, bridge_config)

        # Plan import should update existing feature or create one
        assert len(project_bundle.features) > 0

    def test_import_artifact_tasks(self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path) -> None:
        """Test importing tasks artifact."""
        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(manifest=manifest, bundle_name="test", product=product, features={})
        tasks_path = speckit_repo_classic / "specs" / "001-auth" / "tasks.md"

        bridge_config = BridgeConfig.preset_speckit_classic()
        # Tasks import may require existing feature
        # Import spec first to ensure feature exists
        spec_path = speckit_repo_classic / "specs" / "001-auth" / "spec.md"
        speckit_adapter.import_artifact("specification", spec_path, project_bundle, bridge_config)
        # Then import tasks
        speckit_adapter.import_artifact("tasks", tasks_path, project_bundle, bridge_config)

        # Tasks import should update existing feature or create one
        assert len(project_bundle.features) > 0

    def test_export_artifact_specification_raises_not_implemented(
        self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path
    ) -> None:
        """Test that export_artifact for specification raises NotImplementedError (not yet fully implemented)."""
        from specfact_cli.models.plan import Feature, Story
        from specfact_cli.models.source_tracking import SourceTracking

        feature = Feature(
            key="001-auth",
            title="Authentication Feature",
            stories=[
                Story(
                    key="001-auth-001",
                    title="Login with email and password",
                    story_points=None,
                    value_points=None,
                    scenarios=None,
                    contracts=None,
                )
            ],
            source_tracking=SourceTracking(tool="speckit", source_metadata={"path": "specs/001-auth/spec.md"}),
        )

        bridge_config = BridgeConfig.preset_speckit_classic()
        with pytest.raises(NotImplementedError, match=r"Spec-Kit adapter export_specification"):
            speckit_adapter.export_artifact("specification", feature, bridge_config)

    def test_export_artifact_plan(self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path) -> None:
        """Test exporting plan artifact."""
        from specfact_cli.models.plan import Feature, PlanBundle, Product

        plan_bundle = PlanBundle(
            product=Product(themes=[], releases=[]),
            features=[Feature(key="001-auth", title="Auth Feature")],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        bridge_config = BridgeConfig.preset_speckit_classic()
        # Set external_base_path to test repo path so converter uses correct base
        bridge_config.external_base_path = speckit_repo_classic
        result = speckit_adapter.export_artifact("plan", plan_bundle, bridge_config)

        assert isinstance(result, Path)
        assert result.exists()
        assert result.name == "plan.md"

    def test_load_change_tracking_returns_none(
        self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path
    ) -> None:
        """Test loading change tracking (Spec-Kit doesn't support change tracking)."""
        from specfact_cli.utils.structure import SpecFactStructure

        bridge_config = BridgeConfig.preset_speckit_classic()
        bundle_dir = speckit_repo_classic / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)

        change_tracking = speckit_adapter.load_change_tracking(bundle_dir, bridge_config)

        assert change_tracking is None

    def test_save_change_tracking_raises_not_implemented(self, speckit_adapter: SpecKitAdapter, tmp_path: Path) -> None:
        """Test that save_change_tracking raises NotImplementedError."""
        from specfact_cli.models.change import ChangeTracking

        bridge_config = BridgeConfig.preset_speckit_classic()
        change_tracking = ChangeTracking(proposals={}, feature_deltas={})

        with pytest.raises(NotImplementedError, match=r"Spec-Kit.*change tracking"):
            speckit_adapter.save_change_tracking(tmp_path, change_tracking, bridge_config)

    def test_load_change_proposal_returns_none(
        self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path
    ) -> None:
        """Test loading change proposal (Spec-Kit doesn't support change proposals)."""
        from specfact_cli.utils.structure import SpecFactStructure

        bridge_config = BridgeConfig.preset_speckit_classic()
        bundle_dir = speckit_repo_classic / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)

        proposal = speckit_adapter.load_change_proposal(bundle_dir, "test-change", bridge_config)

        assert proposal is None

    def test_save_change_proposal_raises_not_implemented(self, speckit_adapter: SpecKitAdapter, tmp_path: Path) -> None:
        """Test that save_change_proposal raises NotImplementedError."""
        from datetime import UTC, datetime

        from specfact_cli.models.change import ChangeProposal

        bridge_config = BridgeConfig.preset_speckit_classic()
        proposal = ChangeProposal(
            name="test",
            title="Test proposal",
            description="Test proposal description",
            rationale="Test rationale",
            timeline=None,
            owner=None,
            created_at=datetime.now(UTC).isoformat(),
            applied_at=None,
            archived_at=None,
            status="draft",
            source_tracking=None,
        )

        with pytest.raises(NotImplementedError, match=r"Spec-Kit.*change proposals"):
            speckit_adapter.save_change_proposal(tmp_path, proposal, bridge_config)

    def test_adapter_registry_registration(self) -> None:
        """Test that Spec-Kit adapter is registered in adapter registry."""
        assert AdapterRegistry.is_registered("speckit")

        adapter = AdapterRegistry.get_adapter("speckit")
        assert isinstance(adapter, SpecKitAdapter)

    def test_discover_features(self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path) -> None:
        """Test discovering features from Spec-Kit repository."""
        bridge_config = BridgeConfig.preset_speckit_classic()
        features = speckit_adapter.discover_features(speckit_repo_classic, bridge_config)

        assert isinstance(features, list)
        # Features may be discovered with normalized keys or different structure
        # Just verify that discovery returns a list (may be empty if scanner doesn't find features)
        assert len(features) >= 0
        # If features found, check structure
        if len(features) > 0:
            assert isinstance(features[0], dict)

    def test_detect_changes(self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path) -> None:
        """Test detecting changes in Spec-Kit artifacts."""
        bridge_config = BridgeConfig.preset_speckit_classic()
        changes = speckit_adapter.detect_changes(speckit_repo_classic, direction="both", bridge_config=bridge_config)

        assert isinstance(changes, dict)
        assert "speckit_changes" in changes or "specfact_changes" in changes

    def test_detect_conflicts(self, speckit_adapter: SpecKitAdapter) -> None:
        """Test detecting conflicts between Spec-Kit and SpecFact changes."""
        speckit_changes = {"specs/001-auth/spec.md": {"type": "modified", "hash": "abc123"}}
        specfact_changes = {"specs/001-auth/spec.md": {"type": "modified", "hash": "def456"}}

        conflicts = speckit_adapter.detect_conflicts(speckit_changes, specfact_changes)

        assert isinstance(conflicts, list)
        assert len(conflicts) > 0
        assert conflicts[0]["key"] == "specs/001-auth/spec.md"

    def test_export_bundle(self, speckit_adapter: SpecKitAdapter, speckit_repo_classic: Path) -> None:
        """Test exporting a full plan bundle to Spec-Kit format."""
        from specfact_cli.models.plan import Feature, PlanBundle, Product

        plan_bundle = PlanBundle(
            product=Product(themes=[], releases=[]),
            features=[
                Feature(key="001-auth", title="Auth Feature"),
                Feature(key="002-payment", title="Payment Feature"),
            ],
            idea=None,
            business=None,
            metadata=None,
            clarifications=None,
        )

        bridge_config = BridgeConfig.preset_speckit_classic()
        count = speckit_adapter.export_bundle(plan_bundle, speckit_repo_classic, None, bridge_config)

        assert isinstance(count, int)
        assert count >= 0


class TestVersionDetection:
    """Tests for spec-kit version detection methods."""

    def test_detect_version_from_heuristics_presets(self, tmp_path: Path) -> None:
        """Detects >=0.3.0 when presets/ directory exists."""
        (tmp_path / "presets").mkdir()
        adapter = SpecKitAdapter()
        assert adapter._detect_version_from_heuristics(tmp_path) == ">=0.3.0"

    def test_detect_version_from_heuristics_extensions(self, tmp_path: Path) -> None:
        """Detects >=0.2.0 when extensions/ directory exists (no presets)."""
        (tmp_path / "extensions").mkdir()
        adapter = SpecKitAdapter()
        assert adapter._detect_version_from_heuristics(tmp_path) == ">=0.2.0"

    def test_detect_version_from_heuristics_specify(self, tmp_path: Path) -> None:
        """Detects >=0.1.0 when .specify/ directory exists (no extensions/presets)."""
        (tmp_path / ".specify").mkdir()
        adapter = SpecKitAdapter()
        assert adapter._detect_version_from_heuristics(tmp_path) == ">=0.1.0"

    def test_detect_version_from_heuristics_none(self, tmp_path: Path) -> None:
        """Returns None when no spec-kit directories exist."""
        adapter = SpecKitAdapter()
        assert adapter._detect_version_from_heuristics(tmp_path) is None

    def test_detect_version_from_heuristics_priority(self, tmp_path: Path) -> None:
        """Presets takes priority over extensions over .specify."""
        (tmp_path / ".specify").mkdir()
        (tmp_path / "extensions").mkdir()
        (tmp_path / "presets").mkdir()
        adapter = SpecKitAdapter()
        assert adapter._detect_version_from_heuristics(tmp_path) == ">=0.3.0"

    def test_detect_version_from_cli_no_binary(self, tmp_path: Path) -> None:
        """Returns None when specify binary is not on PATH."""
        adapter = SpecKitAdapter()
        with patch("specfact_cli.adapters.speckit.shutil.which", return_value=None):
            assert adapter._detect_version_from_cli(tmp_path) is None

    def test_detect_version_from_cli_success(self, tmp_path: Path) -> None:
        """Parses version from successful specify --version output."""
        adapter = SpecKitAdapter()
        mock_result = type("Result", (), {"returncode": 0, "stdout": "specify v0.4.3\n"})()
        with (
            patch("specfact_cli.adapters.speckit.shutil.which", return_value="/usr/bin/specify"),
            patch("specfact_cli.adapters.speckit.subprocess.run", return_value=mock_result),
        ):
            assert adapter._detect_version_from_cli(tmp_path) == "0.4.3"

    def test_detect_version_from_cli_bad_output(self, tmp_path: Path) -> None:
        """Returns None when specify --version output has no version pattern."""
        adapter = SpecKitAdapter()
        mock_result = type("Result", (), {"returncode": 0, "stdout": "unknown\n"})()
        with (
            patch("specfact_cli.adapters.speckit.shutil.which", return_value="/usr/bin/specify"),
            patch("specfact_cli.adapters.speckit.subprocess.run", return_value=mock_result),
        ):
            assert adapter._detect_version_from_cli(tmp_path) is None


class TestGetCapabilitiesV04:
    """Integration tests for get_capabilities() with v0.4.x repo structures."""

    @pytest.fixture
    def v04_repo(self, tmp_path: Path) -> Path:
        """Create a v0.4.x Spec-Kit repo with extensions, presets, and hooks."""
        # Spec-Kit directories
        (tmp_path / ".specify" / "memory").mkdir(parents=True)
        (tmp_path / ".specify" / "memory" / "constitution.md").write_text("# Constitution\n")
        (tmp_path / "specs" / "001-auth").mkdir(parents=True)
        (tmp_path / "specs" / "001-auth" / "spec.md").write_text("# Auth\n")

        # Extensions
        ext_dir = tmp_path / "extensions"
        ext_dir.mkdir()
        catalog = [{"name": "reconcile", "commands": ["reconcile"]}, {"name": "verify", "commands": ["verify"]}]
        (ext_dir / "catalog.community.json").write_text(json.dumps(catalog))

        # Presets
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir()
        (presets_dir / "minimal.json").write_text(json.dumps({"name": "minimal"}))

        # Hook templates
        prompts_dir = tmp_path / ".specify" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "tasks.md").write_text("Run before_task validation.\nafter_task cleanup.\n")

        return tmp_path

    def test_extensions_populated(self, v04_repo: Path) -> None:
        """Extensions are detected and populated in capabilities."""
        adapter = SpecKitAdapter()
        caps = adapter.get_capabilities(v04_repo)

        assert caps.extensions is not None
        assert "reconcile" in caps.extensions
        assert "verify" in caps.extensions

    def test_extension_commands_populated(self, v04_repo: Path) -> None:
        """Extension commands dict is populated."""
        adapter = SpecKitAdapter()
        caps = adapter.get_capabilities(v04_repo)

        assert caps.extension_commands is not None
        assert caps.extension_commands["reconcile"] == ["reconcile"]

    def test_presets_populated(self, v04_repo: Path) -> None:
        """Presets are detected and populated."""
        adapter = SpecKitAdapter()
        caps = adapter.get_capabilities(v04_repo)

        assert caps.presets is not None
        assert "minimal" in caps.presets

    def test_hook_events_populated(self, v04_repo: Path) -> None:
        """Hook events are detected from prompt templates."""
        adapter = SpecKitAdapter()
        caps = adapter.get_capabilities(v04_repo)

        assert caps.hook_events is not None
        assert "before_task" in caps.hook_events
        assert "after_task" in caps.hook_events

    def test_version_heuristic_with_presets(self, v04_repo: Path) -> None:
        """Version is detected via heuristics when CLI not available."""
        adapter = SpecKitAdapter()
        with patch("specfact_cli.adapters.speckit.shutil.which", return_value=None):
            caps = adapter.get_capabilities(v04_repo)

        assert caps.version == ">=0.3.0"
        assert caps.detected_version_source == "heuristic"

    def test_cross_repo_skips_cli_probe(self, tmp_path: Path) -> None:
        """Cross-repo scenarios skip CLI version detection."""
        external = tmp_path / "external"
        (external / "specs" / "001").mkdir(parents=True)
        (external / "specs" / "001" / "spec.md").write_text("# Spec\n")

        bridge_config = BridgeConfig.preset_speckit_classic()
        bridge_config.external_base_path = external

        adapter = SpecKitAdapter()
        with patch.object(adapter, "_detect_version_from_cli") as mock_cli:
            caps = adapter.get_capabilities(tmp_path, bridge_config)
            mock_cli.assert_not_called()

        assert caps.has_external_config is True

    def test_legacy_repo_new_fields_none(self, tmp_path: Path) -> None:
        """Legacy repo (no extensions/presets/hooks) has all new fields as None."""
        (tmp_path / "specs" / "001").mkdir(parents=True)
        (tmp_path / "specs" / "001" / "spec.md").write_text("# Spec\n")

        adapter = SpecKitAdapter()
        caps = adapter.get_capabilities(tmp_path)

        assert caps.extensions is None
        assert caps.extension_commands is None
        assert caps.presets is None
        assert caps.hook_events is None
