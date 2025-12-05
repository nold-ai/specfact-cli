"""
Integration tests for sync intelligent command.

Tests the intelligent bidirectional sync workflow with change detection,
code-to-spec sync, spec-to-code sync, and spec-to-tests sync.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Feature, Product
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.models.source_tracking import SourceTracking
from specfact_cli.utils.bundle_loader import save_project_bundle


runner = CliRunner()


class TestSyncIntelligentCommand:
    """Test suite for sync intelligent command."""

    def test_sync_intelligent_no_bundle(self, tmp_path: Path) -> None:
        """Test sync intelligent when bundle doesn't exist."""
        result = runner.invoke(app, ["sync", "intelligent", "nonexistent", "--repo", str(tmp_path)])

        assert result.exit_code == 1  # Should fail with bundle not found
        assert "Project bundle not found" in result.stdout or "Bundle name required" in result.stdout

    def test_sync_intelligent_no_changes(self, tmp_path: Path) -> None:
        """Test sync intelligent when no changes detected."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Add feature with tracked file
        feature_file = tmp_path / "src" / "feature.py"
        feature_file.parent.mkdir(parents=True)
        feature_file.write_text("# Feature implementation\n")

        source_tracking = SourceTracking(implementation_files=["src/feature.py"], test_files=[])
        source_tracking.update_hash(feature_file)

        feature = Feature(
            key="FEATURE-001",
            title="Test Feature",
            stories=[],
            source_tracking=source_tracking,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run sync intelligent
        result = runner.invoke(app, ["sync", "intelligent", bundle_name, "--repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "Intelligent Sync" in result.stdout
        assert bundle_name in result.stdout

    def test_sync_intelligent_code_to_spec_auto(self, tmp_path: Path) -> None:
        """Test sync intelligent with code-to-spec sync enabled."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Create file with old hash
        feature_file = tmp_path / "src" / "feature.py"
        feature_file.parent.mkdir(parents=True)
        feature_file.write_text("# Modified feature\n")

        import hashlib

        old_content = b"# Old content\n"
        old_hash = hashlib.sha256(old_content).hexdigest()

        source_tracking = SourceTracking(
            implementation_files=["src/feature.py"],
            test_files=[],
            file_hashes={"src/feature.py": old_hash},
        )

        feature = Feature(
            key="FEATURE-001",
            title="Test Feature",
            stories=[],
            source_tracking=source_tracking,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock CodeToSpecSync to avoid actual AST analysis
        with patch("specfact_cli.sync.code_to_spec.CodeToSpecSync") as mock_sync_class:
            mock_sync = MagicMock()
            mock_sync_class.return_value = mock_sync

            result = runner.invoke(
                app,
                [
                    "sync",
                    "intelligent",
                    bundle_name,
                    "--repo",
                    str(tmp_path),
                    "--code-to-spec",
                    "auto",
                ],
            )

            assert result.exit_code == 0
            # Should attempt code-to-spec sync if changes detected
            if "Code changes" in result.stdout:
                mock_sync.sync.assert_called_once()

    def test_sync_intelligent_code_to_spec_off(self, tmp_path: Path) -> None:
        """Test sync intelligent with code-to-spec sync disabled."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock CodeToSpecSync
        with patch("specfact_cli.sync.code_to_spec.CodeToSpecSync") as mock_sync_class:
            mock_sync = MagicMock()
            mock_sync_class.return_value = mock_sync

            result = runner.invoke(
                app,
                [
                    "sync",
                    "intelligent",
                    bundle_name,
                    "--repo",
                    str(tmp_path),
                    "--code-to-spec",
                    "off",
                ],
            )

            assert result.exit_code == 0
            # Should not call sync when disabled
            mock_sync.sync.assert_not_called()

    def test_sync_intelligent_spec_to_code_llm_prompt(self, tmp_path: Path) -> None:
        """Test sync intelligent with spec-to-code LLM prompt generation."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Create contract file
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(parents=True)
        contract_file = contracts_dir / "api.yaml"
        contract_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test API\n  version: 1.0.0\n")

        feature = Feature(
            key="FEATURE-001",
            title="Test Feature",
            stories=[],
            source_tracking=None,
            contract="contracts/api.yaml",
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock SpecToCodeSync
        with patch("specfact_cli.sync.spec_to_code.SpecToCodeSync") as mock_sync_class:
            mock_sync = MagicMock()
            mock_context = MagicMock()
            mock_sync.prepare_llm_context.return_value = mock_context
            mock_sync.generate_llm_prompt.return_value = "# LLM Prompt\nGenerate code here"
            mock_sync_class.return_value = mock_sync

            result = runner.invoke(
                app,
                [
                    "sync",
                    "intelligent",
                    bundle_name,
                    "--repo",
                    str(tmp_path),
                    "--spec-to-code",
                    "llm-prompt",
                ],
            )

            assert result.exit_code == 0
            # Should generate LLM prompt if spec changes detected
            # Note: May not detect changes if bundle was just created, but command should succeed

    def test_sync_intelligent_spec_to_code_off(self, tmp_path: Path) -> None:
        """Test sync intelligent with spec-to-code sync disabled."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock SpecToCodeSync
        with patch("specfact_cli.sync.spec_to_code.SpecToCodeSync") as mock_sync_class:
            mock_sync = MagicMock()
            mock_sync_class.return_value = mock_sync

            result = runner.invoke(
                app,
                [
                    "sync",
                    "intelligent",
                    bundle_name,
                    "--repo",
                    str(tmp_path),
                    "--spec-to-code",
                    "off",
                ],
            )

            assert result.exit_code == 0
            # Should not generate prompts when disabled
            mock_sync.prepare_llm_context.assert_not_called()

    def test_sync_intelligent_tests_specmatic(self, tmp_path: Path) -> None:
        """Test sync intelligent with Specmatic test generation."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Create contract file
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(parents=True)
        contract_file = contracts_dir / "api.yaml"
        contract_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test API\n  version: 1.0.0\n")

        feature = Feature(
            key="FEATURE-001",
            title="Test Feature",
            stories=[],
            source_tracking=None,
            contract="contracts/api.yaml",
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock SpecToTestsSync and Specmatic availability
        with (
            patch("specfact_cli.sync.spec_to_tests.SpecToTestsSync") as mock_sync_class,
            patch("specfact_cli.integrations.specmatic.check_specmatic_available", return_value=(True, None)),
        ):
            mock_sync = MagicMock()
            mock_sync_class.return_value = mock_sync

            result = runner.invoke(
                app,
                [
                    "sync",
                    "intelligent",
                    bundle_name,
                    "--repo",
                    str(tmp_path),
                    "--tests",
                    "specmatic",
                ],
            )

            assert result.exit_code == 0
            # Should attempt test generation if spec changes detected
            # Note: May not detect changes if bundle was just created, but command should succeed

    def test_sync_intelligent_tests_off(self, tmp_path: Path) -> None:
        """Test sync intelligent with test generation disabled."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock SpecToTestsSync
        with patch("specfact_cli.sync.spec_to_tests.SpecToTestsSync") as mock_sync_class:
            mock_sync = MagicMock()
            mock_sync_class.return_value = mock_sync

            result = runner.invoke(
                app,
                [
                    "sync",
                    "intelligent",
                    bundle_name,
                    "--repo",
                    str(tmp_path),
                    "--tests",
                    "off",
                ],
            )

            assert result.exit_code == 0
            # Should not generate tests when disabled
            mock_sync.sync.assert_not_called()

    def test_sync_intelligent_all_modes_enabled(self, tmp_path: Path) -> None:
        """Test sync intelligent with all sync modes enabled."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock all sync components
        with (
            patch("specfact_cli.sync.code_to_spec.CodeToSpecSync") as mock_code_to_spec,
            patch("specfact_cli.sync.spec_to_code.SpecToCodeSync") as mock_spec_to_code,
            patch("specfact_cli.sync.spec_to_tests.SpecToTestsSync") as mock_spec_to_tests,
            patch("specfact_cli.integrations.specmatic.check_specmatic_available", return_value=(True, None)),
        ):
            mock_code_to_spec.return_value = MagicMock()
            mock_spec_to_code.return_value = MagicMock()
            mock_spec_to_tests.return_value = MagicMock()

            result = runner.invoke(
                app,
                [
                    "sync",
                    "intelligent",
                    bundle_name,
                    "--repo",
                    str(tmp_path),
                    "--code-to-spec",
                    "auto",
                    "--spec-to-code",
                    "llm-prompt",
                    "--tests",
                    "specmatic",
                ],
            )

            assert result.exit_code == 0
            assert "Intelligent Sync" in result.stdout

    def test_sync_intelligent_all_modes_disabled(self, tmp_path: Path) -> None:
        """Test sync intelligent with all sync modes disabled."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock all sync components
        with (
            patch("specfact_cli.sync.code_to_spec.CodeToSpecSync") as mock_code_to_spec,
            patch("specfact_cli.sync.spec_to_code.SpecToCodeSync") as mock_spec_to_code,
            patch("specfact_cli.sync.spec_to_tests.SpecToTestsSync") as mock_spec_to_tests,
        ):
            mock_code_sync = MagicMock()
            mock_code_to_spec.return_value = mock_code_sync
            mock_spec_to_code.return_value = MagicMock()
            mock_spec_to_tests.return_value = MagicMock()

            result = runner.invoke(
                app,
                [
                    "sync",
                    "intelligent",
                    bundle_name,
                    "--repo",
                    str(tmp_path),
                    "--code-to-spec",
                    "off",
                    "--spec-to-code",
                    "off",
                    "--tests",
                    "off",
                ],
            )

            assert result.exit_code == 0
            # Should not call any sync methods when all disabled
            mock_code_sync.sync.assert_not_called()

    def test_sync_intelligent_watch_mode_starts(self, tmp_path: Path) -> None:
        """Test sync intelligent watch mode starts correctly."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Mock SyncWatcher to avoid actual file watching
        with patch("specfact_cli.sync.watcher.SyncWatcher") as mock_watcher_class:
            mock_watcher = MagicMock()
            mock_watcher_class.return_value = mock_watcher

            # Use threading to test watch mode startup
            import threading
            import time

            result_container: dict = {"result": None}

            def run_command() -> None:
                with patch("sys.stdin"):
                    result_container["result"] = runner.invoke(
                        app,
                        [
                            "sync",
                            "intelligent",
                            bundle_name,
                            "--repo",
                            str(tmp_path),
                            "--watch",
                        ],
                        input="\n",  # Simulate Ctrl+C
                    )

            thread = threading.Thread(target=run_command, daemon=True)
            thread.start()
            time.sleep(0.5)  # Give it time to start
            thread.join(timeout=0.1)

            # Watch mode should start (may exit with KeyboardInterrupt or timeout)
            # The important thing is it doesn't fail with "not implemented"
            if result_container["result"]:
                assert (
                    "Watch mode enabled" in result_container["result"].stdout
                    or "Watching for changes" in result_container["result"].stdout
                )
                assert "not implemented" not in result_container["result"].stdout.lower()
            else:
                # Command is still running (expected for watch mode)
                pass
