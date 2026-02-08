# Tasks: Core Contracts and Module Interface Formalization

## TDD / SDD Order (Enforced)

Per `openspec/config.yaml`, development discipline for SpecFact CLI follows strict SDD+TDD order:

1. **Specs first** — Spec deltas define behavior (Given/When/Then). Already completed in `specs/` directory.
2. **Tests second** — Write unit/integration tests from spec scenarios (one or more tests per scenario); run tests and expect failure (no implementation yet).
3. **Code last** — Implement until tests pass and behavior satisfies the spec. Code must satisfy both (a) spec scenarios and (b) tests.

**Do not implement production code until tests exist and have been run (expecting failure).**

Tests MUST come before implementation tasks in each section below.

---

## 1. Create git branch from dev

- [x] 1.1 Ensure on dev and up to date; create branch `feature/arch-04-core-contracts-interfaces`; verify
  - [x] 1.1.1 `git checkout dev && git pull origin dev`
  - [x] 1.1.2 `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name feature/arch-04-core-contracts-interfaces --checkout` (if issue exists)
  - [x] 1.1.3 Or: `git checkout -b feature/arch-04-core-contracts-interfaces` (if no issue)
  - [x] 1.1.4 `git branch --show-current`

## 2. Foundation: Create contracts directory and protocol definition

- [x] 2.1 Create `src/specfact_cli/contracts/` directory
- [x] 2.2 Create `src/specfact_cli/contracts/__init__.py` (empty or exports)

## 3. Tests: ModuleIOContract protocol (TDD - tests before implementation)

- [x] 3.1 Create `tests/unit/contracts/` directory
- [x] 3.2 Create `tests/unit/contracts/test_module_io_contract.py` with test cases from spec `module-io-contract`:
  - [x] 3.2.1 `test_protocol_defines_four_operations()` - verify Protocol has import_to_bundle, export_from_bundle, sync_with_bundle, validate_bundle
  - [x] 3.2.2 `test_module_without_inheritance_satisfies_protocol()` - structural subtyping test
  - [x] 3.2.3 `test_module_with_partial_implementation_type_checked()` - partial protocol compliance
  - [x] 3.2.4 `test_validation_report_model_structure()` - ValidationReport fields
- [x] 3.3 Run tests: `pytest tests/unit/contracts/test_module_io_contract.py -v`
- [x] 3.4 **EXPECT FAILURE** - ModuleIOContract and ValidationReport don't exist yet

## 4. Implementation: ModuleIOContract protocol and ValidationReport model

- [x] 4.1 Create `src/specfact_cli/contracts/module_interface.py` with:
  - [x] 4.1.1 Import Protocol, abstractmethod, Path from typing/abc/pathlib
  - [x] 4.1.2 Define `ModuleIOContract` Protocol with four methods: import_to_bundle, export_from_bundle, sync_with_bundle, validate_bundle
  - [x] 4.1.3 Add type hints using ProjectBundle from models.project
  - [x] 4.1.4 Add docstrings explaining each operation
- [x] 4.2 Create `ValidationReport` Pydantic model in `src/specfact_cli/models/validation.py`:
  - [x] 4.2.1 Add `status` field with Literal["passed", "failed", "warnings"]
  - [x] 4.2.2 Add `violations` field as list[dict] with severity/message/location
  - [x] 4.2.3 Add `summary` field as dict with total_checks/passed/failed/warnings counts
  - [x] 4.2.4 Add @beartype decorator
- [x] 4.3 Export ValidationReport from `src/specfact_cli/contracts/__init__.py`
- [x] 4.4 Run tests: `pytest tests/unit/contracts/test_module_io_contract.py -v`
- [x] 4.5 **EXPECT PASS** - All protocol tests should pass

## 5. Tests: Core module isolation static analysis (TDD - tests before implementation)

- [x] 5.1 Create `tests/unit/test_core_module_isolation.py` with test cases from spec `core-module-isolation`:
  - [x] 5.1.1 `test_core_has_no_module_imports()` - scan core dirs, fail on `specfact_cli.modules.*` imports
  - [x] 5.1.2 `test_excludes_type_checking_blocks()` - allow imports in `if TYPE_CHECKING:`
  - [x] 5.1.3 `test_multiple_violations_reported_together()` - aggregate violations before failing
  - [x] 5.1.4 `test_violation_message_format()` - verify message includes file:line and module name
  - [x] 5.1.5 Add CORE_DIRS constant: cli.py, registry/, models/, utils/, contracts/
- [x] 5.2 Run test: `pytest tests/unit/test_core_module_isolation.py -v`
- [x] 5.3 **EXPECT PASS** - Should pass initially (no violations in current code)

