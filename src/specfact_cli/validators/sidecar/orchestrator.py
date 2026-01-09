"""
Sidecar validation orchestrator.

This module orchestrates the sidecar validation workflow.
"""

from __future__ import annotations

import os
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
from specfact_cli.validators.sidecar.framework_detector import detect_django_settings_module, detect_framework
from specfact_cli.validators.sidecar.frameworks.django import DjangoExtractor
from specfact_cli.validators.sidecar.frameworks.drf import DRFExtractor
from specfact_cli.validators.sidecar.frameworks.fastapi import FastAPIExtractor
from specfact_cli.validators.sidecar.harness_generator import generate_harness
from specfact_cli.validators.sidecar.models import FrameworkType, SidecarConfig
from specfact_cli.validators.sidecar.specmatic_runner import run_specmatic


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
def run_sidecar_validation(config: SidecarConfig, console: Console | None = None) -> dict[str, Any]:
    """
    Run complete sidecar validation workflow.

    Args:
        config: Sidecar configuration
        console: Optional console instance for progress reporting

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
        "specmatic_results": {},
    }

    if use_progress:
        try:
            progress_columns, progress_kwargs = get_progress_config()
            with Progress(*progress_columns, console=display_console, **progress_kwargs) as progress:
                task = progress.add_task("[cyan]Running sidecar validation...", total=6)

                # Phase 1: Detect framework
                progress.update(task, description="[cyan]Detecting framework...")
                if config.framework_type is None:
                    framework_type = detect_framework(config.repo_path)
                    config.framework_type = framework_type
                results["framework_detected"] = config.framework_type
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
                    harness_generated = generate_harness(config.paths.contracts_dir, config.paths.harness_path)
                    results["harness_generated"] = harness_generated
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
                    )
                    results["crosshair_results"]["harness"] = crosshair_result
                progress.advance(task)

                # Phase 6: Run Specmatic
                if config.tools.run_specmatic and config.paths.contracts_dir.exists():
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
                progress.update(task, completed=6, description="[green]✓ Validation complete")
        except Exception:
            # Fall back to non-progress execution if Progress fails
            use_progress = False

    if not use_progress:
        # Non-progress execution path
        if config.framework_type is None:
            framework_type = detect_framework(config.repo_path)
            config.framework_type = framework_type
        results["framework_detected"] = config.framework_type

        extractor = get_extractor(config.framework_type)
        if extractor:
            routes = extractor.extract_routes(config.repo_path)
            schemas = extractor.extract_schemas(config.repo_path, routes)
            results["routes_extracted"] = len(routes)

            if config.paths.contracts_dir.exists():
                populated = populate_contracts(config.paths.contracts_dir, routes, schemas)
                results["contracts_populated"] = populated

            if config.tools.run_crosshair and config.paths.contracts_dir.exists():
                harness_generated = generate_harness(config.paths.contracts_dir, config.paths.harness_path)
                results["harness_generated"] = harness_generated

                if harness_generated:
                    crosshair_result = run_crosshair(
                        config.paths.harness_path,
                        timeout=config.timeouts.crosshair,
                        pythonpath=config.pythonpath,
                        verbose=config.crosshair.verbose,
                        repo_path=config.repo_path,
                    )
                    results["crosshair_results"]["harness"] = crosshair_result

            if config.tools.run_specmatic and config.paths.contracts_dir.exists():
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
def get_extractor(framework_type: FrameworkType) -> DjangoExtractor | FastAPIExtractor | DRFExtractor | None:
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
    # Check for .venv or venv first (like old sidecar-init.sh)
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

    # Set PYTHONPATH based on detected environment (like old sidecar-init.sh)
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
