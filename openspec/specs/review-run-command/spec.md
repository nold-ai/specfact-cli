# review-run-command Specification

## Purpose

TBD - created by archiving change code-review-08-review-run-integration. Update Purpose after archive.

## Requirements

### Requirement: End-to-End specfact code review run Command

The `specfact code review run` workflow SHALL support the dogfood self-review proof for the SpecFact CLI repository and emit a governed zero-finding report when remediation is complete.

#### Scenario: Dogfood self-review on SpecFact CLI reaches zero tracked findings

- **GIVEN** the SpecFact CLI repository under the `code-review-zero-findings` remediation branch
- **AND** the dogfood self-review tests in `tests/unit/specfact_cli/test_dogfood_self_review.py`
- **WHEN** `specfact code review run --scope full --json --out <report-path>` is executed in an environment where the `code` bundle is installed
- **THEN** the generated report has `overall_verdict` equal to `"PASS"`
- **AND** the report contains zero findings with rules `reportUnknownMemberType`, `print-in-src`, and `MISSING_ICONTRACT`
- **AND** the report contains zero `clean_code` findings with rules `CC16` or higher
- **AND** the report contains zero findings in category `tool_error`
