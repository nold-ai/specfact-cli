"""
Base framework extractor interface.

This module defines the abstract base class for framework-specific extractors
that extract routes and schemas from framework code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class RouteInfo(BaseModel):
    """Information about a route extracted from framework code."""

    path: str = Field(..., description="Route path (e.g., '/api/users/{id}')")
    method: str = Field(..., description="HTTP method (e.g., 'GET', 'POST')")
    operation_id: str = Field(..., description="Operation ID for OpenAPI")
    view: str | None = Field(default=None, description="View function/class reference")
    function: str | None = Field(default=None, description="Function name (FastAPI)")
    path_params: list[dict[str, Any]] = Field(default_factory=list, description="Path parameters")
    request_schema: dict[str, Any] | None = Field(default=None, description="Request schema")
    response_schema: dict[str, Any] | None = Field(default=None, description="Response schema")


class BaseFrameworkExtractor(ABC):
    """Abstract base class for framework-specific route and schema extractors."""

    @abstractmethod
    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def detect(self, repo_path: Any) -> bool:
        """
        Detect if this framework is used in the repository.

        Args:
            repo_path: Path to repository root

        Returns:
            True if this framework is detected
        """
        raise NotImplementedError

    @abstractmethod
    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def extract_routes(self, repo_path: Any) -> list[RouteInfo]:
        """
        Extract route information from framework-specific patterns.

        Args:
            repo_path: Path to repository root

        Returns:
            List of RouteInfo objects with extracted routes
        """
        raise NotImplementedError

    @abstractmethod
    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda routes: isinstance(routes, list), "Routes must be a list")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_schemas(self, repo_path: Any, routes: list[RouteInfo]) -> dict[str, dict[str, Any]]:
        """
        Extract request/response schemas from framework-specific patterns.

        Args:
            repo_path: Path to repository root
            routes: List of extracted routes

        Returns:
            Dictionary mapping route identifiers to schema dictionaries
        """
        raise NotImplementedError
