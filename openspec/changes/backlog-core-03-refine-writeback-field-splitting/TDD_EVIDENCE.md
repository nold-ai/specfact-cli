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

## Review Follow-up: Case-Insensitive Heading Matching

### Pre-Implementation Failing Run

- **Timestamp**: 2026-02-12T10:42:00+01:00
- **Command**: `hatch test -- tests/unit/commands/test_backlog_commands.py -k uppercase_heading_style_notes_and_dependencies -v`
- **Result**: Failed
- **Failure Summary**:
  - `test_preserves_uppercase_heading_style_notes_and_dependencies_in_body_markdown` failed.
  - Parsed `body_markdown` contained only description and dropped uppercase `## NOTES` / `## DEPENDENCIES` narrative sections.

### Post-Implementation Passing Run

- **Timestamp**: 2026-02-12T10:43:00+01:00
- **Command**: `hatch test -- tests/unit/commands/test_backlog_commands.py -k TestParseRefinementOutputFields -v`
- **Result**: Passed
- **Summary**:
  - `4 passed`
  - Includes uppercase heading regression coverage for `## NOTES` and `## DEPENDENCIES`.

## Review Follow-up: Label-Only Output Without Description

### Pre-Implementation Failing Run

- **Timestamp**: 2026-02-12T10:49:00+01:00
- **Command**: `hatch test -- tests/unit/commands/test_backlog_commands.py -k label_only_output_without_description -v`
- **Result**: Failed
- **Failure Summary**:
  - `test_label_only_output_without_description_does_not_fallback_to_raw_payload` failed.
  - Parser retained the full raw label payload as fallback `description` and `body_markdown` when no `Description:` block existed.

### Post-Implementation Passing Run

- **Timestamp**: 2026-02-12T10:50:00+01:00
- **Command**: `hatch test -- tests/unit/commands/test_backlog_commands.py -k TestParseRefinementOutputFields -v`
- **Result**: Passed
- **Summary**:
  - `5 passed`
  - Includes regression coverage for label-only field blocks without `Description:`.

## User Report Follow-up: Prompt Scaffold + Mixed Format Parsing

### Pre-Implementation Failing Run

- **Timestamp**: 2026-02-12T11:06:00+01:00
- **Command**: `hatch test -- tests/unit/commands/test_backlog_commands.py -k mixed_heading_and_inline_notes -v`
- **Result**: Failed
- **Failure Summary**:
  - `test_mixed_heading_and_inline_notes_preserves_description_before_notes` failed.
  - Parser dropped pre-notes description narrative and kept only content starting at inline `**Notes**:`.

- **Timestamp**: 2026-02-12T11:06:00+01:00
- **Command**: `hatch test -- tests/unit/backlog/test_ai_refiner.py -k "expected_output_scaffold or omit_unknown_metadata_fields" -v`
- **Result**: Failed
- **Failure Summary**:
  - Prompt did not include explicit output scaffold instructions.
  - Prompt did not include instruction to omit unknown metadata fields/placeholders.

### Post-Implementation Passing Run

- **Timestamp**: 2026-02-12T11:08:00+01:00
- **Command**: `hatch test -- tests/unit/commands/test_backlog_commands.py -k TestParseRefinementOutputFields -v`
- **Result**: Passed
- **Summary**:
  - `6 passed`
  - Includes mixed heading + inline notes regression.

- **Timestamp**: 2026-02-12T11:08:00+01:00
- **Command**: `hatch test -- tests/unit/backlog/test_ai_refiner.py -k generate_refinement_prompt -v`
- **Result**: Passed
- **Summary**:
  - `5 passed`
  - Includes prompt scaffold and metadata omission instruction coverage.