## 6. Implementation: Core module isolation enforcement

- [x] 6.1 Add helper function `_collect_python_files(dirs: list[Path]) -> list[Path]` to isolation test
- [x] 6.2 Add helper function `_get_module_name(node: ast.Node) -> str` to extract import module name
- [x] 6.3 Add helper function `_is_in_type_checking_block(node: ast.Node, tree: ast.AST) -> bool`
- [x] 6.4 Implement AST parsing logic in `test_core_has_no_module_imports()`:
  - [x] 6.4.1 Walk through AST nodes looking for Import and ImportFrom
  - [x] 6.4.2 Skip nodes within TYPE_CHECKING blocks
  - [x] 6.4.3 Collect violations with file:line:module format
  - [x] 6.4.4 Assert no violations with clear error message
- [x] 6.5 Add `.github/workflows/tests.yml` step for isolation test (if not already covered by pytest all)
- [x] 6.6 Run test: `pytest tests/unit/test_core_module_isolation.py -v`
- [x] 6.7 **EXPECT PASS** - Isolation test should pass on clean code

## 7. Tests: ProjectBundle schema versioning (TDD - tests before implementation)

- [x] 7.1 Create `tests/unit/models/test_project_bundle_schema.py` with tests:
  - [x] 7.1.1 `test_project_bundle_has_schema_version()` - verify schema_version field exists with default "1"
  - [x] 7.1.2 `test_schema_version_can_be_set()` - create ProjectBundle with custom schema_version
  - [x] 7.1.3 `test_schema_version_validation()` - verify Pydantic validates schema_version as string
- [x] 7.2 Run tests: `pytest tests/unit/models/test_project_bundle_schema.py -v`
- [x] 7.3 **EXPECT FAILURE** - schema_version field doesn't exist yet

## 8. Implementation: ProjectBundle schema versioning

- [x] 8.1 Add `schema_version: str = "1"` field to ProjectBundle in `src/specfact_cli/models/project.py`
- [x] 8.2 Add docstring explaining schema versioning strategy
- [x] 8.3 Update ProjectBundle Field(...) with description for schema_version
- [x] 8.4 Run tests: `pytest tests/unit/models/test_project_bundle_schema.py -v`
- [x] 8.5 **EXPECT PASS** - Schema version tests should pass

## 9. Tests: Module package metadata extensions (TDD - tests before implementation)

- [x] 9.1 Create `tests/unit/models/test_module_package_metadata.py` with tests from spec `module-packages`:
  - [x] 9.1.1 `test_metadata_includes_schema_version()` - verify schema_version optional field
  - [x] 9.1.2 `test_metadata_includes_protocol_operations()` - verify protocol_operations list field
  - [x] 9.1.3 `test_metadata_schema_version_defaults_to_none()` - default value test
  - [x] 9.1.4 `test_protocol_operations_defaults_to_empty()` - default value test
- [x] 9.2 Run tests: `pytest tests/unit/models/test_module_package_metadata.py -v`
- [x] 9.3 **EXPECT FAILURE** - New fields don't exist yet

## 10. Implementation: Module package metadata extensions

- [x] 10.1 Update `src/specfact_cli/models/module_package.py` ModulePackageMetadata:
  - [x] 10.1.1 Add `schema_version: str | None = None` field
  - [x] 10.1.2 Add `protocol_operations: list[str] = Field(default_factory=list)` field
  - [x] 10.1.3 Add docstrings for new fields
  - [x] 10.1.4 Add @beartype decorator if not already present
- [x] 10.2 Run tests: `pytest tests/unit/models/test_module_package_metadata.py -v`
- [x] 10.3 **EXPECT PASS** - Metadata extension tests should pass

## 11. Tests: Module discovery protocol validation (TDD - tests before implementation)

- [x] 11.1 Create `tests/unit/registry/test_module_protocol_validation.py` with tests from specs:
  - [x] 11.1.1 `test_discovery_detects_protocol_implementation()` - hasattr checks for ModuleIOContract methods
  - [x] 11.1.2 `test_full_protocol_logged()` - all four methods present
  - [x] 11.1.3 `test_partial_protocol_logged()` - subset of methods present
  - [x] 11.1.4 `test_no_protocol_legacy_mode()` - no methods present
  - [x] 11.1.5 `test_schema_version_compatibility_check()` - compatible/incompatible/missing scenarios
  - [x] 11.1.6 Mock module classes with various protocol implementations
- [x] 11.2 Run tests: `pytest tests/unit/registry/test_module_protocol_validation.py -v`
- [x] 11.3 **EXPECT FAILURE** - Protocol validation not implemented yet

## 12. Implementation: Module discovery protocol validation

