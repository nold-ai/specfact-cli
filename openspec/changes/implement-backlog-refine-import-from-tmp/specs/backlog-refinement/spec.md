# backlog-refinement (delta)

## ADDED Requirements

### Requirement: Import refined content from temporary file

The system SHALL support importing refined backlog content from a temporary markdown file (same format as export) when `specfact backlog refine --import-from-tmp` is used, matching items by ID and updating remote backlog via the adapter when `--write` is set.

#### Scenario: Import refined content from temporary file

- **GIVEN** a markdown file in the same format as the export from `specfact backlog refine --export-to-tmp` (header, then per-item blocks with `## Item N:`, **ID**, **Body** in ```markdown ... ```, **Acceptance Criteria**)
- **AND** the user runs `specfact backlog refine --import-from-tmp --tmp-file <path>` with the same adapter and filters as used for export (so the same set of items is fetched)
- **WHEN** the import file exists and is readable
- **THEN** the system parses the file and matches each block to a fetched item by **ID**
- **AND** for each matched item the system updates `body_markdown` and `acceptance_criteria` (and optionally title/metrics) from the parsed block
- **AND** if `--write` is not set, the system prints a preview (e.g. "Would update N items") and does not call the adapter
- **AND** if `--write` is set, the system calls `adapter.update_backlog_item(item, update_fields=[...])` for each updated item and prints a success summary (e.g. "Updated N backlog items")
- **AND** the system does not show "Import functionality pending implementation"

#### Scenario: Import file not found

- **GIVEN** the user runs `specfact backlog refine --import-from-tmp` (or with `--tmp-file <path>`)
- **WHEN** the resolved import file does not exist
- **THEN** the system prints an error with the expected path and suggests using `--tmp-file` to specify the path
- **AND** the command exits with non-zero status
