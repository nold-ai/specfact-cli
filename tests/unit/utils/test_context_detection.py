"""
Unit tests for context detection system.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.utils.context_detection import ProjectContext, detect_project_context


class TestProjectContext:
    """Test ProjectContext dataclass."""

    def test_project_context_creation(self, tmp_path: Path) -> None:
        """Test creating a ProjectContext instance."""
        context = ProjectContext(repo_path=tmp_path)
        assert context.repo_path == tmp_path
        assert context.has_plan is False
        assert context.has_config is False
        assert context.language is None
        assert context.framework is None

    def test_project_context_to_dict(self, tmp_path: Path) -> None:
        """Test converting ProjectContext to dictionary."""
        context = ProjectContext(repo_path=tmp_path, has_plan=True, language="python")
        context_dict = context.to_dict()
        assert context_dict["repo_path"] == str(tmp_path)
        assert context_dict["has_plan"] is True
        assert context_dict["language"] == "python"


class TestDetectProjectContext:
    """Test detect_project_context function."""

    def test_detect_python_project(self, tmp_path: Path) -> None:
        """Test detecting Python project."""
        # Create pyproject.toml
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        context = detect_project_context(tmp_path)
        assert context.language == "python"

    def test_detect_specfact_config(self, tmp_path: Path) -> None:
        """Test detecting SpecFact configuration."""
        specfact_dir = tmp_path / ".specfact"
        specfact_dir.mkdir()
        (specfact_dir / "config.yaml").write_text("version: 1.0")

        context = detect_project_context(tmp_path)
        assert context.has_config is True

    def test_detect_plan_bundle(self, tmp_path: Path) -> None:
        """Test detecting plan bundle."""
        specfact_dir = tmp_path / ".specfact"
        specfact_dir.mkdir()
        projects_dir = specfact_dir / "projects"
        projects_dir.mkdir()
        bundle_dir = projects_dir / "test-bundle"
        bundle_dir.mkdir()
        # Detection looks for bundle.manifest.yaml
        (bundle_dir / "bundle.manifest.yaml").write_text("versions:\n  schema: '1.0'")

        context = detect_project_context(tmp_path)
        assert context.has_plan is True
        assert "test-bundle" in context.project_bundles

    def test_detect_openapi_specs(self, tmp_path: Path) -> None:
        """Test detecting OpenAPI specs."""
        (tmp_path / "openapi.yaml").write_text("openapi: 3.0.0")

        context = detect_project_context(tmp_path)
        assert len(context.openapi_specs) > 0

    def test_detect_specmatic_config(self, tmp_path: Path) -> None:
        """Test detecting Specmatic configuration."""
        (tmp_path / "specmatic.yaml").write_text("specmatic:")

        context = detect_project_context(tmp_path)
        assert context.has_specmatic_config is True
        assert context.specmatic_config_path == tmp_path / "specmatic.yaml"

    def test_detect_framework_fastapi(self, tmp_path: Path) -> None:
        """Test detecting FastAPI framework."""
        pyproject_content = """[project]
name = "test"
dependencies = ["fastapi>=0.100.0"]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        context = detect_project_context(tmp_path)
        assert context.language == "python"
        assert context.framework == "fastapi"

    def test_detect_framework_django(self, tmp_path: Path) -> None:
        """Test detecting Django framework."""
        pyproject_content = """[project]
name = "test"
dependencies = ["django>=4.0.0"]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        context = detect_project_context(tmp_path)
        assert context.language == "python"
        assert context.framework == "django"

    def test_detect_framework_flask(self, tmp_path: Path) -> None:
        """Test detecting Flask framework."""
        pyproject_content = """[project]
name = "test"
dependencies = ["flask>=2.0.0"]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        context = detect_project_context(tmp_path)
        assert context.language == "python"
        assert context.framework == "flask"
