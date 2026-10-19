from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from scripts import verify_downstream_semgrep as driver


def test_cell_isolates_uv_settings_without_mutating_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in {
        "UV_OVERRIDE": "host-overrides.txt",
        "UV_CONFIG_FILE": "host-uv.toml",
        "UV_NO_VERIFY_HASHES": "1",
        "UV_NO_CONFIG": "0",
        "Uv_No_Config": "false",
        "uv_future_setting": "host-value",
        "CELL_HOST_SENTINEL": "preserved",
    }.items():
        monkeypatch.setenv(key, value)
    parent = dict(os.environ)
    child = driver._Cell(tmp_path, {})._run(
        "environment",
        [
            sys.executable,
            "-c",
            "import json, os; print(json.dumps({k: v for k, v in os.environ.items() "
            "if k.upper().startswith('UV_') or k == 'CELL_HOST_SENTINEL'}))",
        ],
    )
    observed = json.loads(child.stdout)
    assert observed == {"UV_NO_CONFIG": "1", "CELL_HOST_SENTINEL": "preserved"}
    assert dict(os.environ) == parent


@pytest.fixture
def compile_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("Real uv is required for the offline configuration regression")
    for key in tuple(os.environ):
        if key.upper().startswith("UV_"):
            monkeypatch.delenv(key)
    for key, directory in {
        "HOME": "home",
        "XDG_CONFIG_HOME": "user",
        "XDG_CONFIG_DIRS": "system",
        "APPDATA": "user",
        "PROGRAMDATA": "system",
    }.items():
        monkeypatch.setenv(key, str(tmp_path / directory))
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(driver, "ROOT", project)
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    for version in ("1.0", "2.0"):
        info = f"uv_config_fixture-{version}.dist-info"
        files = {
            "uv_config_fixture.py": f"VERSION = {version!r}\n",
            f"{info}/METADATA": f"Metadata-Version: 2.1\nName: uv-config-fixture\nVersion: {version}\n\n",
            f"{info}/WHEEL": "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        }
        files[f"{info}/RECORD"] = "".join(f"{name},,\n" for name in [*files, f"{info}/RECORD"])
        with zipfile.ZipFile(wheels / f"uv_config_fixture-{version}-py3-none-any.whl", "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)
    requirement = tmp_path / "requirements.in"
    constraint = tmp_path / "constraints.txt"
    requirement.write_text("uv-config-fixture==1.0\n", encoding="utf-8")
    constraint.write_text("uv-config-fixture==1.0\n", encoding="utf-8")
    return [
        uv,
        "pip",
        "compile",
        str(requirement),
        "--constraint",
        str(constraint),
        "--generate-hashes",
        "--offline",
        "--no-index",
        "--no-cache",
        "--find-links",
        str(wheels),
        "--python",
        sys.executable,
        "--no-python-downloads",
    ]


@pytest.fixture
def pinned_compile(tmp_path: Path, compile_command: list[str]) -> tuple[list[str], str]:
    baseline = subprocess.run(compile_command, cwd=driver.ROOT, capture_output=True, text=True, check=True, timeout=30)
    wheel = tmp_path / "wheels/uv_config_fixture-1.0-py3-none-any.whl"
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    assert "uv-config-fixture==1.0" in baseline.stdout
    assert f"--hash=sha256:{digest}" in baseline.stdout
    return compile_command, digest


def test_cell_ignores_ambient_uv_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned_compile: tuple[list[str], str]
) -> None:
    command, digest = pinned_compile
    override = tmp_path / "overrides.txt"
    override.write_text("uv-config-fixture==2.0\n", encoding="utf-8")
    monkeypatch.setenv("UV_OVERRIDE", str(override))
    control = subprocess.run(command, cwd=driver.ROOT, capture_output=True, text=True, check=False, timeout=30)
    assert control.returncode == 1, control.stderr
    assert "unsatisfiable" in control.stderr
    result = driver._Cell(tmp_path, {})._run("isolated-compile", command, expected=(0, 1, 2))
    assert result.returncode == 0, result.stderr
    assert "uv-config-fixture==1.0" in result.stdout
    assert f"--hash=sha256:{digest}" in result.stdout


@pytest.mark.parametrize("poison", ["explicit", "project", "pyproject", "user", "system"])
def test_cell_ignores_persistent_uv_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pinned_compile: tuple[list[str], str], poison: str
) -> None:
    command, digest = pinned_compile
    config = {
        "explicit": tmp_path / "explicit.toml",
        "project": driver.ROOT / "uv.toml",
        "pyproject": driver.ROOT / "pyproject.toml",
        "user": tmp_path / "user/uv/uv.toml",
        "system": tmp_path / "system/uv/uv.toml",
    }[poison]
    config.parent.mkdir(parents=True, exist_ok=True)
    section = "tool.uv.pip" if poison == "pyproject" else "pip"
    config.write_text(f'[{section}]\nno-emit-package = ["uv-config-fixture"]\n', encoding="utf-8")
    if poison == "explicit":
        monkeypatch.setenv("UV_CONFIG_FILE", str(config))
    control = subprocess.run(command, cwd=driver.ROOT, capture_output=True, text=True, check=False, timeout=30)
    assert control.returncode == 0, control.stderr
    assert "uv-config-fixture==1.0" not in control.stdout
    result = driver._Cell(tmp_path, {})._run("isolated-compile", command, expected=(0, 1, 2))
    assert result.returncode == 0, result.stderr
    assert "uv-config-fixture==1.0" in result.stdout
    assert f"--hash=sha256:{digest}" in result.stdout
