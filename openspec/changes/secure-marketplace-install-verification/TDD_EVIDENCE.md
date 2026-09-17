# TDD Evidence: secure-marketplace-install-verification

## Failing-before

- **Timestamp**: 2026-09-06 23:54 UTC
- **Command**: `hatch run python -m pytest tests/unit/registry/test_module_installer.py::test_install_module_verifies_official_artifact_before_dependencies -q`
- **Result**: Failed as expected before production edits.
- **Summary**: The dependency callback ran before the only artifact-verification call, and that late call omitted both `require_integrity` and `require_signature`.

## Passing-after

- **Timestamp**: 2026-09-06 23:55 UTC
- **Command**: `hatch run python -m pytest tests/unit/registry/test_module_installer.py -q`
- **Result**: Passed, 37 tests.
- **Summary**: The official artifact regression proves verification is the first event, requires integrity and signature policy, and blocks all dependency processing when verification fails.

- **Timestamp**: 2026-09-06 23:56 UTC
- **Command**: `hatch run python -m pytest tests/unit/registry/test_module_installer.py tests/unit/validators/test_bundle_dependency_install.py tests/unit/registry/test_dependency_resolver_properties.py -q`
- **Result**: Passed, 50 tests.
- **Summary**: Marketplace placement, recursive bundle dependencies, cached archives, dependency identity, and dependency parsing remain compatible.

## Quality and security gates

- `hatch run openspec validate secure-marketplace-install-verification --strict`: passed.
- `hatch run format`: passed.
- `hatch run type-check`: passed with zero errors (repository-wide advisory warnings remain).
- `hatch run lint`: passed.
- `hatch run yaml-lint`: reported pre-existing archived/evidence YAML line-length findings but returned success.
- `hatch run contract-test`: passed from cached unchanged-file results.
- `hatch run python scripts/check_reproducible_delivery.py` and `uv lock --check`: passed after synchronizing the package version in `uv.lock`.
- `bash tools/run_basedpyright.sh --project pyproject.toml --outputjson > /tmp/specfact-basedpyright.json`: passed with zero errors.
- `hatch run security-audit`: passed with no unreviewed frozen-graph vulnerabilities.
- `hatch run semgrep-sast --json --output logs/static-analysis/semgrep.json`, the baseline gate, and `hatch run bandit-scan`: passed with no blocking findings.
- `hatch run verify-modules-signature`: passed for all four bundled module manifests; no signed module assets changed.
- `hatch run smart-test`: the focused and relevant integration tests passed, but the full baseline ended with three unrelated failures: two unavailable companion-module imports and a version-pinning test subsequently updated to `0.55.5`. The updated version test passes in the final focused rerun.
- `hatch run specfact code review run --scope changed --json --out .specfact/code-review.json`: no code findings were produced, but the verdict remained `UNKNOWN` because the review module's verified OCI analyzer cache entries are unavailable in this environment.

## Documentation review

- Reviewed marketplace/security references under `docs/`, plus `README.md`, `docs/index.md`, and navigation.
- Updated `docs/reference/module-security.md` and `docs/module-system/module-marketplace.md` to document mandatory official signatures and verification-before-dependencies; no command, page, or navigation changes were needed.
