"""Unit tests for AnalyzeAgent - AI-first brownfield analysis."""

from __future__ import annotations

import tempfile
from pathlib import Path

from beartype import beartype

from specfact_cli.agents.analyze_agent import AnalyzeAgent
from specfact_cli.models.plan import PlanBundle


class TestAnalyzeAgent:
    """Test suite for AnalyzeAgent - AI-first approach."""

    @beartype
    def test_generate_prompt_with_context(self) -> None:
        """Test that prompt generation includes codebase context."""
        agent = AnalyzeAgent()
        context = {
            "workspace": ".",
            "current_file": "src/main.py",
            "selection": "def analyze()",
        }

        prompt = agent.generate_prompt("import from-code", context)

        assert "semantic understanding" in prompt.lower()
        assert "SpecFact plan bundle" in prompt
        assert "scenarios" in prompt.lower()

    @beartype
    def test_generate_prompt_without_context(self) -> None:
        """Test that prompt generation works without context."""
        agent = AnalyzeAgent()

        prompt = agent.generate_prompt("import from-code", None)

        assert len(prompt) > 0
        assert "semantic understanding" in prompt.lower()

    @beartype
    def test_load_codebase_context(self) -> None:
        """Test loading codebase context for AI analysis."""
        agent = AnalyzeAgent()

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_dir = repo_path / "src"
            src_dir.mkdir()

            # Create sample code files
            (src_dir / "main.py").write_text("class Main:\n    pass\n")
            (src_dir / "utils.py").write_text("def helper():\n    pass\n")
            (repo_path / "requirements.txt").write_text("typer==0.9.0\n")

            context = agent._load_codebase_context(repo_path)

            assert "structure" in context
            assert "files" in context
            assert "dependencies" in context
            assert "summary" in context
            assert len(context["files"]) >= 2
            assert len(context["dependencies"]) >= 1

    @beartype
    def test_load_codebase_context_multi_language(self) -> None:
        """Test that codebase context loads multiple languages."""
        agent = AnalyzeAgent()

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_dir = repo_path / "src"
            src_dir.mkdir()

            # Create files in different languages
            (src_dir / "main.py").write_text("class Main:\n    pass\n")
            (src_dir / "app.ts").write_text("class App {}\n")
            (src_dir / "utils.js").write_text("function helper() {}\n")
            (src_dir / "script.ps1").write_text("function Test-Script {}\n")

            context = agent._load_codebase_context(repo_path)

            assert len(context["files"]) >= 4
            extensions = {Path(f).suffix for f in context["files"]}
            assert ".py" in extensions
            assert ".ts" in extensions
            assert ".js" in extensions
            assert ".ps1" in extensions

    @beartype
    def test_load_codebase_context_filters_ignore_patterns(self) -> None:
        """Test that ignore patterns are filtered out."""
        agent = AnalyzeAgent()

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_dir = repo_path / "src"
            src_dir.mkdir()

            (src_dir / "main.py").write_text("class Main:\n    pass\n")
            (repo_path / "__pycache__").mkdir()
            (repo_path / "__pycache__" / "main.pyc").write_bytes(b"")

            context = agent._load_codebase_context(repo_path)

            # Should not include __pycache__ files
            assert not any("__pycache__" in f for f in context["files"])

    @beartype
    def test_analyze_codebase_returns_plan_bundle(self) -> None:
        """Test that analyze_codebase returns a PlanBundle."""
        agent = AnalyzeAgent()

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_dir = repo_path / "src"
            src_dir.mkdir()

            (src_dir / "main.py").write_text("class Main:\n    pass\n")

            plan_bundle = agent.analyze_codebase(repo_path, confidence=0.5)

            assert isinstance(plan_bundle, PlanBundle)
            assert plan_bundle.version == "1.0"
            assert plan_bundle.idea is not None
            assert plan_bundle.product is not None

    @beartype
    def test_inject_context_adds_workspace_structure(self) -> None:
        """Test that context injection adds workspace structure."""
        agent = AnalyzeAgent()

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            src_dir = repo_path / "src"
            src_dir.mkdir()
            test_dir = repo_path / "tests"
            test_dir.mkdir()

            (src_dir / "main.py").write_text("class Main:\n    pass\n")
            (test_dir / "test_main.py").write_text("def test_main():\n    pass\n")

            context = {
                "workspace": str(repo_path),
                "current_file": "src/main.py",
            }

            enhanced = agent.inject_context(context)

            assert "workspace_structure" in enhanced
            assert "src_dirs" in enhanced["workspace_structure"]
            assert "test_dirs" in enhanced["workspace_structure"]

    @beartype
    def test_execute_returns_structured_result(self) -> None:
        """Test that execute returns structured result."""
        agent = AnalyzeAgent()

        context = {
            "workspace": ".",
            "current_file": "src/main.py",
        }

        result = agent.execute("import from-code", {"repo": "."}, context)

        assert isinstance(result, dict)
        assert result["type"] == "analysis"
        assert result["command"] == "import from-code"
        assert "prompt" in result
        assert result["enhanced"] is True
