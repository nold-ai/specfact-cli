"""Contract-first tests for module dependency validation helpers."""

from __future__ import annotations

from pathlib import Path

from specfact_cli.models.module_package import VersionedModuleDependency
from specfact_cli.registry.module_packages import (
    ModulePackageMetadata,
    _validate_module_dependencies,
    expand_disable_with_dependents,
    expand_enable_with_dependencies,
    validate_disable_safe,
    validate_enable_safe,
)


def _pkg(name: str, deps: list[str] | None = None) -> tuple[Path, ModulePackageMetadata]:
    return (
        Path(f"/tmp/{name}"),
        ModulePackageMetadata(
            name=name,
            version="0.27.0",
            commands=[name],
            module_dependencies=deps or [],
        ),
    )


def test_validate_module_dependencies_no_dependencies() -> None:
    meta = ModulePackageMetadata(name="sync", version="0.27.0", commands=["sync"], module_dependencies=[])
    ok, missing = _validate_module_dependencies(meta, {"sync": True, "plan": True})
    assert ok is True
    assert missing == []


def test_validate_module_dependencies_detects_missing_and_disabled() -> None:
    meta = ModulePackageMetadata(
        name="sync",
        version="0.27.0",
        commands=["sync"],
        module_dependencies=["plan", "sdd", "ghost"],
    )
    ok, missing = _validate_module_dependencies(meta, {"plan": False, "sdd": True, "sync": True})
    assert ok is False
    assert "plan (disabled)" in missing
    assert "ghost (not found)" in missing


def test_validate_module_dependencies_detects_version_mismatch() -> None:
    meta = ModulePackageMetadata(
        name="review",
        version="0.47.0",
        commands=["code"],
        module_dependencies_versioned=[
            VersionedModuleDependency(name="codebase", version_specifier=">=0.41.0"),
        ],
    )

    ok, missing = _validate_module_dependencies(
        meta,
        {"review": True, "codebase": True},
        {"review": "0.47.0", "codebase": "0.40.9"},
    )

    assert ok is False
    assert "codebase (requires >=0.41.0, found 0.40.9)" in missing


def test_validate_disable_safe_blocks_enabled_dependents() -> None:
    packages = [
        _pkg("plan", ["sync"]),
        _pkg("sync", []),
        _pkg("sdd", []),
    ]
    enabled_map = {"plan": True, "sync": True, "sdd": True}

    blocked = validate_disable_safe(["sync"], packages, enabled_map)

    assert blocked == {"sync": ["plan"]}


def test_validate_disable_safe_allows_batch_disable_of_dependents() -> None:
    packages = [
        _pkg("plan", ["sync"]),
        _pkg("sync", []),
    ]
    enabled_map = {"plan": True, "sync": True}

    blocked = validate_disable_safe(["sync", "plan"], packages, enabled_map)

    assert blocked == {}


def test_expand_disable_with_dependents_transitive() -> None:
    packages = [
        _pkg("project", ["plan"]),
        _pkg("plan", ["sync"]),
        _pkg("sync", []),
    ]
    enabled_map = {"project": True, "plan": True, "sync": True}

    expanded = set(expand_disable_with_dependents(["sync"], packages, enabled_map))

    assert expanded == {"sync", "plan", "project"}


def test_expand_enable_with_dependencies_transitive() -> None:
    packages = [
        _pkg("project", ["plan"]),
        _pkg("plan", ["sync"]),
        _pkg("sync", []),
    ]

    expanded = set(expand_enable_with_dependencies(["project"], packages))

    assert expanded == {"project", "plan", "sync"}


def test_validate_enable_safe_blocks_when_dependency_disabled() -> None:
    packages = [
        _pkg("plan", ["sync"]),
        _pkg("sync", []),
    ]
    enabled_map = {"plan": True, "sync": False}

    blocked = validate_enable_safe(["plan"], packages, enabled_map)

    assert blocked == {"plan": ["sync (disabled)"]}
