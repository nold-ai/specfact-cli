"""Property tests for dependency resolver constraint aggregation."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from hypothesis import given, strategies as st

from specfact_cli.models.module_package import ModulePackageMetadata, VersionedPipDependency
from specfact_cli.registry import module_installer
from specfact_cli.registry.dependency_resolver import _collect_constraints
from specfact_cli.registry.module_installer import _dependency_version_satisfies, _extract_bundle_dependency_specs


PACKAGE_NAMES = st.from_regex(r"[a-z][a-z0-9-]{1,12}", fullmatch=True)
VERSION_NUMBERS = st.tuples(
    st.integers(min_value=0, max_value=9),
    st.integers(min_value=0, max_value=20),
    st.integers(min_value=0, max_value=20),
).map(lambda parts: ".".join(str(part) for part in parts))
SPECIFIERS = st.sampled_from([">=0.1.0", ">=1.0.0", "<2.0.0", "==1.2.3", ""])


@given(st.lists(PACKAGE_NAMES, min_size=1, max_size=12))
def test_collect_constraints_dedupes_after_trimming(raw_names: list[str]) -> None:
    """Whitespace variants of the same dependency must not create duplicate constraints."""
    pip_dependencies = [f" {name} " for name in raw_names] + raw_names
    metadata = ModulePackageMetadata(
        name="property-module",
        version="0.1.0",
        commands=["property"],
        pip_dependencies=pip_dependencies,
    )

    constraints = _collect_constraints([metadata])

    assert constraints == list(dict.fromkeys(name.strip() for name in pip_dependencies if name.strip()))


@given(PACKAGE_NAMES, st.sampled_from([">=1.0.0", "<2.0.0", "==1.2.3"]))
def test_collect_constraints_dedupes_versioned_after_trimming(name: str, specifier: str) -> None:
    """Whitespace variants of versioned dependencies collapse to one canonical constraint."""
    metadata = ModulePackageMetadata(
        name="property-module",
        version="0.1.0",
        commands=["property"],
        pip_dependencies_versioned=[
            VersionedPipDependency(name=f" {name} ", version_specifier=f" {specifier} "),
            VersionedPipDependency(name=name, version_specifier=specifier),
        ],
    )

    assert _collect_constraints([metadata]) == [f"{name}{specifier}"]


@given(PACKAGE_NAMES, SPECIFIERS)
def test_bundle_dependency_specs_accept_string_and_object_forms(name: str, specifier: str) -> None:
    """Registry bundle dependencies support legacy strings and versioned objects."""
    raw = {
        "bundle_dependencies": [
            f"nold-ai/{name}",
            {"id": f"nold-ai/{name}-extra", "version": specifier},
        ]
    }

    specs = _extract_bundle_dependency_specs(raw)

    assert [spec.module_id for spec in specs] == [f"nold-ai/{name}", f"nold-ai/{name}-extra"]
    assert specs[1].version_specifier == specifier


@given(PACKAGE_NAMES)
def test_bundle_dependency_specs_trim_registry_ids(name: str) -> None:
    """Registry identity parsing normalizes harmless surrounding whitespace."""
    specs = _extract_bundle_dependency_specs({"bundle_dependencies": [f"  nold-ai/{name}  "]})

    assert [spec.module_id for spec in specs] == [f"nold-ai/{name}"]


@given(st.text(min_size=1, max_size=24).filter(lambda value: not value.islower() or "_" in value or "/" not in value))
def test_bundle_dependency_specs_reject_invalid_registry_ids(raw_id: str) -> None:
    """Registry ids outside namespace/name lowercase-hyphen form fail closed."""
    try:
        _extract_bundle_dependency_specs({"bundle_dependencies": [raw_id]})
    except ValueError as exc:
        message = str(exc)
        assert (
            "Marketplace module id must match namespace/name" in message or "string entry must be non-empty" in message
        )
    else:
        raise AssertionError(f"expected ValueError for invalid registry id {raw_id!r}")


@given(st.one_of(st.none(), st.text(), st.dictionaries(st.text(), st.text())))
def test_bundle_dependency_specs_reject_non_list_values(raw_dependencies: object) -> None:
    """Malformed dependency containers fail closed instead of being silently ignored."""
    if isinstance(raw_dependencies, list):
        return
    try:
        _extract_bundle_dependency_specs({"bundle_dependencies": raw_dependencies})
    except ValueError as exc:
        assert "bundle_dependencies must be a list" in str(exc)
    else:
        raise AssertionError("expected ValueError for malformed bundle_dependencies")


@given(VERSION_NUMBERS, VERSION_NUMBERS)
def test_dependency_version_satisfaction_matches_monotonic_lower_bound(installed: str, required: str) -> None:
    """A >= lower-bound specifier should match packaging's monotonic version ordering."""
    installed_parts = tuple(int(part) for part in installed.split("."))
    required_parts = tuple(int(part) for part in required.split("."))

    assert _dependency_version_satisfies(installed, f">={required}") is (installed_parts >= required_parts)


@given(PACKAGE_NAMES)
def test_self_bundle_dependency_does_not_recurse(name: str) -> None:
    """A direct self-dependency is treated as satisfied and never recurses into install_module."""
    module_id = f"nold-ai/{name}"

    def _unexpected_install(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("self-dependency should not call install_module")

    with (
        TemporaryDirectory() as tmp_dir,
        patch.object(module_installer, "install_module", _unexpected_install),
        patch.object(module_installer, "discover_all_modules", return_value=[]),
        patch.object(module_installer, "resolve_dependencies", return_value=[]),
        patch.object(module_installer, "install_resolved_pip_requirements", return_value=None),
    ):
        ctx = module_installer._BundleDepsInstallContext(
            metadata={"bundle_dependencies": [module_id]},
            metadata_obj=ModulePackageMetadata(name=name, version="0.1.0", commands=[name]),
            target_root=Path(tmp_dir),
            trust_non_official=False,
            non_interactive=True,
            force=False,
            logger=logging.getLogger(__name__),
        )

        module_installer._install_bundle_dependencies_for_module(module_id, ctx)
