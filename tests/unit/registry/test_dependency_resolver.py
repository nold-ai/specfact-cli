"""Unit tests for dependency resolver (pip-compile style resolution with conflict detection)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from specfact_cli.models.module_package import ModulePackageMetadata, VersionedPipDependency
from specfact_cli.registry.dependency_resolver import (
    DependencyConflictError,
    resolve_dependencies,
)


@pytest.fixture
def sample_metadata_no_deps() -> ModulePackageMetadata:
    """Module metadata with no pip dependencies."""
    return ModulePackageMetadata(name="simple-module", version="0.1.0", commands=["simple"])


@pytest.fixture
def sample_metadata_with_deps() -> ModulePackageMetadata:
    """Module metadata with pip dependencies."""
    return ModulePackageMetadata(
        name="with-deps",
        version="0.1.0",
        commands=["withdeps"],
        pip_dependencies=["requests>=2.28", "pydantic>=2.0"],
        pip_dependencies_versioned=[
            VersionedPipDependency(name="requests", version_specifier=">=2.28"),
            VersionedPipDependency(name="pydantic", version_specifier=">=2.0"),
        ],
    )


@pytest.fixture
def sample_metadata_conflict() -> ModulePackageMetadata:
    """Module metadata with dependency that could conflict (requests<2.27)."""
    return ModulePackageMetadata(
        name="conflict-module",
        version="0.1.0",
        commands=["conflict"],
        pip_dependencies=["requests<2.27"],
        pip_dependencies_versioned=[
            VersionedPipDependency(name="requests", version_specifier="<2.27"),
        ],
    )


class TestResolveDependenciesAggregates:
    """Test that resolve_dependencies aggregates pip_dependencies from all modules."""

    def test_aggregates_pip_dependencies(
        self,
        sample_metadata_no_deps: ModulePackageMetadata,
        sample_metadata_with_deps: ModulePackageMetadata,
    ) -> None:
        """resolve_dependencies collects pip_dependencies from all modules."""
        modules = [sample_metadata_no_deps, sample_metadata_with_deps]
        with (
            patch("specfact_cli.registry.dependency_resolver._pip_tools_available", return_value=True),
            patch("specfact_cli.registry.dependency_resolver._run_pip_compile") as mock_run,
        ):
            mock_run.return_value = ["requests==2.31.0", "pydantic==2.5.0"]
            result = resolve_dependencies(modules)
        assert isinstance(result, list)
        assert "requests" in str(result).lower() or "pydantic" in str(result).lower()
        mock_run.assert_called_once()

    def test_resolution_succeeds_without_conflicts(
        self,
        sample_metadata_with_deps: ModulePackageMetadata,
    ) -> None:
        """When no conflicts, resolve_dependencies returns list of resolved package versions."""
        with (
            patch("specfact_cli.registry.dependency_resolver._pip_tools_available", return_value=True),
            patch("specfact_cli.registry.dependency_resolver._run_pip_compile") as mock_run,
        ):
            mock_run.return_value = ["requests==2.31.0", "pydantic==2.5.0"]
            result = resolve_dependencies([sample_metadata_with_deps])
        assert result == ["requests==2.31.0", "pydantic==2.5.0"]

    def test_conflict_detection_incompatible_versions(
        self,
        sample_metadata_with_deps: ModulePackageMetadata,
        sample_metadata_conflict: ModulePackageMetadata,
    ) -> None:
        """When conflicting versions, raises DependencyConflictError with clear error."""
        modules = [sample_metadata_with_deps, sample_metadata_conflict]
        with (
            patch("specfact_cli.registry.dependency_resolver._pip_tools_available", return_value=True),
            patch("specfact_cli.registry.dependency_resolver._run_pip_compile") as mock_run,
        ):
            mock_run.side_effect = DependencyConflictError(
                "Conflicting dependencies: requests>=2.28 (with-deps) vs requests<2.27 (conflict-module)"
            )
            with pytest.raises(DependencyConflictError) as exc_info:
                resolve_dependencies(modules)
        assert "requests" in str(exc_info.value).lower()
        assert "conflict" in str(exc_info.value).lower()

    def test_fallback_basic_resolver_when_pip_tools_unavailable(
        self,
        sample_metadata_with_deps: ModulePackageMetadata,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When pip-tools not available, log warning and use basic pip resolver."""
        with (
            patch("specfact_cli.registry.dependency_resolver._run_pip_compile"),
            patch("specfact_cli.registry.dependency_resolver._pip_tools_available", return_value=False),
            patch("specfact_cli.registry.dependency_resolver._run_basic_resolver") as mock_basic,
        ):
            mock_basic.return_value = ["requests==2.31.0", "pydantic==2.5.0"]
            result = resolve_dependencies([sample_metadata_with_deps])
        assert mock_basic.called
        assert result == ["requests==2.31.0", "pydantic==2.5.0"]

    def test_clear_error_messages_for_conflicts(
        self,
        sample_metadata_with_deps: ModulePackageMetadata,
        sample_metadata_conflict: ModulePackageMetadata,
    ) -> None:
        """DependencyConflictError includes conflicting packages, versions, affected modules."""
        modules = [sample_metadata_with_deps, sample_metadata_conflict]
        with (
            patch("specfact_cli.registry.dependency_resolver._pip_tools_available", return_value=True),
            patch("specfact_cli.registry.dependency_resolver._run_pip_compile") as mock_run,
        ):
            mock_run.side_effect = DependencyConflictError(
                "Conflicting packages: requests. Suggest: uninstall one module, use --force, or --skip-deps."
            )
            with pytest.raises(DependencyConflictError) as exc_info:
                resolve_dependencies(modules)
        msg = str(exc_info.value)
        assert "requests" in msg
        assert "Suggest" in msg or "force" in msg or "skip-deps" in msg
