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

            file_imports: list[str] = []
            file_dependencies: list[str] = []
            file_interfaces: list[dict[str, Any]] = []
            file_routes: list[dict[str, Any]] = []

            for node in ast.walk(tree):
                # Extract imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        file_imports.append(alias.name)
                if isinstance(node, ast.ImportFrom) and node.module:
                    file_imports.append(node.module)

                # Extract interface definitions (abstract classes, protocols)
                if isinstance(node, ast.ClassDef):
                    is_interface = False
                    # Get relative path safely
                    try:
                        rel_file = str(file_path.relative_to(self.repo_path))
                    except ValueError:
                        rel_file = str(file_path)
                    interface_info: dict[str, Any] = {
                        "name": node.name,
                        "file": rel_file,
                        "methods": [],
                        "base_classes": [],
                    }

                    # Check for abstract base class
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_name = base.id
                            interface_info["base_classes"].append(base_name)
                            if base_name in ("ABC", "Protocol", "Interface"):
                                is_interface = True

                    # Check decorators for abstract methods
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == "abstractmethod":
                            is_interface = True

                    if is_interface or any("Protocol" in b for b in interface_info["base_classes"]):
                        # Extract methods
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                interface_info["methods"].append(item.name)
                        file_interfaces.append(interface_info)
                        self.interfaces[node.name] = interface_info

                # Extract framework routes (FastAPI, Flask)
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            # FastAPI: @app.get("/path") or @router.get("/path")
                            if decorator.func.attr in ("get", "post", "put", "delete", "patch", "head", "options"):
                                method = decorator.func.attr.upper()
                                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                    path = decorator.args[0].value
                                    if isinstance(path, str):
                                        # Get relative path safely
                                        try:
                                            rel_file = str(file_path.relative_to(self.repo_path))
                                        except ValueError:
                                            rel_file = str(file_path)
                                        file_routes.append(
                                            {
                                                "method": method,
                                                "path": path,
                                                "function": node.name,
                                                "file": rel_file,
                                            }
                                        )
                            # Flask: @app.route("/path", methods=["GET"])
                            elif decorator.func.attr == "route":
                                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                    path = decorator.args[0].value
                                    if isinstance(path, str):
                                        methods = ["GET"]  # Default
                                        for kw in decorator.keywords:
                                            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                                                methods = [
                                                    elt.value.upper()
                                                    for elt in kw.value.elts
                                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                                                ]
                                        for method in methods:
                                            # Get relative path safely
                                            try:
                                                rel_file = str(file_path.relative_to(self.repo_path))
                                            except ValueError:
                                                rel_file = str(file_path)
                                            file_routes.append(
                                                {
                                                    "method": method,
                                                    "path": path,
                                                    "function": node.name,
                                                    "file": rel_file,
                                                }
                                            )

            # Store relationships (use relative path if possible)
            try:
                file_key = str(file_path.relative_to(self.repo_path))
            except ValueError:
                file_key = str(file_path)
            self.imports[file_key] = file_imports
            self.dependencies[file_key] = file_dependencies
            self.framework_routes[file_key] = file_routes

            return {
                "imports": file_imports,
                "dependencies": file_dependencies,
                "interfaces": file_interfaces,
                "routes": file_routes,
            }

        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors
            result = {"imports": [], "dependencies": [], "interfaces": [], "routes": []}
            # Cache the result even for errors to avoid re-processing
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

    def _analyze_file_parallel(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """
        Analyze a single file for relationships (thread-safe version with caching).

        Args:
            file_path: Path to Python file

        Returns:
            Tuple of (file_key, relationships_dict)
        """
        # Get file key
        try:
            file_key = str(file_path.relative_to(self.repo_path))
        except ValueError:
            file_key = str(file_path)

        # Compute file hash for caching
        file_hash = self._compute_file_hash(file_path)

        # Check if we have cached analysis result for this file hash
        if file_hash and file_hash in self.analysis_cache:
            return (file_key, self.analysis_cache[file_hash])

        # Skip very large files early (>500KB) to speed up processing
        try:
            file_size = file_path.stat().st_size
            if file_size > 500 * 1024:  # 500KB
                result = {"imports": [], "dependencies": [], "interfaces": {}, "routes": []}
                if file_hash:
                    self.analysis_cache[file_hash] = result
                return (file_key, result)
        except Exception:
            pass

        try:
            # Check if we have cached AST
            if file_key in self.ast_cache:
                tree = self.ast_cache[file_key]
            else:
                with file_path.open(encoding="utf-8") as f:
                    content = f.read()
                    # For large files (>100KB), only extract imports (faster)
                    if len(content) > 100 * 1024:  # ~100KB
                        tree = ast.parse(content, filename=str(file_path))
                        large_file_imports: list[str] = []
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    large_file_imports.append(alias.name)
                            if isinstance(node, ast.ImportFrom) and node.module:
                                large_file_imports.append(node.module)
                        result = {"imports": large_file_imports, "dependencies": [], "interfaces": {}, "routes": []}
                        if file_hash:
                            self.analysis_cache[file_hash] = result
                        return (file_key, result)

                    tree = ast.parse(content, filename=str(file_path))
                    # Cache AST for future use
                    self.ast_cache[file_key] = tree

            file_imports: list[str] = []
            file_dependencies: list[str] = []
            file_interfaces: list[dict[str, Any]] = []
            file_routes: list[dict[str, Any]] = []

            for node in ast.walk(tree):
                # Extract imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        file_imports.append(alias.name)
                if isinstance(node, ast.ImportFrom) and node.module:
                    file_imports.append(node.module)

                # Extract interface definitions (abstract classes, protocols)
                if isinstance(node, ast.ClassDef):
                    is_interface = False
                    # Get relative path safely
                    try:
                        rel_file = str(file_path.relative_to(self.repo_path))
                    except ValueError:
                        rel_file = str(file_path)
                    interface_info: dict[str, Any] = {
                        "name": node.name,
                        "file": rel_file,
                        "methods": [],
                        "base_classes": [],
                    }

                    # Check for abstract base class
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_name = base.id
                            interface_info["base_classes"].append(base_name)
                            if base_name in ("ABC", "Protocol", "Interface"):
                                is_interface = True

                    # Check decorators for abstract methods
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == "abstractmethod":
                            is_interface = True

                    if is_interface or any("Protocol" in b for b in interface_info["base_classes"]):
                        # Extract methods
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                interface_info["methods"].append(item.name)
                        file_interfaces.append(interface_info)

                # Extract framework routes (FastAPI, Flask)
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            # FastAPI: @app.get("/path") or @router.get("/path")
                            if decorator.func.attr in ("get", "post", "put", "delete", "patch", "head", "options"):
                                method = decorator.func.attr.upper()
                                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                    path = decorator.args[0].value
                                    if isinstance(path, str):
                                        # Get relative path safely
                                        try:
                                            rel_file = str(file_path.relative_to(self.repo_path))
                                        except ValueError:
                                            rel_file = str(file_path)
                                        file_routes.append(
                                            {
                                                "method": method,
                                                "path": path,
                                                "function": node.name,
                                                "file": rel_file,
                                            }
                                        )
                            # Flask: @app.route("/path", methods=["GET"])
                            elif decorator.func.attr == "route":
                                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                    path = decorator.args[0].value
                                    if isinstance(path, str):
                                        methods = ["GET"]  # Default
                                        for kw in decorator.keywords:
                                            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                                                methods = [
                                                    elt.value.upper()
                                                    for elt in kw.value.elts
                                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                                                ]
                                        for method in methods:
                                            # Get relative path safely
                                            try:
                                                rel_file = str(file_path.relative_to(self.repo_path))
                                            except ValueError:
                                                rel_file = str(file_path)
                                            file_routes.append(
                                                {
                                                    "method": method,
                                                    "path": path,
                                                    "function": node.name,
                                                    "file": rel_file,
                                                }
                                            )

            # Get file key (use relative path if possible)
            try:
                file_key = str(file_path.relative_to(self.repo_path))
            except ValueError:
                file_key = str(file_path)

            # Build interfaces dict (interface_name -> interface_info)
            interfaces_dict: dict[str, dict[str, Any]] = {}
            for interface_info in file_interfaces:
                interfaces_dict[interface_info["name"]] = interface_info

            result = {
                "imports": file_imports,
                "dependencies": file_dependencies,
                "interfaces": interfaces_dict,
                "routes": file_routes,
            }

            # Cache result for future use (keyed by file hash)
            if file_hash:
                self.analysis_cache[file_hash] = result

            return (file_key, result)

        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors
            try:
                file_key = str(file_path.relative_to(self.repo_path))
            except ValueError:
                file_key = str(file_path)
            result = {"imports": [], "dependencies": [], "interfaces": {}, "routes": []}
            # Cache result for syntax errors to avoid re-processing
            if file_hash:
                self.analysis_cache[file_hash] = result
            return (file_key, result)

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
        # Filter Python files
        python_files = [f for f in file_paths if f.suffix == ".py"]

        if not python_files:
            return {
                "imports": {},
                "dependencies": {},
                "interfaces": {},
                "routes": {},
            }

        # Use ThreadPoolExecutor for parallel processing
        # In test mode, use fewer workers to avoid resource contention
        if os.environ.get("TEST_MODE") == "true":
            max_workers = max(1, min(2, len(python_files)))  # Max 2 workers in test mode
        else:
            max_workers = min(os.cpu_count() or 4, 16, len(python_files))  # Cap at 16 workers for faster processing

        executor = ThreadPoolExecutor(max_workers=max_workers)
        interrupted = False
        # In test mode, use wait=False to avoid hanging on shutdown
        wait_on_shutdown = os.environ.get("TEST_MODE") != "true"
        completed_count = 0
        try:
            # Submit all tasks
            future_to_file = {executor.submit(self._analyze_file_parallel, f): f for f in python_files}

            # Collect results as they complete
            try:
                for future in as_completed(future_to_file):
                    try:
                        file_key, result = future.result()
                        # Merge results into instance variables
                        self.imports[file_key] = result["imports"]
                        self.dependencies[file_key] = result["dependencies"]
                        # Merge interfaces
                        for interface_name, interface_info in result["interfaces"].items():
                            self.interfaces[interface_name] = interface_info
                        # Update progress
                        completed_count += 1
                        if progress_callback:
                            progress_callback(completed_count, len(python_files))
                        # Store routes
                        if result["routes"]:
                            self.framework_routes[file_key] = result["routes"]
                    except KeyboardInterrupt:
                        interrupted = True
                        for f in future_to_file:
                            if not f.done():
                                f.cancel()
                        break
                    except Exception:
                        # Skip files that fail to process
                        completed_count += 1
                        if progress_callback:
                            progress_callback(completed_count, len(python_files))
            except KeyboardInterrupt:
                interrupted = True
                for f in future_to_file:
                    if not f.done():
                        f.cancel()
            if interrupted:
                raise KeyboardInterrupt
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
