#!/usr/bin/env python3
"""Ensure release version strings match across canonical source files."""

from __future__ import annotations

import re
import sys
from pathlib import Path


_REMEDIATION = """\
REMEDIATION (same check as .github/workflows/pr-orchestrator.yml → tests job):
  1. Set the SAME semver string in all four places:
       - pyproject.toml → project.version
       - setup.py → version=
       - src/__init__.py → __version__
       - src/specfact_cli/__init__.py → __version__
  2. Validate: hatch run check-version-sources
  3. If you bumped the CLI for release: add a top CHANGELOG.md section like  ## [x.y.z] - YYYY-MM-DD
  4. If publishing: local version must be strictly greater than PyPI; run with network:
       SPECFACT_PYPI_VERSION_CHECK_LENIENT_NETWORK=1 python scripts/check_local_version_ahead_of_pypi.py
     (offline: SPECFACT_SKIP_PYPI_VERSION_CHECK=1 — do not use in CI.)
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_version_pyproject(text: str) -> str | None:
    match = re.search(r'(?m)^version\s*=\s*["\']([^"\']+)["\']', text)
    return match.group(1) if match else None


def _read_version_setup(text: str) -> str | None:
    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', text)
    return match.group(1) if match else None


def _read_version_init(text: str) -> str | None:
    match = re.search(r'(?m)^__version__\s*=\s*["\']([^"\']+)["\']', text)
    return match.group(1) if match else None


def main() -> int:
    root = _repo_root()
    paths = {
        "pyproject.toml": root / "pyproject.toml",
        "setup.py": root / "setup.py",
        "src/__init__.py": root / "src" / "__init__.py",
        "src/specfact_cli/__init__.py": root / "src" / "specfact_cli" / "__init__.py",
    }
    versions: dict[str, str] = {}
    readers = {
        "pyproject.toml": _read_version_pyproject,
        "setup.py": _read_version_setup,
        "src/__init__.py": _read_version_init,
        "src/specfact_cli/__init__.py": _read_version_init,
    }
    for label, path in paths.items():
        if not path.is_file():
            sys.stderr.write(f"check_version_sources: missing file {path.relative_to(root)}\n")
            sys.stderr.write(_REMEDIATION)
            return 2
        text = path.read_text(encoding="utf-8")
        ver = readers[label](text)
        if not ver:
            sys.stderr.write(f"check_version_sources: could not parse version in {label}\n")
            sys.stderr.write(_REMEDIATION)
            return 2
        versions[label] = ver

    unique = sorted(set(versions.values()))
    if len(unique) != 1:
        sys.stderr.write(
            "check_version_sources: version mismatch across pyproject.toml, setup.py, "
            "src/__init__.py, src/specfact_cli/__init__.py:\n"
        )
        for label, ver in sorted(versions.items()):
            sys.stderr.write(f"  {label}: {ver}\n")
        sys.stderr.write(_REMEDIATION)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
