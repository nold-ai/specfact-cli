"""Contract-first tests for module core compatibility constraints."""

from __future__ import annotations

from specfact_cli.registry.module_packages import ModulePackageMetadata, _check_core_compatibility


def _meta(core_compatibility: str | None) -> ModulePackageMetadata:
    return ModulePackageMetadata(
        name="sync",
        version="0.27.0",
        commands=["sync"],
        module_dependencies=[],
        core_compatibility=core_compatibility,
    )


def test_core_compatibility_none_is_compatible() -> None:
    assert _check_core_compatibility(_meta(None), "0.27.0") is True


def test_core_compatibility_version_in_range() -> None:
    assert _check_core_compatibility(_meta(">=0.28.0,<1.0.0"), "0.29.1") is True


def test_core_compatibility_version_out_of_range() -> None:
    assert _check_core_compatibility(_meta(">=0.28.0,<1.0.0"), "1.2.0") is False


def test_core_compatibility_malformed_specifier_is_non_blocking() -> None:
    assert _check_core_compatibility(_meta("not-a-valid-specifier"), "0.29.1") is True
