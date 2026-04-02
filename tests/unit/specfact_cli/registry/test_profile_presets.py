"""Tests for profile presets and init --profile module installation.

Spec: openspec/changes/docs-new-user-onboarding/specs/profile-presets/spec.md
Spec: openspec/changes/docs-new-user-onboarding/specs/first-run-selection/spec.md
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from specfact_cli.modules.init.src.first_run_selection import (
    CANONICAL_BUNDLES,
    PROFILE_PRESETS,
    install_bundles_for_init,
    resolve_profile_bundles,
)


# ── Scenario: Profile canonical bundle mapping is machine-verifiable ──────────


def test_solo_developer_includes_specfact_code_review() -> None:
    """solo-developer profile MUST include specfact-code-review."""
    bundles = PROFILE_PRESETS["solo-developer"]
    assert "specfact-code-review" in bundles, f"solo-developer must include specfact-code-review; got {bundles}"


def test_solo_developer_includes_specfact_codebase() -> None:
    """solo-developer profile MUST include specfact-codebase."""
    bundles = PROFILE_PRESETS["solo-developer"]
    assert "specfact-codebase" in bundles


def test_solo_developer_canonical_set() -> None:
    """solo-developer canonical set is exactly [specfact-codebase, specfact-code-review]."""
    expected = {"specfact-codebase", "specfact-code-review"}
    actual = set(PROFILE_PRESETS["solo-developer"])
    assert actual == expected, f"Expected {expected}, got {actual}"


def test_specfact_code_review_in_canonical_bundles() -> None:
    """specfact-code-review must be in CANONICAL_BUNDLES."""
    assert "specfact-code-review" in CANONICAL_BUNDLES


def test_backlog_team_canonical_set() -> None:
    expected = {"specfact-project", "specfact-backlog", "specfact-codebase"}
    assert set(PROFILE_PRESETS["backlog-team"]) == expected


def test_api_first_team_canonical_set() -> None:
    expected = {"specfact-spec", "specfact-codebase"}
    assert set(PROFILE_PRESETS["api-first-team"]) == expected


def test_enterprise_full_stack_canonical_set() -> None:
    expected = {
        "specfact-project",
        "specfact-backlog",
        "specfact-codebase",
        "specfact-spec",
        "specfact-govern",
    }
    assert set(PROFILE_PRESETS["enterprise-full-stack"]) == expected


def test_resolve_profile_bundles_solo_developer() -> None:
    bundles = resolve_profile_bundles("solo-developer")
    assert "specfact-codebase" in bundles
    assert "specfact-code-review" in bundles


def test_resolve_profile_bundles_invalid_raises() -> None:
    with pytest.raises(ValueError, match="Unknown profile"):
        resolve_profile_bundles("unknown-profile")


# ── Scenario: install_bundles_for_init installs marketplace modules ────────────


def test_install_bundles_for_init_calls_marketplace_for_code_review(tmp_path: Path) -> None:
    """install_bundles_for_init must call the marketplace installer for specfact-code-review."""
    installed_marketplace_ids: list[str] = []

    def _fake_install_module(module_id: str, **kwargs: object) -> Path:
        installed_marketplace_ids.append(module_id)
        return tmp_path / module_id.split("/")[1]

    with (
        patch(
            "specfact_cli.registry.module_installer.install_bundled_module",
            return_value=False,
        ),
        patch(
            "specfact_cli.registry.module_installer.install_module",
            side_effect=_fake_install_module,
        ),
    ):
        install_bundles_for_init(
            ["specfact-code-review"],
            install_root=tmp_path,
            non_interactive=True,
        )

    assert any("specfact-code-review" in mid for mid in installed_marketplace_ids), (
        f"install_module was not called with specfact-code-review; calls: {installed_marketplace_ids}"
    )


def test_install_bundles_for_init_solo_developer_installs_both(tmp_path: Path) -> None:
    """Running install_bundles_for_init for solo-developer bundles installs both codebase and code-review."""
    installed_modules: list[str] = []
    installed_marketplace_ids: list[str] = []

    def _fake_bundled(module_name: str, root: Path, **kwargs: object) -> bool:
        installed_modules.append(module_name)
        return True

    def _fake_marketplace(module_id: str, **kwargs: object) -> Path:
        installed_marketplace_ids.append(module_id)
        return tmp_path / module_id.split("/")[1]

    with (
        patch(
            "specfact_cli.registry.module_installer.install_bundled_module",
            side_effect=_fake_bundled,
        ),
        patch(
            "specfact_cli.registry.module_installer.install_module",
            side_effect=_fake_marketplace,
        ),
    ):
        install_bundles_for_init(
            ["specfact-codebase", "specfact-code-review"],
            install_root=tmp_path,
            non_interactive=True,
        )

    assert len(installed_modules) > 0, "Bundled modules should be installed for specfact-codebase"
    assert any("specfact-code-review" in mid for mid in installed_marketplace_ids), (
        "Marketplace installer should be called for specfact-code-review"
    )
