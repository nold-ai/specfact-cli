"""
Relationship mapper for extracting dependencies, interfaces, and relationships from codebase.

Maps imports, dependencies, interfaces, and relationships to create a "big picture"
understanding of the codebase structure.
"""

from __future__ import annotations

import ast
import hashlib
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


class RelationshipMapper:
    """
    Maps relationships, dependencies, and interfaces in a codebase.

    Extracts:
    - Import relationships (module dependencies)
    - Interface definitions (abstract classes, protocols)
    - Dependency relationships (function/class dependencies)
    - Framework relationships (FastAPI routers, Flask blueprints)
    """

    @beartype
    @require(lambda repo_path: isinstance(repo_path, Path), "Repo path must be Path")
    def __init__(self, repo_path: Path, file_hashes_cache: dict[str, str] | None = None) -> None:
        """
        Initialize relationship mapper.

        Args:
            repo_path: Path to repository root
            file_hashes_cache: Optional pre-computed file hashes (file_path -> hash) for caching
        """
        self.repo_path = repo_path.resolve()
        self.imports: dict[str, list[str]] = defaultdict(list)  # file -> [imported_modules]
        self.dependencies: dict[str, list[str]] = defaultdict(list)  # module -> [dependencies]
        self.interfaces: dict[str, dict[str, Any]] = {}  # interface_name -> interface_info
        self.framework_routes: dict[str, list[dict[str, Any]]] = defaultdict(list)  # file -> [route_info]
        # Cache for file hashes and AST parsing results
        self.file_hashes_cache: dict[str, str] = file_hashes_cache or {}
        self.ast_cache: dict[str, ast.AST] = {}  # file_path -> parsed AST
        self.analysis_cache: dict[str, dict[str, Any]] = {}  # file_hash -> analysis_result

    @beartype
    @require(lambda file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def analyze_file(self, file_path: Path) -> dict[str, Any]:
        """
        Analyze a single file for relationships.

        Args:
            file_path: Path to Python file

        Returns:
            Dictionary with relationships found in file
        """
        try:
            with file_path.open(encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            rel_file = self._file_key(file_path)
            file_imports = self._extract_imports_from_tree(tree)
            file_interfaces = self._extract_interfaces_from_tree(tree, rel_file)
            file_routes = self._extract_routes_from_tree(tree, rel_file)

            # Register interfaces into shared state
            for info in file_interfaces:
                self.interfaces[info["name"]] = info

            file_key = rel_file
            self.imports[file_key] = file_imports
            self.dependencies[file_key] = []
            self.framework_routes[file_key] = file_routes

            return {
                "imports": file_imports,
                "dependencies": [],
                "interfaces": file_interfaces,
                "routes": file_routes,
            }

        except (SyntaxError, UnicodeDecodeError):
            result: dict[str, Any] = {"imports": [], "dependencies": [], "interfaces": [], "routes": []}
            file_hash = self._compute_file_hash(file_path)
            if file_hash:
                self.analysis_cache[file_hash] = result
            return result

    @beartype
    @require(lambda self, file_path: isinstance(file_path, Path), "File path must be Path")
    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Compute SHA256 hash of file content.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash as hex string
        """
        try:
            file_key = str(file_path.relative_to(self.repo_path))
        except ValueError:
            file_key = str(file_path)

        # Check cache first
        if file_key in self.file_hashes_cache:
            return self.file_hashes_cache[file_key]

        # Compute hash
        if not file_path.exists():
            return ""
        try:
            file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            self.file_hashes_cache[file_key] = file_hash
            return file_hash
        except Exception:
            return ""

    def _file_key(self, file_path: Path) -> str:
        """Return a stable string key for a file (repo-relative if possible)."""
        try:
            return str(file_path.relative_to(self.repo_path))
        except ValueError:
            return str(file_path)

    def _extract_imports_from_tree(self, tree: ast.AST) -> list[str]:
        """
        Walk an AST and collect all imported module names.

        Args:
            tree: Parsed AST

        Returns:
            List of imported module name strings
        """
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return imports

    @staticmethod
    def _class_def_interface_info(node: ast.ClassDef, rel_file: str) -> dict[str, Any] | None:
        is_interface = False
        base_classes: list[str] = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
                if base.id in ("ABC", "Protocol", "Interface"):
                    is_interface = True
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "abstractmethod":
                is_interface = True
        if not (is_interface or any("Protocol" in b for b in base_classes)):
            return None
        return {
            "name": node.name,
            "file": rel_file,
            "methods": [item.name for item in node.body if isinstance(item, ast.FunctionDef)],
            "base_classes": base_classes,
        }

    def _extract_interfaces_from_tree(self, tree: ast.AST, rel_file: str) -> list[dict[str, Any]]:
        """
        Walk an AST and collect interface (abstract class / Protocol) definitions.

        Args:
            tree: Parsed AST
            rel_file: Repo-relative file path string for inclusion in results

        Returns:
            List of interface info dicts
        """
        interfaces: list[dict[str, Any]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            info = self._class_def_interface_info(node, rel_file)
            if info:
                interfaces.append(info)
        return interfaces

    def _extract_fastapi_route(
        self, decorator: ast.Call, node: ast.FunctionDef, rel_file: str
    ) -> dict[str, Any] | None:
        """Return a route info dict for a FastAPI-style HTTP method decorator, or None if not applicable."""
        if not (decorator.args and isinstance(decorator.args[0], ast.Constant)):
            return None
        path = decorator.args[0].value
        if not isinstance(path, str):
            return None
        return {
            "method": decorator.func.attr.upper(),  # type: ignore[union-attr]
            "path": path,
            "function": node.name,
            "file": rel_file,
        }

    def _extract_flask_routes(self, decorator: ast.Call, node: ast.FunctionDef, rel_file: str) -> list[dict[str, Any]]:
        """Return route info dicts for a Flask @route decorator (may expand to multiple HTTP methods)."""
        if not (decorator.args and isinstance(decorator.args[0], ast.Constant)):
            return []
        path = decorator.args[0].value
        if not isinstance(path, str):
            return []
        methods = ["GET"]
        for kw in decorator.keywords:
            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                methods = [
                    elt.value.upper()
                    for elt in kw.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
        return [{"method": method, "path": path, "function": node.name, "file": rel_file} for method in methods]

    def _extract_routes_from_tree(self, tree: ast.AST, rel_file: str) -> list[dict[str, Any]]:
        """
        Walk an AST and collect FastAPI/Flask route decorator definitions.

        Args:
            tree: Parsed AST
            rel_file: Repo-relative file path string for inclusion in results

        Returns:
            List of route info dicts with method, path, function, file keys
        """
        routes: list[dict[str, Any]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if not (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)):
                    continue
                if decorator.func.attr in ("get", "post", "put", "delete", "patch", "head", "options"):
                    route = self._extract_fastapi_route(decorator, node, rel_file)
                    if route:
                        routes.append(route)
                elif decorator.func.attr == "route":
                    routes.extend(self._extract_flask_routes(decorator, node, rel_file))
        return routes

    def _analyze_file_parallel_cached_ast(
        self,
        file_path: Path,
        file_key: str,
        file_hash: str,
        tree: ast.AST,
    ) -> tuple[str, dict[str, Any]]:
        rel_file = self._file_key(file_path)
        interfaces_list = self._extract_interfaces_from_tree(tree, rel_file)
        result: dict[str, Any] = {
            "imports": self._extract_imports_from_tree(tree),
            "dependencies": [],
            "interfaces": {info["name"]: info for info in interfaces_list},
            "routes": self._extract_routes_from_tree(tree, rel_file),
        }
        if file_hash:
            self.analysis_cache[file_hash] = result
        return (file_key, result)

    def _analyze_file_parallel_large_body(self, tree: ast.AST, file_hash: str) -> dict[str, Any]:
        result = {
            "imports": self._extract_imports_from_tree(tree),
            "dependencies": [],
            "interfaces": {},
            "routes": [],
        }
        if file_hash:
            self.analysis_cache[file_hash] = result
        return result

    def _analyze_file_parallel(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """
        Analyze a single file for relationships (thread-safe version with caching).

        Args:
            file_path: Path to Python file

        Returns:
            Tuple of (file_key, relationships_dict)
        """
        file_key = self._file_key(file_path)
        file_hash = self._compute_file_hash(file_path)

        if file_hash and file_hash in self.analysis_cache:
            return (file_key, self.analysis_cache[file_hash])

        empty_result: dict[str, Any] = {"imports": [], "dependencies": [], "interfaces": {}, "routes": []}

        # Skip very large files (>500KB)
        try:
            if file_path.stat().st_size > 500 * 1024:
                if file_hash:
                    self.analysis_cache[file_hash] = empty_result
                return (file_key, empty_result)
        except Exception:
            pass

        try:
            if file_key in self.ast_cache:
                tree = self.ast_cache[file_key]
            else:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(file_path))
                # For large files (>100KB), only extract imports
                if len(content) > 100 * 1024:
                    return (file_key, self._analyze_file_parallel_large_body(tree, file_hash))
                self.ast_cache[file_key] = tree

            return self._analyze_file_parallel_cached_ast(file_path, file_key, file_hash, tree)

        except (SyntaxError, UnicodeDecodeError):
            if file_hash:
                self.analysis_cache[file_hash] = empty_result
            return (self._file_key(file_path), empty_result)

    def _merge_file_result(self, file_key: str, result: dict[str, Any]) -> None:
        """Merge a single file's analysis result into instance state."""
        self.imports[file_key] = result["imports"]
        self.dependencies[file_key] = result["dependencies"]
        for interface_name, interface_info in result["interfaces"].items():
            self.interfaces[interface_name] = interface_info
        if result["routes"]:
            self.framework_routes[file_key] = result["routes"]

    def _collect_parallel_results(
        self,
        future_to_file: dict[Any, Path],
        python_files: list[Path],
        progress_callback: Any | None,
    ) -> None:
        """Drain completed futures, merging results; raises KeyboardInterrupt if interrupted."""
        completed_count = 0
        try:
            for future in as_completed(future_to_file):
                try:
                    file_key, result = future.result()
                    self._merge_file_result(file_key, result)
                except KeyboardInterrupt:
                    for f in future_to_file:
                        if not f.done():
                            f.cancel()
                    raise
                except Exception:
                    pass
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, len(python_files))
        except KeyboardInterrupt:
            for f in future_to_file:
                if not f.done():
                    f.cancel()
            raise

    @beartype
    @require(lambda file_paths: isinstance(file_paths, list), "File paths must be list")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def analyze_files(self, file_paths: list[Path], progress_callback: Any | None = None) -> dict[str, Any]:
        """
        Analyze multiple files for relationships (parallelized).

        Args:
            file_paths: List of file paths to analyze
            progress_callback: Optional callback function(completed: int, total: int) for progress updates

        Returns:
            Dictionary with all relationships
        """
        python_files = [f for f in file_paths if f.suffix == ".py"]

        if not python_files:
            return {"imports": {}, "dependencies": {}, "interfaces": {}, "routes": {}}

        if os.environ.get("TEST_MODE") == "true":
            max_workers = max(1, min(2, len(python_files)))
        else:
            max_workers = min(os.cpu_count() or 4, 16, len(python_files))

        wait_on_shutdown = os.environ.get("TEST_MODE") != "true"
        executor = ThreadPoolExecutor(max_workers=max_workers)
        interrupted = False
        try:
            future_to_file = {executor.submit(self._analyze_file_parallel, f): f for f in python_files}
            self._collect_parallel_results(future_to_file, python_files, progress_callback)
        except KeyboardInterrupt:
            interrupted = True
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        finally:
            if not interrupted:
                executor.shutdown(wait=wait_on_shutdown)
            else:
                executor.shutdown(wait=False)

        return {
            "imports": dict(self.imports),
            "dependencies": dict(self.dependencies),
            "interfaces": dict(self.interfaces),
            "routes": {k: v for k, v in self.framework_routes.items() if v},
        }

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def get_relationship_graph(self) -> dict[str, Any]:
        """
        Get relationship graph representation.

        Returns:
            Dictionary with graph structure for visualization
        """
        return {
            "nodes": list(set(self.imports.keys()) | set(self.dependencies.keys())),
            "edges": [{"from": file, "to": dep} for file, deps in self.imports.items() for dep in deps],
            "interfaces": list(self.interfaces.keys()),
            "routes": dict(self.framework_routes),
        }
