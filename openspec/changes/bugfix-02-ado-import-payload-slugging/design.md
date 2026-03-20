# Design: Fix ADO selective bridge import payload contract and title-based change IDs

## Overview

The failure in issue `#425` is a contract break inside the selective bridge import path:

1. `BridgeSync` fetches one backlog item by ID for import.
2. `AdoAdapter.fetch_backlog_item()` returns a reduced summary payload.
3. `AdoAdapter.import_artifact()` and `extract_change_proposal_data()` still expect the native ADO work item shape with `fields`.
4. Import fails before OpenSpec change creation.

Once the raw payload is restored, the fallback naming path still degrades to the numeric ADO work item ID when no OpenSpec metadata is present. That behavior is technically unique but operationally poor. The fallback should stay readable first, with the numeric source ID kept as provenance, not as the primary OpenSpec change name.

## Design Decisions

### 1. Preserve the provider-native payload on selective import

`fetch_backlog_item()` for ADO should return the native work item document needed by the import path. If older call sites benefit from convenience keys such as `title`, `state`, and `description`, those can remain as additive compatibility fields, but they must not replace or strip the provider-native shape.

This keeps the import contract coherent:

- `fetch_backlog_item()` returns an artifact suitable for `import_artifact()`
- `extract_change_proposal_data()` reads the same native payload
- contract tests can verify the round trip directly

### 2. Normalize imported change IDs in one shared place

The fallback naming rule should be centralized in the shared backlog import path rather than hidden in one adapter-specific edge case. The normalizer should:

- prefer an existing OpenSpec change ID if found in provider metadata
- otherwise derive a kebab-case slug from the proposal title
- append a deterministic suffix such as `-<source-id>` when the slug already exists or would otherwise be ambiguous
- avoid using a raw numeric source ID as the entire change name unless the source artifact truly has no usable title

This lets ADO fix its immediate bug while also protecting similar adapters and commands.

### 3. Audit adjacent import commands, not just the failing ADO branch

The regression appeared because one side of the contract evolved while the other kept assuming a richer payload. The implementation should therefore audit all nearby paths that do one or more of:

- call `fetch_backlog_item()`
- call `extract_change_proposal_data()`
- call `import_backlog_item_as_proposal()`
- translate provider IDs into OpenSpec change IDs

The goal is not a broad refactor. The goal is to prove that similar commands either already preserve the native payload correctly or are covered by targeted defensive tests after this fix.

## Implementation Outline

1. Add failing tests for ADO selective import and title-based slug fallback.
2. Restore native payload preservation in ADO selective fetch.
3. Add shared title-first change-ID normalization in the backlog import path.
4. Re-run targeted tests against adjacent adapters/call sites to confirm the contract holds.
5. Update docs and release notes for the patch behavior change.
