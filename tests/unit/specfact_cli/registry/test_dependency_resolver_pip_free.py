"""Tests for pip-free dependency resolver fallback.

Spec: openspec/changes/docs-new-user-onboarding/specs/first-run-selection/spec.md
Bug 2: module install fails under uvx with "No module named pip"
"""

from __future__ import annotations

import subprocess
from typing import cast
from unittest.mock import patch

import pytest

from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry.dependency_resolver import (
    PipDependencyValidationUnavailableError,
    _run_basic_resolver,
    resolve_dependencies,
)


def test_run_basic_resolver_returns_constraints_when_pip_unavailable() -> None:
    """When pip is unavailable (uvx environment), basic resolver must not raise — return constraints."""
    constraints = ["requests>=2.28.0", "pyyaml>=6.0"]

    def _pip_not_available(*cmd_args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=cast(list[str | bytes], [str(a) for a in cmd_args]),
            returncode=1,
            stdout="",
            stderr="No module named pip",
        )

    with patch("specfact_cli.registry.dependency_resolver.subprocess.run", side_effect=_pip_not_available):
        result = _run_basic_resolver(constraints, allow_unvalidated=True)

    # Must not raise; must return something (constraints or empty list)
    assert isinstance(result, list), "Should return a list even when pip is unavailable"


def test_run_basic_resolver_raises_when_pip_unavailable_without_allow_unvalidated() -> None:
    """Without allow_unvalidated, missing pip must not silently skip validation."""

    def _pip_not_available(*cmd_args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=cast(list[str | bytes], [str(a) for a in cmd_args]),
            returncode=1,
            stdout="",
            stderr="No module named pip",
        )

    with (
        patch("specfact_cli.registry.dependency_resolver.subprocess.run", side_effect=_pip_not_available),
        pytest.raises(PipDependencyValidationUnavailableError),
    ):
        _run_basic_resolver(["requests>=1"], allow_unvalidated=False)


def test_resolve_dependencies_does_not_raise_when_pip_unavailable() -> None:
    """resolve_dependencies must complete without raising when pip and pip-compile are both unavailable."""
    module = ModulePackageMetadata(
        name="test-module",
        version="0.1.0",
        commands=["test"],
        pip_dependencies=["requests>=2.28.0"],
    )

    with (
        patch("specfact_cli.registry.dependency_resolver._pip_tools_available", return_value=False),
        patch(
            "specfact_cli.registry.dependency_resolver._run_basic_resolver",
            return_value=["requests>=2.28.0"],
        ) as mock_basic,
    ):
        result = resolve_dependencies([module])

    mock_basic.assert_called_once()
    assert mock_basic.call_args.kwargs.get("allow_unvalidated") is False
    assert isinstance(result, list)


def test_resolve_dependencies_passes_allow_unvalidated_to_basic_resolver() -> None:
    """Module install path requests unvalidated resolution when pip is missing (uvx)."""
    module = ModulePackageMetadata(
        name="test-module",
        version="0.1.0",
        commands=["test"],
        pip_dependencies=["requests>=2.28.0"],
    )

    with (
        patch("specfact_cli.registry.dependency_resolver._pip_tools_available", return_value=False),
        patch(
            "specfact_cli.registry.dependency_resolver._run_basic_resolver",
            return_value=["requests>=2.28.0"],
        ) as mock_basic,
    ):
        resolve_dependencies([module], allow_unvalidated=True)

    assert mock_basic.call_args.kwargs.get("allow_unvalidated") is True


def test_resolve_dependencies_empty_modules_returns_empty() -> None:
    """resolve_dependencies with no pip deps must return [] without calling pip."""
    module = ModulePackageMetadata(
        name="no-pip-deps",
        version="0.1.0",
        commands=["cmd"],
        pip_dependencies=[],
    )
    with patch("specfact_cli.registry.dependency_resolver._pip_tools_available") as mock_check:
        result = resolve_dependencies([module])

    mock_check.assert_not_called()
    assert result == []


def test_basic_resolver_returns_empty_for_empty_constraints() -> None:
    result = _run_basic_resolver([])
    assert result == []
