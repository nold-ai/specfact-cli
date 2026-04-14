#!/usr/bin/env python3
"""Fail if pyproject version is not strictly greater than the latest PyPI release.

PyPI publish (see .github/workflows/scripts/check-and-publish-pypi.sh) skips when the local
version is not newer than PyPI, which hides release problems until merge to main. This script
surfaces that requirement on every PR that runs the tests job.

Set SPECFACT_SKIP_PYPI_VERSION_CHECK=1 to skip (offline / air-gapped only; do not use in CI).

Set SPECFACT_PYPI_VERSION_CHECK_LENIENT_NETWORK=1 so a PyPI fetch failure after retries exits 0
(warning only). Policy failures (local version not ahead of PyPI) still exit 1.
"""

from __future__ import annotations

import json
import os
import sys
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


DEFAULT_PACKAGE = "specfact-cli"
PYPI_JSON_TMPL = "https://pypi.org/pypi/{package}/json"
DEFAULT_TIMEOUT_S = 15.0
_MAX_FETCH_ATTEMPTS = 5


class PypiFetchError(RuntimeError):
    """Raised when the latest PyPI version cannot be fetched after retries (network or HTTP)."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@beartype
@require(lambda pyproject_path: isinstance(pyproject_path, Path))
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


@beartype
@require(lambda package: isinstance(package, str))
@require(lambda timeout_s: isinstance(timeout_s, (int, float)) and timeout_s > 0)
@ensure(lambda result: result is None or isinstance(result, str))
def fetch_latest_pypi_version(
    package: str = DEFAULT_PACKAGE,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> str | None:
    """Return latest published version, or None if the project is not on PyPI (404).

    Retries transient ``URLError`` and non-404 ``HTTPError`` a bounded number of times with
    exponential backoff (same ``timeout_s`` per attempt).
    """
    url = PYPI_JSON_TMPL.format(package=package)
    request = urllib.request.Request(url, headers={"User-Agent": "specfact-cli-version-check"})
    payload: dict[str, Any] | None = None
    for attempt in range(_MAX_FETCH_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if attempt + 1 >= _MAX_FETCH_ATTEMPTS:
                msg = f"check_local_version_ahead_of_pypi: PyPI HTTP {exc.code} for {url}"
                raise PypiFetchError(msg) from exc
        except urllib.error.URLError as exc:
            if attempt + 1 >= _MAX_FETCH_ATTEMPTS:
                msg = f"check_local_version_ahead_of_pypi: network error querying PyPI ({url}): {exc}"
                raise PypiFetchError(msg) from exc
        wait_s = min(2**attempt, 8.0)
        time.sleep(wait_s)

    if payload is None:
        msg = "check_local_version_ahead_of_pypi: exhausted fetch retries without a response body"
        raise PypiFetchError(msg)

    try:
        latest = payload["info"]["version"]
    except (KeyError, TypeError) as exc:
        msg = "check_local_version_ahead_of_pypi: unexpected PyPI JSON shape"
        raise RuntimeError(msg) from exc
    if not isinstance(latest, str) or not latest.strip():
        msg = "check_local_version_ahead_of_pypi: empty PyPI version string"
        raise RuntimeError(msg)
    return latest.strip()


@beartype
@require(lambda local: isinstance(local, str))
@require(lambda pypi_latest: pypi_latest is None or isinstance(pypi_latest, str))
@ensure(lambda result: isinstance(result, tuple) and len(result) == 2)
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


@beartype
@ensure(lambda result: result in (0, 1, 2))
def main() -> int:
    skip = os.environ.get("SPECFACT_SKIP_PYPI_VERSION_CHECK", "").strip().lower()
    if skip in {"1", "true", "yes", "on"}:
        sys.stderr.write(
            "check_local_version_ahead_of_pypi: skipped (SPECFACT_SKIP_PYPI_VERSION_CHECK)\n",
        )
        return 0

    root = _repo_root()
    try:
        local = read_local_version(root / "pyproject.toml")
        pypi_latest = fetch_latest_pypi_version()
    except PypiFetchError as exc:
        lenient = os.environ.get("SPECFACT_PYPI_VERSION_CHECK_LENIENT_NETWORK", "").strip().lower()
        if lenient in {"1", "true", "yes", "on"}:
            sys.stderr.write(
                f"::warning::{exc} — skipping ahead-of-PyPI check (lenient network).\n",
            )
            return 0
        sys.stderr.write(f"{exc}\n")
        return 2
    except (FileNotFoundError, KeyError, ValueError, RuntimeError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 2

    try:
        ok, message = compare_local_to_pypi_version(local, pypi_latest)
    except ValueError as exc:
        sys.stderr.write(f"check_local_version_ahead_of_pypi: invalid version string ({exc})\n")
        return 2

    sys.stderr.write(f"{message}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
