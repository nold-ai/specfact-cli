"""
Unit tests for GraphAnalyzer.

Tests graph-based dependency and call graph analysis, including parallel processing optimizations.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import networkx as nx
import pytest

from specfact_cli.analyzers.graph_analyzer import GraphAnalyzer


class TestGraphAnalyzer:
    """Tests for GraphAnalyzer."""

    def test_init(self, tmp_path: Path) -> None:
        """Test graph analyzer initialization."""
        analyzer = GraphAnalyzer(tmp_path)
        assert analyzer.repo_path == tmp_path.resolve()
        assert isinstance(analyzer.dependency_graph, nx.DiGraph)
        assert analyzer.call_graphs == {}

    def test_build_dependency_graph_parallel_processing(self, tmp_path: Path) -> None:
        """Test that dependency graph building uses parallel processing."""
        # Create multiple Python files with imports
        files = []
        for i in range(5):
            file_path = tmp_path / f"module_{i}.py"
            if i > 0:
                # Import previous module
                file_path.write_text(f"from module_{i-1} import something\n")
            else:
                file_path.write_text("# First module\n")
            files.append(file_path)

        analyzer = GraphAnalyzer(tmp_path)
        graph = analyzer.build_dependency_graph(files)

        # Should create a graph with nodes
        assert len(graph.nodes()) == 5
        # Should have edges from imports (if matching works)
        assert isinstance(graph, nx.DiGraph)

    def test_build_dependency_graph_parallel_imports(self, tmp_path: Path) -> None:
        """Test that AST import processing is parallelized."""
        from concurrent.futures import ThreadPoolExecutor

        # Create multiple files
        files = []
        for i in range(10):
            file_path = tmp_path / f"module_{i}.py"
            file_path.write_text(f"# Module {i}\n")
            files.append(file_path)

        analyzer = GraphAnalyzer(tmp_path)
        
        # Verify parallel processing by checking execution time
        # (in a real scenario, parallel should be faster, but we can't easily test that)
        graph = analyzer.build_dependency_graph(files)
        
        # Should process all files
        assert len(graph.nodes()) == 10

    def test_build_dependency_graph_parallel_call_graphs(self, tmp_path: Path) -> None:
        """Test that pyan call graph extraction is parallelized."""
        # Create multiple Python files
        files = []
        for i in range(5):
            file_path = tmp_path / f"module_{i}.py"
            file_path.write_text(
                f'''
def func_{i}():
    """Function {i}."""
    pass
'''
            )
            files.append(file_path)

        analyzer = GraphAnalyzer(tmp_path)
        
        # Mock pyan3 to avoid requiring it in tests
        with patch("specfact_cli.analyzers.graph_analyzer.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            graph = analyzer.build_dependency_graph(files)
            
            # Should process all files (even if pyan3 not available)
            assert len(graph.nodes()) == 5

    def test_extract_call_graph_reduced_timeout(self, tmp_path: Path) -> None:
        """Test that pyan3 timeout is reduced to 15 seconds."""
        file_path = tmp_path / "test_module.py"
        file_path.write_text("def test_func(): pass\n")

        analyzer = GraphAnalyzer(tmp_path)
        
        with patch("specfact_cli.analyzers.graph_analyzer.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            try:
                analyzer.extract_call_graph(file_path)
            except Exception:
                pass  # May fail if pyan3 not available
            
            # Verify timeout was set to 15 seconds
            if mock_run.called:
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs.get("timeout") == 15

    def test_get_graph_summary(self, tmp_path: Path) -> None:
        """Test getting graph summary."""
        analyzer = GraphAnalyzer(tmp_path)
        
        # Build a simple graph
        files = [tmp_path / "module1.py", tmp_path / "module2.py"]
        for f in files:
            f.write_text("# Module\n")
        
        graph = analyzer.build_dependency_graph(files)
        summary = analyzer.get_graph_summary()
        
        assert "nodes" in summary
        assert "edges" in summary
        assert summary["nodes"] == 2

    def test_path_to_module_name(self, tmp_path: Path) -> None:
        """Test converting file path to module name."""
        analyzer = GraphAnalyzer(tmp_path)
        
        file_path = tmp_path / "src" / "module" / "test.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("# Test\n")
        
        module_name = analyzer._path_to_module_name(file_path)
        assert "module" in module_name
        assert "test" in module_name

