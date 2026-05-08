"""Regression tests for metadata-only module availability classification."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry.module_availability import ModuleAvailabilityStatus, classify_module_availability
from specfact_cli.registry.module_discovery import DiscoveredModule
from specfact_cli.registry.module_packages import clear_module_load_failures


@pytest.fixture(autouse=True)
def _clear_lazy_load_failures() -> Generator[None, None, None]:
    clear_module_load_failures()
    yield
    clear_module_load_failures()


def test_classify_installed_disabled_module_reports_disabled(monkeypatch) -> None:
    entry = DiscoveredModule(
        Path("/tmp/specfact-codebase"),
        ModulePackageMetadata(
            name="nold-ai/specfact-codebase",
            version="0.1.0",
            commands=["analyze"],
            category="codebase",
            bundle_group_command="code",
        ),
        "user",
    )

    monkeypatch.setattr(
        "specfact_cli.registry.module_availability.discover_all_modules_for_project_with_shadowed",
        lambda _: [entry],
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_availability.read_modules_state",
        lambda: {"nold-ai/specfact-codebase": {"version": "0.1.0", "enabled": False}},
    )

    availability = classify_module_availability(module_id="nold-ai/specfact-codebase", command_name="code")

    assert availability.status is ModuleAvailabilityStatus.DISABLED
    assert availability.module_id == "nold-ai/specfact-codebase"
    assert "module enable nold-ai/specfact-codebase" in availability.recovery_command


def test_classify_prioritizes_requested_module_id_over_shared_command_group(monkeypatch) -> None:
    code_review = DiscoveredModule(
        Path("/tmp/specfact-code-review"),
        ModulePackageMetadata(
            name="nold-ai/specfact-code-review",
            version="0.1.0",
            commands=["review"],
            category="codebase",
            bundle_group_command="code",
        ),
        "user",
    )
    codebase = DiscoveredModule(
        Path("/tmp/specfact-codebase"),
        ModulePackageMetadata(
            name="nold-ai/specfact-codebase",
            version="0.1.0",
            commands=["analyze"],
            category="codebase",
            bundle_group_command="code",
        ),
        "user",
    )

    monkeypatch.setattr(
        "specfact_cli.registry.module_availability.discover_all_modules_for_project_with_shadowed",
        lambda _: [code_review, codebase],
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_availability.read_modules_state",
        lambda: {
            "nold-ai/specfact-code-review": {"version": "0.1.0", "enabled": False},
            "nold-ai/specfact-codebase": {"version": "0.1.0", "enabled": False},
        },
    )

    availability = classify_module_availability(module_id="nold-ai/specfact-codebase", command_name="code")

    assert availability.status is ModuleAvailabilityStatus.DISABLED
    assert availability.module_id == "nold-ai/specfact-codebase"


def test_classify_fully_qualified_id_does_not_tail_match_other_namespace(monkeypatch) -> None:
    other_namespace = DiscoveredModule(
        Path("/tmp/specfact-codebase"),
        ModulePackageMetadata(
            name="other-org/specfact-codebase",
            version="0.1.0",
            commands=["analyze"],
            category="codebase",
            bundle_group_command="code",
        ),
        "user",
    )

    monkeypatch.setattr(
        "specfact_cli.registry.module_availability.discover_all_modules_for_project_with_shadowed",
        lambda _: [other_namespace],
    )
    monkeypatch.setattr("specfact_cli.registry.module_availability.read_modules_state", dict)

    availability = classify_module_availability(module_id="nold-ai/specfact-codebase", command_name="code")

    assert availability.status is ModuleAvailabilityStatus.ABSENT


def test_classify_skipped_module_reports_compatibility_reason(monkeypatch) -> None:
    entry = DiscoveredModule(
        Path("/tmp/specfact-codebase"),
        ModulePackageMetadata(
            name="nold-ai/specfact-codebase",
            version="0.1.0",
            commands=["analyze"],
            category="codebase",
            bundle_group_command="code",
            core_compatibility=">=99.0.0",
        ),
        "user",
    )

    monkeypatch.setattr(
        "specfact_cli.registry.module_availability.discover_all_modules_for_project_with_shadowed",
        lambda _: [entry],
    )
    monkeypatch.setattr("specfact_cli.registry.module_availability.read_modules_state", dict)

    availability = classify_module_availability(module_id="nold-ai/specfact-codebase", command_name="code")

    assert availability.status is ModuleAvailabilityStatus.SKIPPED
    assert "requires >=99.0.0" in availability.reason


def test_project_scope_shadow_reports_shadowing_and_available_project_copy(monkeypatch) -> None:
    project_entry = DiscoveredModule(
        Path("/repo/.specfact/modules/specfact-codebase"),
        ModulePackageMetadata(
            name="nold-ai/specfact-codebase",
            version="0.2.0",
            commands=["analyze"],
            category="codebase",
            bundle_group_command="code",
        ),
        "project",
    )
    user_entry = DiscoveredModule(
        Path("/home/user/.specfact/modules/specfact-codebase"),
        ModulePackageMetadata(
            name="nold-ai/specfact-codebase",
            version="0.1.0",
            commands=["analyze"],
            category="codebase",
            bundle_group_command="code",
        ),
        "user",
    )

    monkeypatch.setattr(
        "specfact_cli.registry.module_availability.discover_all_modules_for_project_with_shadowed",
        lambda _: [project_entry, user_entry],
    )
    monkeypatch.setattr("specfact_cli.registry.module_availability.read_modules_state", dict)

    availability = classify_module_availability(module_id="nold-ai/specfact-codebase", command_name="code")

    assert availability.status is ModuleAvailabilityStatus.SHADOWED
    assert availability.shadowed_by == project_entry.package_dir
    assert availability.package_dir == user_entry.package_dir


def test_classify_bare_short_id_reports_ambiguous_across_namespaces(monkeypatch) -> None:
    vendor_a = DiscoveredModule(
        Path("/tmp/vendor-a/specfact-codebase"),
        ModulePackageMetadata(
            name="vendor-a/specfact-codebase",
            version="0.1.0",
            commands=["analyze"],
            category="codebase",
        ),
        "user",
    )
    vendor_b = DiscoveredModule(
        Path("/tmp/vendor-b/specfact-codebase"),
        ModulePackageMetadata(
            name="vendor-b/specfact-codebase",
            version="0.1.0",
            commands=["analyze"],
            category="codebase",
        ),
        "marketplace",
    )

    monkeypatch.setattr(
        "specfact_cli.registry.module_availability.discover_all_modules_for_project_with_shadowed",
        lambda _: [vendor_a, vendor_b],
    )
    monkeypatch.setattr("specfact_cli.registry.module_availability.read_modules_state", dict)

    availability = classify_module_availability(module_id="specfact-codebase")

    assert availability.status is ModuleAvailabilityStatus.AMBIGUOUS
    assert "namespace/name" in availability.reason
