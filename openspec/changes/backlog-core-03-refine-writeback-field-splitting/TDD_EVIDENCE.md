# TDD Evidence: backlog-core-03-refine-writeback-field-splitting

## Pre-Implementation Failing Run

- **Timestamp**: 2026-02-11T14:30:38+01:00
- **Command**: `hatch test -- tests/unit/commands/test_backlog_commands.py -k parse_refinement_output_fields -v`
- **Result**: Failed (collection error)
- **Failure Summary**:
  - `ImportError: cannot import name '_parse_refinement_output_fields'`
  - New parser behavior is specified in tests but not implemented yet.

## Post-Implementation Passing Run

- **Timestamp**: 2026-02-11T14:32:52+01:00
- **Command**: `hatch test -- tests/unit/commands/test_backlog_commands.py tests/unit/adapters/test_github_backlog_adapter.py -v`
- **Result**: Passed
- **Summary**:
  - `41 passed`
  - Includes regression coverage for:
    - label-style refinement field parsing
    - markdown heading refinement parsing
    - GitHub writeback fallback when structured body lacks core field headings.

## Review Follow-up: Heading-Style Narrative Regression

### Pre-Implementation Failing Run

- **Timestamp**: 2026-02-12T10:22:00+01:00
- **Command**: `hatch test -- tests/unit/commands/test_backlog_commands.py -k heading_style_notes_and_dependencies -v`
- **Result**: Failed
- **Failure Summary**:
  - `test_preserves_heading_style_notes_and_dependencies_in_body_markdown` failed.
  - Parsed `body_markdown` contained only description (`User-facing summary.`) and dropped heading-style `## Notes` section.

### Post-Implementation Passing Run

- **Timestamp**: 2026-02-12T10:24:00+01:00
- **Command**: `hatch test -- tests/unit/commands/test_backlog_commands.py -k TestParseRefinementOutputFields -v`
- **Result**: Passed
- **Summary**:
  - `3 passed`
  - Includes heading-style preservation regression test for `## Notes` and `## Dependencies`.
