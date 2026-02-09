# Tasks: Bridge Registry for Cross-Module Service Interoperability

## TDD / SDD Order (Enforced)

Per `openspec/config.yaml`, development discipline follows strict SDD+TDD order:

1. **Specs first** - Spec deltas define behavior in Given/When/Then scenarios.
2. **Tests second** - Write tests from scenarios, run tests, and expect failure before implementation.
3. **Code last** - Implement until tests pass and behavior matches spec scenarios.

Do not implement production code for new behavior until corresponding tests exist and have been run expecting failure.

---

## 1. Create git branch from dev

- [x] 1.1 Ensure `dev` is current and create `feature/arch-05-bridge-registry`
- [x] 1.2 Verify current branch is `feature/arch-05-bridge-registry`

## 2. Tests: bridge registry contract (TDD)

- [x] 2.1 Add `tests/unit/registry/test_bridge_registry.py`
- [x] 2.2 Add tests for register/get behavior and duplicate bridge ID handling
- [x] 2.3 Add tests for missing bridge lookup error behavior
- [x] 2.4 Run `pytest tests/unit/registry/test_bridge_registry.py -v` and expect failure

## 3. Implementation: bridge registry

- [x] 3.1 Create `src/specfact_cli/registry/bridge_registry.py`
- [x] 3.2 Define `SchemaConverter` protocol (`to_bundle`, `from_bundle`) with type hints
- [x] 3.3 Implement `BridgeRegistry` registration and retrieval methods
- [x] 3.4 Add `@beartype` and `@icontract` decorators to public APIs
- [x] 3.5 Run `pytest tests/unit/registry/test_bridge_registry.py -v` and expect pass

## 4. Tests: module manifest service bridge metadata (TDD)

- [x] 4.1 Add tests in `tests/unit/models/test_module_package_metadata.py` for `service_bridges`
- [x] 4.2 Add tests for valid and invalid converter class path metadata
- [x] 4.3 Run `pytest tests/unit/models/test_module_package_metadata.py -v` and expect failure for new fields

## 5. Implementation: manifest metadata extension

- [x] 5.1 Update `src/specfact_cli/models/module_package.py` with `service_bridges` metadata model
- [x] 5.2 Add validation for required bridge metadata keys (`id`, `converter_class`)
- [x] 5.3 Add `@beartype` and `@icontract` decorators to public validation methods
- [x] 5.4 Run `pytest tests/unit/models/test_module_package_metadata.py -v` and expect pass

## 6. Tests: lifecycle bridge registration flow (TDD)

- [x] 6.1 Add `tests/unit/registry/test_module_bridge_registration.py`
- [x] 6.2 Add tests for manifest-driven bridge loading in `register_module_package_commands()`
- [x] 6.3 Add tests that invalid bridge declarations are skipped with warnings, not fatal
- [x] 6.4 Run `pytest tests/unit/registry/test_module_bridge_registration.py -v` and expect failure

## 7. Implementation: lifecycle integration

- [x] 7.1 Update `src/specfact_cli/registry/module_packages.py` to parse and validate `service_bridges`
- [x] 7.2 Register declared bridges through `BridgeRegistry`
- [x] 7.3 Add deterministic handling for duplicate bridge IDs
- [x] 7.4 Ensure no direct core imports from module command internals
- [x] 7.5 Run `pytest tests/unit/registry/test_module_bridge_registration.py -v` and expect pass

## 8. Tests: protocol reporting accuracy and warning deduplication (TDD)

- [x] 8.1 Extend `tests/unit/specfact_cli/registry/test_module_packages.py` with protocol compliance detection assertions for full/partial/legacy modules
- [x] 8.2 Add test coverage ensuring lifecycle warnings are not emitted twice for the same module condition
- [ ] 8.3 Add CLI smoke assertion (`specfact -v`) for single summary emission pattern
- [x] 8.4 Run targeted registry tests and expect failure

## 9. Implementation: protocol reporting and logging cleanup

- [x] 9.1 Update protocol inspection path in `src/specfact_cli/registry/module_packages.py` to classify compliant modules correctly
- [x] 9.2 Ensure protocol operations are persisted on `ModulePackageMetadata.protocol_operations` from effective runtime interface
- [x] 9.3 Eliminate duplicate warning emission in lifecycle startup logs (registry/logger integration)
- [x] 9.4 Run targeted registry tests and expect pass

## 10. Tests: backlog bridge converters (TDD)

- [x] 10.1 Add tests under `tests/unit/modules/backlog/` for converter contract compliance
- [x] 10.2 Add tests for ADO, Jira, Linear, GitHub converter mapping behavior
- [x] 10.3 Add tests for custom mapping override loading behavior
- [x] 10.4 Run `pytest tests/unit/modules/backlog -k converter -v` and expect failure

## 11. Implementation: backlog bridge converters and module protocol migration completion

- [x] 11.1 Add converter modules under `src/specfact_cli/modules/backlog/src/adapters/`
- [x] 11.2 Update backlog module manifest to declare `service_bridges`
- [x] 11.3 Ensure converters satisfy `SchemaConverter` protocol and contract decorators
- [x] 11.4 Upgrade remaining modules to implement/ expose ModuleIOContract operations required for non-legacy classification
- [x] 11.5 Run `pytest tests/unit/modules/backlog -k converter -v` and expect pass
- [x] 11.6 Run module protocol tests and verify improved compliance summary

## 12. Quality gates and validation

- [x] 12.1 Run `hatch run format`
- [ ] 12.2 Run `hatch run lint`
- [x] 12.3 Run `hatch run type-check`
- [x] 12.4 Run `hatch run contract-test`
- [x] 12.5 Run `hatch run smart-test`
- [x] 12.6 Run `openspec validate arch-05-bridge-registry --strict`

## 13. Documentation research and review

- [x] 13.1 Identify affected docs: `docs/reference/`, `docs/guides/`, `README.md`, `docs/index.md`
- [x] 13.2 Add `docs/reference/bridge-registry.md` with contract and usage examples
- [x] 13.3 Add `docs/guides/creating-custom-bridges.md` with manifest and converter examples
- [x] 13.4 Update `docs/reference/architecture.md` with bridge registry integration notes
- [x] 13.5 Document protocol compliance reporting behavior and migration status in reference docs
- [x] 13.6 Update `docs/_layouts/default.html` sidebar links for new docs

## 14. Version and changelog

- [x] 14.1 Determine semantic version bump for new capability
- [x] 14.2 Sync version updates in `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py`
- [x] 14.3 Add CHANGELOG entry for bridge registry, protocol-reporting fixes, and manifest bridge metadata support

## 15. GitHub issue creation

- [x] 15.1 Create issue in `nold-ai/specfact-cli` with title `[Change] Bridge Registry for Cross-Module Service Interoperability`
- [x] 15.2 Use labels `enhancement` and `change-proposal`
- [x] 15.3 Build issue body from proposal Why/What Changes and append footer `*OpenSpec Change Proposal: arch-05-bridge-registry*`
- [x] 15.4 Update `proposal.md` Source Tracking with issue number and URL

## 16. Create pull request to dev (LAST)

- [x] 16.1 Commit all completed work with conventional commit message
- [x] 16.2 Push branch `feature/arch-05-bridge-registry`
- [ ] 16.3 Create PR to `dev` with OpenSpec change reference and quality gate evidence
