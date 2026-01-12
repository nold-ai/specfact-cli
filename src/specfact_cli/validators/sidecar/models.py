"""
Pydantic models for sidecar validation configuration.

This module defines configuration models for sidecar validation workflow,
including framework detection, tool configuration, and path settings.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class FrameworkType(str, Enum):
    """Supported framework types for sidecar validation."""

    DJANGO = "django"
    FASTAPI = "fastapi"
    DRF = "drf"
    FLASK = "flask"
    PURE_PYTHON = "pure-python"
    UNKNOWN = "unknown"


class ToolConfig(BaseModel):
    """Configuration for validation tools."""

    run_crosshair: bool = Field(default=True, description="Run CrossHair symbolic execution")
    run_specmatic: bool = Field(default=True, description="Run Specmatic contract testing")
    run_semgrep: bool = Field(default=False, description="Run Semgrep static analysis")
    run_basedpyright: bool = Field(default=False, description="Run basedpyright type checking")


class PathConfig(BaseModel):
    """Path configuration for sidecar workspace."""

    repo_path: Path = Field(..., description="Path to repository root")
    contracts_dir: Path = Field(..., description="Path to contracts directory")
    harness_path: Path = Field(default=Path("harness_contracts.py"), description="Path to harness file")
    inputs_path: Path = Field(default=Path("inputs.json"), description="Path to test inputs JSON file")
    bindings_path: Path = Field(default=Path("bindings.yaml"), description="Path to bindings YAML file")
    reports_dir: Path = Field(..., description="Path to reports directory")
    source_dirs: list[Path] = Field(default_factory=list, description="Source directories to analyze")
    sidecar_venv_path: Path = Field(default=Path(".specfact/venv"), description="Path to sidecar venv directory")


class TimeoutConfig(BaseModel):
    """Timeout configuration for validation tools."""

    crosshair: int = Field(default=120, description="CrossHair overall timeout in seconds")
    specmatic: int = Field(default=60, description="Specmatic timeout in seconds")
    semgrep: int = Field(default=60, description="Semgrep timeout in seconds")
    basedpyright: int = Field(default=60, description="basedpyright timeout in seconds")
    crosshair_per_path: int | None = Field(
        default=10, description="CrossHair per-path timeout in seconds (prevents single route from blocking)"
    )
    crosshair_per_condition: int | None = Field(default=5, description="CrossHair per-condition timeout in seconds")

    @classmethod
    @beartype
    def safe_defaults_for_repro(cls) -> TimeoutConfig:
        """
        Create TimeoutConfig with safe defaults for repro sidecar mode.

        Returns:
            TimeoutConfig with conservative timeouts to prevent excessive execution time
        """
        return cls(
            crosshair=30,  # Shorter timeout for repro mode
            specmatic=30,
            semgrep=30,
            basedpyright=30,
            crosshair_per_path=5,  # Per-path timeout to prevent long-running paths
            crosshair_per_condition=2,  # Per-condition timeout
        )


class SpecmaticConfig(BaseModel):
    """Configuration for Specmatic execution."""

    cmd: str | None = Field(default=None, description="Specmatic command (CLI, JAR, npm, Python module)")
    jar: str | None = Field(default=None, description="Path to Specmatic JAR file")
    config: str | None = Field(default=None, description="Path to Specmatic config file")
    test_base_url: str | None = Field(default=None, description="Base URL for Specmatic tests")
    host: str | None = Field(default=None, description="Specmatic host")
    port: int | None = Field(default=None, description="Specmatic port")
    timeout: int | None = Field(default=None, description="Specmatic timeout")
    auto_stub: bool = Field(default=True, description="Auto-start Specmatic stub server")
    stub_host: str = Field(default="127.0.0.1", description="Stub server host")
    stub_port: int = Field(default=19000, description="Stub server port")
    stub_wait: int = Field(default=15, description="Stub server wait time in seconds")


class AppConfig(BaseModel):
    """Configuration for application server (for Specmatic)."""

    cmd: str | None = Field(default=None, description="Command to start application server")
    host: str = Field(default="127.0.0.1", description="Application host")
    port: int | None = Field(default=None, description="Application port")
    wait: int = Field(default=15, description="Application wait time in seconds")
    log: str | None = Field(default=None, description="Application log file path")


class CrossHairConfig(BaseModel):
    """Configuration for CrossHair execution."""

    verbose: bool = Field(default=False, description="Verbose output")
    report_all: bool = Field(default=False, description="Report all findings")
    report_verbose: bool = Field(default=False, description="Verbose reporting")
    max_uninteresting_iterations: int | None = Field(default=None, description="Maximum uninteresting iterations")
    extra_plugin: str | None = Field(default=None, description="Extra CrossHair plugin")
    use_deterministic_inputs: bool = Field(default=False, description="Use deterministic inputs from inputs.json")
    safe_defaults: bool = Field(default=True, description="Use safe defaults for timeouts and limits")


class SidecarConfig(BaseModel):
    """Main configuration model for sidecar validation."""

    bundle_name: str = Field(..., description="Project bundle name")
    repo_path: Path = Field(..., description="Path to repository root")
    framework_type: FrameworkType | None = Field(default=None, description="Detected framework type")
    tools: ToolConfig = Field(default_factory=ToolConfig, description="Tool configuration")
    paths: PathConfig = Field(..., description="Path configuration")
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig, description="Timeout configuration")
    specmatic: SpecmaticConfig = Field(default_factory=SpecmaticConfig, description="Specmatic configuration")
    app: AppConfig = Field(default_factory=AppConfig, description="Application configuration")
    crosshair: CrossHairConfig = Field(default_factory=CrossHairConfig, description="CrossHair configuration")
    python_cmd: str = Field(default="python3", description="Python command to use")
    pythonpath: str | None = Field(default=None, description="PYTHONPATH for execution")
    django_settings_module: str | None = Field(default=None, description="Django settings module")

    @classmethod
    @beartype
    @require(lambda bundle_name: bundle_name and len(bundle_name.strip()) > 0, "Bundle name must be non-empty")
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, SidecarConfig), "Must return SidecarConfig")
    def create(
        cls,
        bundle_name: str,
        repo_path: Path,
        contracts_dir: Path | None = None,
        reports_dir: Path | None = None,
    ) -> SidecarConfig:
        """
        Create SidecarConfig with default paths.

        Args:
            bundle_name: Project bundle name
            repo_path: Path to repository root
            contracts_dir: Optional contracts directory (defaults to .specfact/projects/{bundle}/contracts)
            reports_dir: Optional reports directory (defaults to .specfact/projects/{bundle}/reports/sidecar)

        Returns:
            SidecarConfig instance with default paths
        """
        if contracts_dir is None:
            contracts_dir = repo_path / ".specfact" / "projects" / bundle_name / "contracts"
        if reports_dir is None:
            reports_dir = repo_path / ".specfact" / "projects" / bundle_name / "reports" / "sidecar"

        # Detect source directories
        source_dirs: list[Path] = []
        if (repo_path / "src").exists():
            source_dirs.append(repo_path / "src")
        elif (repo_path / "lib").exists():
            source_dirs.append(repo_path / "lib")
        elif (repo_path / "backend" / "app").exists():
            source_dirs.append(repo_path / "backend" / "app")
        else:
            source_dirs.append(repo_path)

        # Sidecar venv path relative to repo_path
        sidecar_venv_path = repo_path / ".specfact" / "venv"

        # Harness path should be in the same directory as contracts
        harness_path = contracts_dir.parent / "harness" / "harness_contracts.py"

        paths = PathConfig(
            repo_path=repo_path,
            contracts_dir=contracts_dir,
            reports_dir=reports_dir,
            harness_path=harness_path,
            source_dirs=source_dirs,
            sidecar_venv_path=sidecar_venv_path,
        )

        return cls(
            bundle_name=bundle_name,
            repo_path=repo_path,
            paths=paths,
        )
