"""
Django REST Framework (DRF) extractor for sidecar validation.

This module extracts routes and schemas from DRF applications.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.validators.sidecar.frameworks.base import BaseFrameworkExtractor, RouteInfo
from specfact_cli.validators.sidecar.frameworks.django import DjangoExtractor


class DRFExtractor(BaseFrameworkExtractor):
    """DRF framework extractor (extends Django extractor)."""

    def __init__(self) -> None:
        """Initialize DRF extractor with Django base."""
        self._django_extractor = DjangoExtractor()

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def detect(self, repo_path: Path) -> bool:
        """
        Detect if DRF is used in the repository.

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
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def extract_routes(self, repo_path: Path) -> list[RouteInfo]:
        """
        Extract routes from DRF (uses Django extractor).

        Args:
            repo_path: Path to repository root

        Returns:
            List of RouteInfo objects
        """
        # DRF uses Django URL patterns, so use Django extractor
        return self._django_extractor.extract_routes(repo_path)

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda routes: isinstance(routes, list), "Routes must be a list")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_schemas(self, repo_path: Path, routes: list[RouteInfo]) -> dict[str, dict[str, Any]]:
        """
        Extract schemas from DRF serializers.

        Args:
            repo_path: Path to repository root
            routes: List of extracted routes

        Returns:
            Dictionary mapping route identifiers to schema dictionaries
        """
        # Simplified schema extraction - full implementation would parse DRF serializers
        # For now, return empty dict - can be enhanced later
        return {}
