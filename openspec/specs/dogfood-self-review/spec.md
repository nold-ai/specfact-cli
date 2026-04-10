# dogfood-self-review Specification

## Purpose

TBD - created by archiving change code-review-zero-findings. Update Purpose after archive.

## Requirements

### Requirement: Self-review policy — specfact-cli runs specfact review on itself

The specfact-cli repository SHALL be subject to `specfact review` as a first-class CI gate, enforcing the same zero-finding standard we recommend to customers.

#### Scenario: Review run on own repo produces zero findings

- **WHEN** `specfact review` is executed against the specfact-cli repository root
- **THEN** `overall_verdict` is `PASS`
- **AND** the findings array is empty
- **AND** the process exits with code 0

#### Scenario: Review run failure blocks CI

- **WHEN** `specfact review` exits with code non-zero on a PR targeting `dev` or `main`
- **THEN** the CI pipeline marks the PR check as failed
- **AND** the PR cannot be merged until findings are resolved

#### Scenario: Review result is machine-readable

- **WHEN** `specfact review --format json` is run in CI
- **THEN** a JSON report is written to `.specfact/code-review.json`
- **AND** the report schema_version is `1.0`
- **AND** `overall_verdict`, `score`, `findings`, and `ci_exit_code` fields are present

#### Scenario: Expanded clean-code categories stay at zero findings

- **GIVEN** the expanded clean-code pack is available from the review module
- **WHEN** `specfact review` runs against the specfact-cli repository root with clean-code categories enabled
- **THEN** categories `naming`, `kiss`, `yagni`, `dry`, and `solid` each report zero findings
- **AND** the zero-finding proof is recorded in `TDD_EVIDENCE.md`

### Requirement: Type-safe codebase — zero basedpyright findings in strict mode

All public API class members and function signatures in `src/specfact_cli/` SHALL be explicitly typed so that `basedpyright` strict mode reports zero `reportUnknownMemberType`, `reportAttributeAccessIssue`, and `reportUnsupportedDunderAll` findings.

#### Scenario: basedpyright strict mode passes on src/

- **WHEN** `hatch run type-check` is executed
- **THEN** basedpyright reports zero errors and zero warnings for files under `src/specfact_cli/`

#### Scenario: Untyped class member introduced in PR fails CI

- **WHEN** a PR introduces a class member without a type annotation
- **THEN** `hatch run type-check` exits non-zero
- **AND** CI marks the type-check step as failed

#### Scenario: TypedDict used for structured dict shapes

- **WHEN** a function accepts or returns a dict with a known schema
- **THEN** a `TypedDict` or Pydantic model is used rather than `dict[str, Any]`
- **AND** basedpyright infers the member types without `reportUnknownMemberType`

### Requirement: Print-free source — all production logging via bridge logger

No `print()` builtin calls SHALL appear in files under `src/specfact_cli/`, `scripts/`, or `tools/`, as detected by the semgrep `print-in-src` rule.

#### Scenario: Logging call replaces print in adapter layer

- **WHEN** `get_bridge_logger()` is called in an adapter module (e.g., `adapters/ado.py`)
- **THEN** structured log messages are routed to the debug log file when `--debug` is active
- **AND** no `print()` call remains in the file
- **AND** semgrep `print-in-src` reports zero findings for that file

#### Scenario: Script-layer progress output uses Rich console or stdlib logging

- **WHEN** a script in `scripts/` or `tools/` needs to write progress to stdout
- **THEN** it uses `rich.console.Console().print()` or `logging.getLogger(__name__)`, not the stdlib `print` builtin
- **AND** semgrep `print-in-src` reports zero findings for that file

### Requirement: Full contract coverage — all public APIs carry icontract decorators

Every public function (non-underscore-prefixed) in `src/specfact_cli/` SHALL have at least one `@require` or `@ensure` decorator from icontract, and a `@beartype` decorator for runtime type enforcement.

#### Scenario: Public function without @require fails contract_runner check

- **WHEN** `contract_runner` scans a file with a public function lacking `@require`/`@ensure`
- **THEN** a `MISSING_ICONTRACT` finding is produced

#### Scenario: Decorated public function produces no missing-contract finding

- **WHEN** a public function has both `@require` (or `@ensure`) and `@beartype`
- **THEN** `contract_runner` produces zero `MISSING_ICONTRACT` findings for that function

#### Scenario: Minimal meaningful contract per function

- **WHEN** a `@require` precondition is added to a public function
- **THEN** the precondition checks a domain-meaningful invariant (e.g., path exists, non-empty string, valid enum)
- **AND** the precondition is NOT a trivial `lambda x: x is not None` that merely restates the type

#### Scenario: Utility contract exploration handles pathological strings gracefully

- **WHEN** CrossHair or unit tests exercise utility helpers with pathological string inputs such as
  control characters or malformed package names
- **THEN** the helpers SHALL return a safe fallback value instead of raising unexpected exceptions
- **AND** `hatch run contract-test` SHALL not report uncaught exceptions for those utility paths

### Requirement: Complexity budget — no function exceeds CC15

No function in `src/specfact_cli/`, `scripts/`, or `tools/` SHALL have cyclomatic complexity >=16, as measured by radon.

#### Scenario: High-complexity function split into helpers passes complexity check

- **WHEN** a function with CC>=16 is refactored into a top-level function and one or more private helpers
- **THEN** `hatch run lint` (radon check) reports no CC>=16 findings for that function
- **AND** each extracted helper has CC<10

#### Scenario: New code written during this change stays below threshold

- **WHEN** any new function is introduced during this change
- **THEN** its cyclomatic complexity is <10 as measured by radon
- **AND** no CC>=13 warning is raised for the new function
