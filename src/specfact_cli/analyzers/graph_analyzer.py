"""
Graph-based dependency and call graph analysis.

Enhances AST and Semgrep analysis with graph-based dependency tracking,
call graph extraction, and architecture visualization.
"""

from __future__ import annotations

import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import networkx as nx
from beartype import beartype
from icontract import ensure, require


class GraphAnalyzer:
    """
    Graph-based dependency and call graph analysis.

    Uses pyan for call graphs, NetworkX for dependency graphs,
    and provides graph-based insights to complement AST and Semgrep.
    """

    @beartype
    @require(lambda repo_path: isinstance(repo_path, Path), "Repo path must be Path")
    def __init__(self, repo_path: Path, file_hashes_cache: dict[str, str] | None = None) -> None:
        """
        Initialize graph analyzer.

        Args:
            repo_path: Path to repository root
            file_hashes_cache: Optional pre-computed file hashes (file_path -> hash) for caching
        """
        self.repo_path = repo_path.resolve()
        self.call_graphs: dict[str, dict[str, list[str]]] = {}  # file -> {function -> [called_functions]}
        self.dependency_graph: nx.DiGraph = nx.DiGraph()
        # Cache for file hashes and import extraction results
        self.file_hashes_cache: dict[str, str] = file_hashes_cache or {}
        self.imports_cache: dict[str, list[str]] = {}  # file_hash -> [imports]
        self.module_name_cache: dict[str, str] = {}  # file_path -> module_name

    @beartype
    @require(lambda file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_call_graph(self, file_path: Path) -> dict[str, list[str]]:
        """
        Extract call graph using pyan.

        Args:
            file_path: Path to Python file

        Returns:
            Dictionary mapping function names to list of called functions
        """
        # Check if pyan3 is available using utility function
        from specfact_cli.utils.optional_deps import check_cli_tool_available

        is_available, _ = check_cli_tool_available("pyan3")
        if not is_available:
            # pyan3 not available, return empty
            return {}

        # Run pyan to generate DOT file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dot", delete=False) as dot_file:
            dot_path = Path(dot_file.name)
            try:
                result = subprocess.run(
                    ["pyan3", str(file_path), "--dot", "--no-defines", "--uses", "--defines"],
                    stdout=dot_file,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15,  # Reduced from 30 to 15 seconds for faster processing
                )

                if result.returncode == 0:
                    # Parse DOT file to extract call relationships
                    call_graph = self._parse_dot_file(dot_path)
                    file_key = str(file_path.relative_to(self.repo_path))
                    self.call_graphs[file_key] = call_graph
                    return call_graph
            finally:
                # Clean up temp file
                if dot_path.exists():
                    dot_path.unlink()

        return {}

    @beartype
    @require(lambda dot_path: isinstance(dot_path, Path), "DOT path must be Path")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _parse_dot_file(self, dot_path: Path) -> dict[str, list[str]]:
        """
        Parse DOT file to extract call graph.

        Args:
            dot_path: Path to DOT file

        Returns:
            Dictionary mapping function names to list of called functions
        """
        call_graph: dict[str, list[str]] = defaultdict(list)

        if not dot_path.exists():
            return {}

        try:
            content = dot_path.read_text(encoding="utf-8")
            # Parse DOT format: "function_a" -> "function_b"
            import re

            # Pattern: "function_a" -> "function_b"
            edge_pattern = r'"([^"]+)"\s*->\s*"([^"]+)"'
            matches = re.finditer(edge_pattern, content)

            for match in matches:
                caller = match.group(1)
                callee = match.group(2)
                # Filter out internal Python functions (start with __)
                if not caller.startswith("__") and not callee.startswith("__"):
                    call_graph[caller].append(callee)
        except (UnicodeDecodeError, Exception):
            # Skip if parsing fails
            pass

        return dict(call_graph)

    def _compute_max_workers(self, python_files: list[Path]) -> int:
        """Compute worker count for thread pool based on environment and file count."""
        import multiprocessing
        import os

        if os.environ.get("TEST_MODE") == "true":
            return max(1, min(2, len(python_files)))
        return max(1, min(multiprocessing.cpu_count() or 4, 16, len(python_files)))

    def _build_import_edges(
        self,
        graph: nx.DiGraph,
        python_files: list[Path],
        known_modules: list[str],
        max_workers: int,
        wait_on_shutdown: bool,
        progress_callback: Any | None,
    ) -> None:
        """Populate graph with edges derived from AST import analysis (parallel phase 1)."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def process_imports(file_path: Path) -> list[tuple[str, str]]:
            module_name = self._path_to_module_name(file_path)
            imports = self._extract_imports_from_ast(file_path)
            edges: list[tuple[str, str]] = []
            for imported in imports:
                if imported in known_modules:
                    edges.append((module_name, imported))
                else:
                    matching_module = self._find_matching_module(imported, known_modules)
                    if matching_module:
                        edges.append((module_name, matching_module))
            return edges

        executor = ThreadPoolExecutor(max_workers=max_workers)
        completed = 0
        try:
            future_to_file = {executor.submit(process_imports, fp): fp for fp in python_files}
            for future in as_completed(future_to_file):
                try:
                    edges = future.result()
                    for module_name, matching_module in edges:
                        graph.add_edge(module_name, matching_module)
                except Exception:
                    pass
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(python_files))
        finally:
            executor.shutdown(wait=wait_on_shutdown)

    def _build_call_graph_edges(
        self,
        graph: nx.DiGraph,
        python_files: list[Path],
        max_workers: int,
        wait_on_shutdown: bool,
        progress_callback: Any | None,
    ) -> None:
        """Populate graph with edges derived from pyan call graphs (parallel phase 2)."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        executor = ThreadPoolExecutor(max_workers=max_workers)
        completed = 0
        try:
            future_to_file = {executor.submit(self.extract_call_graph, fp): fp for fp in python_files}
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    call_graph = future.result()
                    module_name = self._path_to_module_name(file_path)
                    for _caller, callees in call_graph.items():
                        for callee in callees:
                            callee_module = self._resolve_module_from_function(callee, python_files)
                            if callee_module and callee_module in graph:
                                graph.add_edge(module_name, callee_module)
                except Exception:
                    pass
                completed += 1
                if progress_callback:
                    progress_callback(len(python_files) + completed, len(python_files) * 2)
        finally:
            executor.shutdown(wait=wait_on_shutdown)

    @beartype
    @require(lambda python_files: isinstance(python_files, list), "Python files must be list")
    @ensure(lambda result: isinstance(result, nx.DiGraph), "Must return DiGraph")
    def build_dependency_graph(self, python_files: list[Path], progress_callback: Any | None = None) -> nx.DiGraph:
        """
        Build comprehensive dependency graph using NetworkX.

        Combines AST-based imports with pyan call graphs for complete
        dependency tracking.

        Args:
            python_files: List of Python file paths
            progress_callback: Optional callback function(completed: int, total: int) for progress updates

        Returns:
            NetworkX directed graph of module dependencies
        """
        import os

        graph = nx.DiGraph()
        for file_path in python_files:
            module_name = self._path_to_module_name(file_path)
            graph.add_node(module_name, path=str(file_path))

        max_workers = self._compute_max_workers(python_files)
        known_modules = list(graph.nodes())
        wait_on_shutdown = os.environ.get("TEST_MODE") != "true"

        self._build_import_edges(graph, python_files, known_modules, max_workers, wait_on_shutdown, progress_callback)
        self._build_call_graph_edges(graph, python_files, max_workers, wait_on_shutdown, progress_callback)

        self.dependency_graph = graph
        return graph

    @beartype
    @require(lambda file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda result: isinstance(result, str), "Must return str")
    def _path_to_module_name(self, file_path: Path) -> str:
        """Convert file path to module name (cached)."""
        file_key = str(file_path)
        if file_key in self.module_name_cache:
            return self.module_name_cache[file_key]

        try:
            relative_path = file_path.relative_to(self.repo_path)
        except ValueError:
            relative_path = file_path

        parts = [*relative_path.parts[:-1], relative_path.stem]
        module_name = ".".join(parts)
        self.module_name_cache[file_key] = module_name
        return module_name

    _STDLIB_MODULES: frozenset[str] = frozenset(
        {
            "sys",
            "os",
            "json",
            "yaml",
            "pathlib",
            "typing",
            "collections",
            "dataclasses",
            "enum",
            "abc",
            "asyncio",
            "functools",
            "itertools",
            "re",
            "datetime",
            "time",
            "logging",
            "hashlib",
            "base64",
            "urllib",
            "http",
            "socket",
            "threading",
            "multiprocessing",
            "subprocess",
            "tempfile",
            "shutil",
            "importlib",
            "site",
            "pkgutil",
        }
    )

    def _resolve_file_hash(self, file_path: Path) -> str:
        """Return cached or freshly-computed SHA-256 hash for a file, or '' on failure."""
        import hashlib

        try:
            file_key = str(file_path.relative_to(self.repo_path))
        except ValueError:
            file_key = str(file_path)

        if file_key in self.file_hashes_cache:
            return self.file_hashes_cache[file_key]
        if not file_path.exists():
            return ""
        try:
            file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            self.file_hashes_cache[file_key] = file_hash
            return file_hash
        except Exception:
            return ""

    def _parse_non_stdlib_imports(self, file_path: Path) -> set[str]:
        """Parse AST of file and return non-stdlib import paths."""
        import ast

        imports: set[str] = set()
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_path = alias.name
                        if import_path.split(".")[0] not in self._STDLIB_MODULES:
                            imports.add(import_path)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    import_path = node.module
                    if import_path.split(".")[0] not in self._STDLIB_MODULES:
                        imports.add(import_path)
        except (SyntaxError, UnicodeDecodeError):
            pass
        return imports

    @beartype
    @require(lambda file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_imports_from_ast(self, file_path: Path) -> list[str]:
        """
        Extract imported module names from AST (cached by file hash).

        Extracts full import paths (not just root modules) to enable proper matching.
        """
        file_hash = self._resolve_file_hash(file_path)

        if file_hash and file_hash in self.imports_cache:
            return self.imports_cache[file_hash]

        result = list(self._parse_non_stdlib_imports(file_path))
        if file_hash:
            self.imports_cache[file_hash] = result
        return result

    @beartype
    @require(lambda imported: isinstance(imported, str), "Imported name must be str")
    @require(lambda known_modules: isinstance(known_modules, list), "Known modules must be list")
    @ensure(lambda result: result is None or isinstance(result, str), "Must return None or str")
    def _find_matching_module(self, imported: str, known_modules: list[str]) -> str | None:
        """
        Find matching module from known modules using intelligent matching.

        Tries multiple strategies:
        1. Exact match
        2. Last part match (e.g., "import_cmd" matches "src.specfact_cli.modules.import_cmd.src.commands")
        3. Partial path match (e.g., "specfact_cli.commands" matches "src.specfact_cli.modules.import_cmd.src.commands")

        Args:
            imported: Imported module name (e.g., "specfact_cli.modules.import_cmd.src.commands")
            known_modules: List of known module names in the graph

        Returns:
            Matching module name or None
        """
        # Strategy 1: Exact match (already checked in caller, but keep for completeness)
        if imported in known_modules:
            return imported

        # Strategy 2: Last part match
        # e.g., "import_cmd" matches "src.specfact_cli.modules.import_cmd.src.commands"
        imported_last = imported.split(".")[-1]
        for module in known_modules:
            if module.endswith(f".{imported_last}") or module == imported_last:
                return module

        # Strategy 3: Partial path match
        # e.g., "specfact_cli.commands" matches "src.specfact_cli.modules.import_cmd.src.commands"
        for module in known_modules:
            # Check if imported is a prefix of module
            if module.startswith(imported + ".") or module == imported:
                return module
            # Check if module is a prefix of imported
            if imported.startswith(module + "."):
                return module

        # Strategy 4: Check if any part of imported matches any part of known modules
        imported_parts = imported.split(".")
        for module in known_modules:
            module_parts = module.split(".")
            # Check if there's overlap in the path
            # e.g., "commands.import_cmd" might match "src.specfact_cli.modules.import_cmd.src.commands"
            if len(imported_parts) >= 2 and len(module_parts) >= 2 and imported_parts[-2:] == module_parts[-2:]:
                return module

        return None

    @beartype
    @require(lambda function_name: isinstance(function_name, str), "Function name must be str")
    @require(lambda python_files: isinstance(python_files, list), "Python files must be list")
    @ensure(lambda result: result is None or isinstance(result, str), "Must return None or str")
    def _resolve_module_from_function(self, function_name: str, python_files: list[Path]) -> str | None:
        """
        Resolve module name from function name.

        This is a heuristic - tries to find the module containing the function.
        """
        # Simple heuristic: search for function name in files
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                if f"def {function_name}" in content or f"class {function_name}" in content:
                    return self._path_to_module_name(file_path)
            except (UnicodeDecodeError, Exception):
                continue

        return None

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def get_graph_summary(self) -> dict[str, Any]:
        """
        Get summary of dependency graph.

        Returns:
            Dictionary with graph statistics and structure
        """
        if not self.dependency_graph:
            return {}

        return {
            "nodes": len(self.dependency_graph.nodes()),
            "edges": len(self.dependency_graph.edges()),
            "modules": list(self.dependency_graph.nodes()),
            "dependencies": [{"from": source, "to": target} for source, target in self.dependency_graph.edges()],
            "call_graphs": {file_key: len(calls) for file_key, calls in self.call_graphs.items()},
        }
