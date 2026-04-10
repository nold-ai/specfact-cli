# Spec: Core Module Isolation

## ADDED Requirements

### Requirement: Static analysis test enforces zero core-to-module imports

The system SHALL provide a pytest test `tests/unit/test_core_module_isolation.py` that parses AST of core CLI code and fails if any import from `specfact_cli.modules.*` is found.

#### Scenario: Test scans core directories for module imports

- **WHEN** test_core_has_no_module_imports runs
- **THEN** it SHALL scan all Python files in: cli.py, registry/, models/, utils/, contracts/
- **AND** SHALL parse each file's AST looking for Import and ImportFrom nodes

#### Scenario: Test fails on direct module import

- **WHEN** core code contains `import specfact_cli.modules.backlog`
- **THEN** test SHALL fail with message: "<file>:<line> imports specfact_cli.modules.backlog"
- **AND** SHALL list exact file path and line number

#### Scenario: Test fails on from-import of module code

- **WHEN** core code contains `from specfact_cli.modules.sync.src import commands`
- **THEN** test SHALL fail with message: "<file>:<line> imports from specfact_cli.modules.sync.src"
- **AND** SHALL prevent PR merge via CI

#### Scenario: Test allows non-module imports

- **WHEN** core code contains `import specfact_cli.models`
- **THEN** test SHALL pass
- **AND** SHALL NOT flag imports from non-module core directories

### Requirement: Test excludes TYPE_CHECKING blocks

The system SHALL exclude imports within `if TYPE_CHECKING:` blocks from static analysis violations.

#### Scenario: Type hint import in TYPE_CHECKING block is allowed

- **WHEN** core code has `if TYPE_CHECKING: from specfact_cli.modules.backlog import BacklogAdapter`
- **THEN** test SHALL pass
- **AND** SHALL NOT flag as violation since it's only for type checking

#### Scenario: Runtime import disguised as TYPE_CHECKING is caught

- **WHEN** code uses module import outside TYPE_CHECKING but has TYPE_CHECKING block elsewhere
- **THEN** test SHALL still fail on the runtime import
- **AND** SHALL distinguish between conditional type imports and runtime imports

### Requirement: CI enforces isolation test

The system SHALL run `test_core_module_isolation.py` in `.github/workflows/tests.yml` and block PRs that violate core isolation.

#### Scenario: CI runs isolation test on every PR

- **WHEN** PR is opened with core code changes
- **THEN** GitHub Actions SHALL run `pytest tests/unit/test_core_module_isolation.py`
- **AND** SHALL block merge if test fails

#### Scenario: CI provides actionable error message on violation

- **WHEN** isolation test fails in CI
- **THEN** GitHub Actions log SHALL show file path, line number, and import statement
- **AND** SHALL guide developer to use registry pattern instead of direct import

### Requirement: Test provides clear violation messages

The system SHALL format violation messages with file path, line number, and imported module name for easy debugging.

#### Scenario: Violation message includes context

- **WHEN** violation is detected at src/specfact_cli/cli.py line 42
- **THEN** message SHALL be: "src/specfact_cli/cli.py:42 imports specfact_cli.modules.backlog.src.commands"
- **AND** SHALL aggregate all violations before failing (not fail on first)

#### Scenario: Multiple violations are reported together

- **WHEN** multiple core files import from modules
- **THEN** test SHALL list all violations in a single failure message
- **AND** SHALL show total count: "Found 3 core-to-module import violations"

### Requirement: Test is fast and maintainable

The system SHALL ensure the static analysis test completes in under 2 seconds and requires no external dependencies beyond Python standard library.

#### Scenario: Test parses AST efficiently

- **WHEN** test runs on full codebase
- **THEN** it SHALL complete within 2 seconds
- **AND** SHALL use ast.parse() from standard library (no external parsers)

#### Scenario: Test core directories are configurable

- **WHEN** new core directories are added (e.g., contracts/)
- **THEN** test SHALL have a CORE_DIRS constant at top of file
- **AND** SHALL be easily updated by adding new Path to the list

### Requirement: Inversion-of-control enforcement via registry pattern

The system SHALL enforce that core CLI accesses modules only via CommandRegistry lazy loading, never via direct imports.

#### Scenario: Core uses registry for module access

- **WHEN** core CLI needs to invoke a module command
- **THEN** it SHALL call `CommandRegistry.get_typer(command_name)`
- **AND** SHALL NOT import module code directly

#### Scenario: Module code is loaded lazily on demand

- **WHEN** CommandRegistry.get_typer() is called
- **THEN** module SHALL be loaded via importlib.util.module_from_spec
- **AND** SHALL NOT be imported at CLI startup

#### Scenario: Core-to-registry is allowed import

- **WHEN** core CLI imports from `specfact_cli.registry`
- **THEN** static analysis test SHALL pass
- **AND** SHALL distinguish between registry access (allowed) and module access (forbidden)

### Requirement: Documentation of isolation principle

The system SHALL document the core-module isolation principle in `docs/reference/module-contracts.md` for 3rd-party module developers.

#### Scenario: Docs explain inversion-of-control architecture

- **WHEN** developer reads module-contracts.md
- **THEN** docs SHALL explain that core never imports modules
- **AND** SHALL illustrate registry pattern with code examples

#### Scenario: Docs guide module developers on protocol implementation

- **WHEN** developer wants to create a marketplace module
- **THEN** docs SHALL show how to implement ModuleIOContract
- **AND** SHALL clarify that modules are discovered and loaded, not imported by core
