## Context

Backlog refine writeback currently computes reverse mappings by first-seen canonical field keys. Because default mapping order includes `Microsoft.VSTS.Common.StoryPoints` before other story-point candidates, writeback can target the wrong field even when custom mappings are configured. The tmp import workflow also treats `**ID**` as required in parser logic but does not enforce that contract strongly enough in user-facing instructions and mismatch handling.
Separately, ADO comment endpoints (`/workitems/{id}/comments`) are versioned differently from standard work-item endpoints in some tenants, so using stable `7.1` for comment posting can fail while read comments already use preview API versioning.

## Goals / Non-Goals

**Goals:**

- Make canonical-to-provider writeback field resolution deterministic and custom-mapping-safe for ADO.
- Ensure refine tmp import contract explicitly requires preserving `**ID**` for lookup.
- Fail fast with actionable diagnostics when parsed IDs do not map to fetched items.
- Ensure ADO comment read/write operations consistently use endpoint-compatible preview API versioning, without changing stable `7.1` usage for standard operations.

**Non-Goals:**

- No redesign of adapter registry or template detection.
- No change to provider-independent refine output structure beyond explicit ID contract text.

## Decisions

1. Introduce mapper-level write-target resolution helper.

- Add a dedicated method in `AdoFieldMapper` that resolves the preferred ADO field for a canonical field.
- Precedence: custom mapping key(s) first, then provider-present mapped fields (from current item/provider_fields), then default/framework fallback.
- Rationale: centralizes precedence in mapper and avoids duplicated, order-sensitive logic in adapters.

2. Update `AdoAdapter.update_backlog_item` to use resolved canonical targets.

- Replace ad-hoc reverse mapping and membership checks with mapper-resolved targets for each canonical field.
- Rationale: guarantees consistency and removes dependence on Python dict insertion order side effects.

3. Strengthen tmp import contract and mismatch handling.

- Update prompt/export guidance to state `**ID**` is mandatory and must be unchanged.
- Add explicit command error when parsed blocks exist but zero IDs match fetched items.
- Rationale: prevents silent no-op writeback and improves Copilot workflow reliability.

4. Split ADO API version selection by endpoint class.

- Keep standard work-item and WIQL operations on `api-version=7.1`.
- Route comment endpoint reads/writes (`/comments`) to `api-version=7.1-preview.4`.
- Rationale: aligns with observed tenant compatibility for comment activities while preserving stable API on core operations.

## Risks / Trade-offs

- [Risk] Mapper helper introduces new logic branch for target selection.
  - Mitigation: Add focused unit tests for custom/default precedence and adapter patch-path assertions.
- [Risk] Stricter tmp import validation may fail previously permissive malformed files.
  - Mitigation: Provide explicit remediation text in error output and prompt instructions.
- [Risk] API-version divergence can drift if future comment calls are added ad hoc.
  - Mitigation: Add targeted tests asserting preview version for comment write path and keep stable version assertions for representative standard operations.

## Migration Plan

1. Add/modify specs and tests for mapping precedence and ID mismatch behavior.
2. Capture failing test evidence in `TDD_EVIDENCE.md`.
3. Implement mapper + adapter + command changes.
4. Re-run targeted tests and then full required quality gates.

## Open Questions

- None for v1. Current scope fully covers reported custom story points and ID contract failures.
