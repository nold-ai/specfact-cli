"""Tests for scripts/check_version_sources.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _copy_version_script(tmp_path: Path) -> Path:
    script_src = Path(__file__).resolve().parents[3] / "scripts" / "check_version_sources.py"
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    script = scripts_dir / "check_version_sources.py"
    script.write_text(script_src.read_text(encoding="utf-8"), encoding="utf-8")
    return script


def _write_canonical_version_files(tmp_path: Path, version: str) -> None:
    (tmp_path / "pyproject.toml").write_text(f'version = "{version}"\n', encoding="utf-8")
    (tmp_path / "setup.py").write_text(f'version="{version}"', encoding="utf-8")
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "__init__.py").write_text(f'__version__ = "{version}"\n', encoding="utf-8")
    (tmp_path / "src" / "specfact_cli").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "specfact_cli" / "__init__.py").write_text(
        f'__version__ = "{version}"\n',
        encoding="utf-8",
    )


def _init_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True, text=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True, text=True
    )


def test_check_version_sources_passes_on_repo() -> None:
    """Current checkout must keep canonical version files aligned."""
    script = Path(__file__).resolve().parents[3] / "scripts" / "check_version_sources.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_check_version_sources_detects_mismatch(tmp_path: Path) -> None:
    """Mismatched __version__ in one file must fail the check."""
    script = _copy_version_script(tmp_path)

    (tmp_path / "pyproject.toml").write_text('version = "9.9.9"\n', encoding="utf-8")
    (tmp_path / "setup.py").write_text('version="9.9.9"', encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text('__version__ = "9.9.9"\n', encoding="utf-8")
    (tmp_path / "src" / "specfact_cli").mkdir(parents=True)
    (tmp_path / "src" / "specfact_cli" / "__init__.py").write_text('__version__ = "1.0.0"\n', encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "mismatch" in completed.stderr.lower()


def test_check_version_sources_fails_when_packaged_artifact_changes_without_staged_version_bundle(
    tmp_path: Path,
) -> None:
    """Staged packaged-artifact changes must carry the four version files and CHANGELOG."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n\n- Initial release entry.\n", encoding="utf-8")
    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 1\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True, text=True)

    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "src/specfact_cli/runtime.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "missing staged version file" in completed.stderr


def test_check_version_sources_passes_when_packaged_artifact_changes_with_version_bundle_and_changelog(
    tmp_path: Path,
) -> None:
    """Staged packaged-artifact changes should pass once the package version and changelog are updated together."""
    script = _copy_version_script(tmp_path)
    _write_canonical_version_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - 2026-04-16\n\n- Initial release entry.\n", encoding="utf-8")
    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 1\n", encoding="utf-8")
    _init_git_repo(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True, text=True)

    (tmp_path / "src" / "specfact_cli" / "runtime.py").write_text("VALUE = 2\n", encoding="utf-8")
    _write_canonical_version_files(tmp_path, "1.2.4")
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.4] - 2026-04-16\n\n- Runtime update.\n", encoding="utf-8")
    subprocess.run(
        [
            "git",
            "add",
            "src/specfact_cli/runtime.py",
            "pyproject.toml",
            "setup.py",
            "src/__init__.py",
            "src/specfact_cli/__init__.py",
            "CHANGELOG.md",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
