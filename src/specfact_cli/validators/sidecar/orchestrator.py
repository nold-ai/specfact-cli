"""
Sidecar validation orchestrator.

This module orchestrates the sidecar validation workflow.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import Progress

from specfact_cli.runtime import get_configured_console
from specfact_cli.utils.env_manager import detect_env_manager
from specfact_cli.utils.terminal import get_progress_config
from specfact_cli.validators.sidecar.contract_populator import populate_contracts
from specfact_cli.validators.sidecar.crosshair_runner import CrosshairRunOptions, run_crosshair
from specfact_cli.validators.sidecar.crosshair_summary import (
    generate_summary_file,
    parse_crosshair_output,
)
from specfact_cli.validators.sidecar.dependency_installer import (
    create_sidecar_venv,
    install_dependencies,
)
from specfact_cli.validators.sidecar.framework_detector import detect_django_settings_module, detect_framework
from specfact_cli.validators.sidecar.frameworks.django import DjangoExtractor
from specfact_cli.validators.sidecar.frameworks.drf import DRFExtractor
from specfact_cli.validators.sidecar.frameworks.fastapi import FastAPIExtractor
from specfact_cli.validators.sidecar.frameworks.flask import FlaskExtractor
from specfact_cli.validators.sidecar.harness_generator import generate_harness
from specfact_cli.validators.sidecar.models import FrameworkType, SidecarConfig
from specfact_cli.validators.sidecar.specmatic_runner import has_service_configuration, run_specmatic


def _is_test_mode() -> bool:
    """Check if running in test mode."""
    return os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None


def _should_use_progress(console: Console) -> bool:
    """Check if progress display should be used."""
    if _is_test_mode():
        return False
    try:
        if hasattr(console, "_live") and console._live is not None:
            return False
    except AttributeError:
        pass
    return True


def _setup_sidecar_venv(config: SidecarConfig, results: dict[str, Any]) -> None:
    """
    Create sidecar virtual environment, install dependencies, and update config paths in-place.

    Args:
        config: Sidecar configuration (mutated: pythonpath and python_cmd updated)
        results: Results dict to record venv creation outcome (mutated in-place)
    """
    sidecar_venv_path = config.paths.sidecar_venv_path
    if not sidecar_venv_path.is_absolute():
        sidecar_venv_path = config.repo_path / sidecar_venv_path

    venv_created = create_sidecar_venv(sidecar_venv_path, config.repo_path)
    results["sidecar_venv_created"] = venv_created
    if not venv_created:
        results["dependencies_installed"] = False
        return

    deps_installed = install_dependencies(sidecar_venv_path, config.repo_path, config.framework_type)
    results["dependencies_installed"] = deps_installed

    if sys.platform == "win32":
        site_packages = sidecar_venv_path / "Lib" / "site-packages"
    else:
        python_dirs = list(sidecar_venv_path.glob("lib/python*/site-packages"))
        site_packages = python_dirs[0] if python_dirs else sidecar_venv_path / "lib" / "python3." / "site-packages"

    if site_packages.exists():
        config.pythonpath = f"{site_packages}:{config.pythonpath}" if config.pythonpath else str(site_packages)

    venv_python = (
        sidecar_venv_path / "Scripts" / "python.exe"
        if sys.platform == "win32"
        else sidecar_venv_path / "bin" / "python"
    )
    if venv_python.exists():
        config.python_cmd = str(venv_python)


def _run_crosshair_phase(config: SidecarConfig, results: dict[str, Any]) -> None:
    """
    Run the CrossHair harness generation and analysis phases, updating results in-place.

    Args:
        config: Sidecar configuration
        results: Results dict to populate (mutated in-place)
    """
    if not (config.tools.run_crosshair and config.paths.contracts_dir.exists()):
        return
    harness_generated = generate_harness(config.paths.contracts_dir, config.paths.harness_path, config.repo_path)
    results["harness_generated"] = harness_generated
    if harness_generated and results.get("unannotated_functions"):
        results["harness_for_unannotated"] = True
    if not harness_generated:
        return
    crosshair_result = run_crosshair(
        config.paths.harness_path,
        CrosshairRunOptions(
            timeout=config.timeouts.crosshair,
            pythonpath=config.pythonpath,
            verbose=config.crosshair.verbose,
            repo_path=config.repo_path,
            inputs_path=config.paths.inputs_path if config.crosshair.use_deterministic_inputs else None,
            per_path_timeout=config.timeouts.crosshair_per_path,
            per_condition_timeout=config.timeouts.crosshair_per_condition,
            python_cmd=config.python_cmd,
        ),
    )
    results["crosshair_results"]["harness"] = crosshair_result
    if crosshair_result.get("stdout") or crosshair_result.get("stderr"):
        summary = parse_crosshair_output(
            crosshair_result.get("stdout", ""),
            crosshair_result.get("stderr", ""),
        )
        results["crosshair_summary"] = summary
        results["crosshair_summary_file"] = str(generate_summary_file(summary, config.paths.reports_dir))


def _run_specmatic_phase(config: SidecarConfig, results: dict[str, Any], display_console: Console) -> None:
    """
    Run the Specmatic validation phase, skipping automatically if no service is configured.

    Args:
        config: Sidecar configuration (run_specmatic flag may be mutated)
        results: Results dict to populate (mutated in-place)
        display_console: Console for skip-warning output
    """
    if not (config.tools.run_specmatic and config.paths.contracts_dir.exists()):
        return
    if not has_service_configuration(config.specmatic, config.app):
        display_console.print(
            "[yellow]⚠[/yellow] Skipping Specmatic: No service configuration detected (use --run-specmatic to override)"
        )
        config.tools.run_specmatic = False
        results["specmatic_skipped"] = True
        results["specmatic_skip_reason"] = "No service configuration detected"
        return
    contract_files = list(config.paths.contracts_dir.glob("*.yaml")) + list(config.paths.contracts_dir.glob("*.yml"))
    for contract_file in contract_files:
        results["specmatic_results"][contract_file.name] = run_specmatic(
            contract_file,
            base_url=config.specmatic.test_base_url,
            timeout=config.timeouts.specmatic,
            repo_path=config.repo_path,
        )


def _run_all_phases(config: SidecarConfig, results: dict[str, Any], display_console: Console) -> None:
    """
    Execute all six sidecar validation phases, updating results and config in-place.

    Args:
        config: Sidecar configuration (mutated during venv setup)
        results: Results dict populated with phase outcomes
        display_console: Console for user-facing messages
    """
    if config.framework_type is None:
        config.framework_type = detect_framework(config.repo_path)
    results["framework_detected"] = config.framework_type

    _setup_sidecar_venv(config, results)

    extractor = get_extractor(config.framework_type)
    routes: list[Any] = []
    schemas: dict[str, dict[str, Any]] = {}
    if extractor:
        routes = extractor.extract_routes(config.repo_path)
        schemas = extractor.extract_schemas(config.repo_path, routes)
        results["routes_extracted"] = len(routes)
        if config.paths.contracts_dir.exists():
            results["contracts_populated"] = populate_contracts(config.paths.contracts_dir, routes, schemas)

    _run_crosshair_phase(config, results)
    _run_specmatic_phase(config, results, display_console)


@ensure(lambda result: isinstance(result, dict), "Must return dict")
def run_sidecar_validation(
    config: SidecarConfig,
    console: Console | None = None,
    unannotated_functions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Run complete sidecar validation workflow.

    Args:
        config: Sidecar configuration
        console: Optional console instance for progress reporting
        unannotated_functions: Optional list of unannotated functions detected (for repro integration)

    Returns:
        Dictionary with validation results
    """
    display_console = console if console is not None else get_configured_console()
    use_progress = _should_use_progress(display_console)

    results: dict[str, Any] = {
        "framework_detected": None,
        "routes_extracted": 0,
        "contracts_populated": 0,
        "harness_generated": False,
        "crosshair_results": {},
        "crosshair_summary": None,
        "specmatic_results": {},
        "unannotated_functions": unannotated_functions,
    }

    if use_progress:
        try:
            progress_columns, progress_kwargs = get_progress_config()
            with Progress(*progress_columns, console=display_console, **progress_kwargs) as progress:
                task = progress.add_task("[cyan]Running sidecar validation...", total=7)

                def _advance(description: str) -> None:
                    progress.update(task, description=description)
                    progress.advance(task)

                _advance("[cyan]Detecting framework...")
                if config.framework_type is None:
                    config.framework_type = detect_framework(config.repo_path)
                results["framework_detected"] = config.framework_type

                _advance("[cyan]Setting up sidecar environment...")
                _setup_sidecar_venv(config, results)

                _advance("[cyan]Extracting routes...")
                extractor = get_extractor(config.framework_type)
                routes: list[Any] = []
                schemas: dict[str, dict[str, Any]] = {}
                if extractor:
                    routes = extractor.extract_routes(config.repo_path)
                    schemas = extractor.extract_schemas(config.repo_path, routes)
                    results["routes_extracted"] = len(routes)

                _advance("[cyan]Populating contracts...")
                if extractor and config.paths.contracts_dir.exists():
                    results["contracts_populated"] = populate_contracts(config.paths.contracts_dir, routes, schemas)

                _advance("[cyan]Generating harness...")
                _run_crosshair_phase(config, results)

                progress.update(task, description="[cyan]Running CrossHair analysis...")
                progress.advance(task)

                _run_specmatic_phase(config, results, display_console)
                progress.update(task, completed=7, description="[green]✓ Validation complete")
            return results
        except Exception:
            use_progress = False

    if not use_progress:
        _run_all_phases(config, results, display_console)

    return results


