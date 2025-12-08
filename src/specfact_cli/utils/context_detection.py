"""
Context detection system for auto-detecting project state.

This module provides utilities for detecting project context including:
- Existing OpenAPI/AsyncAPI specs
- Existing plan bundles
- Language/framework detection
- Specmatic configuration
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.utils.structure import SpecFactStructure


@dataclass
class ProjectContext:
    """Detected project context information."""

    repo_path: Path
    has_plan: bool = False
    has_config: bool = False
    spec_files: list[Path] = field(default_factory=list)
    openapi_specs: list[Path] = field(default_factory=list)
    asyncapi_specs: list[Path] = field(default_factory=list)
    language: str | None = None
    framework: str | None = None
    has_specmatic_config: bool = False
    specmatic_config_path: Path | None = None
    project_bundles: list[str] = field(default_factory=list)
    contract_coverage: float = 0.0
    last_enforcement: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "repo_path": str(self.repo_path),
            "has_plan": self.has_plan,
            "has_config": self.has_config,
            "spec_files": [str(p) for p in self.spec_files],
            "openapi_specs": [str(p) for p in self.openapi_specs],
            "asyncapi_specs": [str(p) for p in self.asyncapi_specs],
            "language": self.language,
            "framework": self.framework,
            "has_specmatic_config": self.has_specmatic_config,
            "specmatic_config_path": str(self.specmatic_config_path) if self.specmatic_config_path else None,
            "project_bundles": self.project_bundles,
            "contract_coverage": self.contract_coverage,
            "last_enforcement": self.last_enforcement,
        }


@beartype
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(
    lambda repo_path: isinstance(repo_path, Path) and bool(repo_path.exists()),
    "Repository path must exist",
)
@require(
    lambda repo_path: isinstance(repo_path, Path) and bool(repo_path.is_dir()),
    "Repository path must be a directory",
)
@ensure(lambda result: isinstance(result, ProjectContext), "Must return ProjectContext")
def detect_project_context(repo_path: Path | None = None) -> ProjectContext:
    """
    Auto-detect project type, specs, and configuration.

    Detects:
    - Existing OpenAPI/AsyncAPI specs
    - Existing plan bundles
    - Language/framework
    - Specmatic configuration

    Args:
        repo_path: Path to repository root (default: current directory)

    Returns:
        ProjectContext with detected information
    """
    repo_path = Path.cwd() if repo_path is None else repo_path.resolve()

    context = ProjectContext(repo_path=repo_path)

    # Detect SpecFact configuration
    specfact_config = repo_path / SpecFactStructure.CONFIG_YAML
    context.has_config = specfact_config.exists()

    # Detect project bundles
    projects_dir = repo_path / SpecFactStructure.PROJECTS
    if projects_dir.exists():
        for bundle_dir in projects_dir.iterdir():
            if bundle_dir.is_dir():
                manifest = bundle_dir / "bundle.manifest.yaml"
                if manifest.exists():
                    context.project_bundles.append(bundle_dir.name)
        context.has_plan = len(context.project_bundles) > 0

    # Detect OpenAPI/AsyncAPI specs
    _detect_api_specs(repo_path, context)

    # Detect language/framework
    _detect_language_framework(repo_path, context)

    # Detect Specmatic configuration
    _detect_specmatic_config(repo_path, context)

    return context


@beartype
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda context: isinstance(context, ProjectContext), "Context must be ProjectContext")
@ensure(lambda result: result is None, "Must return None")
def _detect_api_specs(repo_path: Path, context: ProjectContext) -> None:
    """Detect OpenAPI and AsyncAPI specification files."""
    # Common spec file patterns
    spec_patterns = [
        "**/openapi.yaml",
        "**/openapi.yml",
        "**/openapi.json",
        "**/swagger.yaml",
        "**/swagger.yml",
        "**/swagger.json",
        "**/asyncapi.yaml",
        "**/asyncapi.yml",
        "**/asyncapi.json",
    ]

    for pattern in spec_patterns:
        for spec_file in repo_path.glob(pattern):
            # Skip node_modules, .git, etc.
            if any(part in spec_file.parts for part in (".git", "node_modules", "__pycache__", ".venv", "venv")):
                continue

            context.spec_files.append(spec_file)

            # Categorize by type
            name_lower = spec_file.name.lower()
            if "openapi" in name_lower or "swagger" in name_lower:
                context.openapi_specs.append(spec_file)
            elif "asyncapi" in name_lower:
                context.asyncapi_specs.append(spec_file)


@beartype
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda context: isinstance(context, ProjectContext), "Context must be ProjectContext")
@ensure(lambda result: result is None, "Must return None")
def _detect_language_framework(repo_path: Path, context: ProjectContext) -> None:
    """Detect programming language and framework."""
    # Python detection
    if (
        (repo_path / "pyproject.toml").exists()
        or (repo_path / "setup.py").exists()
        or (repo_path / "requirements.txt").exists()
    ):
        context.language = "python"
        # Detect Python framework
        if (repo_path / "pyproject.toml").exists():
            try:
                # Try tomllib (Python 3.11+)
                try:
                    import tomllib  # type: ignore[import-untyped]

                    with open(repo_path / "pyproject.toml", "rb") as f:
                        pyproject = tomllib.load(f)
                except ImportError:
                    # Fallback to tomli for older Python versions
                    try:
                        import tomli  # type: ignore[import-untyped]

                        with open(repo_path / "pyproject.toml", "rb") as f:
                            pyproject = tomli.load(f)
                    except ImportError:
                        # Neither available, skip framework detection
                        pyproject = {}

                if pyproject:
                    deps = pyproject.get("project", {}).get("dependencies", [])
                    optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})
                    all_deps = deps + [dep for deps_list in optional_deps.values() for dep in deps_list]

                    if any("django" in dep.lower() for dep in all_deps):
                        context.framework = "django"
                    elif any("flask" in dep.lower() for dep in all_deps):
                        context.framework = "flask"
                    elif any("fastapi" in dep.lower() for dep in all_deps):
                        context.framework = "fastapi"
            except Exception:
                pass

        # Check requirements.txt
        if context.framework is None and (repo_path / "requirements.txt").exists():
            try:
                with open(repo_path / "requirements.txt") as f:
                    content = f.read().lower()
                    if "django" in content:
                        context.framework = "django"
                    elif "flask" in content:
                        context.framework = "flask"
                    elif "fastapi" in content:
                        context.framework = "fastapi"
            except Exception:
                pass

    # JavaScript/TypeScript detection
    elif (repo_path / "package.json").exists():
        context.language = "javascript"
        try:
            with open(repo_path / "package.json") as f:
                package_json = json.load(f)
                deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}

                if "express" in deps:
                    context.framework = "express"
                elif "next" in deps:
                    context.framework = "next"
                elif "react" in deps:
                    context.framework = "react"
                elif "vue" in deps:
                    context.framework = "vue"
        except Exception:
            pass

    # Java detection
    elif (repo_path / "pom.xml").exists() or (repo_path / "build.gradle").exists():
        context.language = "java"
        if (repo_path / "pom.xml").exists():
            context.framework = "maven"
        elif (repo_path / "build.gradle").exists():
            context.framework = "gradle"

    # Go detection
    elif (repo_path / "go.mod").exists() or (repo_path / "go.sum").exists():
        context.language = "go"


@beartype
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(lambda context: isinstance(context, ProjectContext), "Context must be ProjectContext")
@ensure(lambda result: result is None, "Must return None")
def _detect_specmatic_config(repo_path: Path, context: ProjectContext) -> None:
    """Detect Specmatic configuration."""
    # Check for .specmatic directory
    specmatic_dir = repo_path / ".specmatic"
    if specmatic_dir.exists() and specmatic_dir.is_dir():
        context.has_specmatic_config = True
        context.specmatic_config_path = specmatic_dir

    # Check for specmatic.json
    specmatic_json = repo_path / "specmatic.json"
    if specmatic_json.exists():
        context.has_specmatic_config = True
        context.specmatic_config_path = specmatic_json

    # Check for specmatic.yaml/yml
    for specmatic_yaml in [repo_path / "specmatic.yaml", repo_path / "specmatic.yml"]:
        if specmatic_yaml.exists():
            context.has_specmatic_config = True
            context.specmatic_config_path = specmatic_yaml
            break
