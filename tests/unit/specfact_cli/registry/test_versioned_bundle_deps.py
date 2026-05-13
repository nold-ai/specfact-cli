"""Tests for versioned bundle dependency resolution.

Spec: openspec/changes/docs-new-user-onboarding/specs/dependency-resolution/spec.md
Tasks: 7d.1 - 7d.10
"""

from __future__ import annotations

from typing import Any

import pytest

from specfact_cli.registry import module_installer
from specfact_cli.registry.module_installer import _dependency_version_satisfies, _extract_bundle_dependencies


# ── Scenario: Registry entry declares a versioned bundle dependency ───────────


def test_extract_bundle_dependencies_handles_versioned_object() -> None:
    """_extract_bundle_dependencies must handle {"id": "...", "version": ">=x.y.z"} form."""
    metadata: dict[str, Any] = {"bundle_dependencies": [{"id": "nold-ai/specfact-project", "version": ">=0.41.0"}]}
    deps = _extract_bundle_dependencies(metadata)
    assert "nold-ai/specfact-project" in deps, f"Versioned object form not handled; got {deps}"


def test_extract_bundle_dependencies_handles_plain_string() -> None:
    """_extract_bundle_dependencies must still handle plain string entries (backward compat)."""
    metadata: dict[str, Any] = {"bundle_dependencies": ["nold-ai/specfact-project"]}
    deps = _extract_bundle_dependencies(metadata)
    assert "nold-ai/specfact-project" in deps


def test_extract_bundle_dependencies_handles_mixed_list() -> None:
    """_extract_bundle_dependencies must handle a mix of string and versioned object entries."""
    metadata: dict[str, Any] = {
        "bundle_dependencies": [
            "nold-ai/specfact-project",
            {"id": "nold-ai/specfact-codebase", "version": ">=0.40.0"},
        ]
    }
    deps = _extract_bundle_dependencies(metadata)
    assert "nold-ai/specfact-project" in deps
    assert "nold-ai/specfact-codebase" in deps


def test_extract_bundle_dependencies_empty_list() -> None:
    metadata: dict[str, Any] = {"bundle_dependencies": []}
    deps = _extract_bundle_dependencies(metadata)
    assert deps == []


def test_extract_bundle_dependencies_missing_key() -> None:
    metadata: dict[str, Any] = {}
    deps = _extract_bundle_dependencies(metadata)
    assert deps == []


def test_extract_bundle_dependencies_rejects_object_without_id() -> None:
    """Malformed bundle_dependencies objects must fail manifest validation, not be skipped."""
    metadata: dict[str, Any] = {"bundle_dependencies": [{"version": ">=1.0.0"}]}
    with pytest.raises(ValueError, match="non-empty 'id'"):
        _extract_bundle_dependencies(metadata)


def test_extract_bundle_dependencies_rejects_empty_id_object() -> None:
    metadata: dict[str, Any] = {"bundle_dependencies": [{"id": "", "version": ">=1.0.0"}]}
    with pytest.raises(ValueError, match="non-empty 'id'"):
        _extract_bundle_dependencies(metadata)


def test_extract_bundle_dependencies_rejects_empty_string_entry() -> None:
    metadata: dict[str, Any] = {"bundle_dependencies": ["nold-ai/specfact-project", ""]}
    with pytest.raises(ValueError, match="string entry must be non-empty"):
        _extract_bundle_dependencies(metadata)


def test_dependency_version_satisfies_logs_malformed_inputs(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    logger = module_installer.logging.getLogger("test.module_installer.version")
    logger.propagate = True
    monkeypatch.setattr(module_installer, "get_bridge_logger", lambda _name: logger)
    caplog.set_level("DEBUG")

    assert _dependency_version_satisfies("not-a-version", ">=1.0") is False

    assert "not-a-version" in caplog.text
    assert ">=1.0" in caplog.text


# ── core_compatibility actionable error ───────────────────────────────────────


def test_validate_install_manifest_constraints_actionable_error() -> None:
    """core_compatibility mismatch must produce actionable message, not bare ValueError."""
    from specfact_cli.registry.module_installer import _validate_install_manifest_constraints

    metadata: dict[str, Any] = {
        "name": "specfact-code-review",
        "version": "0.1.0",
        "core_compatibility": ">=99.0.0,<100.0.0",  # impossibly high — always fails
    }

    with pytest.raises((ValueError, SystemExit)) as exc_info:
        _validate_install_manifest_constraints(
            metadata,
            "specfact-code-review",
            trust_non_official=True,
            non_interactive=True,
        )

    exc_val = str(exc_info.value)
    # Must include version info, not just "incompatible"
    assert any(
        phrase in exc_val.lower() for phrase in ["requires", "specfact cli", ">=", "run:", "upgrade", "99.0.0"]
    ), f"Error message not actionable: {exc_val!r}"
