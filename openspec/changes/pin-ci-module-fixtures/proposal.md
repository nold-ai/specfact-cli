## Why

CodeQL flags fixture revisions passed through step outputs to checkouts in CI jobs that can run on the default branch.

## What Changes

- Pin the module repository and revision at each affected checkout while retaining lock verification.
- Keep the existing Requirements and documentation fixture identities.

## Impact

This change affects fixture acquisition in the PR orchestrator, Contract Validation and Docs Review. The module cutoff, signing keys and publication policy stay unchanged.
