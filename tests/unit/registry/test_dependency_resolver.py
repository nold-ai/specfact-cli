"""Unit tests for dependency resolver (pip-compile style resolution with conflict detection)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from specfact_cli.models.module_package import ModulePackageMetadata, VersionedPipDependency
from specfact_cli.registry.dependency_resolver import (
    DependencyConflictError,
    PipDependencyInstallError,
    install_resolved_pip_requirements,
    resolve_dependencies,
)


def test_pip_compile_honors_pip_install_constraints(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Forward the same ordered constraint files pip will read at installation."""
    reviewed_pin = tmp_path / "reviewed.txt"
    platform_pin = tmp_path / "platform.txt"
    reviewed_pin.write_text("typer==0.27.0\n", encoding="utf-8")
    platform_pin.write_text("click>=8.3.3\n", encoding="utf-8")
    monkeypatch.setenv("PIP_CONSTRAINT", f"{reviewed_pin} {platform_pin}")

    def compile_pinned_requirements(command: list[str], **_options: object) -> subprocess.CompletedProcess[str]:
        assert [arg for arg in command if arg.startswith("--constraint=")] == [
            f"--constraint={reviewed_pin}",
            f"--constraint={platform_pin}",
        ]
        Path(command[command.index("-o") + 1]).write_text("typer==0.27.0\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    module = ModulePackageMetadata(name="with-typer", version="0.1.0", commands=["test"], pip_dependencies=["typer"])
    with (
        patch("specfact_cli.registry.dependency_resolver._pip_tools_available", return_value=True),
        patch("specfact_cli.registry.dependency_resolver.subprocess.run", side_effect=compile_pinned_requirements),
    ):
        assert resolve_dependencies([module]) == ["typer==0.27.0"]


@pytest.fixture
def module_without_dependencies() -> ModulePackageMetadata:
    """Module metadata with no pip dependencies."""
    return ModulePackageMetadata(name="simple-module", version="0.1.0", commands=["simple"])


@pytest.fixture
def module_with_compatible_dependencies() -> ModulePackageMetadata:
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
def module_with_conflicting_dependencies() -> ModulePackageMetadata:
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
        module_without_dependencies: ModulePackageMetadata,
        module_with_compatible_dependencies: ModulePackageMetadata,
    ) -> None:
        """resolve_dependencies collects pip_dependencies from all modules."""
        modules = [module_without_dependencies, module_with_compatible_dependencies]
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
        module_with_compatible_dependencies: ModulePackageMetadata,
    ) -> None:
        """When no conflicts, resolve_dependencies returns list of resolved package versions."""
        with (
            patch("specfact_cli.registry.dependency_resolver._pip_tools_available", return_value=True),
            patch("specfact_cli.registry.dependency_resolver._run_pip_compile") as mock_run,
        ):
            mock_run.return_value = ["requests==2.31.0", "pydantic==2.5.0"]
            result = resolve_dependencies([module_with_compatible_dependencies])
        assert result == ["requests==2.31.0", "pydantic==2.5.0"]

    def test_conflict_detection_incompatible_versions(
        self,
        module_with_compatible_dependencies: ModulePackageMetadata,
        module_with_conflicting_dependencies: ModulePackageMetadata,
    ) -> None:
        """When conflicting versions, raises DependencyConflictError with clear error."""
        modules = [module_with_compatible_dependencies, module_with_conflicting_dependencies]
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
        module_with_compatible_dependencies: ModulePackageMetadata,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When pip-tools not available, log warning and use basic pip resolver."""
        with (
            patch("specfact_cli.registry.dependency_resolver._run_pip_compile"),
            patch("specfact_cli.registry.dependency_resolver._pip_tools_available", return_value=False),
            patch("specfact_cli.registry.dependency_resolver._run_basic_resolver") as mock_basic,
        ):
            mock_basic.return_value = ["requests==2.31.0", "pydantic==2.5.0"]
            result = resolve_dependencies([module_with_compatible_dependencies])
        assert mock_basic.called
        assert result == ["requests==2.31.0", "pydantic==2.5.0"]

    def test_clear_error_messages_for_conflicts(
        self,
        module_with_compatible_dependencies: ModulePackageMetadata,
        module_with_conflicting_dependencies: ModulePackageMetadata,
    ) -> None:
        """DependencyConflictError includes conflicting packages, versions, affected modules."""
        modules = [module_with_compatible_dependencies, module_with_conflicting_dependencies]
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


class TestInstallResolvedPipRequirements:
    """Tests for install_resolved_pip_requirements."""

    def test_no_op_when_empty(self) -> None:
        with patch("specfact_cli.registry.dependency_resolver.subprocess.run") as mock_run:
            install_resolved_pip_requirements([])
        mock_run.assert_not_called()

    def test_invokes_pip_install_with_pins(self) -> None:
        ok = MagicMock()
        ok.returncode = 0
        with (
            patch("specfact_cli.registry.dependency_resolver._pip_module_available", return_value=True),
            patch("specfact_cli.registry.dependency_resolver.subprocess.run") as mock_run,
        ):
            mock_run.return_value = ok
            install_resolved_pip_requirements(["requests==2.31.0", "pydantic==2.5.0"])
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "pip" in cmd
        assert "install" in cmd
        assert "--no-input" in cmd
        assert "requests==2.31.0" in cmd
        assert "pydantic==2.5.0" in cmd

    def test_skips_when_pip_module_unavailable(self) -> None:
        with (
            patch("specfact_cli.registry.dependency_resolver._pip_module_available", return_value=False),
            patch("specfact_cli.registry.dependency_resolver.subprocess.run") as mock_run,
        ):
            install_resolved_pip_requirements(["x==1"])
        mock_run.assert_not_called()

    def test_raises_on_pip_failure(self) -> None:
        bad = MagicMock()
        bad.returncode = 1
        bad.stderr = "boom"
        bad.stdout = ""
        with (
            patch("specfact_cli.registry.dependency_resolver._pip_module_available", return_value=True),
            patch("specfact_cli.registry.dependency_resolver.subprocess.run") as mock_run,
        ):
            mock_run.return_value = bad
            with pytest.raises(PipDependencyInstallError):
                install_resolved_pip_requirements(["x==1"])
