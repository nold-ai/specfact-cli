## ADDED Requirements

### Requirement: Sync Kernel
The system SHALL provide a session-based sync kernel with preview/apply safety gates, conflict handling, and offline journaling.

#### Scenario: Preview mode computes patch set without writing
- **GIVEN** `specfact sync --preview`
- **WHEN** sync analysis runs
- **THEN** JSON patch operations are produced for candidate writes
- **AND** no provider write call is executed.

#### Scenario: Apply mode enforces optimistic concurrency
- **GIVEN** `specfact sync --apply` and remote data changed after preview
- **WHEN** kernel attempts write
- **THEN** stale writes are rejected using ETag or equivalent concurrency checks
- **AND** conflict records are created for manual resolution.

#### Scenario: Offline write requests are journaled
- **GIVEN** apply mode is requested while provider is unavailable
- **WHEN** kernel cannot reach upstream
- **THEN** pending writes are stored under `.specfact/sync/journal/`
- **AND** queued writes are eligible for retry in a later session.
