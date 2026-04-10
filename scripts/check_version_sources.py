#!/usr/bin/env python3
"""Ensure release version strings match across canonical source files."""

from __future__ import annotations

import re
import sys
from pathlib import Path


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
            return 2
        text = path.read_text(encoding="utf-8")
        ver = readers[label](text)
        if not ver:
            sys.stderr.write(f"check_version_sources: could not parse version in {label}\n")
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
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
