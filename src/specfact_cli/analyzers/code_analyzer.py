"""Code analyzer for extracting features from brownfield codebases."""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import networkx as nx
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from specfact_cli.analyzers.contract_extractor import ContractExtractor
from specfact_cli.analyzers.control_flow_analyzer import ControlFlowAnalyzer
from specfact_cli.analyzers.requirement_extractor import RequirementExtractor
from specfact_cli.analyzers.test_pattern_extractor import TestPatternExtractor
from specfact_cli.models.plan import Feature, Idea, Metadata, PlanBundle, Product, Story
from specfact_cli.utils.feature_keys import to_classname_key, to_sequential_key


console = Console()


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
    @require(
        lambda entry_point: entry_point is None or isinstance(entry_point, Path),
        "Entry point must be None or Path",
    )
    def __init__(
        self,
        repo_path: Path,
        confidence_threshold: float = 0.5,
        key_format: str = "classname",
        plan_name: str | None = None,
        entry_point: Path | None = None,
    ) -> None:
        """
        Initialize code analyzer.

        Args:
            repo_path: Path to repository root
            confidence_threshold: Minimum confidence score (0.0-1.0)
            key_format: Feature key format ('classname' or 'sequential', default: 'classname')
            plan_name: Custom plan name (will be used for idea.title, optional)
            entry_point: Optional entry point path for partial analysis (relative to repo_path)
        """
        self.repo_path = Path(repo_path).resolve()
        self.confidence_threshold = confidence_threshold
        self.key_format = key_format
        self.plan_name = plan_name
        self.entry_point: Path | None = None
        if entry_point is not None:
            # Resolve entry point relative to repo_path
            if entry_point.is_absolute():
                self.entry_point = entry_point
            else:
                self.entry_point = (self.repo_path / entry_point).resolve()
            # Validate entry point exists and is within repo
            if not self.entry_point.exists():
                raise ValueError(f"Entry point does not exist: {self.entry_point}")
            if not str(self.entry_point).startswith(str(self.repo_path)):
                raise ValueError(f"Entry point must be within repository: {self.entry_point}")
        self.features: list[Feature] = []
        self.themes: set[str] = set()
        self.dependency_graph: nx.DiGraph[str] = nx.DiGraph()  # Module dependency graph
        self.type_hints: dict[str, dict[str, str]] = {}  # Module -> {function: type_hint}
        self.async_patterns: dict[str, list[str]] = {}  # Module -> [async_methods]
        self.commit_bounds: dict[str, tuple[str, str]] = {}  # Feature -> (first_commit, last_commit)
        self.external_dependencies: set[str] = set()  # External modules imported from outside entry point
        # Use entry_point for test extractor if provided, otherwise repo_path
        test_extractor_path = self.entry_point if self.entry_point else self.repo_path
        self.test_extractor = TestPatternExtractor(test_extractor_path)
        self.control_flow_analyzer = ControlFlowAnalyzer()
        self.requirement_extractor = RequirementExtractor()
        self.contract_extractor = ContractExtractor()

    @beartype
    @ensure(lambda result: isinstance(result, PlanBundle), "Must return PlanBundle")
    @ensure(
        lambda result: isinstance(result, PlanBundle)
        and hasattr(result, "version")
        and hasattr(result, "features")
        and result.version == "1.0"  # type: ignore[reportUnknownMemberType]
        and len(result.features) >= 0,  # type: ignore[reportUnknownMemberType]
        "Plan bundle must be valid",
    )
    def analyze(self) -> PlanBundle:
        """
        Analyze repository and generate plan bundle.

        Returns:
            Generated PlanBundle from code analysis
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Phase 1: Discover Python files
            task1 = progress.add_task("[cyan]Phase 1: Discovering Python files...", total=None)
            if self.entry_point:
                # Scope analysis to entry point directory
                python_files = list(self.entry_point.rglob("*.py"))
                entry_point_rel = self.entry_point.relative_to(self.repo_path)
                progress.update(
                    task1,
                    description=f"[green]✓ Found {len(python_files)} Python files in {entry_point_rel}",
                )
            else:
                # Full repository analysis
                python_files = list(self.repo_path.rglob("*.py"))
                progress.update(task1, description=f"[green]✓ Found {len(python_files)} Python files")
            progress.remove_task(task1)

            # Phase 2: Build dependency graph
            task2 = progress.add_task("[cyan]Phase 2: Building dependency graph...", total=None)
            self._build_dependency_graph(python_files)
            progress.update(task2, description="[green]✓ Dependency graph built")
            progress.remove_task(task2)

            # Phase 3: Analyze files and extract features
            task3 = progress.add_task(
                "[cyan]Phase 3: Analyzing files and extracting features...", total=len(python_files)
            )
            for file_path in python_files:
                if self._should_skip_file(file_path):
                    progress.advance(task3)
                    continue

                self._analyze_file(file_path)
                progress.advance(task3)
            progress.update(
                task3,
                description=f"[green]✓ Analyzed {len(python_files)} files, extracted {len(self.features)} features",
            )
            progress.remove_task(task3)

            # Phase 4: Analyze commit history
            task4 = progress.add_task("[cyan]Phase 4: Analyzing commit history...", total=None)
            self._analyze_commit_history()
            progress.update(task4, description="[green]✓ Commit history analyzed")
            progress.remove_task(task4)

            # Phase 5: Enhance features with dependencies
            task5 = progress.add_task("[cyan]Phase 5: Enhancing features with dependency information...", total=None)
            self._enhance_features_with_dependencies()
            progress.update(task5, description="[green]✓ Features enhanced")
            progress.remove_task(task5)

            # Phase 6: Extract technology stack
            task6 = progress.add_task("[cyan]Phase 6: Extracting technology stack...", total=None)
            technology_constraints = self._extract_technology_stack_from_dependencies()
            progress.update(task6, description="[green]✓ Technology stack extracted")
            progress.remove_task(task6)

        # If sequential format, update all keys now that we know the total count
        if self.key_format == "sequential":
            for idx, feature in enumerate(self.features, start=1):
                feature.key = to_sequential_key(feature.key, idx)

        # Generate plan bundle
        # Use plan_name if provided, otherwise use entry point name or repo name
        if self.plan_name:
            # Use the plan name (already sanitized, but humanize for title)
            title = self.plan_name.replace("_", " ").replace("-", " ").title()
        elif self.entry_point:
            # Use entry point name for partial analysis
            entry_point_name = self.entry_point.name or self.entry_point.relative_to(self.repo_path).as_posix()
            title = f"{self._humanize_name(entry_point_name)} Module"
        else:
            repo_name = self.repo_path.name or "Unknown Project"
            title = self._humanize_name(repo_name)

        narrative = f"Auto-derived plan from brownfield analysis of {title}"
        if self.entry_point:
            entry_point_rel = self.entry_point.relative_to(self.repo_path)
            narrative += f" (scoped to {entry_point_rel})"

        idea = Idea(
            title=title,
            narrative=narrative,
            constraints=technology_constraints,
            metrics=None,
        )

        product = Product(
            themes=sorted(self.themes) if self.themes else ["Core"],
            releases=[],
        )

        # Build metadata with scope information
        metadata = Metadata(
            stage="draft",
            promoted_at=None,
            promoted_by=None,
            analysis_scope="partial" if self.entry_point else "full",
            entry_point=str(self.entry_point.relative_to(self.repo_path)) if self.entry_point else None,
            external_dependencies=sorted(self.external_dependencies),
        )

        return PlanBundle(
            version="1.0",
            idea=idea,
            business=None,
            product=product,
            features=self.features,
            metadata=metadata,
            clarifications=None,
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
        outcomes: list[str] = []
        if docstring:
            # Take first paragraph as primary outcome
            first_para = docstring.split("\n\n")[0].strip()
            outcomes.append(first_para)  # type: ignore[reportUnknownMemberType]
        else:
            outcomes.append(f"Provides {self._humanize_name(node.name)} functionality")  # type: ignore[reportUnknownMemberType]

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

        # Extract complete requirements (Step 1.3)
        complete_requirement = self.requirement_extractor.extract_complete_requirement(node)
        acceptance_criteria = (
            [complete_requirement] if complete_requirement else [f"{node.name} class provides documented functionality"]
        )

        # Extract NFRs from code patterns (Step 1.3)
        nfrs = self.requirement_extractor.extract_nfrs(node)
        # Add NFRs as constraints
        constraints = nfrs if nfrs else []

        return Feature(
            key=feature_key,
            title=self._humanize_name(node.name),
            outcomes=outcomes,
            acceptance=acceptance_criteria,
            constraints=constraints,
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

        stories: list[Story] = []
        story_counter = 1

        for group_name, group_methods in method_groups.items():
            if not group_methods:
                continue

            # Create a user story for this group
            story = self._create_story_from_method_group(group_name, group_methods, class_name, story_counter)

            if story:
                stories.append(story)  # type: ignore[reportUnknownMemberType]
                story_counter += 1

        return stories

    def _group_methods_by_functionality(self, methods: list[ast.FunctionDef]) -> dict[str, list[ast.FunctionDef]]:
        """Group methods by their functionality patterns."""
        groups: dict[str, list[ast.FunctionDef]] = defaultdict(list)

        # Filter out private methods (except __init__)
        public_methods = [m for m in methods if not m.name.startswith("_") or m.name == "__init__"]

        for method in public_methods:
            # CRUD operations
            if any(crud in method.name.lower() for crud in ["create", "add", "insert", "new"]):
                groups["Create Operations"].append(method)  # type: ignore[reportUnknownMemberType]
            elif any(read in method.name.lower() for read in ["get", "read", "fetch", "find", "list", "retrieve"]):
                groups["Read Operations"].append(method)  # type: ignore[reportUnknownMemberType]
            elif any(update in method.name.lower() for update in ["update", "modify", "edit", "change", "set"]):
                groups["Update Operations"].append(method)  # type: ignore[reportUnknownMemberType]
            elif any(delete in method.name.lower() for delete in ["delete", "remove", "destroy"]):
                groups["Delete Operations"].append(method)  # type: ignore[reportUnknownMemberType]

            # Validation
            elif any(val in method.name.lower() for val in ["validate", "check", "verify", "is_valid"]):
                groups["Validation"].append(method)  # type: ignore[reportUnknownMemberType]

            # Processing/Computation
            elif any(
                proc in method.name.lower() for proc in ["process", "compute", "calculate", "transform", "convert"]
            ):
                groups["Processing"].append(method)  # type: ignore[reportUnknownMemberType]

            # Analysis
            elif any(an in method.name.lower() for an in ["analyze", "parse", "extract", "detect"]):
                groups["Analysis"].append(method)  # type: ignore[reportUnknownMemberType]

            # Generation
            elif any(gen in method.name.lower() for gen in ["generate", "build", "create", "make"]):
                groups["Generation"].append(method)  # type: ignore[reportUnknownMemberType]

            # Comparison
            elif any(cmp in method.name.lower() for cmp in ["compare", "diff", "match"]):
                groups["Comparison"].append(method)  # type: ignore[reportUnknownMemberType]

            # Setup/Configuration
            elif method.name == "__init__" or any(
                setup in method.name.lower() for setup in ["setup", "configure", "initialize"]
            ):
                groups["Configuration"].append(method)  # type: ignore[reportUnknownMemberType]

            # Catch-all for other public methods
            else:
                groups["Core Functionality"].append(method)  # type: ignore[reportUnknownMemberType]

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

        # Extract testable acceptance criteria using test patterns
        acceptance: list[str] = []
        tasks: list[str] = []

        # Try to extract test patterns from existing tests
        test_patterns = self.test_extractor.extract_test_patterns_for_class(class_name)

        # If test patterns found, use them
        if test_patterns:
            acceptance.extend(test_patterns)

        # Also extract from code patterns (for methods without tests)
        for method in methods:
            # Add method as task
            tasks.append(f"{method.name}()")

            # Extract test patterns from code if no test file patterns found
            if not test_patterns:
                code_patterns = self.test_extractor.infer_from_code_patterns(method, class_name)
                acceptance.extend(code_patterns)

            # Also check docstrings for additional context
            docstring = ast.get_docstring(method)
            if docstring:
                # Check if docstring contains Given/When/Then format
                if "Given" in docstring and "When" in docstring and "Then" in docstring:
                    # Extract Given/When/Then from docstring
                    gwt_match = re.search(
                        r"Given\s+(.+?),\s*When\s+(.+?),\s*Then\s+(.+?)(?:\.|$)", docstring, re.IGNORECASE
                    )
                    if gwt_match:
                        acceptance.append(
                            f"Given {gwt_match.group(1)}, When {gwt_match.group(2)}, Then {gwt_match.group(3)}"
                        )
                else:
                    # Use first line as fallback (will be converted to Given/When/Then later)
                    first_line = docstring.split("\n")[0].strip()
                    if first_line and first_line not in acceptance:
                        # Convert to Given/When/Then format
                        acceptance.append(self._convert_to_gwt_format(first_line, method.name, class_name))

        # Add default testable acceptance if none found
        if not acceptance:
            acceptance.append(
                f"Given {class_name} instance, When {group_name.lower()} is performed, Then operation completes successfully"
            )

        # Extract scenarios from control flow (Step 1.2)
        scenarios: dict[str, list[str]] | None = None
        if methods:
            # Extract scenarios from the first method (representative of the group)
            # In the future, we could merge scenarios from all methods in the group
            primary_method = methods[0]
            scenarios = self.control_flow_analyzer.extract_scenarios_from_method(
                primary_method, class_name, primary_method.name
            )

        # Extract contracts from function signatures (Step 2.1)
        contracts: dict[str, Any] | None = None
        if methods:
            # Extract contracts from the first method (representative of the group)
            # In the future, we could merge contracts from all methods in the group
            primary_method = methods[0]
            contracts = self.contract_extractor.extract_function_contracts(primary_method)

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
            scenarios=scenarios,
            contracts=contracts,
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
                        elif self.entry_point and not any(
                            imported_module.startswith(prefix) for prefix in ["src.", "lib.", "app.", "main.", "core."]
                        ):
                            # Track external dependencies when using entry point
                            # Check if it's a standard library or third-party import
                            # (heuristic: if it doesn't start with known repo patterns)
                            # Likely external dependency
                            self.external_dependencies.add(imported_module)
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
        parts = [*relative_path.parts[:-1], relative_path.stem]  # Remove .py extension
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
        resolved_imports: list[str] = []
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
            # Note: This mapping would be implemented in a full version
            # For now, we track commit bounds per feature
            for _feature in self.features:
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
                            commit_hash = commit.hexsha[:8]  # Short hash

                            # Find feature by key format (FEATURE-001, FEATURE-1, etc.)
                            for feature in self.features:
                                # Match feature key patterns: FEATURE-001, FEATURE-1, Feature-001, etc.
                                if re.search(rf"feature[-\s]?{feature_num}", feature.key, re.IGNORECASE):
                                    # Update commit bounds for this feature
                                    if feature.key not in self.commit_bounds:
                                        # First commit found for this feature
                                        self.commit_bounds[feature.key] = (commit_hash, commit_hash)
                                    else:
                                        # Update last commit (commits are in reverse chronological order)
                                        first_commit, _last_commit = self.commit_bounds[feature.key]
                                        self.commit_bounds[feature.key] = (first_commit, commit_hash)
                                    break
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
        for _feature in self.features:
            # Find dependencies for this feature's module
            # This is simplified - would need to track which module each feature comes from
            pass

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_technology_stack_from_dependencies(self) -> list[str]:
        """
        Extract technology stack from dependency files (requirements.txt, pyproject.toml).

        Returns:
            List of technology constraints extracted from dependency files
        """
        constraints: list[str] = []

        # Try to read requirements.txt
        requirements_file = self.repo_path / "requirements.txt"
        if requirements_file.exists():
            try:
                content = requirements_file.read_text(encoding="utf-8")
                # Parse requirements.txt format: package==version or package>=version
                for line in content.splitlines():
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Remove version specifiers for framework detection
                    package = (
                        line.split("==")[0]
                        .split(">=")[0]
                        .split(">")[0]
                        .split("<=")[0]
                        .split("<")[0]
                        .split("~=")[0]
                        .strip()
                    )
                    package_lower = package.lower()

                    # Detect Python version requirement
                    if package_lower == "python":
                        # Extract version from line
                        if ">=" in line:
                            version = line.split(">=")[1].split(",")[0].strip()
                            constraints.append(f"Python {version}+")
                        elif "==" in line:
                            version = line.split("==")[1].split(",")[0].strip()
                            constraints.append(f"Python {version}")

                    # Detect frameworks
                    framework_map = {
                        "fastapi": "FastAPI framework",
                        "django": "Django framework",
                        "flask": "Flask framework",
                        "typer": "Typer for CLI",
                        "tornado": "Tornado framework",
                        "bottle": "Bottle framework",
                    }

                    if package_lower in framework_map:
                        constraints.append(framework_map[package_lower])

                    # Detect databases
                    db_map = {
                        "psycopg2": "PostgreSQL database",
                        "psycopg2-binary": "PostgreSQL database",
                        "mysql-connector-python": "MySQL database",
                        "pymongo": "MongoDB database",
                        "redis": "Redis database",
                        "sqlalchemy": "SQLAlchemy ORM",
                    }

                    if package_lower in db_map:
                        constraints.append(db_map[package_lower])

                    # Detect testing tools
                    test_map = {
                        "pytest": "pytest for testing",
                        "unittest": "unittest for testing",
                        "nose": "nose for testing",
                        "tox": "tox for testing",
                    }

                    if package_lower in test_map:
                        constraints.append(test_map[package_lower])

                    # Detect deployment tools
                    deploy_map = {
                        "docker": "Docker for containerization",
                        "kubernetes": "Kubernetes for orchestration",
                    }

                    if package_lower in deploy_map:
                        constraints.append(deploy_map[package_lower])

                    # Detect data validation
                    if package_lower == "pydantic":
                        constraints.append("Pydantic for data validation")
            except Exception:
                # If reading fails, continue silently
                pass

        # Try to read pyproject.toml
        pyproject_file = self.repo_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import tomli  # type: ignore[import-untyped]

                content = pyproject_file.read_text(encoding="utf-8")
                data = tomli.loads(content)

                # Extract Python version requirement
                if "project" in data and "requires-python" in data["project"]:
                    python_req = data["project"]["requires-python"]
                    if python_req:
                        constraints.append(f"Python {python_req}")

                # Extract dependencies
                if "project" in data and "dependencies" in data["project"]:
                    deps = data["project"]["dependencies"]
                    for dep in deps:
                        # Similar parsing as requirements.txt
                        package = (
                            dep.split("==")[0]
                            .split(">=")[0]
                            .split(">")[0]
                            .split("<=")[0]
                            .split("<")[0]
                            .split("~=")[0]
                            .strip()
                        )
                        package_lower = package.lower()

                        # Apply same mapping as requirements.txt
                        framework_map = {
                            "fastapi": "FastAPI framework",
                            "django": "Django framework",
                            "flask": "Flask framework",
                            "typer": "Typer for CLI",
                            "tornado": "Tornado framework",
                            "bottle": "Bottle framework",
                        }

                        if package_lower in framework_map:
                            constraints.append(framework_map[package_lower])

                        db_map = {
                            "psycopg2": "PostgreSQL database",
                            "psycopg2-binary": "PostgreSQL database",
                            "mysql-connector-python": "MySQL database",
                            "pymongo": "MongoDB database",
                            "redis": "Redis database",
                            "sqlalchemy": "SQLAlchemy ORM",
                        }

                        if package_lower in db_map:
                            constraints.append(db_map[package_lower])

                        if package_lower == "pydantic":
                            constraints.append("Pydantic for data validation")
            except ImportError:
                # tomli not available, try tomllib (Python 3.11+)
                try:
                    import tomllib  # type: ignore[import-untyped]

                    # tomllib.load() takes a file object opened in binary mode
                    with pyproject_file.open("rb") as f:
                        data = tomllib.load(f)

                    # Extract Python version requirement
                    if "project" in data and "requires-python" in data["project"]:
                        python_req = data["project"]["requires-python"]
                        if python_req:
                            constraints.append(f"Python {python_req}")

                    # Extract dependencies
                    if "project" in data and "dependencies" in data["project"]:
                        deps = data["project"]["dependencies"]
                        for dep in deps:
                            package = (
                                dep.split("==")[0]
                                .split(">=")[0]
                                .split(">")[0]
                                .split("<=")[0]
                                .split("<")[0]
                                .split("~=")[0]
                                .strip()
                            )
                            package_lower = package.lower()

                            framework_map = {
                                "fastapi": "FastAPI framework",
                                "django": "Django framework",
                                "flask": "Flask framework",
                                "typer": "Typer for CLI",
                                "tornado": "Tornado framework",
                                "bottle": "Bottle framework",
                            }

                            if package_lower in framework_map:
                                constraints.append(framework_map[package_lower])

                            db_map = {
                                "psycopg2": "PostgreSQL database",
                                "psycopg2-binary": "PostgreSQL database",
                                "mysql-connector-python": "MySQL database",
                                "pymongo": "MongoDB database",
                                "redis": "Redis database",
                                "sqlalchemy": "SQLAlchemy ORM",
                            }

                            if package_lower in db_map:
                                constraints.append(db_map[package_lower])

                            if package_lower == "pydantic":
                                constraints.append("Pydantic for data validation")
                except ImportError:
                    # Neither tomli nor tomllib available, skip
                    pass
            except Exception:
                # If parsing fails, continue silently
                pass

        # Remove duplicates while preserving order
        seen: set[str] = set()
        unique_constraints: list[str] = []
        for constraint in constraints:
            if constraint not in seen:
                seen.add(constraint)
                unique_constraints.append(constraint)

        # Default fallback if nothing extracted
        if not unique_constraints:
            unique_constraints = ["Python 3.11+", "Typer for CLI", "Pydantic for data validation"]

        return unique_constraints

    @beartype
    def _convert_to_gwt_format(self, text: str, method_name: str, class_name: str) -> str:
        """
        Convert a text description to Given/When/Then format.

        Args:
            text: Original text description
            method_name: Name of the method
            class_name: Name of the class

        Returns:
            Acceptance criterion in Given/When/Then format
        """
        # If already in Given/When/Then format, return as-is
        if "Given" in text and "When" in text and "Then" in text:
            return text

        # Try to extract action and outcome from text
        text_lower = text.lower()

        # Common patterns
        if "must" in text_lower or "should" in text_lower:
            # Extract action after modal verb
            action_match = re.search(r"(?:must|should)\s+(.+?)(?:\.|$)", text_lower)
            if action_match:
                action = action_match.group(1).strip()
                return f"Given {class_name} instance, When {method_name} is called, Then {action}"

        # Default conversion
        return f"Given {class_name} instance, When {method_name} is called, Then {text}"

    def _get_module_dependencies(self, module_name: str) -> list[str]:
        """Get list of modules that the given module depends on."""
        if module_name not in self.dependency_graph:
            return []

        return list(self.dependency_graph.successors(module_name))
