# clean-code-semgrep-rules Specification

## Purpose

TBD - created by archiving change code-review-05-semgrep-clean-code-rules. Update Purpose after archive.

## Requirements

### Requirement: Five Custom Semgrep Rules for Project-Specific Anti-Patterns

The system SHALL provide five semgrep rules covering get+modify in same method, unguarded nested attribute access, cross-layer calls, module-level network instantiation, and print() in src/. Each rule SHALL be validated with bad/good fixture pairs.

#### Scenario: get+modify rule fires on combined read/write method

- **GIVEN** `bad_get_modify.py` contains a method that both reads and writes state
- **WHEN** semgrep runs the `get-modify-same-method` rule on that file
- **THEN** at least one match is reported

#### Scenario: get+modify rule does not fire on separated methods

- **GIVEN** `good_get_modify.py` separates read and write into different methods
- **WHEN** semgrep runs the rule
- **THEN** no match is reported

#### Scenario: Nested attribute access rule fires on unguarded a.b.c

- **GIVEN** `bad_nested_access.py` contains `result = obj.config.value` without None-check
- **WHEN** semgrep runs the `unguarded-nested-access` rule
- **THEN** a match is reported

#### Scenario: Cross-layer rule fires on mixed repository and http_client calls

- **GIVEN** a function calls both `repository.find_by_id(...)` and `http_client.post(...)`
- **WHEN** semgrep runs the `cross-layer-call` rule
- **THEN** a match is reported

#### Scenario: print-in-src rule fires on print() in src/ files

- **GIVEN** a file in `src/` contains `print("debug")`
- **WHEN** semgrep runs the `print-in-src` rule
- **THEN** a match is reported
