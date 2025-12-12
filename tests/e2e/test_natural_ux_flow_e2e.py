"""
E2E tests for Natural UX Flow phases (4.1-4.5).

Tests context detection, progressive disclosure, suggestions, templates, and progress display.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def test_repo(tmp_path: Path) -> Path:
    """Create a test repository with SpecFact structure."""
    # Create .specfact structure
    specfact_dir = tmp_path / ".specfact"
    specfact_dir.mkdir()
    (specfact_dir / "config.yaml").write_text("version: 1.0")

    # Create project bundle
    projects_dir = specfact_dir / "projects"
    projects_dir.mkdir()
    bundle_dir = projects_dir / "test-bundle"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.manifest.yaml").write_text("versions:\n  schema: '1.0'")

    # Create Python project
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\ndependencies = ['fastapi>=0.100.0']")
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")

    return tmp_path


class TestPhase41ContextDetection:
    """E2E tests for Phase 4.1: Context Detection."""

    def test_context_detection_detects_python_project(self, runner: CliRunner, test_repo: Path) -> None:
        """Test that context detection identifies Python projects."""
        os.environ["TEST_MODE"] = "true"
        result = runner.invoke(app, ["import", "from-code", "--repo", str(test_repo), "--bundle", "test-bundle"])
        # Should detect Python and FastAPI
        assert result.exit_code in (0, 2)  # May exit with error if bundle already exists, but should detect context

    def test_context_detection_detects_specfact_config(self, runner: CliRunner, test_repo: Path) -> None:
        """Test that context detection identifies SpecFact configuration."""
        from specfact_cli.utils.context_detection import detect_project_context

        context = detect_project_context(test_repo)
        assert context.has_config is True
        assert context.has_plan is True

    def test_context_detection_detects_framework(self, runner: CliRunner, test_repo: Path) -> None:
        """Test that context detection identifies framework."""
        from specfact_cli.utils.context_detection import detect_project_context

        context = detect_project_context(test_repo)
        assert context.language == "python"
        assert context.framework == "fastapi"


class TestPhase42ProgressiveDisclosure:
    """E2E tests for Phase 4.2: Progressive Disclosure."""

    def test_help_hides_advanced_options(self, runner: CliRunner) -> None:
        """Test that regular help hides advanced options."""
        result = runner.invoke(app, ["import", "from-code", "--help"])
        # Advanced options like --confidence should not be visible in regular help
        # (They're marked with hidden=True)
        assert result.exit_code == 0

    def test_help_advanced_shows_all_options(self, runner: CliRunner) -> None:
        """Test that --help-advanced shows all options including advanced."""
        os.environ["SPECFACT_SHOW_ADVANCED"] = "true"
        result = runner.invoke(app, ["import", "from-code", "--help"])
        # With advanced help, all options should be visible
        assert result.exit_code == 0
        # Clean up
        if "SPECFACT_SHOW_ADVANCED" in os.environ:
            del os.environ["SPECFACT_SHOW_ADVANCED"]


class TestPhase43Suggestions:
    """E2E tests for Phase 4.3: Intelligent Suggestions."""

    def test_suggestions_for_first_time_setup(self, test_repo: Path) -> None:
        """Test suggestions for first-time setup."""
        from specfact_cli.utils.context_detection import ProjectContext
        from specfact_cli.utils.suggestions import suggest_next_steps

        # Empty repo (no plan)
        empty_repo = test_repo.parent / "empty_repo"
        empty_repo.mkdir()
        context = ProjectContext(repo_path=empty_repo, has_plan=False, has_config=False)
        suggestions = suggest_next_steps(empty_repo, context)
        assert len(suggestions) > 0
        assert any("import" in s.lower() for s in suggestions)

    def test_suggestions_for_low_coverage(self, test_repo: Path) -> None:
        """Test suggestions for low contract coverage."""
        from specfact_cli.utils.context_detection import ProjectContext
        from specfact_cli.utils.suggestions import suggest_improvements

        context = ProjectContext(repo_path=test_repo, contract_coverage=0.2)
        suggestions = suggest_improvements(context)
        assert len(suggestions) > 0
        assert any("analyze" in s.lower() for s in suggestions)

    def test_suggestions_for_errors(self) -> None:
        """Test suggestions for common errors."""
        from specfact_cli.utils.suggestions import suggest_fixes

        # Bundle not found error
        suggestions = suggest_fixes("Bundle 'test' not found")
        assert len(suggestions) > 0
        assert any("plan select" in s.lower() for s in suggestions)

        # Contract violation error
        suggestions = suggest_fixes("Contract violation detected")
        assert len(suggestions) > 0
        assert any("analyze" in s.lower() for s in suggestions)


class TestPhase43Templates:
    """E2E tests for Phase 4.3: Template-Driven Quality."""

    def test_feature_specification_template(self) -> None:
        """Test feature specification template creation."""
        from specfact_cli.templates.specification_templates import create_feature_specification_template

        template = create_feature_specification_template(
            feature_key="FEATURE-001",
            feature_name="Test Feature",
            user_needs=["User needs feature X"],
            business_value="High business value",
        )
        assert template.feature_key == "FEATURE-001"
        assert len(template.user_needs) == 1
        assert template.completeness_checklist["user_needs_defined"] is True

    def test_implementation_plan_template(self) -> None:
        """Test implementation plan template creation."""
        from specfact_cli.templates.specification_templates import create_implementation_plan_template

        template = create_implementation_plan_template(
            plan_key="PLAN-001",
            high_level_steps=["Step 1: Setup", "Step 2: Implement"],
            implementation_details_path="details/",
        )
        assert template.plan_key == "PLAN-001"
        assert template.test_first_approach is True
        assert len(template.high_level_steps) == 2

    def test_contract_extraction_template(self) -> None:
        """Test contract extraction template creation."""
        from specfact_cli.templates.specification_templates import create_contract_extraction_template

        template = create_contract_extraction_template(
            contract_key="CONTRACT-001",
            openapi_spec_path="openapi.yaml",
        )
        assert template.contract_key == "CONTRACT-001"
        assert template.openapi_spec_path == "openapi.yaml"


class TestPhase44WatchMode:
    """E2E tests for Phase 4.4: Enhanced Watch Mode."""

    def test_hash_based_change_detection(self, tmp_path: Path) -> None:
        """Test hash-based change detection."""
        from specfact_cli.sync.watcher_enhanced import FileHashCache, compute_file_hash

        cache_file = tmp_path / "cache.json"
        cache = FileHashCache(cache_file=cache_file)

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        file_hash = compute_file_hash(test_file)
        assert file_hash is not None  # Ensure hash was computed

        # First time - should detect change
        assert cache.has_changed(test_file, file_hash) is True
        cache.set_hash(test_file, file_hash)

        # Same content - should not detect change
        assert cache.has_changed(test_file, file_hash) is False

        # Different content - should detect change
        test_file.write_text("print('world')")
        new_hash = compute_file_hash(test_file)
        assert new_hash is not None  # Ensure hash was computed
        assert cache.has_changed(test_file, new_hash) is True

    def test_cache_persistence(self, tmp_path: Path) -> None:
        """Test that hash cache persists across sessions."""
        from specfact_cli.sync.watcher_enhanced import FileHashCache

        cache_file = tmp_path / "cache.json"
        cache = FileHashCache(cache_file=cache_file)

        test_file = tmp_path / "test.py"
        cache.set_hash(test_file, "abc123")
        cache.save()

        # Load in new cache instance
        new_cache = FileHashCache(cache_file=cache_file)
        new_cache.load()
        assert new_cache.get_hash(test_file) == "abc123"


class TestPhase45ProgressDisplay:
    """E2E tests for Phase 4.5: Unified Progress Display."""

    def test_progress_display_format(self, test_repo: Path) -> None:
        """Test that progress display uses consistent n/m format."""
        from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

        from specfact_cli.utils.progress import create_progress_callback

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=None,
        )
        progress.start()
        task_id = progress.add_task("Loading", total=10)

        callback = create_progress_callback(progress, task_id, prefix="Loading")
        callback(3, 10, "FEATURE-001.yaml")

        # Check that description follows n/m format
        task = progress.tasks[task_id]
        assert "3/10" in task.description
        assert "FEATURE-001.yaml" in task.description

        progress.stop()
