"""Contract tests for frozen-delivery support scripts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_reproducible_delivery_checker_is_versioned() -> None:
    """The lock/export/fixture verifier must be available to local and CI callers."""
    checker = REPO_ROOT / "scripts" / "check_reproducible_delivery.py"
    assert checker.is_file()


def test_reproducible_delivery_checker_verifies_hashed_export() -> None:
    """The frozen export must be a checked-in, hash-protected install input."""
    checker = REPO_ROOT / "scripts" / "check_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("check_reproducible_delivery", checker)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.LOCKED_EXPORT.is_file()
    module.verify_locked_export()


def test_reproducible_delivery_refresh_uses_locked_export_contract() -> None:
    """Refresh is explicit and re-validates the generated delivery inputs."""
    refresh = (REPO_ROOT / "scripts" / "refresh_reproducible_delivery.py").read_text(encoding="utf-8")
    assert '"uv", "lock"' in refresh
    assert '"export",' in refresh
    assert "--locked" in refresh
    assert "--no-emit-project" in refresh
    assert "check_reproducible_delivery.py" in refresh
    assert "timeout=" in refresh
    assert "TimeoutExpired" in refresh


def test_reproducible_delivery_verifier_bounds_uv_commands_and_fails_closed_on_timeout() -> None:
    """Frozen-delivery validation must not hang indefinitely on a stalled uv process."""
    checker = (REPO_ROOT / "scripts" / "check_reproducible_delivery.py").read_text(encoding="utf-8")
    assert checker.count("timeout=") >= 2
    assert "subprocess.TimeoutExpired" in checker


def test_reproducible_delivery_wheel_build_uses_a_locked_backend() -> None:
    """The no-isolation wheel proof must use the backend pinned in delivery inputs."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["build-system"]["requires"] == ["hatchling==1.32.0"]
    assert "hatchling==1.32.0" in project["project"]["optional-dependencies"]["dev"]
    assert "twine>=7.0" in project["project"]["optional-dependencies"]["dev"]
    assert "core-metadata-version" not in project["tool"]["hatch"]["build"]["targets"]["wheel"]

    workflow = (REPO_ROOT / ".github" / "workflows" / "pr-orchestrator.yml").read_text(encoding="utf-8")
    assert "Build package once\n        run: uv build --wheel --no-build-isolation" in workflow


def test_reproducible_delivery_pins_patched_pip_to_tooling_only() -> None:
    """The fixed pip floor must cover tooling without expanding core runtime dependencies."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = project["project"]["optional-dependencies"]["dev"]
    hatch_dependencies = project["tool"]["hatch"]["envs"]["default"]["dependencies"]
    runtime_names = {Requirement(dependency).name.casefold() for dependency in project["project"]["dependencies"]}

    assert "pip>=26.2" in dev_dependencies
    assert "pip>=26.2" in hatch_dependencies
    assert "pip" not in runtime_names
    assert '\n            "pip' not in (REPO_ROOT / "setup.py").read_text(encoding="utf-8").casefold()


def test_reproducible_delivery_pins_pycg_consistently_across_tool_groups() -> None:
    """All development tool groups must select the reviewed PyCG release."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    optional_dependencies = project["project"]["optional-dependencies"]
    hatch_dependencies = project["tool"]["hatch"]["envs"]["default"]["dependencies"]
    hatch_test_dependencies = project["tool"]["hatch"]["envs"]["hatch-test"]["dependencies"]

    assert "pycg==0.0.8" in optional_dependencies["dev"]
    assert "pycg==0.0.8" in optional_dependencies["enhanced-analysis"]
    assert "pycg==0.0.8" in hatch_dependencies
    assert "pycg==0.0.8" in hatch_test_dependencies


def test_reproducible_delivery_refresh_rejects_a_symlinked_output_parent(tmp_path: Path) -> None:
    """Refresh must not write a generated export through a repository symlink."""
    refresh_path = REPO_ROOT / "scripts" / "refresh_reproducible_delivery.py"
    spec = importlib.util.spec_from_file_location("refresh_reproducible_delivery", refresh_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    requirements = repository / "requirements"
    requirements.symlink_to(outside, target_is_directory=True)
    output = requirements / "ci" / "locked.txt"

    with pytest.raises(OSError, match="symlink"):
        module.validate_locked_export_path(output, repository)


def test_locked_sbom_renderer_uses_pip_inspect_without_generator_dependency(tmp_path: Path) -> None:
    """Delivery SBOM evidence must be local, deterministic, and dependency-free."""
    renderer = REPO_ROOT / "scripts" / "render_locked_sbom.py"
    assert renderer.is_file()

    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = project["project"]["optional-dependencies"]["dev"]
    assert all("cyclonedx" not in dependency.lower() for dependency in dev_dependencies)

    inspect_report = tmp_path / "inspect.json"
    inspect_report.write_text(
        json.dumps(
            {
                "installed": [
                    {"metadata": {"name": "Example-CLI", "version": "2.0.0"}},
                    {"metadata": {"name": "another-package", "version": "1.0.0"}},
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "locked.spdx.json"

    completed = subprocess.run(
        [sys.executable, str(renderer), "--inspect", str(inspect_report), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["spdxVersion"] == "SPDX-2.3"
    assert payload["creationInfo"]["created"] == "1970-01-01T00:00:00Z"
    assert [(package["name"], package["versionInfo"]) for package in payload["packages"]] == [
        ("another-package", "1.0.0"),
        ("Example-CLI", "2.0.0"),
    ]
    assert payload["packages"][0]["externalRefs"] == [
        {
            "referenceCategory": "PACKAGE-MANAGER",
            "referenceLocator": "pkg:pypi/another-package@1.0.0",
            "referenceType": "purl",
        }
    ]
