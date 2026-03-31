## ADDED Requirements

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
