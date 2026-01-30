# backlog-refinement (delta)

## ADDED Requirements

### Requirement: Ignore Already-Refined Items by Default

The system SHALL support `--ignore-refined` (default) and `--no-ignore-refined` so that when `--limit N` is used, the limit applies to items that need refinement (already-refined items are excluded from the batch by default).

#### Scenario: Limit applies to items needing refinement when ignore-refined

- **GIVEN** the user runs `specfact backlog refine <adapter> --limit 3` (default `--ignore-refined`)
- **AND** the adapter returns at least 5 items, of which the first 3 are already refined (checkboxes + all required sections or high confidence with no missing fields)
- **WHEN** the command processes items
- **THEN** the system filters out already-refined items, then takes the first 3 that need refinement
- **AND** the user sees up to 3 items that actually require refinement (no loop of the same 3 refined items)

#### Scenario: No-ignore-refined preserves previous behavior

- **GIVEN** the user runs `specfact backlog refine <adapter> --limit 3 --no-ignore-refined`
- **WHEN** the command processes items
- **THEN** the system takes the first 3 items from the fetch and processes them in order
- **AND** already-refined items are skipped in the loop (current behavior)

### Requirement: Focused Refinement by Issue ID

The system SHALL support `--id ISSUE_ID` to refine only the backlog item with the given issue or work item ID.

#### Scenario: Refine single item by ID

- **GIVEN** the user runs `specfact backlog refine <adapter> --id 123` (with required adapter options)
- **WHEN** the adapter returns items including item with id 123
- **THEN** the system filters to only the item with id 123 and refines only that item
- **AND** other items are not processed

#### Scenario: ID not found

- **GIVEN** the user runs `specfact backlog refine <adapter> --id 999` (with required adapter options)
- **WHEN** no item with id 999 is in the fetched set
- **THEN** the system prints a clear error (e.g. "No backlog item with id 999 found") and exits with non-zero status
