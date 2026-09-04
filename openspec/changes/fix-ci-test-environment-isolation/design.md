# Design: CI test environment isolation

## Decision

Override `GITHUB_BASE_REF` with an empty value only in the two workflow steps
that execute the primary Python 3.12 suite and the Python 3.11 compatibility
suite. `check_version_sources.py` already treats an empty value as absent, so
synthetic repositories use their own Git history without changing production
logic or test helpers.

The override is step-scoped rather than job-scoped. Setup, signature checks,
change detection, release validation, and any later workflow routing continue
to see GitHub's authentic base reference.

## Alternatives

- Updating `_run_version_check` was rejected because it teaches one test helper
  about CI routing and cannot be represented safely by the current retained-RED
  freshness model when the helper and selected tests share a file.
- Changing `check_version_sources.py` was rejected because the production gate
  must continue using `GITHUB_BASE_REF` in real pull-request execution.
- A repository-wide automatic pytest fixture was rejected because it would
  silently change every local test and could interfere with tests that
  deliberately exercise GitHub environment handling.
- A generic Requirements freshness exception was rejected because it would
  weaken provenance rather than fix the environmental boundary.

## Security and compatibility

The workflow continues to use the trusted GitHub base reference outside the
two test steps. No secret, token, dependency, cache, checkout, or permission
surface changes. Setting the variable to an empty string is portable across the
existing Ubuntu runners and both supported Python lanes.

## Rollback

Revert the workflow and test commit. No data migration, published artifact
rewrite, or dependency rollback is required.
