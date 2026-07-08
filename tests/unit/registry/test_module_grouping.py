"""Tests for module category metadata and group_modules_by_category (module-grouping)."""

from __future__ import annotations

from pathlib import Path

import pytest

from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry.module_grouping import ModuleManifestError, group_modules_by_category
from specfact_cli.registry.module_packages import discover_package_metadata


def _write_manifest(
    root: Path,
    module_name: str,
    *,
    category: str | None = None,
    bundle: str | None = None,
    bundle_group_command: str | None = None,
    bundle_sub_command: str | None = None,
) -> None:
    module_dir = root / module_name
    module_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"name: {module_name}",
        "version: '0.1.0'",
        f"commands: [{module_name}]",
    ]
    if category is not None:
        lines.append(f"category: {category}")
    if bundle is not None:
        lines.append(f"bundle: {bundle}")
    if bundle_group_command is not None:
        lines.append(f"bundle_group_command: {bundle_group_command}")
    if bundle_sub_command is not None:
        lines.append(f"bundle_sub_command: {bundle_sub_command}")
    (module_dir / "module-package.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (module_dir / "src").mkdir(parents=True, exist_ok=True)


def test_module_package_yaml_with_category_codebase_passes_validation(tmp_path: Path) -> None:
    """module-package.yaml with category: codebase passes validation."""
    _write_manifest(
        tmp_path,
        "analyze",
        category="codebase",
        bundle="specfact-codebase",
        bundle_group_command="code",
        bundle_sub_command="analyze",
    )
    packages = discover_package_metadata(tmp_path, source="builtin")
    assert len(packages) == 1
    meta = packages[0][1]
    assert meta.category == "codebase"
    assert meta.bundle == "specfact-codebase"
    assert meta.bundle_group_command == "code"
    assert meta.bundle_sub_command == "analyze"


def test_module_package_yaml_with_category_requirements_passes_validation(tmp_path: Path) -> None:
    """requirements modules mount under the requirements group command."""
    _write_manifest(
        tmp_path,
        "requirements",
        category="requirements",
        bundle="specfact-requirements",
        bundle_group_command="requirements",
        bundle_sub_command="requirements",
    )
    packages = discover_package_metadata(tmp_path, source="builtin")
    assert len(packages) == 1
    meta = packages[0][1]
    assert meta.category == "requirements"
    assert meta.bundle_group_command == "requirements"


def test_prerelease_project_requirements_group_is_normalized(tmp_path: Path) -> None:
    """Prerelease requirements manifests using project category normalize before validation."""
    _write_manifest(
        tmp_path,
        "requirements",
        category="project",
        bundle="specfact-requirements",
        bundle_group_command="requirements",
        bundle_sub_command="requirements",
    )
    packages = discover_package_metadata(tmp_path, source="builtin")
    assert len(packages) == 1
    meta = packages[0][1]
    assert meta.category == "requirements"
    assert meta.bundle_group_command == "requirements"


def test_legacy_codebase_bundle_group_command_is_normalized(tmp_path: Path) -> None:
    """Legacy marketplace manifests using codebase as group command are normalized to code."""
    _write_manifest(
        tmp_path,
        "code",
        category="codebase",
        bundle="nold-ai/specfact-codebase",
        bundle_group_command="codebase",
        bundle_sub_command="code",
    )
    packages = discover_package_metadata(tmp_path, source="marketplace")
    assert len(packages) == 1
    meta = packages[0][1]
    assert meta.category == "codebase"
    assert meta.bundle_group_command == "code"


def test_module_package_yaml_with_category_unknown_raises_module_manifest_error(
    tmp_path: Path,
) -> None:
    """module-package.yaml with category: unknown raises ModuleManifestError."""
    _write_manifest(tmp_path, "foo", category="unknown")
    (tmp_path / "foo" / "src").mkdir(parents=True, exist_ok=True)
    with pytest.raises(ModuleManifestError) as exc_info:
        discover_package_metadata(tmp_path, source="builtin")
    assert "unknown" in str(exc_info.value).lower() or "category" in str(exc_info.value).lower()


def test_module_package_yaml_without_category_mounts_ungrouped_warning_logged(
    tmp_path: Path,
) -> None:
    """module-package.yaml without category field mounts as ungrouped (no error; warning logged in production)."""
    _write_manifest(tmp_path, "legacy_mod")
    packages = discover_package_metadata(tmp_path, source="builtin")
    assert len(packages) == 1
    meta = packages[0][1]
    assert meta.category is None
    assert meta.bundle_group_command is None


def test_bundle_group_command_mismatch_raises_module_manifest_error(tmp_path: Path) -> None:
    """bundle_group_command mismatch vs canonical category raises ModuleManifestError."""
    _write_manifest(
        tmp_path,
        "analyze",
        category="codebase",
        bundle="specfact-codebase",
        bundle_group_command="wrong_group",
        bundle_sub_command="analyze",
    )
    with pytest.raises(ModuleManifestError) as exc_info:
        discover_package_metadata(tmp_path, source="builtin")
    assert "bundle_group_command" in str(exc_info.value) or "code" in str(exc_info.value)


def test_core_category_modules_have_no_bundle_or_bundle_group_command(tmp_path: Path) -> None:
    """Core-category modules have no bundle or bundle_group_command."""
    _write_manifest(
        tmp_path,
        "init",
        category="core",
        bundle_sub_command="init",
    )
    packages = discover_package_metadata(tmp_path, source="builtin")
    assert len(packages) == 1
    meta = packages[0][1]
    assert meta.category == "core"
    assert meta.bundle is None
    assert meta.bundle_group_command is None
    assert meta.bundle_sub_command == "init"


def test_group_modules_by_category_returns_correct_grouping() -> None:
    """group_modules_by_category() returns correct grouping dict from list of manifests."""
    manifests = [
        ModulePackageMetadata(
            name="analyze", version="0.1.0", commands=["analyze"], category="codebase", bundle_group_command="code"
        ),
        ModulePackageMetadata(
            name="validate", version="0.1.0", commands=["validate"], category="codebase", bundle_group_command="code"
        ),
        ModulePackageMetadata(
            name="backlog", version="0.1.0", commands=["backlog"], category="backlog", bundle_group_command="backlog"
        ),
    ]
    grouped = group_modules_by_category(manifests)
    assert "code" in grouped
    assert "backlog" in grouped
    assert len(grouped["code"]) == 2
    assert len(grouped["backlog"]) == 1
    names_code = {m.name for m in grouped["code"]}
    assert names_code == {"analyze", "validate"}
    assert grouped["backlog"][0].name == "backlog"
