# Delta: docs-cross-site-link-check

Adds automated HTTP checks for `https://modules.specfact.io/…` URLs referenced from core docs.

## ADDED Requirements

### Requirement: Cross-site modules URLs are discoverable from markdown

The repository SHALL provide a script that extracts `https://modules.specfact.io/…` URLs from `docs/**/*.md`, performs HTTP HEAD/GET checks with redirects allowed, and reports source file context for failures.

#### Scenario: Link check runs in docs-review with warn-only mode

- **WHEN** the docs-review workflow runs
- **THEN** it executes `hatch run check-cross-site-links --warn-only`
- **AND** failures are printed but do not fail the job while the live site may lag content deploys

### Requirement: Handoff map URLs MUST be verifiable with opt-in live checks

The handoff migration map SHALL be covered by opt-in HTTP tests that verify each listed modules URL is reachable when `SPECFACT_RUN_HANDOFF_URL_CHECK=1`; the default test run SHALL skip those checks to avoid flaky network or deploy lag in CI.

#### Scenario: Opt-in network test

- **WHEN** a maintainer sets `SPECFACT_RUN_HANDOFF_URL_CHECK=1`
- **THEN** pytest runs the handoff map URL reachability test against production
- **AND** the default CI run skips that test to avoid flaky or lagging deploy noise