- [x] 12.1 Update `src/specfact_cli/registry/module_packages.py`:
  - [x] 12.1.1 Add helper `_check_protocol_compliance(module_class: type) -> list[str]` that checks hasattr for four methods
  - [x] 12.1.2 Add helper `_check_schema_compatibility(module_schema: str | None, current: str) -> bool`
  - [x] 12.1.3 Update `register_module_package_commands()` to call protocol checks
  - [x] 12.1.4 Store protocol_operations in metadata after detection
  - [x] 12.1.5 Log INFO/WARNING based on protocol compliance
  - [x] 12.1.6 Skip registration if schema incompatible
  - [x] 12.1.7 Add @beartype and @icontract decorators to new functions
- [x] 12.2 Run tests: `pytest tests/unit/registry/test_module_protocol_validation.py -v`
- [x] 12.3 **EXPECT PASS** - Protocol validation tests should pass

## 13. Tests: Module implementation updates (TDD - tests before implementation)

- [x] 13.1 For each module (backlog, sync, plan, generate, enforce), create test in `tests/unit/modules/<module>/test_module_io_contract.py`:
  - [x] 13.1.1 `test_module_implements_protocol()` - verify hasattr for ModuleIOContract methods
  - [x] 13.1.2 `test_import_to_bundle_signature()` - verify method signature matches protocol
  - [x] 13.1.3 `test_export_from_bundle_signature()` - verify method signature matches protocol
  - [x] 13.1.4 `test_methods_have_contracts()` - verify @icontract and @beartype decorators present
- [x] 13.2 Run tests: `pytest tests/unit/modules/ -k test_module_io_contract -v`
- [x] 13.3 **EXPECT FAILURE** - Modules don't implement ModuleIOContract yet

## 14. Implementation: Update backlog module (template for others)

- [x] 14.1 Update `src/specfact_cli/modules/backlog/src/commands.py`:
  - [x] 14.1.1 Add ModuleIOContract import from contracts.module_interface
  - [x] 14.1.2 Implement import_to_bundle method with @icontract @require/@ensure and @beartype
  - [x] 14.1.3 Implement export_from_bundle method with contracts
  - [x] 14.1.4 Implement sync_with_bundle method with contracts
  - [x] 14.1.5 Implement validate_bundle method with contracts
  - [x] 14.1.6 Add docstrings for each method
- [x] 14.2 Run tests: `pytest tests/unit/modules/backlog/test_module_io_contract.py -v`
- [x] 14.3 **EXPECT PASS** - Backlog module protocol tests should pass

## 15. Implementation: Update remaining modules (sync, plan, generate, enforce)

- [x] 15.1 Update sync module following backlog template (tasks 14.1.1-14.1.6)
- [x] 15.2 Update plan module following backlog template
- [x] 15.3 Update generate module following backlog template
- [x] 15.4 Update enforce module following backlog template
- [x] 15.5 Run tests: `pytest tests/unit/modules/ -k test_module_io_contract -v`
- [x] 15.6 **EXPECT PASS** - All module protocol tests should pass

## 16. Quality gates and validation

- [x] 16.1 Run formatters: `hatch run format`
- [x] 16.2 Run type checking: `hatch run type-check` (expect no errors)
- [x] 16.3 Run contract tests: `hatch run contract-test` (CrossHair symbolic execution)
- [ ] 16.4 Run full test suite: `hatch test --cover -v` (expect >80% coverage)
- [ ] 16.5 Run linting: `hatch run lint` (expect no errors)
- [x] 16.6 Validate OpenSpec change: `openspec validate arch-04-core-contracts-interfaces --strict`

## 17. Documentation research and review

- [x] 17.1 Identify affected documentation:
  - [x] 17.1.1 List files: `docs/reference/`, `docs/guides/`, `README.md`, `docs/index.md`, `docs/_layouts/default.html`
- [x] 17.2 Create `docs/reference/projectbundle-schema.md`:
  - [x] 17.2.1 Add Jekyll front-matter (layout: default, title: ProjectBundle Schema, permalink, description)
  - [x] 17.2.2 Document ProjectBundle fields, schema_version, and versioning strategy
  - [x] 17.2.3 Include examples of ProjectBundle with schema version
  - [x] 17.2.4 Explain backward compatibility approach
- [x] 17.3 Create `docs/reference/module-contracts.md`:
  - [x] 17.3.1 Add Jekyll front-matter
  - [x] 17.3.2 Document ModuleIOContract protocol with four operations
  - [x] 17.3.3 Provide code examples of implementing the protocol
  - [x] 17.3.4 Explain inversion-of-control architecture (core never imports modules)
  - [x] 17.3.5 Include guidance for 3rd-party module developers
  - [x] 17.3.6 Document ValidationReport structure
