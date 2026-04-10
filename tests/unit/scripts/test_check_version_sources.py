"""Tests for scripts/check_version_sources.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


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
    script_src = Path(__file__).resolve().parents[3] / "scripts" / "check_version_sources.py"
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    script = scripts_dir / "check_version_sources.py"
    script.write_text(script_src.read_text(encoding="utf-8"), encoding="utf-8")

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
