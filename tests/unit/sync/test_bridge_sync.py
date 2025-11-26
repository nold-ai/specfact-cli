"""Unit tests for bridge-based sync functionality."""

from specfact_cli.models.bridge import AdapterType, ArtifactMapping, BridgeConfig
from specfact_cli.models.project import ProjectBundle
from specfact_cli.sync.bridge_sync import BridgeSync, SyncOperation, SyncResult


class TestBridgeSync:
    """Test BridgeSync class."""

    def test_init_with_bridge_config(self, tmp_path):
        """Test BridgeSync initialization with bridge config."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        assert sync.repo_path == tmp_path.resolve()
        assert sync.bridge_config == bridge_config

    def test_init_auto_detect(self, tmp_path):
        """Test BridgeSync initialization with auto-detection."""
        # Create Spec-Kit structure
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir()
        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        sync = BridgeSync(tmp_path)
        assert sync.bridge_config is not None
        assert sync.bridge_config.adapter == AdapterType.SPECKIT

    def test_resolve_artifact_path(self, tmp_path):
        """Test resolving artifact path using bridge config."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        resolved = sync.resolve_artifact_path("specification", "001-auth", "test-bundle")

        assert resolved == tmp_path / "specs" / "001-auth" / "spec.md"

    def test_resolve_artifact_path_modern_layout(self, tmp_path):
        """Test resolving artifact path with modern layout."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="docs/specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        resolved = sync.resolve_artifact_path("specification", "001-auth", "test-bundle")

        assert resolved == tmp_path / "docs" / "specs" / "001-auth" / "spec.md"

    def test_import_artifact_not_found(self, tmp_path):
        """Test importing artifact when file doesn't exist."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        # Create project bundle
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)
        (bundle_dir / "bundle.manifest.yaml").write_text("versions:\n  schema: '1.0'\n  project: '0.1.0'\n")

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        result = sync.import_artifact("specification", "001-auth", "test-bundle")

        assert result.success is False
        assert len(result.errors) > 0
        assert any("not found" in error.lower() for error in result.errors)

    def test_export_artifact(self, tmp_path):
        """Test exporting artifact to tool format."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        # Create project bundle
        from specfact_cli.models.project import BundleManifest, BundleVersions, Product
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="test-bundle",
            product=product,
            features={},
        )

        from specfact_cli.utils.bundle_loader import save_project_bundle

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        result = sync.export_artifact("specification", "001-auth", "test-bundle")

        assert result.success is True
        assert len(result.operations) == 1
        assert result.operations[0].direction == "export"

        # Verify file was created
        artifact_path = tmp_path / "specs" / "001-auth" / "spec.md"
        assert artifact_path.exists()

    def test_export_artifact_conflict_detection(self, tmp_path):
        """Test conflict detection warning when target file exists."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        # Create project bundle
        from specfact_cli.models.project import BundleManifest, BundleVersions, Product
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="test-bundle",
            product=product,
            features={},
        )

        from specfact_cli.utils.bundle_loader import save_project_bundle

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Create existing target file (simulates conflict)
        artifact_path = tmp_path / "specs" / "001-auth" / "spec.md"
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_text("# Existing spec\n", encoding="utf-8")

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        result = sync.export_artifact("specification", "001-auth", "test-bundle")

        # Should succeed but with warning
        assert result.success is True
        assert len(result.warnings) > 0
        assert any("already exists" in warning.lower() for warning in result.warnings)

    def test_export_artifact_with_feature(self, tmp_path):
        """Test exporting artifact with feature in bundle."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        # Create project bundle with feature
        from specfact_cli.models.plan import Feature as PlanFeature
        from specfact_cli.models.project import BundleManifest, BundleVersions, Product
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        feature = PlanFeature(key="FEATURE-001", title="Authentication", stories=[])
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="test-bundle",
            product=product,
            features={"FEATURE-001": feature},
        )

        from specfact_cli.utils.bundle_loader import save_project_bundle

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        result = sync.export_artifact("specification", "FEATURE-001", "test-bundle")

        assert result.success is True
        artifact_path = tmp_path / "specs" / "FEATURE-001" / "spec.md"
        assert artifact_path.exists()
        content = artifact_path.read_text()
        assert "Authentication" in content

    def test_sync_bidirectional(self, tmp_path):
        """Test bidirectional sync."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        # Create project bundle
        from specfact_cli.models.project import BundleManifest, BundleVersions, Product
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="test-bundle",
            product=product,
            features={},
        )

        from specfact_cli.utils.bundle_loader import save_project_bundle

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        result = sync.sync_bidirectional("test-bundle", feature_ids=["001-auth"])

        # Should succeed (even if no artifacts found, validation should pass)
        assert isinstance(result, SyncResult)

    def test_discover_feature_ids(self, tmp_path):
        """Test discovering feature IDs from bridge-resolved paths."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        # Create specs directory with feature directories
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        (specs_dir / "001-auth").mkdir()
        (specs_dir / "001-auth" / "spec.md").write_text("# Auth Feature")
        (specs_dir / "002-payment").mkdir()
        (specs_dir / "002-payment" / "spec.md").write_text("# Payment Feature")

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        feature_ids = sync._discover_feature_ids()

        assert "001-auth" in feature_ids
        assert "002-payment" in feature_ids

    def test_import_generic_markdown(self, tmp_path):
        """Test importing generic markdown artifact."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.GENERIC_MARKDOWN,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        # Create artifact file
        artifact_path = tmp_path / "specs" / "001-auth" / "spec.md"
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_text("# Feature Specification")

        # Create project bundle
        from specfact_cli.models.project import BundleManifest, BundleVersions, Product
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="test-bundle",
            product=product,
            features={},
        )

        from specfact_cli.utils.bundle_loader import save_project_bundle

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        result = sync.import_artifact("specification", "001-auth", "test-bundle")

        # Should succeed (generic import is placeholder but doesn't error)
        assert isinstance(result, SyncResult)

    def test_export_generic_markdown(self, tmp_path):
        """Test exporting generic markdown artifact."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.GENERIC_MARKDOWN,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        # Create project bundle
        from specfact_cli.models.project import BundleManifest, BundleVersions, Product
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="test-bundle",
            product=product,
            features={},
        )

        from specfact_cli.utils.bundle_loader import save_project_bundle

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = BridgeSync(tmp_path, bridge_config=bridge_config)
        result = sync.export_artifact("specification", "001-auth", "test-bundle")

        assert result.success is True
        artifact_path = tmp_path / "specs" / "001-auth" / "spec.md"
        assert artifact_path.exists()


class TestSyncOperation:
    """Test SyncOperation dataclass."""

    def test_create_sync_operation(self):
        """Test creating sync operation."""
        operation = SyncOperation(
            artifact_key="specification",
            feature_id="001-auth",
            direction="import",
            bundle_name="test-bundle",
        )
        assert operation.artifact_key == "specification"
        assert operation.feature_id == "001-auth"
        assert operation.direction == "import"
        assert operation.bundle_name == "test-bundle"


class TestSyncResult:
    """Test SyncResult dataclass."""

    def test_create_sync_result(self):
        """Test creating sync result."""
        result = SyncResult(
            success=True,
            operations=[],
            errors=[],
            warnings=[],
        )
        assert result.success is True
        assert len(result.operations) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
