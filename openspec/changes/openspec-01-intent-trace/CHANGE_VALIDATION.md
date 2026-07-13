# Change Validation Report: openspec-01-intent-trace

**Validation Date**: 2026-07-13 (Europe/Berlin)
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Dry-run interface and dependency analysis against the current core CLI worktree.

## Executive Summary

- Breaking Changes: 0 detected / 0 unresolved
- Dependent Files: 3 direct core surfaces, plus the paired module runtime issue
- Impact Level: Medium (new validation behavior; no removed public interface)
- Validation Result: Pass
- User Decision: Apply the evidence-compatible required-field mapping and the
  fail-closed source compatibility boundary approved on 2026-07-13.

The rescoped change preserves the existing `RequirementInput` schema,
`--from-file` flow, and source types while adding core-owned OpenSpec/Spec Kit
normalization and deterministic validation gates. The approved
evidence-compatible required-field mapping defines their semantics against
that schema without widening it.
The `specfact-requirements` command wiring remains explicitly paired with
`nold-ai/specfact-cli-modules#168`; it does not block the core implementation.

The approved compatibility extension adds no public parameter or model change.
It accepts only fixture-backed default OpenSpec and Spec Kit structural
profiles, returning `unsupported-source-schema` and no partial records for
custom or unrecognized sources. This is a non-breaking, additive diagnostic
contract; #168 will surface it without reimplementing compatibility logic.

## Resolved Required-Field Contract

`id`, `title`, `acceptance`, and `trace_links` map to `requirement_id`,
`title`, `business_rules`, and `evidence_links`, respectively. Other profile
fields produce a machine-readable `unsupported-profile-field` advisory and do
not make imported records incomplete. Owner, risk, and exception metadata stay
outside this import-first schema until a separately scoped enrichment change
defines an accountable source for them.

## Interface and Dependency Analysis

### New Core Interfaces

- `src/specfact_cli/requirements/`: OpenSpec and Spec Kit import normalizers
  will consume existing parser outputs and return `RequirementInput` records.
- `src/specfact_cli/requirements/context.py`: validation gains four additive
  finding categories and layered-profile resolution when no explicit profile
  is supplied.

No parameter is removed, no required parameter is added to an existing public
API, and no existing model field changes type. The pending decision concerns
the profile-default validation semantics, not interface compatibility.

### Dependent Files Affected

#### Critical Updates Required

- None before core implementation.

#### Recommended Updates

- `src/specfact_cli/requirements/__init__.py`: export the new core helpers.
- `tests/unit/requirements/test_context_adapter.py`: cover import normalization,
  gate categories, profile resolution, idempotency, and source-directory
  immutability.
- `nold-ai/specfact-cli-modules#168`: add module command flags and persistence
  wiring after the core helpers are available.

## Risk Assessment

- Upstream-format drift is contained by a fail-closed compatibility preflight:
  unsupported schemas or template profiles return
  `unsupported-source-schema` and no requirement records. Adding a newer
  profile requires a pinned fixture and explicit core update; import never
  fetches or guesses a live upstream version.
- Content hashes intentionally treat any byte change as stale; re-import is the
  rollback path and remains idempotent.
- The new default profile source can change validation severity for callers
  that omit `--profile`; tests must prove explicit profiles still override it.

## Format Validation

- **proposal.md Format**: Pass — required sections, capability mapping, source
  tracking, ownership split, impact, and rollback constraints are present.
- **tasks.md Format**: Pass — TDD order is explicit; the required worktree was
  created first; GitHub synchronization now precedes PR creation; post-merge
  cleanup is recorded.
- **specs Format**: Pass — requirements use Given/When/Then scenarios and map
  to the declared capabilities.
- **Config.yaml Compliance**: Pass — offline/read-only constraints, contracts,
  documentation, test-first evidence, and the required-field mapping are
  accounted for.

## OpenSpec Validation

- **Status**: Pass
- **Command**: `openspec validate openspec-01-intent-trace --strict`
- **Issues Found/Fixed**: 2 — task ordering/cleanup and required-field mapping.

## Validation Artifacts

- Worktree: `/Users/dom/git/nold-ai/specfact-cli-worktrees/feature/openspec-01-intent-trace`
- GitHub readiness: issue #350 is open and Todo, with parent #371, required
  labels/project assignment, closed blockers #238 and #239, and no items it
  blocks.
