"""Code analyzer for extracting features from brownfield codebases."""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path

import networkx as nx
from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import Feature, Idea, Metadata, PlanBundle, Product, Story
from specfact_cli.utils.feature_keys import to_classname_key, to_sequential_key


class CodeAnalyzer:
    """
    Analyzes Python code to auto-derive plan bundles.

    Extracts features from classes and user stories from method patterns
    following Scrum/Agile practices.
    """

    # Fibonacci sequence for story points
    FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

    @beartype
    @require(lambda repo_path: repo_path is not None and isinstance(repo_path, Path), "Repo path must be Path")
    @require(lambda confidence_threshold: 0.0 <= confidence_threshold <= 1.0, "Confidence threshold must be 0.0-1.0")
    @require(lambda plan_name: plan_name is None or isinstance(plan_name, str), "Plan name must be None or str")
    def __init__(
        self,
        repo_path: Path,
        confidence_threshold: float = 0.5,
        key_format: str = "classname",
        plan_name: str | None = None,
    ) -> None:
        """
        Initialize code analyzer.

        Args:
            repo_path: Path to repository root
            confidence_threshold: Minimum confidence score (0.0-1.0)
            key_format: Feature key format ('classname' or 'sequential', default: 'classname')
            plan_name: Custom plan name (will be used for idea.title, optional)
        """
        self.repo_path = Path(repo_path)
        self.confidence_threshold = confidence_threshold
        self.key_format = key_format
        self.plan_name = plan_name
        self.features: list[Feature] = []
        self.themes: set[str] = set()
        self.dependency_graph: nx.DiGraph = nx.DiGraph()  # Module dependency graph
        self.type_hints: dict[str, dict[str, str]] = {}  # Module -> {function: type_hint}
        self.async_patterns: dict[str, list[str]] = {}  # Module -> [async_methods]
        self.commit_bounds: dict[str, tuple[str, str]] = {}  # Feature -> (first_commit, last_commit)

    @beartype
    @ensure(lambda result: isinstance(result, PlanBundle), "Must return PlanBundle")
    @ensure(lambda result: result.version == "1.0", "Plan bundle version must be 1.0")
    @ensure(lambda result: len(result.features) >= 0, "Features list must be non-negative length")
    def analyze(self) -> PlanBundle:
        """
        Analyze repository and generate plan bundle.

        Returns:
            Generated PlanBundle from code analysis
        """
        # Find all Python files
        python_files = list(self.repo_path.rglob("*.py"))

        # Build module dependency graph first
        self._build_dependency_graph(python_files)

        # Analyze each file
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue

            self._analyze_file(file_path)

        # Analyze commit history for feature boundaries
        self._analyze_commit_history()

        # Enhance features with dependency information
        self._enhance_features_with_dependencies()

        # If sequential format, update all keys now that we know the total count
        if self.key_format == "sequential":
            for idx, feature in enumerate(self.features, start=1):
                feature.key = to_sequential_key(feature.key, idx)

        # Generate plan bundle
        # Use plan_name if provided, otherwise use repo name, otherwise fallback
        if self.plan_name:
            # Use the plan name (already sanitized, but humanize for title)
            title = self.plan_name.replace("_", " ").replace("-", " ").title()
        else:
            repo_name = self.repo_path.name or "Unknown Project"
            title = self._humanize_name(repo_name)
        
        idea = Idea(
            title=title,
            narrative=f"Auto-derived plan from brownfield analysis of {title}",
            metrics=None,
        )

        product = Product(
            themes=sorted(self.themes) if self.themes else ["Core"],
            releases=[],
        )

        return PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=self.features,
            metadata=Metadata(stage="draft", promoted_at=None, promoted_by=None),
        )

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__",
            ".git",
            "venv",
            ".venv",
            "env",
            ".pytest_cache",
            "htmlcov",
            "dist",
            "build",
            ".eggs",
            "tests",  # Skip test files
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            # Extract module-level info
            self._extract_themes_from_imports(tree)

            # Extract type hints
            self._extract_type_hints(tree, file_path)

            # Detect async patterns
            self._detect_async_patterns(tree, file_path)

            # Extract classes as features
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    feature = self._extract_feature_from_class(node, file_path)
                    if feature:
                        self.features.append(feature)

        except (SyntaxError, UnicodeDecodeError):
            # Skip files that can't be parsed
            pass

    def _extract_themes_from_imports(self, tree: ast.AST) -> None:
        """Extract themes from import statements."""
        theme_keywords = {
            "fastapi": "API",
            "flask": "API",
            "django": "Web",
            "redis": "Caching",
            "postgres": "Database",
            "mysql": "Database",
            "asyncio": "Async",
            "typer": "CLI",
            "click": "CLI",
            "pydantic": "Validation",
            "pytest": "Testing",
            "sqlalchemy": "ORM",
            "requests": "HTTP Client",
            "aiohttp": "Async HTTP",
        }

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for keyword, theme in theme_keywords.items():
                            if keyword in alias.name.lower():
                                self.themes.add(theme)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    for keyword, theme in theme_keywords.items():
                        if keyword in node.module.lower():
                            self.themes.add(theme)

    def _extract_feature_from_class(self, node: ast.ClassDef, file_path: Path) -> Feature | None:
        """Extract feature from class definition."""
        # Skip private classes and test classes
        if node.name.startswith("_") or node.name.startswith("Test"):
            return None

        # Generate feature key based on configured format
        if self.key_format == "sequential":
            # Use sequential numbering (will be updated after all features are collected)
            feature_key = f"FEATURE-{len(self.features) + 1:03d}"
        else:
            # Default: classname format
            feature_key = to_classname_key(node.name)

        # Extract docstring as outcome
        docstring = ast.get_docstring(node)
        outcomes = []
        if docstring:
            # Take first paragraph as primary outcome
            first_para = docstring.split("\n\n")[0].strip()
            outcomes.append(first_para)
        else:
            outcomes.append(f"Provides {self._humanize_name(node.name)} functionality")

        # Collect all methods
        methods = [item for item in node.body if isinstance(item, ast.FunctionDef)]

        # Group methods into user stories
        stories = self._extract_stories_from_methods(methods, node.name)

        # Calculate confidence based on documentation and story quality
        confidence = self._calculate_feature_confidence(node, stories)

        if confidence < self.confidence_threshold:
            return None

        # Skip if no meaningful stories
        if not stories:
            return None

        return Feature(
            key=feature_key,
            title=self._humanize_name(node.name),
            outcomes=outcomes,
            acceptance=[f"{node.name} class provides documented functionality"],
            stories=stories,
            confidence=round(confidence, 2),
        )

    def _extract_stories_from_methods(self, methods: list[ast.FunctionDef], class_name: str) -> list[Story]:
        """
        Extract user stories from methods by grouping related functionality.

        Groups methods by:
        - CRUD operations (create, read, update, delete)
        - Common prefixes (get_, set_, validate_, process_)
        - Functionality patterns
        """
        # Group methods by pattern
        method_groups = self._group_methods_by_functionality(methods)

        stories = []
        story_counter = 1

        for group_name, group_methods in method_groups.items():
            if not group_methods:
                continue

            # Create a user story for this group
            story = self._create_story_from_method_group(group_name, group_methods, class_name, story_counter)

            if story:
                stories.append(story)
                story_counter += 1

        return stories

    def _group_methods_by_functionality(self, methods: list[ast.FunctionDef]) -> dict[str, list[ast.FunctionDef]]:
        """Group methods by their functionality patterns."""
        groups = defaultdict(list)

        # Filter out private methods (except __init__)
        public_methods = [m for m in methods if not m.name.startswith("_") or m.name == "__init__"]

        for method in public_methods:
            # CRUD operations
            if any(crud in method.name.lower() for crud in ["create", "add", "insert", "new"]):
                groups["Create Operations"].append(method)
            elif any(read in method.name.lower() for read in ["get", "read", "fetch", "find", "list", "retrieve"]):
                groups["Read Operations"].append(method)
            elif any(update in method.name.lower() for update in ["update", "modify", "edit", "change", "set"]):
                groups["Update Operations"].append(method)
            elif any(delete in method.name.lower() for delete in ["delete", "remove", "destroy"]):
                groups["Delete Operations"].append(method)

            # Validation
            elif any(val in method.name.lower() for val in ["validate", "check", "verify", "is_valid"]):
                groups["Validation"].append(method)

            # Processing/Computation
            elif any(
                proc in method.name.lower() for proc in ["process", "compute", "calculate", "transform", "convert"]
            ):
                groups["Processing"].append(method)

            # Analysis
            elif any(an in method.name.lower() for an in ["analyze", "parse", "extract", "detect"]):
                groups["Analysis"].append(method)

            # Generation
            elif any(gen in method.name.lower() for gen in ["generate", "build", "create", "make"]):
                groups["Generation"].append(method)

            # Comparison
            elif any(cmp in method.name.lower() for cmp in ["compare", "diff", "match"]):
                groups["Comparison"].append(method)

            # Setup/Configuration
            elif method.name == "__init__" or any(
                setup in method.name.lower() for setup in ["setup", "configure", "initialize"]
            ):
                groups["Configuration"].append(method)

            # Catch-all for other public methods
            else:
                groups["Core Functionality"].append(method)

        return dict(groups)

    def _create_story_from_method_group(
        self, group_name: str, methods: list[ast.FunctionDef], class_name: str, story_number: int
    ) -> Story | None:
        """Create a user story from a group of related methods."""
        if not methods:
            return None

        # Generate story key
        story_key = f"STORY-{class_name.upper()}-{story_number:03d}"

        # Create user-centric title based on group
        title = self._generate_story_title(group_name, class_name)

        # Extract acceptance criteria from docstrings
        acceptance = []
        tasks = []

        for method in methods:
            # Add method as task
            tasks.append(f"{method.name}()")

            # Extract acceptance from docstring
            docstring = ast.get_docstring(method)
            if docstring:
                # Take first line as acceptance criterion
                first_line = docstring.split("\n")[0].strip()
                if first_line and first_line not in acceptance:
                    acceptance.append(first_line)

        # Add default acceptance if none found
        if not acceptance:
            acceptance.append(f"{group_name} functionality works as expected")

        # Calculate story points (complexity) based on number of methods and their size
        story_points = self._calculate_story_points(methods)

        # Calculate value points based on public API exposure
        value_points = self._calculate_value_points(methods, group_name)

        return Story(
            key=story_key,
            title=title,
            acceptance=acceptance,
            story_points=story_points,
            value_points=value_points,
            tasks=tasks,
            confidence=0.8 if len(methods) > 1 else 0.6,
        )

    def _generate_story_title(self, group_name: str, class_name: str) -> str:
        """Generate user-centric story title."""
        # Map group names to user-centric titles
        title_templates = {
            "Create Operations": f"As a user, I can create new {self._humanize_name(class_name)} records",
            "Read Operations": f"As a user, I can view {self._humanize_name(class_name)} data",
            "Update Operations": f"As a user, I can update {self._humanize_name(class_name)} records",
            "Delete Operations": f"As a user, I can delete {self._humanize_name(class_name)} records",
            "Validation": f"As a developer, I can validate {self._humanize_name(class_name)} data",
            "Processing": f"As a user, I can process data using {self._humanize_name(class_name)}",
            "Analysis": f"As a user, I can analyze data with {self._humanize_name(class_name)}",
            "Generation": f"As a user, I can generate outputs from {self._humanize_name(class_name)}",
            "Comparison": f"As a user, I can compare {self._humanize_name(class_name)} data",
            "Configuration": f"As a developer, I can configure {self._humanize_name(class_name)}",
            "Core Functionality": f"As a user, I can use {self._humanize_name(class_name)} features",
        }

        return title_templates.get(group_name, f"As a user, I can work with {self._humanize_name(class_name)}")

    def _calculate_story_points(self, methods: list[ast.FunctionDef]) -> int:
        """
        Calculate story points (complexity) using Fibonacci sequence.

        Based on:
        - Number of methods
        - Average method size
        - Complexity indicators (loops, conditionals)
        """
        # Base complexity on number of methods
        method_count = len(methods)

        # Count total lines across all methods
        total_lines = sum(len(ast.unparse(m).split("\n")) for m in methods)
        avg_lines = total_lines / method_count if method_count > 0 else 0

        # Simple heuristic: 1-2 methods = small, 3-5 = medium, 6+ = large
        if method_count <= 2 and avg_lines < 20:
            base_points = 2  # Small
        elif method_count <= 5 and avg_lines < 40:
            base_points = 5  # Medium
        elif method_count <= 8:
            base_points = 8  # Large
        else:
            base_points = 13  # Extra Large

        # Return nearest Fibonacci number
        return min(self.FIBONACCI, key=lambda x: abs(x - base_points))

    def _calculate_value_points(self, methods: list[ast.FunctionDef], group_name: str) -> int:
        """
        Calculate value points (business value) using Fibonacci sequence.

        Based on:
        - Public API exposure
        - CRUD operations have high value
        - Validation has medium value
        """
        # CRUD operations are high value
        crud_groups = ["Create Operations", "Read Operations", "Update Operations", "Delete Operations"]
        if group_name in crud_groups:
            base_value = 8  # High business value

        # User-facing operations
        elif group_name in ["Processing", "Analysis", "Generation", "Comparison"]:
            base_value = 5  # Medium-high value

        # Developer/internal operations
        elif group_name in ["Validation", "Configuration"]:
            base_value = 3  # Medium value

        # Core functionality
        else:
            base_value = 3  # Default medium value

        # Adjust based on number of public methods (more = higher value)
        public_count = sum(1 for m in methods if not m.name.startswith("_"))
        if public_count >= 3:
            base_value = min(base_value + 2, 13)

        # Return nearest Fibonacci number
        return min(self.FIBONACCI, key=lambda x: abs(x - base_value))

    def _calculate_feature_confidence(self, node: ast.ClassDef, stories: list[Story]) -> float:
        """Calculate confidence score for a feature."""
        score = 0.3  # Base score

        # Has docstring
        if ast.get_docstring(node):
            score += 0.2

        # Has stories
        if stories:
            score += 0.2

        # Has multiple stories (better coverage)
        if len(stories) > 2:
            score += 0.2

        # Stories are well-documented
        documented_stories = sum(1 for s in stories if s.acceptance and len(s.acceptance) > 1)
        if stories and documented_stories > len(stories) / 2:
            score += 0.1

        return min(score, 1.0)

    def _humanize_name(self, name: str) -> str:
        """Convert snake_case or PascalCase to human-readable title."""
        # Handle PascalCase
        name = re.sub(r"([A-Z])", r" \1", name).strip()
        # Handle snake_case
        name = name.replace("_", " ").replace("-", " ")
        return name.title()

    def _build_dependency_graph(self, python_files: list[Path]) -> None:
        """
        Build module dependency graph using AST imports.

        Creates a directed graph where nodes are modules and edges represent imports.
        """
        # First pass: collect all modules as nodes
        modules: dict[str, Path] = {}
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue

            # Convert file path to module name
            module_name = self._path_to_module_name(file_path)
            modules[module_name] = file_path
            self.dependency_graph.add_node(module_name, path=file_path)

        # Second pass: add edges based on imports
        for module_name, file_path in modules.items():
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)

                # Extract imports
                imports = self._extract_imports_from_ast(tree, file_path)
                for imported_module in imports:
                    # Only add edges for modules we know about (within repo)
                    # Try exact match first, then partial match
                    if imported_module in modules:
                        self.dependency_graph.add_edge(module_name, imported_module)
                    else:
                        # Try to find matching module (e.g., "module_a" matches "src.module_a")
                        matching_module = None
                        for known_module in modules:
                            # Check if imported name matches the module name (last part)
                            if imported_module == known_module.split(".")[-1]:
                                matching_module = known_module
                                break
                        if matching_module:
                            self.dependency_graph.add_edge(module_name, matching_module)
            except (SyntaxError, UnicodeDecodeError):
                # Skip files that can't be parsed
                continue

    def _path_to_module_name(self, file_path: Path) -> str:
        """Convert file path to module name (e.g., src/foo/bar.py -> src.foo.bar)."""
        # Get relative path from repo root
        try:
            relative_path = file_path.relative_to(self.repo_path)
        except ValueError:
            # File is outside repo, use full path
            relative_path = file_path

        # Convert to module name
        parts = list(relative_path.parts[:-1]) + [relative_path.stem]  # Remove .py extension
        return ".".join(parts)

    def _extract_imports_from_ast(self, tree: ast.AST, file_path: Path) -> list[str]:
        """
        Extract imported module names from AST.

        Returns:
            List of module names (relative to repo root if possible)
        """
        imports: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Import aliases (e.g., import foo as bar)
                    if "." in alias.name:
                        # Extract root module (e.g., foo.bar.baz -> foo)
                        root_module = alias.name.split(".")[0]
                        imports.add(root_module)
                    else:
                        imports.add(alias.name)

            elif isinstance(node, ast.ImportFrom) and node.module:
                # From imports (e.g., from foo.bar import baz)
                if "." in node.module:
                    # Extract root module
                    root_module = node.module.split(".")[0]
                    imports.add(root_module)
                else:
                    imports.add(node.module)

        # Try to resolve local imports (relative to current file)
        resolved_imports = []
        current_module = self._path_to_module_name(file_path)

        for imported in imports:
            # Skip stdlib imports (common patterns)
            stdlib_modules = {
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
            }

            if imported in stdlib_modules:
                continue

            # Try to resolve relative imports
            # If imported module matches a pattern from our repo, resolve it
            potential_module = self._resolve_local_import(imported, current_module)
            if potential_module:
                resolved_imports.append(potential_module)
            else:
                # Keep as external dependency
                resolved_imports.append(imported)

        return resolved_imports

    def _resolve_local_import(self, imported: str, current_module: str) -> str | None:
        """
        Try to resolve a local import relative to current module.

        Returns:
            Resolved module name if found in repo, None otherwise
        """
        # Check if it's already in our dependency graph
        if imported in self.dependency_graph:
            return imported

        # Try relative import resolution (e.g., from .foo import bar)
        # This is simplified - full resolution would need to handle package structure
        current_parts = current_module.split(".")
        if len(current_parts) > 1:
            # Try parent package
            parent_module = ".".join(current_parts[:-1])
            potential = f"{parent_module}.{imported}"
            if potential in self.dependency_graph:
                return potential

        return None

    def _extract_type_hints(self, tree: ast.AST, file_path: Path) -> dict[str, str]:
        """
        Extract type hints from function/method signatures.

        Returns:
            Dictionary mapping function names to their return type hints
        """
        type_hints: dict[str, str] = {}
        module_name = self._path_to_module_name(file_path)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                return_type = "None"

                # Extract return type annotation
                if node.returns:
                    # Convert AST node to string representation
                    if isinstance(node.returns, ast.Name):
                        return_type = node.returns.id
                    elif isinstance(node.returns, ast.Subscript):
                        # Handle generics like List[str], Dict[str, int]
                        container = node.returns.value.id if isinstance(node.returns.value, ast.Name) else "Any"
                        return_type = str(container)  # Simplified representation

                type_hints[func_name] = return_type

        # Store per module
        if module_name not in self.type_hints:
            self.type_hints[module_name] = {}
        self.type_hints[module_name].update(type_hints)

        return type_hints

    def _detect_async_patterns(self, tree: ast.AST, file_path: Path) -> list[str]:
        """
        Detect async/await patterns in code.

        Returns:
            List of async method/function names
        """
        async_methods: list[str] = []
        module_name = self._path_to_module_name(file_path)

        for node in ast.walk(tree):
            # Check for async functions
            if isinstance(node, ast.AsyncFunctionDef):
                async_methods.append(node.name)

            # Check for await statements (even in sync functions)
            if isinstance(node, ast.Await):
                # Find containing function
                for parent in ast.walk(tree):
                    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for child in ast.walk(parent):
                            if child == node:
                                if parent.name not in async_methods:
                                    async_methods.append(parent.name)
                                break

        # Store per module
        self.async_patterns[module_name] = async_methods

        return async_methods

    def _analyze_commit_history(self) -> None:
        """
        Mine commit history to identify feature boundaries.

        Uses GitPython to analyze commit messages and associate them with features.
        Limits analysis to recent commits to avoid performance issues.
        """
        try:
            from git import Repo

            if not (self.repo_path / ".git").exists():
                return

            repo = Repo(self.repo_path)
            # Limit to last 100 commits to avoid performance issues with large repositories
            max_commits = 100
            commits = list(repo.iter_commits(max_count=max_commits))

            # Map commits to files to features
            file_to_feature: dict[str, list[str]] = {}
            for feature in self.features:
                # Extract potential file paths from feature key
                # This is simplified - in reality we'd track which files contributed to which features
                pass

            # Analyze commit messages for feature references
            for commit in commits:
                try:
                    # Skip commits that can't be accessed (corrupted or too old)
                    # Use commit.message which is lazy-loaded but faster than full commit object
                    commit_message = commit.message
                    if isinstance(commit_message, bytes):
                        commit_message = commit_message.decode("utf-8", errors="ignore")
                    message = commit_message.lower()
                    # Look for feature patterns (e.g., FEATURE-001, feat:, feature:)
                    if "feat" in message or "feature" in message:
                        # Try to extract feature keys from commit message
                        feature_match = re.search(r"feature[-\s]?(\d+)", message, re.IGNORECASE)
                        if feature_match:
                            feature_num = feature_match.group(1)
                            # Associate commit with feature (simplified)
                except Exception:
                    # Skip individual commits that fail (corrupted, etc.)
                    continue

        except ImportError:
            # GitPython not available, skip
            pass
        except Exception:
            # Git operations failed, skip gracefully
            pass

    def _enhance_features_with_dependencies(self) -> None:
        """Enhance features with dependency graph information."""
        for feature in self.features:
            # Find dependencies for this feature's module
            # This is simplified - would need to track which module each feature comes from
            pass

    def _get_module_dependencies(self, module_name: str) -> list[str]:
        """Get list of modules that the given module depends on."""
        if module_name not in self.dependency_graph:
            return []

        return list(self.dependency_graph.successors(module_name))
