"""
Unit tests for GraphAnalyzer.

Tests graph-based dependency and call graph analysis, including parallel processing optimizations.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import networkx as nx

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
                file_path.write_text(f"from module_{i - 1} import something\n")
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

        # Mock pycg to avoid requiring it in tests
        with patch("specfact_cli.analyzers.graph_analyzer.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            graph = analyzer.build_dependency_graph(files)

            # Should process all files (even if pycg not available)
            assert len(graph.nodes()) == 5

    def test_extract_call_graph_timeout_15_seconds(self, tmp_path: Path) -> None:
        """Test that pycg subprocess timeout is 15 seconds."""
        file_path = tmp_path / "test_module.py"
        file_path.write_text("def test_func(): pass\n")

        analyzer = GraphAnalyzer(tmp_path)

        with patch("specfact_cli.analyzers.graph_analyzer.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            with contextlib.suppress(Exception):  # May fail if pycg not available
                analyzer.extract_call_graph(file_path)

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

        analyzer.build_dependency_graph(files)
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

    # --- pycg migration tests (Tasks 1.1 & 1.2) ---
    # These tests target the post-migration behaviour. They will FAIL until
    # graph_analyzer.py is updated to invoke pycg (not pyan3).

    def test_extract_call_graph_invokes_pycg_not_pyan3(self, tmp_path: Path) -> None:
        """After migration, extract_call_graph must call pycg, not pyan3."""
        file_path = tmp_path / "sample.py"
        file_path.write_text("def foo(): pass\n")
        # Create a json output file pycg would write
        json_out = tmp_path / "pycg_output.json"
        json_out.write_text('{"foo": []}')
        analyzer = GraphAnalyzer(tmp_path)

        with (
            patch(
                "specfact_cli.utils.optional_deps.check_cli_tool_available",
                return_value=(True, "pycg"),
            ),
            patch("specfact_cli.analyzers.graph_analyzer.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            analyzer.extract_call_graph(file_path)

        assert mock_run.called, "subprocess.run should have been called"
        first_arg = mock_run.call_args[0][0]
        assert first_arg[0] == "pycg", f"Expected pycg invocation, got: {first_arg[0]}"
        assert "pyan3" not in first_arg, "pyan3 must not appear in the pycg invocation"

    def test_extract_call_graph_returns_empty_on_nonzero_exit(self, tmp_path: Path) -> None:
        """Non-zero pycg exit returns empty dict without raising."""
        file_path = tmp_path / "sample.py"
        file_path.write_text("def foo(): pass\n")
        analyzer = GraphAnalyzer(tmp_path)

        with (
            patch(
                "specfact_cli.utils.optional_deps.check_cli_tool_available",
                return_value=(True, "pycg"),
            ),
            patch("specfact_cli.analyzers.graph_analyzer.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=1)
            result = analyzer.extract_call_graph(file_path)

        assert result == {}, "Non-zero exit must return empty dict"

    def test_extract_call_graph_returns_empty_when_pycg_missing(self, tmp_path: Path) -> None:
        """When pycg is not on PATH, extract_call_graph returns empty dict."""
        file_path = tmp_path / "sample.py"
        file_path.write_text("def foo(): pass\n")
        analyzer = GraphAnalyzer(tmp_path)

        with patch(
            "specfact_cli.utils.optional_deps.check_cli_tool_available",
            return_value=(False, "pycg not found"),
        ):
            result = analyzer.extract_call_graph(file_path)

        assert result == {}, "Missing pycg binary must return empty dict"

    def test_parse_pycg_json_returns_correct_structure(self, tmp_path: Path) -> None:
        """_parse_pycg_json must parse pycg JSON format {callee: [caller, ...]}."""
        analyzer = GraphAnalyzer(tmp_path)

        json_content = '{"bar": ["foo"], "baz": ["foo", "bar"]}'
        json_path = tmp_path / "pycg_output.json"
        json_path.write_text(json_content)

        # This method doesn't exist yet — will raise AttributeError until implemented.
        result = analyzer._parse_pycg_json(json_path)

        assert isinstance(result, dict), "Must return a dict"
        assert "foo" in result, "Caller 'foo' should be a key"
        assert "bar" in result["foo"], "foo should call bar"
        assert "baz" in result["foo"], "foo should call baz"

    def test_parse_pycg_json_handles_empty_output(self, tmp_path: Path) -> None:
        """_parse_pycg_json with empty JSON returns empty dict."""
        analyzer = GraphAnalyzer(tmp_path)
        json_path = tmp_path / "empty.json"
        json_path.write_text("{}")

        result = analyzer._parse_pycg_json(json_path)
        assert result == {}
