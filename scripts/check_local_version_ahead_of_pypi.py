#!/usr/bin/env python3
"""Fail if pyproject version is not strictly greater than the latest PyPI release.

PyPI publish (see .github/workflows/scripts/check-and-publish-pypi.sh) skips when the local
version is not newer than PyPI, which hides release problems until merge to main. This script
surfaces that requirement on every PR that runs the tests job.

Set SPECFACT_SKIP_PYPI_VERSION_CHECK=1 to skip (offline / air-gapped only; do not use in CI).
"""

from __future__ import annotations

import json
import os
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_PACKAGE = "specfact-cli"
PYPI_JSON_TMPL = "https://pypi.org/pypi/{package}/json"
DEFAULT_TIMEOUT_S = 15.0


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_local_version(pyproject_path: Path) -> str:
    if not pyproject_path.is_file():
        msg = f"check_local_version_ahead_of_pypi: missing {pyproject_path}"
        raise FileNotFoundError(msg)
    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)
    try:
        version = data["project"]["version"]
    except KeyError as exc:
        msg = "check_local_version_ahead_of_pypi: project.version missing in pyproject.toml"
        raise KeyError(msg) from exc
    if not isinstance(version, str) or not version.strip():
        msg = "check_local_version_ahead_of_pypi: invalid project.version in pyproject.toml"
        raise ValueError(msg)
    return version.strip()


def fetch_latest_pypi_version(
    package: str = DEFAULT_PACKAGE,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> str | None:
    """Return latest published version, or None if the project is not on PyPI (404)."""
    url = PYPI_JSON_TMPL.format(package=package)
    request = urllib.request.Request(url, headers={"User-Agent": "specfact-cli-version-check"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        msg = f"check_local_version_ahead_of_pypi: PyPI HTTP {exc.code} for {url}"
        raise RuntimeError(msg) from exc
    except urllib.error.URLError as exc:
        msg = f"check_local_version_ahead_of_pypi: network error querying PyPI ({url}): {exc}"
        raise RuntimeError(msg) from exc

    try:
        latest = payload["info"]["version"]
    except (KeyError, TypeError) as exc:
        msg = "check_local_version_ahead_of_pypi: unexpected PyPI JSON shape"
        raise RuntimeError(msg) from exc
    if not isinstance(latest, str) or not latest.strip():
        msg = "check_local_version_ahead_of_pypi: empty PyPI version string"
        raise RuntimeError(msg)
    return latest.strip()


def compare_local_to_pypi_version(local: str, pypi_latest: str | None) -> tuple[bool, str]:
    """Return (ok, message). ok is True when local is strictly greater than PyPI (or PyPI missing)."""
    from packaging.version import parse as vparse

    local_v = vparse(local)
    if pypi_latest is None:
        return True, f"✅ Project not on PyPI yet; local version {local!r} is acceptable."
    pypi_v = vparse(pypi_latest)
    if local_v > pypi_v:
        return (
            True,
            f"✅ Local version {local!r} is ahead of PyPI latest {pypi_latest!r}.",
        )
    detail = (
        f"check_local_version_ahead_of_pypi: local version {local!r} must be greater than "
        f"PyPI latest {pypi_latest!r} (publish would skip). Bump the version in pyproject.toml, "
        "setup.py, src/__init__.py, and src/specfact_cli/__init__.py (see hatch run check-version-sources) "
        "and add a CHANGELOG entry."
    )
    return False, detail


def main() -> int:
    skip = os.environ.get("SPECFACT_SKIP_PYPI_VERSION_CHECK", "").strip().lower()
    if skip in {"1", "true", "yes", "on"}:
        print(
            "check_local_version_ahead_of_pypi: skipped (SPECFACT_SKIP_PYPI_VERSION_CHECK)",
            file=sys.stderr,
        )
        return 0

    root = _repo_root()
    try:
        local = read_local_version(root / "pyproject.toml")
        pypi_latest = fetch_latest_pypi_version()
    except (FileNotFoundError, KeyError, ValueError, RuntimeError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 2

    ok, message = compare_local_to_pypi_version(local, pypi_latest)
    print(message, file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
