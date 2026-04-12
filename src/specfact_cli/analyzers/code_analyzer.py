"""Code analyzer for extracting features from brownfield codebases."""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import networkx as nx
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn

from specfact_cli.analyzers.contract_extractor import ContractExtractor
from specfact_cli.analyzers.control_flow_analyzer import ControlFlowAnalyzer
from specfact_cli.analyzers.requirement_extractor import RequirementExtractor
from specfact_cli.analyzers.test_pattern_extractor import TestPatternExtractor
from specfact_cli.migrations.plan_migrator import get_current_schema_version
from specfact_cli.models.plan import Feature, Idea, Metadata, PlanBundle, Product, Story
from specfact_cli.utils.feature_keys import to_classname_key, to_sequential_key


console = Console()


@dataclass
class _SemgrepFeatureBuckets:
    api_endpoints: list[str] = field(default_factory=list)
    data_models: list[str] = field(default_factory=list)
    auth_patterns: list[str] = field(default_factory=list)
    crud_operations: list[dict[str, str]] = field(default_factory=list)
    anti_patterns: list[str] = field(default_factory=list)
    code_smells: list[str] = field(default_factory=list)


class CodeAnalyzer:
    """
    Analyzes Python code to auto-derive plan bundles.

    Extracts features from classes and user stories from method patterns
    following Scrum/Agile practices.
    """

    # Fibonacci sequence for story points
    FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    FEATURE_EVIDENCE_FLAGS = {
        "api": "has_api_endpoints",
        "model": "has_database_models",
        "crud": "has_crud_operations",
        "auth": "has_auth_patterns",
        "framework": "has_framework_patterns",
        "test": "has_test_patterns",
        "anti": "has_anti_patterns",
        "security": "has_security_issues",
    }
    DEPENDENCY_CONSTRAINTS = {
        "fastapi": "FastAPI framework",
        "django": "Django framework",
        "flask": "Flask framework",
        "typer": "Typer for CLI",
        "tornado": "Tornado framework",
        "bottle": "Bottle framework",
        "psycopg2": "PostgreSQL database",
        "psycopg2-binary": "PostgreSQL database",
        "mysql-connector-python": "MySQL database",
        "pymongo": "MongoDB database",
        "redis": "Redis database",
        "sqlalchemy": "SQLAlchemy ORM",
        "pytest": "pytest for testing",
        "unittest": "unittest for testing",
        "nose": "nose for testing",
        "tox": "tox for testing",
        "docker": "Docker for containerization",
        "kubernetes": "Kubernetes for orchestration",
        "pydantic": "Pydantic for data validation",
    }
    METHOD_GROUP_MATCHERS = (
        ("Create Operations", ("create", "add", "insert", "new")),
        ("Read Operations", ("get", "read", "fetch", "find", "list", "retrieve")),
        ("Update Operations", ("update", "modify", "edit", "change", "set")),
        ("Delete Operations", ("delete", "remove", "destroy")),
        ("Validation", ("validate", "check", "verify", "is_valid")),
        ("Processing", ("process", "compute", "calculate", "transform", "convert")),
        ("Analysis", ("analyze", "parse", "extract", "detect")),
        ("Generation", ("generate", "build", "create", "make")),
        ("Comparison", ("compare", "diff", "match")),
    )

    @staticmethod
    def _resolve_analyzer_entry_point(repo_path: Path, entry_point: Path | None) -> Path | None:
        if entry_point is None:
            return None
        resolved = entry_point if entry_point.is_absolute() else (repo_path / entry_point).resolve()
        if not resolved.exists():
            raise ValueError(f"Entry point does not exist: {resolved}")
        if not str(resolved).startswith(str(repo_path)):
            raise ValueError(f"Entry point must be within repository: {resolved}")
        return resolved

    def _init_semgrep_configs(self) -> None:
        self.semgrep_enabled = True
        self.semgrep_config = None
        self.semgrep_quality_config = None
        resources_config = Path(__file__).parent.parent / "resources" / "semgrep" / "feature-detection.yml"
        tools_config = self.repo_path / "tools" / "semgrep" / "feature-detection.yml"
        resources_quality_config = Path(__file__).parent.parent / "resources" / "semgrep" / "code-quality.yml"
        tools_quality_config = self.repo_path / "tools" / "semgrep" / "code-quality.yml"
        self.semgrep_config = (
            resources_config if resources_config.exists() else (tools_config if tools_config.exists() else None)
        )
        self.semgrep_quality_config = (
            resources_quality_config
            if resources_quality_config.exists()
            else (tools_quality_config if tools_quality_config.exists() else None)
        )
        if os.environ.get("TEST_MODE") == "true" or self.semgrep_config is None or not self._check_semgrep_available():
            self.semgrep_enabled = False

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
        incremental_callback: Any | None = None,
    ) -> None:
        """
        Initialize code analyzer.

        Args:
            repo_path: Path to repository root
            confidence_threshold: Minimum confidence score (0.0-1.0)
            key_format: Feature key format ('classname' or 'sequential', default: 'classname')
            plan_name: Custom plan name (will be used for idea.title, optional)
            entry_point: Optional entry point path for partial analysis (relative to repo_path)
            incremental_callback: Optional callback function(features_count, themes) for incremental results (Phase 4.9)
        """
        self.repo_path = Path(repo_path).resolve()
        self.confidence_threshold = confidence_threshold
        self.key_format = key_format
        self.plan_name = plan_name
        self.incremental_callback = incremental_callback
        self.entry_point = self._resolve_analyzer_entry_point(self.repo_path, entry_point)
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

        self._init_semgrep_configs()

    @beartype
    @ensure(lambda result: isinstance(result, PlanBundle), "Must return PlanBundle")
    @ensure(
        lambda result: (
            isinstance(result, PlanBundle)
            and hasattr(result, "version")
            and hasattr(result, "features")
            and result.version == get_current_schema_version()  # type: ignore[reportUnknownMemberType]
            and len(result.features) >= 0
        ),  # type: ignore[reportUnknownMemberType]
        "Plan bundle must be valid",
    )
    def analyze(self) -> PlanBundle:
        """
        Analyze repository and generate plan bundle.

        Returns:
            Generated PlanBundle from code analysis
        """
        python_files: list[Path] = []
        technology_constraints: list[str] = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            python_files = self._run_discovery_phase(progress)
            self._run_dependency_graph_phase(progress, python_files)
            self._run_file_analysis_phase(progress, python_files)
            self._run_simple_phase(
                progress,
                "[cyan]Phase 4: Analyzing commit history...",
                self._analyze_commit_history,
                "[green]✓ Commit history analyzed",
            )
            self._run_simple_phase(
                progress,
                "[cyan]Phase 5: Enhancing features with dependency information...",
                self._enhance_features_with_dependencies,
                "[green]✓ Features enhanced",
            )
            technology_constraints = self._run_technology_phase(progress)

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
            summary=None,
        )

        return PlanBundle(
            version=get_current_schema_version(),
            idea=idea,
            business=None,
            product=product,
            features=self.features,
            metadata=metadata,
            clarifications=None,
        )

    def _run_discovery_phase(self, progress: Progress) -> list[Path]:
        """Discover Python files for the current analysis scope."""
        task = progress.add_task("[cyan]Phase 1: Discovering Python files...", total=None)
        python_files = list((self.entry_point or self.repo_path).rglob("*.py"))
        if self.entry_point:
            entry_point_rel = self.entry_point.relative_to(self.repo_path)
            description = f"[green]✓ Found {len(python_files)} Python files in {entry_point_rel}"
        else:
            description = f"[green]✓ Found {len(python_files)} Python files"
        progress.update(task, description=description)
        progress.remove_task(task)
        return python_files

    def _run_dependency_graph_phase(self, progress: Progress, python_files: list[Path]) -> None:
        """Build the repository dependency graph."""
        self._run_simple_phase(
            progress,
            "[cyan]Phase 2: Building dependency graph...",
            lambda: self._build_dependency_graph(python_files),
            "[green]✓ Dependency graph built",
        )

    def _run_simple_phase(self, progress: Progress, description: str, action: Any, success_message: str) -> None:
        """Run a simple progress phase with no incremental updates."""
        task = progress.add_task(description, total=None)
        action()
        progress.update(task, description=success_message)
        progress.remove_task(task)

    def _run_file_analysis_phase(self, progress: Progress, python_files: list[Path]) -> None:
        """Analyze relevant files and merge extracted features."""
        task = progress.add_task("[cyan]Phase 3: Analyzing files and extracting features...", total=len(python_files))
        files_to_analyze = [f for f in python_files if not self._should_skip_file(f)]
        if files_to_analyze:
            if os.environ.get("TEST_MODE") == "true":
                self._analyze_files_sequential(files_to_analyze, progress, task)
            else:
                self._analyze_files_parallel(files_to_analyze, progress, task)
        self._finalize_analysis_progress(progress, task, python_files, files_to_analyze)

    def _analyze_file_safe(self, file_path: Path) -> dict[str, Any]:
        """Analyze a file and return thread-safe results."""
        return self._analyze_file_parallel(file_path)

    def _update_analysis_progress(self, progress: Progress, task_id: TaskID, completed_count: int) -> None:
        """Update progress text with the current feature count."""
        features_count = len(self.features)
        progress.update(
            task_id,
            completed=completed_count,
            description=f"[cyan]Phase 3: Analyzing files and extracting features... ({features_count} features discovered)",
        )

    def _handle_analysis_results(
        self,
        progress: Progress,
        task_id: TaskID,
        results: dict[str, Any],
        completed_count: int,
    ) -> None:
        """Merge analysis results and report incremental callbacks when needed."""
        prev_features_count = len(self.features)
        self._merge_analysis_results(results)
        self._update_analysis_progress(progress, task_id, completed_count)
        if self.incremental_callback and len(self.features) > prev_features_count:
            self.incremental_callback(len(self.features), sorted(self.themes))

    def _log_analysis_failure(
        self,
        progress: Progress,
        task_id: TaskID,
        file_path: Path,
        error: Exception,
        completed_count: int,
    ) -> None:
        """Log a failed file analysis and keep progress moving."""
        console.print(f"[dim]⚠ Warning: Failed to analyze {file_path}: {error}[/dim]")
        self._update_analysis_progress(progress, task_id, completed_count)

    def _analyze_files_sequential(self, files_to_analyze: list[Path], progress: Progress, task_id: TaskID) -> None:
        """Analyze files sequentially for test-mode stability."""
        for completed_count, file_path in enumerate(files_to_analyze, start=1):
            try:
                results = self._analyze_file_safe(file_path)
                self._handle_analysis_results(progress, task_id, results, completed_count)
            except Exception as error:
                self._log_analysis_failure(progress, task_id, file_path, error, completed_count)

    def _analyze_files_parallel(self, files_to_analyze: list[Path], progress: Progress, task_id: TaskID) -> None:
        """Analyze files in parallel and merge results sequentially."""
        max_workers = max(1, min(os.cpu_count() or 4, 8, len(files_to_analyze)))
        executor = ThreadPoolExecutor(max_workers=max_workers)
        interrupted = False
        completed_count = 0
        try:
            future_to_file = {
                executor.submit(self._analyze_file_safe, file_path): file_path for file_path in files_to_analyze
            }
            try:
                for future in as_completed(future_to_file):
                    completed_count += 1
                    try:
                        results = future.result()
                        self._handle_analysis_results(progress, task_id, results, completed_count)
                    except KeyboardInterrupt:
                        interrupted = True
                        self._cancel_pending_futures(future_to_file)
                        break
                    except Exception as error:
                        self._log_analysis_failure(progress, task_id, future_to_file[future], error, completed_count)
            except KeyboardInterrupt:
                interrupted = True
                self._cancel_pending_futures(future_to_file)
            if interrupted:
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            interrupted = True
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        finally:
            executor.shutdown(wait=not interrupted)

    def _cancel_pending_futures(self, future_to_file: dict[Any, Path]) -> None:
        """Cancel pending file-analysis futures."""
        for future in future_to_file:
            if not future.done():
                future.cancel()

    def _finalize_analysis_progress(
        self,
        progress: Progress,
        task_id: TaskID,
        python_files: list[Path],
        files_to_analyze: list[Path],
    ) -> None:
        """Finish the analysis progress bar after skipped-file accounting."""
        if len(files_to_analyze) < len(python_files):
            self._update_analysis_progress(progress, task_id, len(python_files))
        progress.update(
            task_id,
            description=f"[green]✓ Analyzed {len(python_files)} files, extracted {len(self.features)} features",
        )
        progress.remove_task(task_id)

    def _run_technology_phase(self, progress: Progress) -> list[str]:
        """Extract technology constraints with progress reporting."""
        task = progress.add_task("[cyan]Phase 6: Extracting technology stack...", total=None)
        constraints = self._extract_technology_stack_from_dependencies()
        progress.update(task, description="[green]✓ Technology stack extracted")
        progress.remove_task(task)
        return constraints

    def _check_semgrep_available(self) -> bool:
        """Check if Semgrep is available in PATH."""
        # Skip Semgrep check in test mode to avoid timeouts
        if os.environ.get("TEST_MODE") == "true":
            return False

        # Fast check: use shutil.which first to avoid subprocess overhead
        if shutil.which("semgrep") is None:
            return False

        try:
            result = subprocess.run(
                ["semgrep", "--version"],
                capture_output=True,
                text=True,
                timeout=5,  # Increased timeout to 5s (Semgrep may need time to initialize)
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    @ensure(lambda result: isinstance(result, list), "Must return list")
    def get_plugin_status(self) -> list[dict[str, Any]]:
        """
        Get status of all analysis plugins.

        Returns:
            List of plugin status dictionaries with keys: name, enabled, used, reason
        """
        from specfact_cli.utils.optional_deps import check_cli_tool_available, check_python_package_available

        plugins: list[dict[str, Any]] = []

        # AST Analysis (always enabled)
        plugins.append(
            {
                "name": "AST Analysis",
                "enabled": True,
                "used": True,
                "reason": "Core analysis engine",
            }
        )

        # Semgrep Pattern Detection
        semgrep_available = self._check_semgrep_available()
        semgrep_enabled = self.semgrep_enabled and semgrep_available
        semgrep_used = semgrep_enabled and self.semgrep_config is not None

        if not semgrep_available:
            reason = "Semgrep CLI not installed (install: pip install semgrep)"
        elif self.semgrep_config is None:
            reason = "Semgrep config not found"
        else:
            reason = "Pattern detection enabled"
            if self.semgrep_quality_config:
                reason += " (with code quality rules)"

        plugins.append(
            {
                "name": "Semgrep Pattern Detection",
                "enabled": semgrep_enabled,
                "used": semgrep_used,
                "reason": reason,
            }
        )

        # Dependency Graph Analysis (requires pyan3 and networkx)
        pyan3_available, _ = check_cli_tool_available("pyan3")
        networkx_available = check_python_package_available("networkx")
        graph_enabled = pyan3_available and networkx_available
        graph_used = graph_enabled  # Used if both dependencies are available

        if not pyan3_available and not networkx_available:
            reason = "pyan3 and networkx not installed (install: pip install pyan3 networkx)"
        elif not pyan3_available:
            reason = "pyan3 not installed (install: pip install pyan3)"
        elif not networkx_available:
            reason = "networkx not installed (install: pip install networkx)"
        else:
            reason = "Dependency graph analysis enabled"

        plugins.append(
            {
                "name": "Dependency Graph Analysis",
                "enabled": graph_enabled,
                "used": graph_used,
                "reason": reason,
            }
        )

        return plugins

    def _run_semgrep_patterns(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Run Semgrep for pattern detection on a single file.

        Returns:
            List of Semgrep findings (empty list if Semgrep not available or error)
        """
        # Skip Semgrep in test mode to avoid timeouts
        if os.environ.get("TEST_MODE") == "true":
            return []

        if not self.semgrep_enabled or self.semgrep_config is None:
            return []

        try:
            # Check if semgrep is available quickly
            if not shutil.which("semgrep"):
                return []

            # Run feature detection
            configs = [str(self.semgrep_config)]
            # Also include code-quality config if available (for anti-patterns)
            if self.semgrep_quality_config is not None:
                configs.append(str(self.semgrep_quality_config))

            # Use shorter timeout in test environments (though we already skip in TEST_MODE)
            timeout = 10

            result = subprocess.run(
                ["semgrep", "--config", *configs, "--json", str(file_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Semgrep may return non-zero for valid findings
            # Only fail if stderr indicates actual error
            if result.returncode != 0 and ("error" in result.stderr.lower() or "not found" in result.stderr.lower()):
                return []

            # Parse JSON results
            findings = json.loads(result.stdout)
            return findings.get("results", [])
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError, ValueError):
            # Semgrep not available or config missing - continue without it
            return []

    def _should_skip_file(self, file_path: Path) -> bool:
        """
        Check if file should be skipped.

        Test files are always skipped from feature extraction because:
        - Tests are validation artifacts, not specification artifacts
        - Tests validate code, they don't define what code should do
        - Test files should only be used for linking to production features and extracting examples
        """
        file_str = str(file_path)
        file_name = file_path.name

        # Skip common non-source directories
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
        ]

        if any(pattern in file_str for pattern in skip_patterns):
            return True

        # Skip test directories (both "test/" and "tests/")
        # Check if any path component is a test directory
        path_parts = file_path.parts
        if any(part in ("test", "tests") for part in path_parts):
            return True

        # Skip test files by naming pattern (test_*.py, *_test.py)
        return file_name.startswith("test_") or file_name.endswith("_test.py")

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file (legacy sequential version)."""
        results = self._analyze_file_parallel(file_path)
        self._merge_analysis_results(results)

    def _analyze_file_parallel(self, file_path: Path) -> dict[str, Any]:
        """
        Analyze a single Python file and return results (thread-safe).

        Returns:
            Dictionary with extracted data:
            - 'themes': set of theme strings
            - 'type_hints': dict mapping module -> {function: type_hint}
            - 'async_patterns': dict mapping module -> [async_methods]
            - 'features': list of Feature objects
        """
        results: dict[str, Any] = {
            "themes": set(),
            "type_hints": {},
            "async_patterns": {},
            "features": [],
        }

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            # Extract module-level info (return themes instead of modifying self)
            themes = self._extract_themes_from_imports_parallel(tree)
            results["themes"].update(themes)

            # Extract type hints (return instead of modifying self)
            module_name = self._path_to_module_name(file_path)
            type_hints = self._extract_type_hints_parallel(tree, file_path)
            if type_hints:
                results["type_hints"][module_name] = type_hints

            # Detect async patterns (return instead of modifying self)
            async_methods = self._detect_async_patterns_parallel(tree, file_path)
            if async_methods:
                results["async_patterns"][module_name] = async_methods

            # NEW: Run Semgrep for pattern detection
            semgrep_findings = self._run_semgrep_patterns(file_path)

            # Extract classes as features
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    feature = self._extract_feature_for_results(node, file_path, semgrep_findings)
                    if feature is not None:
                        results["features"].append(feature)

        except (SyntaxError, UnicodeDecodeError):
            # Skip files that can't be parsed
            pass

        return results

    def _extract_feature_for_results(
        self,
        node: ast.ClassDef,
        file_path: Path,
        semgrep_findings: list[dict[str, Any]],
    ) -> Feature | None:
        """Extract one feature while isolating per-class enhancement failures."""
        current_count = 0 if self.key_format == "sequential" else len(self.features)
        class_start_line = node.lineno if hasattr(node, "lineno") else None
        class_end_line = node.end_lineno if hasattr(node, "end_lineno") else None
        semgrep_evidence = self._extract_semgrep_evidence(semgrep_findings, node.name, class_start_line, class_end_line)

        feature = self._extract_feature_from_class_parallel(node, file_path, current_count, semgrep_evidence)
        if feature is None:
            return None

        try:
            self._enhance_feature_with_semgrep(
                feature, semgrep_findings, file_path, node.name, class_start_line, class_end_line
            )
        except Exception as exc:
            console.print(f"[dim]⚠ Warning: Skipped Semgrep enhancement for {file_path}:{node.name}: {exc}[/dim]")

        return feature

    def _merge_analysis_results(self, results: dict[str, Any]) -> None:
        """Merge parallel analysis results into instance variables."""
        # Merge themes
        self.themes.update(results.get("themes", set()))

        # Merge type hints
        for module, hints in results.get("type_hints", {}).items():
            if module not in self.type_hints:
                self.type_hints[module] = {}
            self.type_hints[module].update(hints)

        # Merge async patterns
        for module, methods in results.get("async_patterns", {}).items():
            if module not in self.async_patterns:
                self.async_patterns[module] = []
            self.async_patterns[module].extend(methods)

        # Merge features (append to list)
        self.features.extend(results.get("features", []))

    def _extract_themes_from_imports(self, tree: ast.AST) -> None:
        """Extract themes from import statements (legacy version)."""
        themes = self._extract_themes_from_imports_parallel(tree)
        self.themes.update(themes)

    @staticmethod
    def _themes_for_import_module(module_name: str, theme_keywords: dict[str, str]) -> set[str]:
        lowered = module_name.lower()
        return {theme for keyword, theme in theme_keywords.items() if keyword in lowered}

    def _themes_for_import_node(self, node: ast.Import | ast.ImportFrom, theme_keywords: dict[str, str]) -> set[str]:
        if isinstance(node, ast.Import):
            found: set[str] = set()
            for alias in node.names:
                found.update(self._themes_for_import_module(alias.name, theme_keywords))
            return found
        if isinstance(node, ast.ImportFrom) and node.module:
            return self._themes_for_import_module(node.module, theme_keywords)
        return set()

    def _extract_themes_from_imports_parallel(self, tree: ast.AST) -> set[str]:
        """Extract themes from import statements (thread-safe, returns themes)."""
        themes: set[str] = set()
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
                themes.update(self._themes_for_import_node(node, theme_keywords))

        return themes

    def _extract_semgrep_evidence(
        self,
        semgrep_findings: list[dict[str, Any]],
        class_name: str,
        class_start_line: int | None,
        class_end_line: int | None,
    ) -> dict[str, Any]:
        """
        Extract Semgrep evidence for confidence scoring.

        Args:
            semgrep_findings: List of Semgrep findings
            class_name: Name of the class
            class_start_line: Starting line number of the class
            class_end_line: Ending line number of the class

        Returns:
            Evidence dict with boolean flags for different pattern types
        """
        evidence: dict[str, Any] = dict.fromkeys(self.FEATURE_EVIDENCE_FLAGS.values(), False)

        for finding in semgrep_findings:
            rule_id = str(finding.get("check_id", "")).lower()
            if not self._finding_matches_class(finding, class_name, class_start_line, class_end_line, rule_id):
                continue
            self._apply_semgrep_evidence_flag(evidence, rule_id)

        return evidence

    def _finding_matches_class(
        self,
        finding: dict[str, Any],
        class_name: str,
        class_start_line: int | None,
        class_end_line: int | None,
        rule_id: str | None = None,
    ) -> bool:
        """Check whether a Semgrep finding belongs to the target class."""
        effective_rule_id = rule_id or str(finding.get("check_id", "")).lower()
        message = str(finding.get("message", "")).lower()
        class_name_lower = class_name.lower()
        if class_name_lower in message or class_name_lower in effective_rule_id:
            return True
        finding_line = self._semgrep_finding_line(finding)
        return bool(
            class_start_line and class_end_line and finding_line and class_start_line <= finding_line <= class_end_line
        )

    def _semgrep_finding_line(self, finding: dict[str, Any]) -> int:
        """Extract the start line from a Semgrep finding."""
        raw_start = finding.get("start", {})
        if not isinstance(raw_start, dict):
            return 0
        start: dict[str, Any] = raw_start
        return int(start.get("line", 0))

    def _apply_semgrep_evidence_flag(self, evidence: dict[str, Any], rule_id: str) -> None:
        """Apply the first matching evidence flag for a rule id."""
        matchers = (
            ("api", ("route-detection", "api-endpoint")),
            ("model", ("model-detection", "database-model")),
            ("crud", ("crud",)),
            ("auth", ("auth", "authentication", "permission")),
            ("framework", ("framework", "async", "context-manager")),
            ("test", ("test", "pytest", "unittest")),
            (
                "anti",
                (
                    "antipattern",
                    "code-smell",
                    "god-class",
                    "mutable-default",
                    "lambda-assignment",
                    "string-concatenation",
                    "deprecated",
                ),
            ),
            (
                "security",
                ("security", "unsafe", "insecure", "weak-cryptographic", "hardcoded-secret", "command-injection"),
            ),
        )
        for category, keywords in matchers:
            if any(keyword in rule_id for keyword in keywords):
                evidence[self.FEATURE_EVIDENCE_FLAGS[category]] = True
                return

    def _extract_feature_from_class(self, node: ast.ClassDef, file_path: Path) -> Feature | None:
        """Extract feature from class definition (legacy version)."""
        return self._extract_feature_from_class_parallel(node, file_path, len(self.features), None)

    def _extract_feature_from_class_parallel(
        self,
        node: ast.ClassDef,
        file_path: Path,
        current_feature_count: int,
        semgrep_evidence: dict[str, Any] | None = None,
    ) -> Feature | None:
        """Extract feature from class definition (thread-safe version)."""
        # Skip private classes and test classes
        if node.name.startswith("_") or node.name.startswith("Test"):
            return None

        # Generate feature key based on configured format
        # For sequential keys, use placeholder (will be fixed after all features collected)
        # During parallel processing, we can't know the final position
        feature_key = (
            "FEATURE-PLACEHOLDER"  # Will be replaced in post-processing
            if self.key_format == "sequential"
            else to_classname_key(node.name)
        )

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

        # Calculate confidence based on documentation, story quality, and Semgrep evidence
        confidence = self._calculate_feature_confidence(node, stories, semgrep_evidence)

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
            source_tracking=None,
            contract=None,
            protocol=None,
        )

    def _filter_relevant_semgrep_findings(
        self,
        semgrep_findings: list[dict[str, Any]],
        file_path: Path,
        class_name: str,
        class_start_line: int | None,
        class_end_line: int | None,
    ) -> list[dict[str, Any]]:
        """
        Filter Semgrep findings to only those relevant to a specific class in a file.

        Matches by class name mention, line range, or anti-pattern proximity.

        Args:
            semgrep_findings: All findings for the repository
            file_path: Path to the file being analyzed
            class_name: Name of the class to match against
            class_start_line: First line of the class definition
            class_end_line: Last line of the class definition

        Returns:
            Filtered list of findings relevant to the class
        """
        relevant: list[dict[str, Any]] = []
        for finding in semgrep_findings:
            finding_path = finding.get("path", "")
            if str(file_path) not in finding_path and finding_path not in str(file_path):
                continue
            if self._finding_matches_class(finding, class_name, class_start_line, class_end_line):
                relevant.append(finding)
                continue
            finding_line = self._semgrep_finding_line(finding)
            check_id = str(finding.get("check_id", "")).lower()
            if self._is_nearby_anti_pattern(check_id, finding_line, class_start_line, class_end_line):
                relevant.append(finding)
        return relevant

    def _is_nearby_anti_pattern(
        self,
        check_id: str,
        finding_line: int,
        class_start_line: int | None,
        class_end_line: int | None,
    ) -> bool:
        """Check whether a finding is a nearby anti-pattern for the class."""
        if not class_start_line or not finding_line:
            return False
        is_anti_pattern = any(
            term in check_id for term in ("antipattern", "code-smell", "god-class", "deprecated", "security")
        )
        if not is_anti_pattern or finding_line < class_start_line:
            return False
        if class_end_line:
            return finding_line <= class_end_line
        return finding_line <= (class_start_line + 100)

    def _categorise_semgrep_finding(
        self,
        finding: dict[str, Any],
    ) -> tuple[str, str]:
        """
        Categorise a single Semgrep finding into a type string and its payload value.

        Args:
            finding: Single Semgrep finding dict

        Returns:
            Tuple of (category, value) where category is one of
            "api", "model", "auth", "crud", "antipattern", "codesmell", or "".
        """
        rule_id = str(finding.get("check_id", "")).lower()
        extra_raw = finding.get("extra", {})
        extra: dict[str, Any] = extra_raw if isinstance(extra_raw, dict) else {}
        metadata_raw = extra.get("metadata", {})
        metadata: dict[str, Any] = metadata_raw if isinstance(metadata_raw, dict) else {}
        category_builders = (
            self._categorise_api_finding,
            self._categorise_model_finding,
            self._categorise_auth_finding,
            self._categorise_crud_finding,
            self._categorise_antipattern_finding,
            self._categorise_codesmell_finding,
        )
        for builder in category_builders:
            category, value = builder(finding, rule_id, metadata, extra)
            if category:
                return category, value
        return "", ""

    def _categorise_api_finding(
        self,
        _finding: dict[str, Any],
        rule_id: str,
        metadata: dict[str, Any],
        _extra: Any,
    ) -> tuple[str, str]:
        """Categorise API findings."""
        if "route-detection" not in rule_id:
            return "", ""
        method = str(metadata.get("method", "")).upper()
        path = str(metadata.get("path", ""))
        return ("api", f"{method} {path}") if method and path else ("", "")

    def _categorise_model_finding(
        self,
        _finding: dict[str, Any],
        rule_id: str,
        metadata: dict[str, Any],
        _extra: Any,
    ) -> tuple[str, str]:
        """Categorise model findings."""
        if "model-detection" not in rule_id:
            return "", ""
        model_name = str(metadata.get("model", ""))
        return ("model", model_name) if model_name else ("", "")

    def _categorise_auth_finding(
        self,
        _finding: dict[str, Any],
        rule_id: str,
        metadata: dict[str, Any],
        _extra: Any,
    ) -> tuple[str, str]:
        """Categorise auth findings."""
        if "auth" not in rule_id:
            return "", ""
        permission = str(metadata.get("permission", ""))
        return "auth", permission or "authentication required"

    def _categorise_crud_finding(
        self,
        finding: dict[str, Any],
        rule_id: str,
        metadata: dict[str, Any],
        extra: Any,
    ) -> tuple[str, str]:
        """Categorise CRUD findings."""
        if "crud" not in rule_id:
            return "", ""
        operation = str(metadata.get("operation", "")).upper()
        entity = self._extract_crud_entity(finding, extra)
        return ("crud", f"{operation or 'UNKNOWN'}:{entity or 'unknown'}") if (operation or entity) else ("", "")

    def _extract_crud_entity(self, finding: dict[str, Any], extra: Any) -> str:
        """Extract the target entity from a CRUD finding."""
        if isinstance(extra, dict):
            extra_d: dict[str, Any] = cast(dict[str, Any], extra)
            func_name = str(extra_d.get("message", ""))
        else:
            func_name = ""
        if func_name:
            parts = func_name.split("_")
            return "_".join(parts[1:]) if len(parts) > 1 else ""
        message = str(finding.get("message", "")).lower()
        for operation in ["create", "get", "update", "delete", "add", "find", "remove"]:
            if operation in message:
                parts = message.split(operation + "_")
                if len(parts) > 1 and parts[1]:
                    return parts[1].split()[0]
        return ""

    def _categorise_antipattern_finding(
        self,
        finding: dict[str, Any],
        rule_id: str,
        _metadata: dict[str, Any],
        _extra: Any,
    ) -> tuple[str, str]:
        """Categorise anti-pattern findings."""
        terms = (
            "antipattern",
            "code-smell",
            "god-class",
            "mutable-default",
            "lambda-assignment",
            "string-concatenation",
        )
        return ("antipattern", str(finding.get("message", ""))) if any(term in rule_id for term in terms) else ("", "")

    def _categorise_codesmell_finding(
        self,
        finding: dict[str, Any],
        rule_id: str,
        _metadata: dict[str, Any],
        _extra: Any,
    ) -> tuple[str, str]:
        """Categorise code-smell and security findings."""
        terms = (
            "security",
            "unsafe",
            "insecure",
            "weak-cryptographic",
            "hardcoded-secret",
            "command-injection",
            "deprecated",
        )
        return ("codesmell", str(finding.get("message", ""))) if any(term in rule_id for term in terms) else ("", "")

    def _apply_semgrep_findings_to_feature(self, feature: Feature, buckets: _SemgrepFeatureBuckets) -> None:
        """
        Apply categorised Semgrep findings to a feature by updating outcomes and constraints.

        Args:
            feature: Feature to update in-place
            buckets: Categorised Semgrep finding lists (API, models, auth, CRUD, anti-patterns, smells).
        """
        if buckets.api_endpoints:
            feature.outcomes.append(f"Exposes API endpoints: {', '.join(buckets.api_endpoints)}")
        if buckets.data_models:
            feature.outcomes.append(f"Defines data models: {', '.join(buckets.data_models)}")
        if buckets.auth_patterns:
            feature.outcomes.append(f"Requires authentication: {', '.join(buckets.auth_patterns)}")
        if buckets.crud_operations:
            crud_str = ", ".join(
                f"{op.get('operation', 'UNKNOWN')} {op.get('entity', 'unknown')}" for op in buckets.crud_operations
            )
            feature.outcomes.append(f"Provides CRUD operations: {crud_str}")
        if buckets.anti_patterns:
            anti_str = "; ".join(buckets.anti_patterns[:3])
            if anti_str:
                if feature.constraints:
                    feature.constraints.append(f"Code quality: {anti_str}")
                else:
                    feature.constraints = [f"Code quality: {anti_str}"]
        if buckets.code_smells:
            smell_str = "; ".join(buckets.code_smells[:3])
            if smell_str:
                if feature.constraints:
                    feature.constraints.append(f"Issues detected: {smell_str}")
                else:
                    feature.constraints = [f"Issues detected: {smell_str}"]

    def _accumulate_semgrep_finding_bucket(self, buckets: _SemgrepFeatureBuckets, category: str, value: str) -> None:
        if category == "api":
            buckets.api_endpoints.append(value)
            self.themes.add("API")
            return
        if category == "model":
            buckets.data_models.append(value)
            self.themes.add("Database")
            return
        if category == "auth":
            buckets.auth_patterns.append(value)
            self.themes.add("Security")
            return
        if category == "crud":
            op, _, entity = value.partition(":")
            buckets.crud_operations.append({"operation": op, "entity": entity})
            return
        if category == "antipattern":
            buckets.anti_patterns.append(value)
            return
        if category == "codesmell":
            buckets.code_smells.append(value)

    def _enhance_feature_with_semgrep(
        self,
        feature: Feature,
        semgrep_findings: list[dict[str, Any]],
        file_path: Path,
        class_name: str,
        class_start_line: int | None = None,
        class_end_line: int | None = None,
    ) -> None:
        """
        Enhance feature with Semgrep pattern detection results.

        Args:
            feature: Feature to enhance
            semgrep_findings: List of Semgrep findings for the file
            file_path: Path to the file being analyzed
            class_name: Name of the class this feature represents
            class_start_line: Starting line number of the class definition
            class_end_line: Ending line number of the class definition
        """
        if not semgrep_findings:
            return

        relevant_findings = self._filter_relevant_semgrep_findings(
            semgrep_findings, file_path, class_name, class_start_line, class_end_line
        )
        if not relevant_findings:
            return

        buckets = _SemgrepFeatureBuckets()

        for finding in relevant_findings:
            category, value = self._categorise_semgrep_finding(finding)
            self._accumulate_semgrep_finding_bucket(buckets, category, value)

        self._apply_semgrep_findings_to_feature(feature, buckets)

        # Confidence is already calculated with Semgrep evidence in _calculate_feature_confidence
        # No need to adjust here - this method only adds outcomes, constraints, and themes

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
        for method in self._public_methods(methods):
            groups[self._classify_method_group(method.name)].append(method)  # type: ignore[reportUnknownMemberType]

        return dict(groups)

    def _public_methods(self, methods: list[ast.FunctionDef]) -> list[ast.FunctionDef]:
        """Return public methods plus __init__."""
        return [method for method in methods if not method.name.startswith("_") or method.name == "__init__"]

    def _classify_method_group(self, method_name: str) -> str:
        """Classify a method into a functional group."""
        method_name_lower = method_name.lower()
        for group_name, keywords in self.METHOD_GROUP_MATCHERS:
            if any(keyword in method_name_lower for keyword in keywords):
                return group_name
        if method_name == "__init__" or any(
            keyword in method_name_lower for keyword in ("setup", "configure", "initialize")
        ):
            return "Configuration"
        return "Core Functionality"

    def _create_story_from_method_group(
        self, group_name: str, methods: list[ast.FunctionDef], class_name: str, story_number: int
    ) -> Story | None:
        """Create a user story from a group of related methods."""
        if not methods:
            return None
        story_key = f"STORY-{class_name.upper()}-{story_number:03d}"
        title = self._generate_story_title(group_name, class_name)
        acceptance, tasks = self._build_story_acceptance_and_tasks(methods, class_name, group_name)
        scenarios, contracts = self._extract_story_artifacts(methods, class_name)

        story_points = self._calculate_story_points(methods)
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

    def _build_story_acceptance_and_tasks(
        self,
        methods: list[ast.FunctionDef],
        class_name: str,
        group_name: str,
    ) -> tuple[list[str], list[str]]:
        """Build acceptance criteria and task labels for a story."""
        acceptance = self._initial_story_acceptance(class_name)
        tasks = [f"{method.name}()" for method in methods]
        if not acceptance:
            for method in methods:
                acceptance.extend(self.test_extractor.infer_from_code_patterns(method, class_name))
        for method in methods:
            self._append_docstring_acceptance(acceptance, ast.get_docstring(method))
        if not acceptance:
            acceptance.append(f"{group_name} functionality works correctly")
        return acceptance, tasks

    def _initial_story_acceptance(self, class_name: str) -> list[str]:
        """Get the initial acceptance criteria from extracted test patterns."""
        test_patterns = self.test_extractor.extract_test_patterns_for_class(class_name, as_openapi_examples=True)
        return list(test_patterns[:3]) if test_patterns else []

    def _append_docstring_acceptance(self, acceptance: list[str], docstring: str | None) -> None:
        """Append acceptance criteria derived from a method docstring."""
        if not docstring:
            return
        extracted = self._extract_docstring_acceptance(docstring)
        if extracted and extracted not in acceptance:
            acceptance.append(extracted)

    def _extract_docstring_acceptance(self, docstring: str) -> str:
        """Extract a concise acceptance statement from a docstring."""
        if "Given" in docstring and "When" in docstring and "Then" in docstring:
            gwt_match = re.search(r"Given\s+(.+?),\s*When\s+(.+?),\s*Then\s+(.+?)(?:\.|$)", docstring, re.IGNORECASE)
            if gwt_match:
                return gwt_match.group(3).strip()
        return docstring.split("\n")[0].strip()

    def _extract_story_artifacts(
        self,
        methods: list[ast.FunctionDef],
        class_name: str,
    ) -> tuple[dict[str, list[str]] | None, dict[str, Any] | None]:
        """Extract scenarios and contracts from the representative method."""
        if not methods:
            return None, None
        primary_method = methods[0]
        try:
            scenarios = self.control_flow_analyzer.extract_scenarios_from_method(
                primary_method, class_name, primary_method.name
            )
        except Exception:
            scenarios = None
        try:
            contracts = self.contract_extractor.extract_function_contracts(primary_method)
        except Exception:
            contracts = None
        return scenarios, contracts

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

    def _calculate_feature_confidence(
        self,
        node: ast.ClassDef,
        stories: list[Story],
        semgrep_evidence: dict[str, Any] | None = None,
    ) -> float:
        """
        Calculate confidence score for a feature combining AST + Semgrep evidence.

        Args:
            node: AST class node
            stories: List of stories extracted from methods
            semgrep_evidence: Optional Semgrep findings evidence dict with keys:
                - has_api_endpoints: bool
                - has_database_models: bool
                - has_crud_operations: bool
                - has_auth_patterns: bool
                - has_framework_patterns: bool
                - has_test_patterns: bool
                - has_anti_patterns: bool
                - has_security_issues: bool

        Returns:
            Confidence score (0.0-1.0) combining AST and Semgrep evidence
        """
        score = 0.3
        score += self._ast_confidence_bonus(node, stories)
        score += self._semgrep_confidence_bonus(semgrep_evidence)
        return min(max(score, 0.0), 1.0)

    def _ast_confidence_bonus(self, node: ast.ClassDef, stories: list[Story]) -> float:
        """Calculate AST-derived confidence bonuses."""
        score = 0.0
        if ast.get_docstring(node):
            score += 0.2
        if stories:
            score += 0.2
        if len(stories) > 2:
            score += 0.2
        documented_stories = sum(1 for story in stories if story.acceptance and len(story.acceptance) > 1)
        if stories and documented_stories > len(stories) / 2:
            score += 0.1
        return score

    def _semgrep_confidence_bonus(self, semgrep_evidence: dict[str, Any] | None) -> float:
        """Calculate confidence adjustments from Semgrep evidence."""
        if not semgrep_evidence:
            return 0.0
        positive_adjustments = {
            "has_api_endpoints": 0.1,
            "has_database_models": 0.15,
            "has_crud_operations": 0.1,
            "has_auth_patterns": 0.1,
            "has_framework_patterns": 0.05,
            "has_test_patterns": 0.1,
        }
        negative_adjustments = {
            "has_anti_patterns": -0.05,
            "has_security_issues": -0.1,
        }
        score = 0.0
        for key, value in positive_adjustments.items():
            if semgrep_evidence.get(key, False):
                score += value
        for key, value in negative_adjustments.items():
            if semgrep_evidence.get(key, False):
                score += value
        return score

    def _humanize_name(self, name: str) -> str:
        """Convert snake_case or PascalCase to human-readable title."""
        # Handle PascalCase
        name = re.sub(r"([A-Z])", r" \1", name).strip()
        # Handle snake_case
        name = name.replace("_", " ").replace("-", " ")
        return name.title()

    _REPO_IMPORT_PREFIXES: tuple[str, ...] = ("src.", "lib.", "app.", "main.", "core.")

    def _resolve_import_to_known_module(self, imported_module: str, modules: dict[str, Path]) -> str | None:
        if imported_module in modules:
            return imported_module
        for known_module in modules:
            if imported_module == known_module.split(".")[-1]:
                return known_module
        return None

    def _maybe_record_external_dependency(self, imported_module: str) -> None:
        if not self.entry_point:
            return
        if any(imported_module.startswith(prefix) for prefix in self._REPO_IMPORT_PREFIXES):
            return
        self.external_dependencies.add(imported_module)

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
                    target = self._resolve_import_to_known_module(imported_module, modules)
                    if target:
                        self.dependency_graph.add_edge(module_name, target)
                    else:
                        self._maybe_record_external_dependency(imported_module)
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
        Extract type hints from function/method signatures (legacy version).
        """
        return self._extract_type_hints_parallel(tree, file_path)

    def _extract_type_hints_parallel(self, tree: ast.AST, file_path: Path) -> dict[str, str]:
        """
        Extract type hints from function/method signatures (thread-safe version).

        Returns:
            Dictionary mapping function names to their return type hints
        """
        type_hints: dict[str, str] = {}

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

        return type_hints

    def _detect_async_patterns(self, tree: ast.AST, file_path: Path) -> list[str]:
        """
        Detect async/await patterns in code (legacy version).
        """
        async_methods = self._detect_async_patterns_parallel(tree, file_path)
        module_name = self._path_to_module_name(file_path)
        if module_name not in self.async_patterns:
            self.async_patterns[module_name] = []
        self.async_patterns[module_name].extend(async_methods)
        return async_methods

    @staticmethod
    def _function_name_holding_ast_subtree(tree: ast.AST, target: ast.AST) -> str | None:
        for parent in ast.walk(tree):
            if not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for child in ast.walk(parent):
                if child is target:
                    return parent.name
        return None

    def _detect_async_patterns_parallel(self, tree: ast.AST, file_path: Path) -> list[str]:
        """
        Detect async/await patterns in code (thread-safe version).

        Returns:
            List of async method/function names
        """
        async_methods: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_methods.append(node.name)
            if not isinstance(node, ast.Await):
                continue
            host = self._function_name_holding_ast_subtree(tree, node)
            if host and host not in async_methods:
                async_methods.append(host)

        return async_methods

    def _apply_commit_hash_to_matching_features(self, feature_num: str, commit_hash: str) -> None:
        for feature in self.features:
            if not re.search(rf"feature[-\s]?{feature_num}", feature.key, re.IGNORECASE):
                continue
            if feature.key not in self.commit_bounds:
                self.commit_bounds[feature.key] = (commit_hash, commit_hash)
            else:
                first_commit, _last_commit = self.commit_bounds[feature.key]
                self.commit_bounds[feature.key] = (first_commit, commit_hash)
            break

    def _process_commit_for_feature_bounds(self, commit: Any) -> None:
        commit_message = commit.message
        if isinstance(commit_message, bytes):
            commit_message = commit_message.decode("utf-8", errors="ignore")
        message = commit_message.lower()
        if "feat" not in message and "feature" not in message:
            return
        feature_match = re.search(r"feature[-\s]?(\d+)", message, re.IGNORECASE)
        if not feature_match:
            return
        self._apply_commit_hash_to_matching_features(feature_match.group(1), commit.hexsha[:8])

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
                    self._process_commit_for_feature_bounds(commit)
                except (OSError, ValueError):
                    # Skip individual commits that fail (corrupted, etc.)
                    continue

        except ImportError:
            # GitPython not available, skip
            pass
        except OSError:
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
        constraints = self._extract_constraints_from_requirements()
        constraints.extend(self._extract_constraints_from_pyproject())
        unique_constraints = self._dedupe_constraints(constraints)
        return unique_constraints or ["Python 3.11+", "Typer for CLI", "Pydantic for data validation"]

    def _extract_constraints_from_requirements(self) -> list[str]:
        """Extract dependency constraints from requirements.txt."""
        requirements_file = self.repo_path / "requirements.txt"
        if not requirements_file.exists():
            return []
        try:
            content = requirements_file.read_text(encoding="utf-8")
        except Exception:
            return []
        constraints: list[str] = []
        for line in content.splitlines():
            self._extend_constraints_from_dependency(line.strip(), constraints)
        return constraints

    def _extract_constraints_from_pyproject(self) -> list[str]:
        """Extract dependency constraints from pyproject.toml."""
        pyproject_file = self.repo_path / "pyproject.toml"
        if not pyproject_file.exists():
            return []
        project_data = self._load_pyproject_project_data(pyproject_file)
        if not project_data:
            return []
        constraints: list[str] = []
        python_req = project_data.get("requires-python")
        if python_req:
            constraints.append(f"Python {python_req}")
        dependencies = project_data.get("dependencies", [])
        for dependency in dependencies if isinstance(dependencies, list) else []:
            self._extend_constraints_from_dependency(str(dependency).strip(), constraints)
        return constraints

    def _load_pyproject_project_data(self, pyproject_file: Path) -> dict[str, Any] | None:
        """Load the [project] table from pyproject.toml using available TOML parsers."""
        loaders = (self._load_pyproject_with_tomli, self._load_pyproject_with_tomllib)
        for loader in loaders:
            data = loader(pyproject_file)
            if data is not None:
                project_data = data.get("project")
                return project_data if isinstance(project_data, dict) else None
        return None

    def _load_pyproject_with_tomli(self, pyproject_file: Path) -> dict[str, Any] | None:
        """Load pyproject data via tomli when available."""
        try:
            import tomli  # type: ignore[import-untyped]
        except ImportError:
            return None
        try:
            return tomli.loads(pyproject_file.read_text(encoding="utf-8"))  # type: ignore[reportUnknownMemberType]
        except Exception:
            return None

    def _load_pyproject_with_tomllib(self, pyproject_file: Path) -> dict[str, Any] | None:
        """Load pyproject data via tomllib when available."""
        try:
            import tomllib  # type: ignore[import-untyped]
        except ImportError:
            return None
        try:
            with pyproject_file.open("rb") as file_obj:
                return tomllib.load(file_obj)
        except Exception:
            return None

    def _extend_constraints_from_dependency(self, dependency: str, constraints: list[str]) -> None:
        """Append recognized constraints from a dependency specifier."""
        if not dependency or dependency.startswith("#"):
            return
        package_name = self._dependency_package_name(dependency)
        package_lower = package_name.lower()
        if package_lower == "python":
            python_constraint = self._python_constraint_from_dependency(dependency)
            if python_constraint:
                constraints.append(python_constraint)
        mapped_constraint = self.DEPENDENCY_CONSTRAINTS.get(package_lower)
        if mapped_constraint:
            constraints.append(mapped_constraint)

    def _dependency_package_name(self, dependency: str) -> str:
        """Extract the package name from a dependency specifier."""
        package = dependency
        for separator in ("==", ">=", ">", "<=", "<", "~=", "["):
            package = package.split(separator)[0]
        return package.strip()

    def _python_constraint_from_dependency(self, dependency: str) -> str | None:
        """Extract a human-readable Python constraint from a dependency line."""
        for operator, suffix in ((">=", "+"), ("==", "")):
            if operator in dependency:
                version = dependency.split(operator, 1)[1].split(",", 1)[0].strip()
                return f"Python {version}{suffix}" if version else None
        return None

    def _dedupe_constraints(self, constraints: list[str]) -> list[str]:
        """Dedupe constraints while preserving order."""
        seen: set[str] = set()
        unique_constraints: list[str] = []
        for constraint in constraints:
            if constraint not in seen:
                seen.add(constraint)
                unique_constraints.append(constraint)
        return unique_constraints

    @beartype
    def _convert_to_gwt_format(self, text: str, method_name: str, class_name: str) -> str:
        """
        DEPRECATED: Convert a text description to Given/When/Then format.

        This method is deprecated. We now use simple text descriptions instead of verbose GWT format.
        Detailed examples are extracted to OpenAPI contracts for Specmatic.

        Args:
            text: Original text description
            method_name: Name of the method
            class_name: Name of the class

        Returns:
            Simple text description (legacy GWT format preserved for backward compatibility)
        """
        # Return simple text instead of GWT format
        # If text already contains GWT keywords, extract the "Then" part
        if "Given" in text and "When" in text and "Then" in text:
            # Extract the "Then" part from existing GWT format
            then_match = re.search(r"Then\s+(.+?)(?:\.|$)", text, re.IGNORECASE)
            if then_match:
                return then_match.group(1).strip()

        # Return simple text description
        return text if text else f"{method_name} works correctly"

    def _get_module_dependencies(self, module_name: str) -> list[str]:
        """Get list of modules that the given module depends on."""
        if module_name not in self.dependency_graph:
            return []

        return list(self.dependency_graph.successors(module_name))
