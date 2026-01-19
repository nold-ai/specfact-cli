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
from icontract import ensure
from rich.console import Console
from rich.progress import Progress

from specfact_cli.runtime import get_configured_console
from specfact_cli.utils.env_manager import detect_env_manager
from specfact_cli.utils.terminal import get_progress_config
from specfact_cli.validators.sidecar.contract_populator import populate_contracts
from specfact_cli.validators.sidecar.crosshair_runner import run_crosshair
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
    except Exception:
        pass
    return True


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

                # Phase 1: Detect framework
                progress.update(task, description="[cyan]Detecting framework...")
                if config.framework_type is None:
                    framework_type = detect_framework(config.repo_path)
                    config.framework_type = framework_type
                results["framework_detected"] = config.framework_type
                progress.advance(task)

                # Phase 1.5: Setup sidecar venv and install dependencies
                progress.update(task, description="[cyan]Setting up sidecar environment...")
                sidecar_venv_path = config.paths.sidecar_venv_path
                if not sidecar_venv_path.is_absolute():
                    sidecar_venv_path = config.repo_path / sidecar_venv_path

                venv_created = create_sidecar_venv(sidecar_venv_path, config.repo_path)
                if venv_created:
                    deps_installed = install_dependencies(sidecar_venv_path, config.repo_path, config.framework_type)
                    results["sidecar_venv_created"] = venv_created
                    results["dependencies_installed"] = deps_installed
                    # Update pythonpath to include sidecar venv
                    if sys.platform == "win32":
                        site_packages = sidecar_venv_path / "Lib" / "site-packages"
                    else:
                        python_dirs = list(sidecar_venv_path.glob("lib/python*/site-packages"))
                        if python_dirs:
                            site_packages = python_dirs[0]
                        else:
                            site_packages = sidecar_venv_path / "lib" / "python3." / "site-packages"

                    if site_packages.exists():
                        if config.pythonpath:
                            config.pythonpath = f"{site_packages}:{config.pythonpath}"
                        else:
                            config.pythonpath = str(site_packages)
                    # Update python_cmd to use venv python
                    if sys.platform == "win32":
                        venv_python = sidecar_venv_path / "Scripts" / "python.exe"
                    else:
                        venv_python = sidecar_venv_path / "bin" / "python"
                    if venv_python.exists():
                        config.python_cmd = str(venv_python)
                else:
                    results["sidecar_venv_created"] = False
                    results["dependencies_installed"] = False
                progress.advance(task)

                # Phase 2: Extract routes
                progress.update(task, description="[cyan]Extracting routes...")
                extractor = get_extractor(config.framework_type)
                routes: list[Any] = []
                schemas: dict[str, dict[str, Any]] = {}
                if extractor:
                    routes = extractor.extract_routes(config.repo_path)
                    schemas = extractor.extract_schemas(config.repo_path, routes)
                    results["routes_extracted"] = len(routes)
                progress.advance(task)

                # Phase 3: Populate contracts
                progress.update(task, description="[cyan]Populating contracts...")
                if extractor and config.paths.contracts_dir.exists():
                    populated = populate_contracts(config.paths.contracts_dir, routes, schemas)
                    results["contracts_populated"] = populated
                progress.advance(task)

                # Phase 4: Generate harness
                progress.update(task, description="[cyan]Generating harness...")
                if config.tools.run_crosshair and config.paths.contracts_dir.exists():
                    harness_generated = generate_harness(
                        config.paths.contracts_dir, config.paths.harness_path, config.repo_path
                    )
                    results["harness_generated"] = harness_generated

                    # If harness was generated, check for unannotated code (for repro integration)
                    if harness_generated and results.get("unannotated_functions"):
                        results["harness_for_unannotated"] = True
                progress.advance(task)

                # Phase 5: Run CrossHair
                if config.tools.run_crosshair and results.get("harness_generated"):
                    progress.update(task, description="[cyan]Running CrossHair analysis...")
                    crosshair_result = run_crosshair(
                        config.paths.harness_path,
                        timeout=config.timeouts.crosshair,
                        pythonpath=config.pythonpath,
                        verbose=config.crosshair.verbose,
                        repo_path=config.repo_path,
                        inputs_path=config.paths.inputs_path if config.crosshair.use_deterministic_inputs else None,
                        per_path_timeout=config.timeouts.crosshair_per_path,
                        per_condition_timeout=config.timeouts.crosshair_per_condition,
                        python_cmd=config.python_cmd,
                    )
                    results["crosshair_results"]["harness"] = crosshair_result

                    # Parse CrossHair output for summary
                    if crosshair_result.get("stdout") or crosshair_result.get("stderr"):
                        summary = parse_crosshair_output(
                            crosshair_result.get("stdout", ""),
                            crosshair_result.get("stderr", ""),
                        )
                        results["crosshair_summary"] = summary

                        # Generate summary file
                        summary_file = generate_summary_file(
                            summary,
                            config.paths.reports_dir,
                        )
                        results["crosshair_summary_file"] = str(summary_file)
                progress.advance(task)

                # Phase 6: Run Specmatic (with auto-skip detection)
                if config.tools.run_specmatic and config.paths.contracts_dir.exists():
                    # Check if service configuration is available
                    has_service = has_service_configuration(config.specmatic, config.app)
                    if not has_service:
                        # Auto-skip Specmatic when no service configuration detected
                        display_console.print(
                            "[yellow]⚠[/yellow] Skipping Specmatic: No service configuration detected "
                            "(use --run-specmatic to override)"
                        )
                        config.tools.run_specmatic = False
                        results["specmatic_skipped"] = True
                        results["specmatic_skip_reason"] = "No service configuration detected"
                    else:
                        progress.update(task, description="[cyan]Running Specmatic validation...")
                        contract_files = list(config.paths.contracts_dir.glob("*.yaml")) + list(
                            config.paths.contracts_dir.glob("*.yml")
                        )
                        for contract_file in contract_files:
                            specmatic_result = run_specmatic(
                                contract_file,
                                base_url=config.specmatic.test_base_url,
                                timeout=config.timeouts.specmatic,
                                repo_path=config.repo_path,
                            )
                            results["specmatic_results"][contract_file.name] = specmatic_result
                progress.update(task, completed=7, description="[green]✓ Validation complete")
        except Exception:
            # Fall back to non-progress execution if Progress fails
            use_progress = False

    if not use_progress:
        # Non-progress execution path
        if config.framework_type is None:
            framework_type = detect_framework(config.repo_path)
            config.framework_type = framework_type
        results["framework_detected"] = config.framework_type

        # Setup sidecar venv and install dependencies
        sidecar_venv_path = config.paths.sidecar_venv_path
        if not sidecar_venv_path.is_absolute():
            sidecar_venv_path = config.repo_path / sidecar_venv_path

        venv_created = create_sidecar_venv(sidecar_venv_path, config.repo_path)
        if venv_created:
            deps_installed = install_dependencies(sidecar_venv_path, config.repo_path, config.framework_type)
            results["sidecar_venv_created"] = venv_created
            results["dependencies_installed"] = deps_installed
            # Update pythonpath to include sidecar venv
            if sys.platform == "win32":
                site_packages = sidecar_venv_path / "Lib" / "site-packages"
            else:
                python_dirs = list(sidecar_venv_path.glob("lib/python*/site-packages"))
                if python_dirs:
                    site_packages = python_dirs[0]
                else:
                    site_packages = sidecar_venv_path / "lib" / "python3." / "site-packages"

            if site_packages.exists():
                if config.pythonpath:
                    config.pythonpath = f"{site_packages}:{config.pythonpath}"
                else:
                    config.pythonpath = str(site_packages)
            # Update python_cmd to use venv python
            if sys.platform == "win32":
                venv_python = sidecar_venv_path / "Scripts" / "python.exe"
            else:
                venv_python = sidecar_venv_path / "bin" / "python"
            if venv_python.exists():
                config.python_cmd = str(venv_python)
        else:
            results["sidecar_venv_created"] = False
            results["dependencies_installed"] = False

        extractor = get_extractor(config.framework_type)
        if extractor:
            routes = extractor.extract_routes(config.repo_path)
            schemas = extractor.extract_schemas(config.repo_path, routes)
            results["routes_extracted"] = len(routes)

            if config.paths.contracts_dir.exists():
                populated = populate_contracts(config.paths.contracts_dir, routes, schemas)
                results["contracts_populated"] = populated

            if config.tools.run_crosshair and config.paths.contracts_dir.exists():
                harness_generated = generate_harness(
                    config.paths.contracts_dir, config.paths.harness_path, config.repo_path
                )
                results["harness_generated"] = harness_generated

                if harness_generated:
                    crosshair_result = run_crosshair(
                        config.paths.harness_path,
                        timeout=config.timeouts.crosshair,
                        pythonpath=config.pythonpath,
                        verbose=config.crosshair.verbose,
                        repo_path=config.repo_path,
                        inputs_path=config.paths.inputs_path if config.crosshair.use_deterministic_inputs else None,
                        per_path_timeout=config.timeouts.crosshair_per_path,
                        per_condition_timeout=config.timeouts.crosshair_per_condition,
                        python_cmd=config.python_cmd,
                    )
                    results["crosshair_results"]["harness"] = crosshair_result

                    # Parse CrossHair output for summary
                    if crosshair_result.get("stdout") or crosshair_result.get("stderr"):
                        summary = parse_crosshair_output(
                            crosshair_result.get("stdout", ""),
                            crosshair_result.get("stderr", ""),
                        )
                        results["crosshair_summary"] = summary

                        # Generate summary file
                        summary_file = generate_summary_file(
                            summary,
                            config.paths.reports_dir,
                        )
                        results["crosshair_summary_file"] = str(summary_file)

            if config.tools.run_specmatic and config.paths.contracts_dir.exists():
                # Check if service configuration is available
                has_service = has_service_configuration(config.specmatic, config.app)
                if not has_service:
                    # Auto-skip Specmatic when no service configuration detected
                    display_console.print(
                        "[yellow]⚠[/yellow] Skipping Specmatic: No service configuration detected "
                        "(use --run-specmatic to override)"
                    )
                    config.tools.run_specmatic = False
                    results["specmatic_skipped"] = True
                    results["specmatic_skip_reason"] = "No service configuration detected"
                else:
                    contract_files = list(config.paths.contracts_dir.glob("*.yaml")) + list(
                        config.paths.contracts_dir.glob("*.yml")
                    )
                    for contract_file in contract_files:
                        specmatic_result = run_specmatic(
                            contract_file,
                            base_url=config.specmatic.test_base_url,
                            timeout=config.timeouts.specmatic,
                            repo_path=config.repo_path,
                        )
                        results["specmatic_results"][contract_file.name] = specmatic_result

    return results


@beartype
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

    # Set Python command based on detected environment
    # Check for .venv or venv first
    venv_python = None
    if (config.repo_path / ".venv" / "bin" / "python").exists():
        venv_python = str(config.repo_path / ".venv" / "bin" / "python")
    elif (config.repo_path / "venv" / "bin" / "python").exists():
        venv_python = str(config.repo_path / "venv" / "bin" / "python")

    if venv_python:
        config.python_cmd = venv_python
    elif env_info.command_prefix:
        # For hatch/poetry/uv, use their Python
        # The command prefix will be used when building tool commands
        config.python_cmd = "python3"  # Will be prefixed with env manager

    # Set PYTHONPATH based on detected environment
    pythonpath_parts = []

    # Add venv site-packages if venv exists
    if venv_python:
        venv_dir = Path(venv_python).parent.parent
        # Find actual Python version directory
        python_version_dirs = list(venv_dir.glob("lib/python*/site-packages"))
        if python_version_dirs:
            pythonpath_parts.append(str(python_version_dirs[0]))

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