@beartype
@require(lambda framework_type: isinstance(framework_type, FrameworkType), "framework_type must be a FrameworkType")
def get_extractor(
    framework_type: FrameworkType,
) -> DjangoExtractor | FastAPIExtractor | DRFExtractor | FlaskExtractor | None:
    """
    Get framework extractor for framework type.

    Args:
        framework_type: Framework type

    Returns:
        Framework extractor instance or None
    """
    if framework_type == FrameworkType.DJANGO:
        return DjangoExtractor()
    if framework_type == FrameworkType.FASTAPI:
        return FastAPIExtractor()
    if framework_type == FrameworkType.DRF:
        return DRFExtractor()
    if framework_type == FrameworkType.FLASK:
        return FlaskExtractor()
    return None


def _detect_repo_venv_python(repo_path: Path) -> str | None:
    for rel in (".venv/bin/python", "venv/bin/python"):
        candidate = repo_path / rel
        if candidate.exists():
            return str(candidate)
    return None


def _prepend_venv_site_packages(pythonpath_parts: list[str], venv_python: str) -> None:
    venv_dir = Path(venv_python).parent.parent
    site_dirs = list(venv_dir.glob("lib/python*/site-packages"))
    if site_dirs:
        pythonpath_parts.append(str(site_dirs[0]))


