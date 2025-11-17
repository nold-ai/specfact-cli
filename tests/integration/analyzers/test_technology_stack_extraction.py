"""Integration tests for technology stack extraction from dependencies."""

from __future__ import annotations

import tempfile
from pathlib import Path

from specfact_cli.analyzers.code_analyzer import CodeAnalyzer
from specfact_cli.models.plan import PlanBundle


class TestTechnologyStackExtraction:
    """Integration tests for technology stack extraction from dependency files."""

    def test_extract_technology_stack_from_requirements_txt(self) -> None:
        """Test extracting technology stack from requirements.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create a simple Python file
            (src_path / "service.py").write_text(
                '''
"""Service module."""
class Service:
    """Service class."""
    pass
'''
            )

            # Create requirements.txt with various dependencies
            requirements = """python>=3.11
fastapi==0.104.1
pydantic>=2.0.0
psycopg2-binary==2.9.9
pytest==7.4.3
redis==5.0.1
"""
            (repo_path / "requirements.txt").write_text(requirements)

            # Analyze codebase
            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            plan_bundle = analyzer.analyze()

            # Verify technology stack was extracted
            assert isinstance(plan_bundle, PlanBundle)
            assert plan_bundle.idea is not None
            assert len(plan_bundle.idea.constraints) > 0

            constraints = plan_bundle.idea.constraints

            # Verify Python version was extracted
            assert any("python" in c.lower() and "3.11" in c.lower() for c in constraints)

            # Verify frameworks were extracted
            assert any("fastapi" in c.lower() for c in constraints)

            # Verify databases were extracted
            assert any("postgres" in c.lower() for c in constraints)
            assert any("redis" in c.lower() for c in constraints)

            # Verify testing tools were extracted
            assert any("pytest" in c.lower() for c in constraints)

    def test_extract_technology_stack_from_pyproject_toml(self) -> None:
        """Test extracting technology stack from pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create a simple Python file
            (src_path / "service.py").write_text(
                '''
"""Service module."""
class Service:
    """Service class."""
    pass
'''
            )

            # Create pyproject.toml with dependencies
            pyproject = """[project]
name = "test-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "django>=4.2.0",
    "pydantic>=2.0.0",
    "pymongo>=4.6.0",
]
"""
            (repo_path / "pyproject.toml").write_text(pyproject)

            # Analyze codebase
            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            plan_bundle = analyzer.analyze()

            # Verify technology stack was extracted
            assert isinstance(plan_bundle, PlanBundle)
            assert plan_bundle.idea is not None
            assert len(plan_bundle.idea.constraints) > 0

            constraints = plan_bundle.idea.constraints

            # Verify Python version was extracted
            assert any("python" in c.lower() and "3.12" in c.lower() for c in constraints)

            # Verify frameworks were extracted
            assert any("django" in c.lower() for c in constraints)

            # Verify databases were extracted
            assert any("mongodb" in c.lower() for c in constraints)

    def test_extract_technology_stack_fallback_to_defaults(self) -> None:
        """Test that defaults are used when no dependency files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create a simple Python file
            (src_path / "service.py").write_text(
                '''
"""Service module."""
class Service:
    """Service class."""
    pass
'''
            )

            # No dependency files

            # Analyze codebase
            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            plan_bundle = analyzer.analyze()

            # Verify technology stack has defaults
            assert isinstance(plan_bundle, PlanBundle)
            assert plan_bundle.idea is not None
            constraints = plan_bundle.idea.constraints

            # Should have default constraints
            assert len(constraints) > 0
            constraint_str = " ".join(constraints).lower()
            assert "python" in constraint_str or "typer" in constraint_str or "pydantic" in constraint_str

    def test_extract_technology_stack_removes_duplicates(self) -> None:
        """Test that duplicate technology stack items are removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_path = repo_path / "src"
            src_path.mkdir()

            # Create a simple Python file
            (src_path / "service.py").write_text(
                '''
"""Service module."""
class Service:
    """Service class."""
    pass
'''
            )

            # Create requirements.txt with duplicate entries
            requirements = """fastapi==0.104.1
fastapi[all]==0.104.1
pydantic>=2.0.0
pydantic[email]>=2.0.0
"""
            (repo_path / "requirements.txt").write_text(requirements)

            # Analyze codebase
            analyzer = CodeAnalyzer(repo_path, confidence_threshold=0.5)
            plan_bundle = analyzer.analyze()

            # Verify technology stack was extracted without duplicates
            assert isinstance(plan_bundle, PlanBundle)
            assert plan_bundle.idea is not None
            constraints = plan_bundle.idea.constraints

            # Count occurrences
            fastapi_count = sum(1 for c in constraints if "fastapi" in c.lower())
            pydantic_count = sum(1 for c in constraints if "pydantic" in c.lower())

            # Should have at most one entry per technology
            assert fastapi_count <= 1
            assert pydantic_count <= 1
