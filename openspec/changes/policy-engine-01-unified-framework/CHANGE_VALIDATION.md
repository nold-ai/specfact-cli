# Change Validation Report: policy-engine-01-unified-framework

**Validation Date**: 2026-02-02  
**Plan Reference**: specfact-cli-internal/docs/internal/implementation/2026-02-01-backlog-changes-improvement.md (Δ1)  
**Validation Method**: Plan alignment + OpenSpec strict validation

## Executive Summary

- **Plan Delta (Δ1)**: Unified Policy Engine (DoR/DoD/Flow/PI); `policy.validate` (deterministic), `policy.suggest` (AI-assisted, patch-ready); config `.specfact/policy.yaml`; JSON + Markdown output.
- **Breaking Changes**: 0 (new capability).
- **Validation Result**: Pass.
- **OpenSpec Validation**: `openspec validate unify-policies-engine --strict` — valid.

## Alignment with Plan Δ1

- **Δ1**: One policy engine for DoR, DoD, Kanban entry/exit, SAFe PI readiness. **Done**: proposal and spec define validate/suggest, config, result format (rule id, severity, evidence, recommended action); no network required when using snapshots.

## USP / Value-Add

- **One policy engine**: Plan guiding principle—DoR, DoD, Kanban/SAFe policies share one mechanism and consistent reporting.
- **Trust by design**: validate = deterministic; suggest = confidence-scored, patch-ready; no silent writes.
- **Foundation**: Unlocks E1 (standup exceptions), E2 (DoR coverage in sprint summary), E5 (backlog add policy-first).

## Format Validation

- proposal.md: Why, What Changes, Capabilities, Impact, Source Tracking present.
- specs/policy-engine/spec.md: Given/When/Then for validate, suggest, config.
- tasks.md: TDD/SDD order; branch first, PR last; format OK.

## Module Architecture Alignment (Re-validated 2026-02-10)

This change was re-validated after renaming and updating to align with the modular architecture (arch-01 through arch-07):

- Module package structure updated to `modules/{name}/module-package.yaml` pattern
- CLI command registration moved from `cli.py` to `module-package.yaml` declarations
- Core model modifications replaced with arch-07 schema extensions where applicable
- Adapter protocol extensions use arch-05 bridge registry (no direct mixin modification)
- Publisher and integrity metadata added for arch-06 marketplace readiness
- All old change ID references updated to new module-scoped naming

**Result**: Pass — format compliant, module architecture aligned, no breaking changes introduced.

## Scope Extension Re-validation (2026-02-18)

- **Requested extension**: Add policy template scaffolding (`specfact policy init`), include docs hints on `policy validate` config errors, and require built-in templates under `resources/templates/policies/`.
- **Spec updates**:
  - Added `Requirement: Policy config scaffolding templates` with interactive and non-interactive scenarios.
  - Added `Requirement: Policy validate docs hints` for missing/invalid config guidance.
  - Added acceptance criterion requiring template assets from `resources/templates/policies/`.
- **Task updates**:
  - Added Section 6 for extension scope delivery; marked 6.1 complete (spec scenarios added).
- **Implementation status**:
  - Added template-backed `policy init` scaffolding behavior in module code.
  - Added docs-hint output behavior for missing/invalid policy config during `policy validate`.
  - Added extension tests and TDD evidence updates.
- **OpenSpec strict validation**:
  - Command: `openspec validate policy-engine-01-unified-framework --strict`
  - Result: `Change 'policy-engine-01-unified-framework' is valid`
  - Note: PostHog telemetry network flush errors were emitted by the CLI environment but did not affect validation result.

## Scope Extension Re-validation (2026-02-18, artifact auto-discovery)

- **Requested extension**: Align policy input handling with existing `.specfact` artifact schemas so `policy validate|suggest` can run without explicit `--snapshot` when foundation artifacts already exist.
- **Spec updates**:
  - Added `Requirement: Policy input auto-discovery from .specfact artifacts`.
  - Added `Requirement: Policy input format normalization`.
- **Task updates**:
  - Added Section 7 for auto-discovery and payload normalization; implementation/test/doc items marked complete.
- **Implementation status**:
  - Added artifact resolution precedence: explicit `--snapshot`, then `.specfact/backlog-baseline.json`, then latest `.specfact/plans/backlog-*`.
  - Added normalization support for `items` as list/dict and `backlog_graph.items` as list/dict.
  - Updated command help and docs to describe artifact precedence and accepted payload shapes.
- **OpenSpec strict validation**:
  - Command: `openspec validate policy-engine-01-unified-framework --strict`
  - Result: `Change 'policy-engine-01-unified-framework' is valid`
  - Note: Telemetry network flush errors in sandbox environment were non-blocking.

## Scope Extension Re-validation (2026-02-18, compatibility mapping)

- **Requested extension**: Reduce false-positive policy failures on imported artifacts by mapping provider/raw aliases to canonical policy fields.
- **Spec updates**:
  - Added requirement for compatibility mapping from raw/provider fields and description sections.
- **Implementation status**:
  - Added alias mapping for `acceptance_criteria`, `business_value`, and `definition_of_done`.
  - Added markdown section extraction for `Acceptance Criteria` and `Definition of Done` from item descriptions.
  - Added integration test proving baseline artifacts can satisfy policy requirements through compatibility mapping.

## Scope Extension Re-validation (2026-02-18, filter/limit/group output)

- **Requested extension**: Make validate/suggest actionable on large snapshots via filtering, limits, and item-grouped output.
- **Spec updates**:
  - Added requirements for `--rule`, `--limit`, and `--group-by-item`.
- **Implementation status**:
  - Added filter/limit option handling for both `policy validate` and `policy suggest`.
  - Added grouped JSON/Markdown output structures keyed by `items[N]`.
  - Added integration tests covering filter/limit/group behavior.

## Scope Extension Re-validation (2026-02-18, grouped-limit semantics)

- **Requested extension**: In grouped mode, `--limit` should cap backlog item groups, not per-field suggestion/finding rows.
- **Spec updates**:
  - Added grouped-limit scenario clarifying `--group-by-item --limit N` limits item groups.
  - Clarified grouped suggest payload behavior to avoid duplicate top-level flat list output.
- **Implementation status**:
  - Updated grouped-mode filtering pipeline so `--limit` applies to unique item indexes after rule filtering.
  - Added integration regressions for both commands:
    - `test_policy_validate_grouped_limit_applies_to_item_count`
    - `test_policy_suggest_grouped_limit_applies_to_item_count`
- **Verification**:
  - `hatch run pytest tests/integration/commands/test_policy_engine_commands.py -q` → 14 passed.
  - `openspec validate policy-engine-01-unified-framework --strict` → valid.
  - Telemetry network flush errors from PostHog remain non-blocking in this environment.

## Scope Extension Re-validation (2026-02-18, review findings hardening)

- **Requested extension**: Address review findings for explicit snapshot path resolution and package import robustness.
- **Implementation status**:
  - Explicit relative `--snapshot` paths are now resolved against `--repo` in policy snapshot loader.
  - Policy module command shims and internal package imports were converted to package-relative imports.
- **Verification**:
  - `hatch run pytest tests/integration/commands/test_policy_engine_commands.py -q` → pass.
  - `hatch run pytest tests/unit/commands/test_policy_module_import.py -q` → pass.
  - `hatch run type-check | grep error` → `0 errors` (warnings pre-exist).