@ensure(lambda result: isinstance(result, bool), "Must return bool")
def initialize_sidecar_workspace(config: SidecarConfig) -> bool:
    """
    Initialize sidecar workspace.

    Args:
        config: Sidecar configuration

    Returns:
        True if initialization was successful
    """
    # Create reports directory
    config.paths.reports_dir.mkdir(parents=True, exist_ok=True)

    # Create contracts directory
    config.paths.contracts_dir.mkdir(parents=True, exist_ok=True)

    # Create initial contract file if it doesn't exist
    initial_contract = config.paths.contracts_dir / "api.yaml"
    if not initial_contract.exists():
        initial_contract.write_text("openapi: 3.0.0\ninfo:\n  title: API Contract\n  version: 1.0.0\npaths: {}\n")

    # Detect environment manager and set Python command/path
    env_info = detect_env_manager(config.repo_path)

    venv_python = _detect_repo_venv_python(config.repo_path)

    if venv_python:
        config.python_cmd = venv_python
    elif env_info.command_prefix:
        # For hatch/poetry/uv, use their Python
        # The command prefix will be used when building tool commands
        config.python_cmd = "python3"  # Will be prefixed with env manager

    # Set PYTHONPATH based on detected environment
    pythonpath_parts: list[str] = []

    if venv_python:
        _prepend_venv_site_packages(pythonpath_parts, venv_python)

    # Add source directories
    for source_dir in config.paths.source_dirs:
        pythonpath_parts.append(str(source_dir))

    # Add repo root
    pythonpath_parts.append(str(config.repo_path))

    if pythonpath_parts:
        config.pythonpath = ":".join(pythonpath_parts)

    # Detect framework if not set
    if config.framework_type is None:
        config.framework_type = detect_framework(config.repo_path)

    # Detect Django settings module if Django
    if config.framework_type == FrameworkType.DJANGO:
        django_settings = detect_django_settings_module(config.repo_path)
        if django_settings:
            config.django_settings_module = django_settings

    return True
