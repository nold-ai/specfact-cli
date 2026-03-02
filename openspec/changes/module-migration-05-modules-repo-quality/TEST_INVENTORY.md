# TEST_INVENTORY for module-migration-05-modules-repo-quality

This file lists tests in `specfact-cli` that exercise the 17 migrated modules / 5 bundles,
and the target locations in `specfact-cli-modules`.

## Unit tests (specfact-cli)

- `tests/unit/bundles/test_bundle_layout.py` → bundles: specfact-project, specfact-backlog, specfact-codebase, specfact-spec, specfact-govern → target: `tests/unit/bundles/test_bundle_layout.py`
- `tests/unit/specfact_cli/registry/test_module_packages.py` → bundles: all (registry wiring) → target: `tests/unit/registry/test_module_packages.py`
- `tests/unit/specfact_cli/registry/test_module_lifecycle.py` → bundles: all → target: `tests/unit/registry/test_module_lifecycle.py`
- `tests/unit/registry/test_module_discovery.py` → bundles: all → target: `tests/unit/registry/test_module_discovery.py`
- `tests/unit/registry/test_module_installer.py` → bundles: all → target: `tests/unit/registry/test_module_installer.py`
- `tests/unit/registry/test_marketplace_client.py` → bundles: all → target: `tests/unit/registry/test_marketplace_client.py`
- `tests/unit/scripts/test_publish_module_bundle.py` → bundles: all → target: `tests/unit/scripts/test_publish_module_bundle.py`
- `tests/unit/registry/test_category_groups.py` → bundles: all → target: `tests/unit/registry/test_category_groups.py`
- `tests/unit/registry/test_module_grouping.py` → bundles: all → target: `tests/unit/registry/test_module_grouping.py`
- `tests/unit/registry/test_custom_registries.py` → bundles: all → target: `tests/unit/registry/test_custom_registries.py`
- `tests/unit/registry/test_module_security.py` → bundles: all → target: `tests/unit/registry/test_module_security.py`
- `tests/unit/registry/test_bridge_registry.py` → bundles: all → target: `tests/unit/registry/test_bridge_registry.py`
- `tests/unit/registry/test_module_bridge_registration.py` → bundles: all → target: `tests/unit/registry/test_module_bridge_registration.py`
- `tests/unit/registry/test_cross_bundle_imports.py` → bundles: all → target: `tests/unit/registry/test_cross_bundle_imports.py`
- `tests/unit/specfact_cli/test_module_migration_compatibility.py` → bundles: all → target: `tests/unit/specfact_cli/test_module_migration_compatibility.py`

## Integration tests (specfact-cli)

- `tests/integration/test_bundle_install.py` → bundles: all → target: `tests/integration/test_bundle_install.py`
- `tests/integration/test_category_group_routing.py` → bundles: all → target: `tests/integration/test_category_group_routing.py`

## E2E tests (specfact-cli)

- `tests/e2e/test_bundle_extraction_e2e.py` → bundles: all → target: `tests/e2e/test_bundle_extraction_e2e.py`

