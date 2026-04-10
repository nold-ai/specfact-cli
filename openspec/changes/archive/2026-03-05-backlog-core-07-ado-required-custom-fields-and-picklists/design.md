## Context

`backlog add` already supports provider-specific payload construction, but required/allowed-value semantics for ADO custom fields are incomplete. `backlog map-fields` currently stores mapping keys but not sufficient dynamic constraint metadata (required by work item type, picklist allowed values) to guarantee deterministic add-time validation.

This change improves the ADO branch of the bridge adapter workflow while preserving provider-agnostic command structure.

Current ownership after module migration:

- `specfact-cli-modules` (`specfact-backlog`) owns `specfact backlog map-fields`.
- `specfact-cli` owns `backlog-core add` command orchestration and shared ADO adapter create path.

Design must keep these boundaries explicit so each repo change is independently testable, while the end-to-end behavior is validated together.

## Goals / Non-Goals

**Goals:**

- Persist ADO field constraint metadata during `map-fields` for add-time checks.
- Provide interactive picklist selection for constrained ADO fields.
- Enforce and explain constrained value validation in non-interactive mode.
- Keep add-flow behavior deterministic when API discovery is unavailable.

**Non-Goals:**

- Rework GitHub/Jira/Linear field mapping UX in this change.
- Add new remote caching services or cloud dependencies.
- Introduce breaking schema changes outside backlog config field metadata.

## Decisions

### 1. Persist field constraints by work item type in backlog config

- Decision: extend persisted ADO mapping metadata to include `required` and `allowed_values` keyed by ADO field ref-name and work item type.
- Rationale: keeps interactive and non-interactive behavior aligned and offline-capable for known mappings.
- Alternative considered: live API checks only during add. Rejected due to offline/latency coupling and inconsistent non-interactive determinism.

### 2. Interactive picker uses constrained option lists from metadata API

- Decision: in interactive add mode, when a mapped field has constrained values, render a terminal picker (up/down, enter) for selection instead of free-form input.
- Rationale: avoids invalid values and improves UX for long enterprise picklists.
- Alternative considered: prompt free-form plus post-submit validation. Rejected due to repeated failure loops and poor discoverability.

### 3. Non-interactive validation is fail-fast with allowed-values hint

- Decision: validate provided values before create call and fail with explicit accepted values when invalid.
- Rationale: script-friendly deterministic failure and actionable remediation.
- Alternative considered: silent coercion/case-insensitive fuzzy matching. Rejected due to ambiguity and risk of wrong field data.

### 4. Contract enforcement remains on public command/service boundaries

- Decision: keep/extend `@icontract` and `@beartype` annotations on public validation/payload functions touched by the change.
- Rationale: contract-first baseline for regression prevention.

### 5. Cross-repo schema compatibility for provider metadata

- Decision: persisted metadata keys for required/constrained fields are additive and backward-compatible so either repo can read safely during staged rollout.
- Rationale: map-fields and add/create are split across repositories; temporary version skew must not crash commands.
- Alternative considered: strict schema bump requiring lockstep release. Rejected due to operational friction and higher rollback risk.

## Risks / Trade-offs

- **[ADO metadata API variability]** -> Mitigation: fallback to persisted metadata; emit clear warning when live lookup unavailable.
- **[Large picklist payloads may impact interactive latency]** -> Mitigation: lazy-fetch only for fields present in selected mapping/work item type.
- **[Config schema drift for existing projects]** -> Mitigation: additive metadata keys with backward-compatible defaults and migration-safe readers.
- **[Mismatch between persisted and current server-side allowed values]** -> Mitigation: prefer live values in interactive mode; use persisted values as fallback and include stale-metadata warning.

## Migration Plan

1. In `specfact-cli-modules`, add additive metadata fields to mapping persistence logic (`required`, `allowed_values`, `constraint_source`, work-item-type keying).
2. In `specfact-cli`, update add-flow field resolution and adapter create path to consume metadata with backward-compatible defaults.
3. Introduce interactive picker path for constrained fields and retain free-text prompts for unconstrained fields.
4. Add/adjust tests in TDD order (failing first, passing after implementation) across both repos.
5. Coordinate docs/changelog updates in both repos before merge.

Rollback: revert map/add metadata and validation path changes; config remains readable because new keys are additive.

## Open Questions

- Should list-of-values validation be case-sensitive or normalized per ADO field metadata flags?
- Should multi-select constrained fields be included in this change or explicitly deferred?