- [x] 17.4 Update `docs/reference/architecture.md`:
  - [x] 17.4.1 Add section on contract-first module development
  - [x] 17.4.2 Explain core-module isolation principle
  - [x] 17.4.3 Reference ModuleIOContract protocol
- [x] 17.5 Update `docs/_layouts/default.html` sidebar navigation:
  - [x] 17.5.1 Add link to ProjectBundle Schema under Reference section
  - [x] 17.5.2 Add link to Module Contracts under Reference section
- [x] 17.6 Update `README.md`:
  - [x] 17.6.1 Add brief mention of contract-first module architecture (if relevant to main intro)
- [ ] 17.7 Run documentation link checker: `markdownlint --config .markdownlint.json docs/`
- [ ] 17.8 Verify docs render correctly at <https://docs.specfact.io> (local preview with Jekyll)

## 18. Version and changelog

- [x] 18.1 Determine version bump (minor version for new feature: arch-04 adds contracts)
- [x] 18.2 Update version in `pyproject.toml`
- [x] 18.3 Update version in `setup.py`
- [x] 18.4 Update version in `src/__init__.py`
- [x] 18.5 Update version in `src/specfact_cli/__init__.py`
- [x] 18.6 Add CHANGELOG.md entry under new version section:
  - [x] 18.6.1 Section: `[X.Y.Z] - 2026-02-XX` (use actual date)
  - [x] 18.6.2 `### Added (X.Y.Z)` subsection with:
    - ModuleIOContract protocol for formal module interfaces
    - Static analysis enforcement of core-module isolation
    - ProjectBundle schema versioning (schema_version field)
    - ValidationReport model for structured validation results
    - Protocol compliance tracking in module metadata
  - [x] 18.6.3 `### Changed (X.Y.Z)` subsection:
    - Updated 5 modules (backlog, sync, plan, generate, enforce) to implement ModuleIOContract
  - [x] 18.6.4 Reference GitHub issue: `(fixes #<issue-number>)`

## 19. GitHub issue creation

- [x] 19.1 Create GitHub issue in nold-ai/specfact-cli:
  - [x] 19.1.1 Title: `[Change] Core Contracts and Module Interface Formalization`
  - [x] 19.1.2 Labels: `enhancement`, `change-proposal`
  - [x] 19.1.3 Body from proposal.md: Why, What Changes sections
  - [x] 19.1.4 Add acceptance criteria from proposal Impact section
  - [x] 19.1.5 Footer: `*OpenSpec Change Proposal: arch-04-core-contracts-interfaces*`
  - [x] 19.1.6 Create: `gh issue create --repo nold-ai/specfact-cli --title "..." --body-file /tmp/issue-arch-04.md --label enhancement --label change-proposal`
- [x] 19.2 Link issue to project: `gh project item-add 1 --owner nold-ai --url <ISSUE_URL>`
- [x] 19.3 Update `proposal.md` Source Tracking section with issue number and URL

## 20. Create pull request to dev

- [x] 20.1 Prepare commit:
  - [x] 20.1.1 `git add .`
  - [x] 20.1.2 Commit with conventional message:

    ```bash
    git commit -m "$(cat <<'EOF'
    feat: add ModuleIOContract protocol and core-module isolation

    - Create ModuleIOContract protocol with four core operations
    - Add static analysis enforcement preventing core→module imports
    - Add ProjectBundle schema versioning (schema_version field)
    - Update 5 modules to implement ModuleIOContract
    - Add protocol compliance tracking in module discovery
    - Create docs for ProjectBundle schema and module contracts

    Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
    EOF
    )"
    ```

  - [x] 20.1.3 `git push origin feature/arch-04-core-contracts-interfaces`
- [x] 20.2 Create PR body from `.github/pull_request_template.md`:
  - [x] 20.2.1 Use full repo path for issue ref: `Fixes nold-ai/specfact-cli#<number>`
  - [x] 20.2.2 Include OpenSpec change ID in description
  - [x] 20.2.3 List key deliverables: protocol, isolation test, schema versioning, module updates, docs
- [x] 20.3 Create PR:

  ```bash
  gh pr create --repo nold-ai/specfact-cli --base dev --head feature/arch-04-core-contracts-interfaces --title "feat: Core Contracts and Module Interface Formalization" --body-file /tmp/pr-body-arch-04.md
  ```

- [x] 20.4 Link PR to project: `gh project item-add 1 --owner nold-ai --url <PR_URL>`
- [ ] 20.5 Verify Development link appears on GitHub issue
- [ ] 20.6 Update project board status to "In Progress" (if applicable)
