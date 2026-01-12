"""
Framework detection logic for sidecar validation.

This module provides functionality to detect which framework is used in a repository
(Django, FastAPI, DRF, pure-python) for appropriate route/schema extraction.
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.validators.sidecar.models import FrameworkType


@beartype
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
@ensure(lambda result: isinstance(result, FrameworkType), "Must return FrameworkType")
def detect_framework(repo_path: Path) -> FrameworkType:
    """
    Detect framework type from repository structure and code patterns.

    Detection priority:
    1. FastAPI: Check for FastAPI imports in main.py or app.py
    2. Flask: Check for Flask imports and Flask() instantiation
    3. Django: Check for manage.py or urls.py files
    4. DRF: Check for rest_framework imports (if Django is also present)
    5. Pure Python: No framework detected

    Args:
        repo_path: Path to repository root

    Returns:
        Detected FrameworkType
    """
    # FastAPI detection: Check for FastAPI imports
    for candidate_file in ["main.py", "app.py"]:
        file_path = repo_path / candidate_file
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                if "from fastapi import" in content or "FastAPI(" in content:
                    return FrameworkType.FASTAPI
            except (UnicodeDecodeError, PermissionError):
                # Skip files that can't be read
                continue

    # Also check in common FastAPI locations
    for search_path in [repo_path, repo_path / "src", repo_path / "app", repo_path / "backend" / "app"]:
        if not search_path.exists():
            continue
        for py_file in search_path.rglob("*.py"):
            if py_file.name in ["main.py", "app.py"]:
                try:
                    content = py_file.read_text(encoding="utf-8")
                    if "from fastapi import" in content or "FastAPI(" in content:
                        return FrameworkType.FASTAPI
                except (UnicodeDecodeError, PermissionError):
                    continue

    # Flask detection: Check for Flask imports and Flask() instantiation
    # This must come BEFORE Django urls.py check to avoid false positives
    flask_detected = False
    for search_path in [repo_path, repo_path / "src", repo_path / "app"]:
        if not search_path.exists():
            continue
        # Limit search to avoid scanning entire large codebases
        for py_file in list(search_path.rglob("*.py"))[:50]:  # Check first 50 files
            try:
                content = py_file.read_text(encoding="utf-8")
                # Check for Flask-specific patterns
                if (
                    "from flask import Flask" in content
                    or ("import flask" in content and "Flask(" in content)
                    or ("from flask" in content and "Flask" in content)
                ):
                    flask_detected = True
                    break
            except (UnicodeDecodeError, PermissionError):
                continue
        if flask_detected:
            break

    # Django detection: Check for manage.py first (strongest indicator)
    manage_py = repo_path / "manage.py"
    if manage_py.exists():
        # Check if DRF is also present
        if _has_drf(repo_path):
            return FrameworkType.DRF
        return FrameworkType.DJANGO

    # If Flask was detected, return FLASK
    if flask_detected:
        return FrameworkType.FLASK

    # Check for urls.py files (Django pattern)
    # Only check if Flask wasn't detected and manage.py doesn't exist
    urls_files = list(repo_path.rglob("urls.py"))
    if urls_files:
        # Check if DRF is also present
        if _has_drf(repo_path):
            return FrameworkType.DRF
        return FrameworkType.DJANGO

    # No framework detected
    return FrameworkType.PURE_PYTHON


@beartype
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def _has_drf(repo_path: Path) -> bool:
    """
    Check if Django REST Framework is present in the repository.

    Args:
        repo_path: Path to repository root

    Returns:
        True if DRF is detected
    """
    # Check for rest_framework imports
    for py_file in repo_path.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            if "rest_framework" in content or "from rest_framework" in content:
                return True
        except (UnicodeDecodeError, PermissionError):
            continue

    # Check for rest_framework in requirements files
    for req_file in [repo_path / "requirements.txt", repo_path / "pyproject.toml"]:
        if req_file.exists():
            try:
                content = req_file.read_text(encoding="utf-8")
                if "djangorestframework" in content or "django-rest-framework" in content:
                    return True
            except (UnicodeDecodeError, PermissionError):
                continue

    return False


@beartype
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
@ensure(lambda result: isinstance(result, str) or result is None, "Must return str or None")
def detect_django_settings_module(repo_path: Path) -> str | None:
    """
    Detect Django settings module from manage.py or environment.

    Args:
        repo_path: Path to repository root

    Returns:
        Django settings module name, or None if not detected
    """
    manage_py = repo_path / "manage.py"
    if not manage_py.exists():
        return None

    try:
        content = manage_py.read_text(encoding="utf-8")
        # Look for DJANGO_SETTINGS_MODULE assignment
        import re

        match = re.search(r"DJANGO_SETTINGS_MODULE\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return match.group(1)
    except (UnicodeDecodeError, PermissionError):
        pass

    # Try common Django settings module patterns
    for settings_file in repo_path.rglob("settings.py"):
        # Convert path to module name
        relative_path = settings_file.relative_to(repo_path)
        module_parts = list(relative_path.parts[:-1])  # Remove settings.py
        if module_parts:
            return ".".join(module_parts) + ".settings"

    return None
