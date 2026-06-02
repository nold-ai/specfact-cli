# code-review-module Specification

## Purpose

TBD - created by archiving change code-review-01-module-scaffold. Update Purpose after archive.

## Requirements

### Requirement: Code Review Module Registration

The `nold-ai/specfact-code-review` module SHALL be installable and extend `specfact code` with a `review` subgroup exposing `run`, `ledger`, and `rules` subcommands.

#### Scenario: Module install surfaces review subgroup

- **GIVEN** the module is installed via `specfact module install nold-ai/specfact-code-review`
- **WHEN** the user runs `specfact code --help`
- **THEN** a `review` subgroup appears in the command list
- **AND** `specfact code review --help` shows `run`, `ledger`, and `rules` subcommands

#### Scenario: module-package.yaml has required fields

- **GIVEN** `packages/specfact-code-review/module-package.yaml` exists
- **WHEN** the module loader parses it
- **THEN** `bundle_group_command` equals `code`, `tier` equals `official`, `name` equals `nold-ai/specfact-code-review`
- **AND** `core_compatibility` matches `>=0.40.0,<1.0.0`

#### Scenario: Module not installed produces no surface

- **GIVEN** the module is NOT installed
- **WHEN** the user runs `specfact code --help`
- **THEN** no `review` subgroup appears and no error is raised

#### Scenario: Duplicate install is idempotent

- **GIVEN** the module is already installed
- **WHEN** the user installs it again
- **THEN** no duplicate `review` entries appear in `specfact code --help`

### Requirement: Self-referential scan — review module can scan itself without errors

The `specfact-code-review` module SHALL be able to review its own source files (including the files that implement the reviewer) without infinite loops, false positives from meta-scanning, or unhandled exceptions.

#### Scenario: Review run on specfact-cli repo completes without tool_error findings

- **WHEN** `specfact review` is run with the specfact-cli repo as the target
- **THEN** no finding with `tool` equal to `code-review-module` or `category` equal to `tool_error` is produced
- **AND** the run exits with code 0 (assuming all other findings are resolved)

#### Scenario: Tool error finding is surfaced as error severity

- **WHEN** any configured tool fails to invoke (e.g., missing binary)
- **THEN** a finding with `category="tool_error"` and `severity="error"` is produced
- **AND** the finding message includes the tool name and failure reason

### Requirement: CI gate integration — review must be runnable non-interactively

The review module SHALL support a `--ci` or equivalent non-interactive flag that suppresses prompts, writes machine-readable output to `.specfact/code-review.json`, and exits with code 1 on any finding at severity `error` or higher.

#### Scenario: Non-interactive CI run writes JSON report and exits non-zero on errors

- **WHEN** `specfact review run --ci` is executed and error-severity findings exist
- **THEN** `.specfact/code-review.json` is written with `overall_verdict: "FAIL"` and `ci_exit_code: 1`
- **AND** the process exits with code 1

#### Scenario: Non-interactive CI run exits zero on clean codebase

- **WHEN** `specfact review run --ci` is executed and no findings exist
- **THEN** `.specfact/code-review.json` is written with `overall_verdict: "PASS"` and `ci_exit_code: 0`
- **AND** the process exits with code 0

### Requirement: Code Review module page routes users to canonical bundle docs

The core Code Review module page SHALL explain the module's purpose and route users to modules-owned command documentation for exact runtime behavior.

#### Scenario: Module page summarizes cleanup forecast capability

- **WHEN** the page describes AI-shaped bloat advisories
- **THEN** it SHALL also describe cleanup forecasts, AI-bloat index, preserve signals, and remediation packets at a high-level summary
- **AND** it SHALL route users to `modules.specfact.io` for exact flags, JSON fields, and AI IDE workflow details
- **AND** it SHALL preserve the warning that bloat-shape findings are not AI-authorship proof

#### Scenario: Core handoff page avoids becoming a duplicate command reference

- **WHEN** the Code Review module page mentions simplify-focused flags or JSON fields
- **THEN** it SHALL keep those mentions at workflow level
- **AND** it SHALL link to the modules Code Review run guide and AI bloat quickstart for exact flags, invalid combinations, and report schema details
