# docs-command-validation Specification

## Purpose
TBD - created by archiving change docs-12-docs-validation-ci. Update Purpose after archive.
## Requirements
### Requirement: Docs command examples resolve to a valid CLI path

Documentation under `docs/` SHALL include `specfact …` examples in fenced code blocks only when some prefix of the command tokens matches a command path that accepts `--help` in the current CLI (or is a bundle-only group that reports “not installed” when bundles are absent).

#### Scenario: CI runs command validation on docs changes

- **WHEN** the docs-review workflow runs on a branch that touches docs or validation scripts
- **THEN** it executes `hatch run check-docs-commands`
- **AND** the step fails the job when an example cannot be resolved to a valid command path

### Requirement: Historical migration docs are excluded from strict command parity

Content under `docs/migration/` and other explicitly listed illustrative pages MAY retain historical or placeholder command lines that no longer exist in the CLI; those paths SHALL be excluded from automated command validation so the check targets current user-facing docs.

#### Scenario: Migration pages are skipped

- **WHEN** `check-docs-commands` scans `docs/`
- **THEN** it skips `docs/migration/**` and other configured exclusions
- **AND** it does not fail on removed commands documented only for historical context

