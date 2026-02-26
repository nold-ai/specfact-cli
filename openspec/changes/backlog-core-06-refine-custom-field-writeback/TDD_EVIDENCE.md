# TDD Evidence: backlog-core-06-refine-custom-field-writeback

## Pre-Implementation Failing Run

- Timestamp (UTC): 2026-02-25T12:48:54Z
- Command:

```bash
hatch run pytest \
  tests/unit/backlog/test_field_mappers.py::TestAdoFieldMapper::test_resolve_write_target_prefers_custom_mapping_field \
  tests/unit/adapters/test_ado_backlog_adapter.py::TestAdoBacklogAdapter::test_update_backlog_item_uses_custom_story_points_field_mapping \
  tests/unit/commands/test_backlog_commands.py::TestBuildRefineExportContent::test_refine_export_marks_id_as_mandatory_for_import \
  tests/unit/commands/test_backlog_commands.py::TestRefineImportFromTmp::test_import_from_tmp_fails_when_no_parsed_ids_match_fetched_items \
  -v
```

- Result: **FAILED (4 failed)**
- Failure summary:
  - `AdoFieldMapper` missing `resolve_write_target_field` API.
  - ADO adapter did not PATCH `Microsoft.VSTS.Scheduling.StoryPoints` under custom mapping.
  - refine export content missing mandatory ID contract text.
  - refine import from tmp returned success on unmatched IDs instead of explicit failure.

## Post-Implementation Passing Run

- Timestamp (UTC): 2026-02-25T12:02:36Z
- Command:

```bash
hatch run pytest \
  tests/unit/commands/test_backlog_commands.py::TestResolveTargetTemplateForRefineItem::test_ado_user_story_type_prefers_user_story_template \
  tests/unit/commands/test_backlog_commands.py::TestParseRefinedExportMarkdown::test_parses_item_when_file_starts_with_item_header \
  tests/unit/adapters/test_ado_backlog_adapter.py::TestAdoBacklogAdapter::test_create_issue_uses_custom_mapped_fields_and_markdown_multiline_format \
  tests/unit/adapters/test_ado_backlog_adapter.py::TestAdoBacklogAdapter::test_update_backlog_item_strips_leading_description_heading_for_ado \
  tests/integration/backlog/test_ado_markdown_rendering.py::TestAdoMarkdownRendering::test_update_backlog_item_with_markdown_format \
  -q
```

- Result: **PASSED (5 passed)**
- Passing summary:
  - ADO user-story work item types are steered to `user_story_v1` template resolution.
  - Refine tmp import parser handles first-block headers and does not leak `## Item N:` into title.
  - ADO create path honors custom mapped write targets and markdown format metadata.
  - ADO update path strips leading `## Description` scaffold heading before write-back.
  - ADO markdown write-back includes multiline markdown format operations for mapped rich-text fields.

## Regression Fix: Rich Text Normalization (Review Findings)

### Pre-Implementation Failing Run

- Timestamp (UTC): 2026-02-25T20:51:00Z
- Command:

```bash
hatch test -- tests/unit/backlog/test_field_mappers.py -v
```

- Result: **FAILED (2 failed)**
- Failure summary:
  - `<br />` tags were not converted to newline because of escaped `\\s` in regex and lines collapsed in extracted content.
  - Non-HTML angle-bracket text (for example `<tenant_id>` or `x < y > z`) was incorrectly treated as HTML and stripped.

### Post-Implementation Passing Run

- Timestamp (UTC): 2026-02-25T20:54:53Z
- Command:

```bash
hatch test -- tests/unit/backlog/test_field_mappers.py -v
```

- Result: **PASSED (37 passed)**
- Passing summary:
  - `<br>`, `<br/>`, and `<br />` are normalized to newlines.
  - Rich text normalization only activates for known HTML tags, preventing accidental stripping of non-HTML placeholders and angle-bracket content.

## Regression Fix: ADO Comment API Version Compatibility

### Pre-Implementation Failing Run

- Timestamp (UTC): 2026-02-26 18:40:42 UTC
- Command:

```bash
hatch test -- tests/unit/adapters/test_ado.py -k "add_work_item_comment or build_ado_url_defaults_to_stable_api_version_for_standard_operations" -v
```

- Result: **FAILED (1 failed, 1 passed)**
- Failure summary:
  - `_add_work_item_comment` posted to `/workitems/{id}/comments` with `api-version=7.1` instead of `7.1-preview.4`.
  - Standard endpoint helper default remained stable `7.1` as expected.

### Post-Implementation Passing Run

- Timestamp (UTC): 2026-02-26 18:41:27 UTC
- Command:

```bash
hatch test -- tests/unit/adapters/test_ado.py -k "add_work_item_comment or build_ado_url_defaults_to_stable_api_version_for_standard_operations" -v
```

- Result: **PASSED (2 passed, 35 deselected)**
- Passing summary:
  - ADO comment POST path now targets `/comments?api-version=7.1-preview.4`.
  - Standard endpoint URL builder default remains stable `api-version=7.1`.
