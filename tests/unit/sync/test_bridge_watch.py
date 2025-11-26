"""Unit tests for bridge-based watch mode."""

from specfact_cli.models.bridge import AdapterType, ArtifactMapping, BridgeConfig
from specfact_cli.sync.bridge_watch import BridgeWatch, BridgeWatchEventHandler
from specfact_cli.sync.watcher import FileChange


class TestBridgeWatchEventHandler:
    """Test BridgeWatchEventHandler class."""

    def test_init(self, tmp_path):
        """Test BridgeWatchEventHandler initialization."""
        from collections import deque

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        change_queue: deque[FileChange] = deque()
        handler = BridgeWatchEventHandler(tmp_path, change_queue, bridge_config)

        assert handler.repo_path == tmp_path.resolve()
        assert handler.bridge_config == bridge_config

    def test_detect_change_type_speckit(self, tmp_path):
        """Test detecting Spec-Kit change type."""
        from collections import deque

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        change_queue: deque[FileChange] = deque()
        handler = BridgeWatchEventHandler(tmp_path, change_queue, bridge_config)

        spec_file = tmp_path / "specs" / "001-auth" / "spec.md"
        change_type = handler._detect_change_type(spec_file)

        assert change_type == "spec_kit"

    def test_detect_change_type_specfact(self, tmp_path):
        """Test detecting SpecFact change type."""
        from collections import deque

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        change_queue: deque[FileChange] = deque()
        handler = BridgeWatchEventHandler(tmp_path, change_queue, bridge_config)

        specfact_file = tmp_path / ".specfact" / "projects" / "test" / "bundle.manifest.yaml"
        change_type = handler._detect_change_type(specfact_file)

        assert change_type == "specfact"

    def test_detect_change_type_code(self, tmp_path):
        """Test detecting code change type."""
        from collections import deque

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        change_queue: deque[FileChange] = deque()
        handler = BridgeWatchEventHandler(tmp_path, change_queue, bridge_config)

        code_file = tmp_path / "src" / "main.py"
        change_type = handler._detect_change_type(code_file)

        assert change_type == "code"


class TestBridgeWatch:
    """Test BridgeWatch class."""

    def test_init_with_bridge_config(self, tmp_path):
        """Test BridgeWatch initialization with bridge config."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        watch = BridgeWatch(tmp_path, bridge_config=bridge_config, bundle_name="test-bundle")

        assert watch.repo_path == tmp_path.resolve()
        assert watch.bridge_config == bridge_config
        assert watch.bundle_name == "test-bundle"

    def test_init_auto_detect(self, tmp_path):
        """Test BridgeWatch initialization with auto-detection."""
        # Create Spec-Kit structure
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir()
        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        watch = BridgeWatch(tmp_path, bundle_name="test-bundle")

        assert watch.bridge_config is not None
        assert watch.bridge_config.adapter == AdapterType.SPECKIT

    def test_resolve_watch_paths(self, tmp_path):
        """Test resolving watch paths from bridge config."""
        # Create specs directory
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        watch = BridgeWatch(tmp_path, bridge_config=bridge_config)
        watch_paths = watch._resolve_watch_paths()

        assert specs_dir in watch_paths

    def test_resolve_watch_paths_modern_layout(self, tmp_path):
        """Test resolving watch paths with modern layout."""
        # Create docs/specs directory
        docs_specs_dir = tmp_path / "docs" / "specs"
        docs_specs_dir.mkdir(parents=True)

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="docs/specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        watch = BridgeWatch(tmp_path, bridge_config=bridge_config)
        watch_paths = watch._resolve_watch_paths()

        assert docs_specs_dir in watch_paths

    def test_resolve_watch_paths_includes_specfact(self, tmp_path):
        """Test that .specfact directory is included in watch paths."""
        # Create .specfact directory
        specfact_dir = tmp_path / ".specfact"
        specfact_dir.mkdir()

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        watch = BridgeWatch(tmp_path, bridge_config=bridge_config)
        watch_paths = watch._resolve_watch_paths()

        assert specfact_dir in watch_paths

    def test_extract_feature_id_from_path(self, tmp_path):
        """Test extracting feature ID from file path."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        watch = BridgeWatch(tmp_path, bridge_config=bridge_config)
        feature_id = watch._extract_feature_id_from_path(tmp_path / "specs" / "001-auth" / "spec.md")

        assert feature_id == "001-auth"

    def test_extract_feature_id_from_path_not_found(self, tmp_path):
        """Test extracting feature ID when not found."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        watch = BridgeWatch(tmp_path, bridge_config=bridge_config)
        feature_id = watch._extract_feature_id_from_path(tmp_path / "other" / "file.md")

        assert feature_id is None

    def test_determine_artifact_key(self, tmp_path):
        """Test determining artifact key from file path."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
                "plan": ArtifactMapping(
                    path_pattern="specs/{feature_id}/plan.md",
                    format="markdown",
                ),
            },
        )

        watch = BridgeWatch(tmp_path, bridge_config=bridge_config)
        artifact_key = watch._determine_artifact_key(tmp_path / "specs" / "001-auth" / "spec.md")

        assert artifact_key == "specification"

    def test_determine_artifact_key_plan(self, tmp_path):
        """Test determining artifact key for plan.md."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
                "plan": ArtifactMapping(
                    path_pattern="specs/{feature_id}/plan.md",
                    format="markdown",
                ),
            },
        )

        watch = BridgeWatch(tmp_path, bridge_config=bridge_config)
        artifact_key = watch._determine_artifact_key(tmp_path / "specs" / "001-auth" / "plan.md")

        assert artifact_key == "plan"

    def test_determine_artifact_key_not_found(self, tmp_path):
        """Test determining artifact key when not found."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        watch = BridgeWatch(tmp_path, bridge_config=bridge_config)
        artifact_key = watch._determine_artifact_key(tmp_path / "other" / "file.md")

        assert artifact_key is None

    def test_stop_when_not_running(self, tmp_path):
        """Test stopping when not running."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        watch = BridgeWatch(tmp_path, bridge_config=bridge_config)
        watch.stop()  # Should not error

        assert watch.running is False
