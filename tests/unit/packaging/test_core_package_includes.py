"""Tests for core-only package includes in pyproject.toml / setup.py (module-migration-03)."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement


REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT = REPO_ROOT / "pyproject.toml"
SETUP_PY = REPO_ROOT / "setup.py"
INIT_PY = REPO_ROOT / "src" / "specfact_cli" / "__init__.py"

CORE_MODULE_NAMES = {"init", "module_registry", "upgrade"}
DELETED_17_NAMES = {
    "project",
    "plan",
    "import_cmd",
    "sync",
    "migrate",
    "backlog",
    "policy_engine",
    "analyze",
    "drift",
    "validate",
    "repro",
    "contract",
    "spec",
    "sdd",
    "generate",
    "enforce",
    "patch_mode",
}


def _project_version() -> str:
    """Return the canonical project version from package metadata."""
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    version = project["version"]
    assert isinstance(version, str)
    return version


def _project_dependencies() -> set[str]:
    """Return the declared core package dependencies."""
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    dependencies = project["dependencies"]
    assert isinstance(dependencies, list)
    return set(dependencies)


def test_pyproject_wheel_packages_exist() -> None:
    """pyproject.toml [tool.hatch.build.targets.wheel] must define packages."""
    assert PYPROJECT.exists()
    raw = PYPROJECT.read_text(encoding="utf-8")
    assert "packages" in raw
    assert "specfact_cli" in raw


def test_pyproject_wheel_explicitly_maps_src_package_root() -> None:
    """Wheel build config must explicitly map the src package root for specfact_cli."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    wheel = data["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert wheel.get("only-include") == ["src/specfact_cli"]
    assert wheel.get("sources") == ["src"]


def test_project_scripts_target_cli_main() -> None:
    """Both console scripts must resolve to the importable CLI entrypoint."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    scripts = data["project"]["scripts"]
    assert scripts["specfact"] == "specfact_cli.cli:cli_main"
    assert scripts["specfact-cli"] == "specfact_cli.cli:cli_main"


def test_pyproject_force_include_does_not_reference_deleted_modules() -> None:
    """force-include must not reference the 17 deleted module dirs (exact key match)."""
    raw = PYPROJECT.read_text(encoding="utf-8")
    assert '"modules/auth"' not in raw
    for name in DELETED_17_NAMES:
        if re.search(r'"modules/' + re.escape(name) + r'"\s*=', raw):
            pytest.fail(f"pyproject force-include must not reference deleted module dir: modules/{name}")


def test_package_version_sources_are_synchronized() -> None:
    """Canonical package metadata and both import surfaces must share one version."""
    in_pyproject = _project_version()
    init_text = INIT_PY.read_text(encoding="utf-8")
    assert f'__version__ = "{in_pyproject}"' in init_text or f"__version__ = '{in_pyproject}'" in init_text
    setup_text = SETUP_PY.read_text(encoding="utf-8")
    assert f'version="{in_pyproject}"' in setup_text or f"version='{in_pyproject}'" in setup_text


def test_core_dependency_bounds_allow_patched_click_and_typer_releases() -> None:
    """Core requirements must retain the reviewed security version bounds."""
    dependencies = _project_dependencies()

    assert {
        "click>=8.3.3,<9",
        "typer>=0.24.0,<1",
        "pycparser>=2.22,!=3.0.*",
        "rich>=13.5.2,<16.0.0",
    } <= dependencies
    assert not any(dependency.startswith("opentelemetry-") for dependency in dependencies)

    setup_text = SETUP_PY.read_text(encoding="utf-8")
    assert all(
        requirement in setup_text
        for requirement in ('"click>=8.3.3,<9"', '"typer>=0.24.0,<1"', '"pycparser>=2.22,!=3.0.*"')
    )
    assert '"rich>=13.5.2,<16.0.0"' in setup_text
    assert '"opentelemetry-sdk' not in setup_text
    assert '"opentelemetry-exporter-otlp-proto-http' not in setup_text


def test_pycparser_requirement_excludes_the_alerted_release_family() -> None:
    """The published requirement must exclude the complete alerted 3.0 family."""
    dependencies = _project_dependencies()
    pycparser_requirement = Requirement(next(item for item in dependencies if item.startswith("pycparser")))
    assert pycparser_requirement.specifier.contains("2.22")
    assert not pycparser_requirement.specifier.contains("3.0")
    assert not pycparser_requirement.specifier.contains("3.0.1")
    assert not pycparser_requirement.specifier.contains("3.0.post1")


def test_telemetry_dependencies_are_opt_in_extra() -> None:
    """OpenTelemetry should stay out of core but remain available for explicit telemetry installs."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    telemetry = set(data["project"]["optional-dependencies"]["telemetry"])

    assert "opentelemetry-sdk>=1.27.0" in telemetry
    assert "opentelemetry-exporter-otlp-proto-http>=1.27.0" in telemetry


def test_hatch_gate_scripts_quote_pythonpath_interpreter_substitution() -> None:
    """Shell gates must preserve env-manager interpreter paths containing spaces."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    scripts = data["tool"]["hatch"]["envs"]["default"]["scripts"]
    quoted_pythonpath = "--pythonpath \"$(python -c 'import sys; print(sys.executable)')\""

    for script_name in ("type-check", "lint"):
        script = scripts[script_name]
        assert quoted_pythonpath in script
        assert "--pythonpath $(python -c" not in script
