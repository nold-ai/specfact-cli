# Design: CI test environment isolation

## Decision

Run `unset GITHUB_BASE_REF` inside only the two Bash workflow steps that execute
the primary Python 3.12 suite and the Python 3.11 compatibility suite, before
either Python launcher starts. Synthetic repositories then use their own Git
history without changing production logic or test helpers.

A workflow `env` override is not sufficient: GitHub documents that assignments
to default `GITHUB_*` variables are ignored. The shell-level removal therefore
defines the effective process boundary. Both affected steps declare Bash
explicitly.

The removal is shell- and step-scoped rather than job-scoped. Setup, signature
checks, change detection, release validation, and any later workflow routing
continue to see GitHub's authentic base reference.

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
surface changes. Bash `unset` is portable across the existing Ubuntu runners
and both supported Python lanes.

Primary reference: <https://docs.github.com/en/actions/reference/workflows-and-actions/variables>.

## Rollback

Revert the workflow and test commit. No data migration, published artifact
rewrite, or dependency rollback is required.
