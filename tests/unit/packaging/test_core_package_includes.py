"""Tests for core-only package includes in pyproject.toml / setup.py (module-migration-03)."""

from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement


REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT = REPO_ROOT / "pyproject.toml"
SETUP_PY = REPO_ROOT / "setup.py"
ROOT_INIT_PY = REPO_ROOT / "src" / "__init__.py"
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


def _project_dependencies() -> list[str]:
    """Return the declared core package dependencies."""
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    dependencies = project["dependencies"]
    assert isinstance(dependencies, list)
    assert all(isinstance(dependency, str) for dependency in dependencies)
    return dependencies


def _module_version(module_path: Path) -> str:
    """Return the literal ``__version__`` assignment from a package module."""
    module = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    assignments = [
        statement
        for statement in module.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "__version__"
    ]
    assert len(assignments) == 1, f"{module_path} must contain exactly one __version__ assignment"
    version = assignments[0].value
    assert isinstance(version, ast.Constant) and isinstance(version.value, str)
    return version.value


def _setup_metadata() -> tuple[str, list[str]]:
    """Return literal version and dependency values passed to the setup() call."""
    setup_module = ast.parse(SETUP_PY.read_text(encoding="utf-8"), filename=str(SETUP_PY))
    setup_calls = [
        node
        for node in ast.walk(setup_module)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setup"
    ]
    assert len(setup_calls) == 1, "setup.py must contain exactly one setup() call"
    keywords = {keyword.arg: keyword.value for keyword in setup_calls[0].keywords if keyword.arg is not None}

    version = ast.literal_eval(keywords["version"])
    dependencies = ast.literal_eval(keywords["install_requires"])
    assert isinstance(version, str)
    assert isinstance(dependencies, list)
    assert all(isinstance(dependency, str) for dependency in dependencies)
    return version, dependencies


def _requirements_named(dependencies: list[str], package_name: str) -> list[Requirement]:
    """Return every parsed dependency declaration for one normalized package name."""
    return [requirement for dependency in dependencies if (requirement := Requirement(dependency)).name == package_name]


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
    setup_version, _ = _setup_metadata()

    assert _module_version(ROOT_INIT_PY) == in_pyproject
    assert _module_version(INIT_PY) == in_pyproject
    assert setup_version == in_pyproject


def test_core_dependency_bounds_allow_patched_click_and_typer_releases() -> None:
    """Core requirements must retain the reviewed security version bounds."""
    dependencies = _project_dependencies()
    _, setup_dependencies = _setup_metadata()

    expected_dependencies = {
        "click>=8.3.3,<9",
        "typer>=0.24.0,<1",
        "pycparser>=2.22,!=3.0.*",
        "rich>=13.5.2,<16.0.0",
    }
    assert expected_dependencies <= set(dependencies)
    assert dependencies == setup_dependencies
    assert not any(dependency.startswith("opentelemetry-") for dependency in dependencies)
    assert not any(dependency.startswith("opentelemetry-") for dependency in setup_dependencies)


def test_pycparser_requirement_excludes_the_alerted_release_family() -> None:
    """The published requirement must exclude the complete alerted 3.0 family."""
    _, setup_dependencies = _setup_metadata()

    for dependencies in (_project_dependencies(), setup_dependencies):
        pycparser_requirements = _requirements_named(dependencies, "pycparser")
        assert len(pycparser_requirements) == 1
        pycparser_requirement = pycparser_requirements[0]
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
