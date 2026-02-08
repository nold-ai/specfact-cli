# Tasks: Bridge Registry for Cross-Module Service Interoperability

## TDD / SDD Order (Enforced)

Per `openspec/config.yaml`, development discipline follows strict SDD+TDD order:

1. **Specs first** - Spec deltas define behavior in Given/When/Then scenarios.
2. **Tests second** - Write tests from scenarios, run tests, and expect failure before implementation.
3. **Code last** - Implement until tests pass and behavior matches spec scenarios.

Do not implement production code for new behavior until corresponding tests exist and have been run expecting failure.

---

## 1. Create git branch from dev

- [ ] 1.1 Ensure `dev` is current and create `feature/arch-05-bridge-registry`
- [ ] 1.2 Verify current branch is `feature/arch-05-bridge-registry`

## 2. Tests: bridge registry contract (TDD)

- [ ] 2.1 Add `tests/unit/registry/test_bridge_registry.py`
- [ ] 2.2 Add tests for register/get behavior and duplicate bridge ID handling
- [ ] 2.3 Add tests for missing bridge lookup error behavior
- [ ] 2.4 Run `pytest tests/unit/registry/test_bridge_registry.py -v` and expect failure

## 3. Implementation: bridge registry

- [ ] 3.1 Create `src/specfact_cli/registry/bridge_registry.py`
- [ ] 3.2 Define `SchemaConverter` protocol (`to_bundle`, `from_bundle`) with type hints
- [ ] 3.3 Implement `BridgeRegistry` registration and retrieval methods
- [ ] 3.4 Add `@beartype` and `@icontract` decorators to public APIs
- [ ] 3.5 Run `pytest tests/unit/registry/test_bridge_registry.py -v` and expect pass

## 4. Tests: module manifest service bridge metadata (TDD)

- [ ] 4.1 Add tests in `tests/unit/models/test_module_package_metadata.py` for `service_bridges`
- [ ] 4.2 Add tests for valid and invalid converter class path metadata
- [ ] 4.3 Run `pytest tests/unit/models/test_module_package_metadata.py -v` and expect failure for new fields

## 5. Implementation: manifest metadata extension

- [ ] 5.1 Update `src/specfact_cli/models/module_package.py` with `service_bridges` metadata model
- [ ] 5.2 Add validation for required bridge metadata keys (`id`, `converter_class`)
- [ ] 5.3 Add `@beartype` and `@icontract` decorators to public validation methods
- [ ] 5.4 Run `pytest tests/unit/models/test_module_package_metadata.py -v` and expect pass

## 6. Tests: lifecycle bridge registration flow (TDD)

- [ ] 6.1 Add `tests/unit/registry/test_module_bridge_registration.py`
- [ ] 6.2 Add tests for manifest-driven bridge loading in `register_module_package_commands()`
- [ ] 6.3 Add tests that invalid bridge declarations are skipped with warnings, not fatal
- [ ] 6.4 Run `pytest tests/unit/registry/test_module_bridge_registration.py -v` and expect failure

## 7. Implementation: lifecycle integration

- [ ] 7.1 Update `src/specfact_cli/registry/module_packages.py` to parse and validate `service_bridges`
- [ ] 7.2 Register declared bridges through `BridgeRegistry`
- [ ] 7.3 Add deterministic handling for duplicate bridge IDs
- [ ] 7.4 Ensure no direct core imports from module command internals
- [ ] 7.5 Run `pytest tests/unit/registry/test_module_bridge_registration.py -v` and expect pass

## 8. Tests: protocol reporting accuracy and warning deduplication (TDD)

- [ ] 8.1 Extend `tests/unit/specfact_cli/registry/test_module_packages.py` with protocol compliance detection assertions for full/partial/legacy modules
- [ ] 8.2 Add test coverage ensuring lifecycle warnings are not emitted twice for the same module condition
- [ ] 8.3 Add CLI smoke assertion (`specfact -v`) for single summary emission pattern
- [ ] 8.4 Run targeted registry tests and expect failure

## 9. Implementation: protocol reporting and logging cleanup

- [ ] 9.1 Update protocol inspection path in `src/specfact_cli/registry/module_packages.py` to classify compliant modules correctly
- [ ] 9.2 Ensure protocol operations are persisted on `ModulePackageMetadata.protocol_operations` from effective runtime interface
- [ ] 9.3 Eliminate duplicate warning emission in lifecycle startup logs (registry/logger integration)
- [ ] 9.4 Run targeted registry tests and expect pass

## 10. Tests: backlog bridge converters (TDD)

- [ ] 10.1 Add tests under `tests/unit/modules/backlog/` for converter contract compliance
- [ ] 10.2 Add tests for ADO, Jira, Linear, GitHub converter mapping behavior
- [ ] 10.3 Add tests for custom mapping override loading behavior
- [ ] 10.4 Run `pytest tests/unit/modules/backlog -k converter -v` and expect failure

## 11. Implementation: backlog bridge converters and module protocol migration completion

- [ ] 11.1 Add converter modules under `src/specfact_cli/modules/backlog/src/adapters/`
- [ ] 11.2 Update backlog module manifest to declare `service_bridges`
- [ ] 11.3 Ensure converters satisfy `SchemaConverter` protocol and contract decorators
- [ ] 11.4 Upgrade remaining modules to implement/ expose ModuleIOContract operations required for non-legacy classification
- [ ] 11.5 Run `pytest tests/unit/modules/backlog -k converter -v` and expect pass
- [ ] 11.6 Run module protocol tests and verify improved compliance summary

## 12. Quality gates and validation

- [ ] 12.1 Run `hatch run format`
- [ ] 12.2 Run `hatch run lint`
- [ ] 12.3 Run `hatch run type-check`
- [ ] 12.4 Run `hatch run contract-test`
- [ ] 12.5 Run `hatch run smart-test`
- [ ] 12.6 Run `openspec validate arch-05-bridge-registry --strict`

## 13. Documentation research and review

- [ ] 13.1 Identify affected docs: `docs/reference/`, `docs/guides/`, `README.md`, `docs/index.md`
- [ ] 13.2 Add `docs/reference/bridge-registry.md` with contract and usage examples
- [ ] 13.3 Add `docs/guides/creating-custom-bridges.md` with manifest and converter examples
- [ ] 13.4 Update `docs/reference/architecture.md` with bridge registry integration notes
- [ ] 13.5 Document protocol compliance reporting behavior and migration status in reference docs
- [ ] 13.6 Update `docs/_layouts/default.html` sidebar links for new docs

## 14. Version and changelog

- [ ] 14.1 Determine semantic version bump for new capability
- [ ] 14.2 Sync version updates in `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py`
- [ ] 14.3 Add CHANGELOG entry for bridge registry, protocol-reporting fixes, and manifest bridge metadata support

## 15. GitHub issue creation

- [ ] 15.1 Create issue in `nold-ai/specfact-cli` with title `[Change] Bridge Registry for Cross-Module Service Interoperability`
- [ ] 15.2 Use labels `enhancement` and `change-proposal`
- [ ] 15.3 Build issue body from proposal Why/What Changes and append footer `*OpenSpec Change Proposal: arch-05-bridge-registry*`
- [ ] 15.4 Update `proposal.md` Source Tracking with issue number and URL

## 16. Create pull request to dev (LAST)

- [ ] 16.1 Commit all completed work with conventional commit message
- [ ] 16.2 Push branch `feature/arch-05-bridge-registry`
- [ ] 16.3 Create PR to `dev` with OpenSpec change reference and quality gate evidence
