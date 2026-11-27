"""Exercise compilation and installation with an option-bearing pip constraint file."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest

from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry.dependency_resolver import install_resolved_pip_requirements, resolve_dependencies


def _write_fixture_wheel(directory: Path, version: str) -> None:
    """Create an offline wheel whose only payload is its distribution metadata."""
    dist_info = f"resolver_fixture-{version}.dist-info"
    with ZipFile(directory / f"resolver_fixture-{version}-py3-none-any.whl", "w") as wheel:
        wheel.writestr(
            f"{dist_info}/METADATA",
            f"Metadata-Version: 2.1\nName: resolver-fixture\nVersion: {version}\n",
        )
        wheel.writestr(f"{dist_info}/WHEEL", "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
        wheel.writestr(f"{dist_info}/RECORD", "")


def test_constraint_source_options_are_used_by_compiler_and_installer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both tools find the constrained wheel while the installer receives requirement arguments."""
    _write_fixture_wheel(tmp_path, "1.0")
    _write_fixture_wheel(tmp_path, "2.0")
    constraints = tmp_path / "constraints.txt"
    constraints.write_text(f"--find-links {tmp_path.as_uri()}\nresolver-fixture==1.0\n", encoding="utf-8")
    target = tmp_path / "installed"
    monkeypatch.setenv("PIP_CONFIG_FILE", "/dev/null")
    monkeypatch.setenv("PIP_CONSTRAINT", str(constraints))
    monkeypatch.setenv("PIP_NO_INDEX", "1")
    monkeypatch.setenv("PIP_FIND_LINKS", "")
    monkeypatch.setenv("PIP_TARGET", str(target))
    monkeypatch.setenv("PIP_TOOLS_CACHE_DIR", str(tmp_path / "cache"))
    module = ModulePackageMetadata(
        name="with-local-wheel", version="0.1.0", commands=["test"], pip_dependencies=["resolver-fixture"]
    )

    resolved = resolve_dependencies([module])

    assert resolved == ["resolver-fixture==1.0"]
    install_resolved_pip_requirements(resolved)
    assert (target / "resolver_fixture-1.0.dist-info" / "METADATA").is_file()
