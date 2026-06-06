# Change: Parked Validation Intent Helper

## Status

PARKED. The old upstream intent-engineering and SQUER workflow is no longer part
of the active product path.

## Why

SpecFact should not compete with Spec Kit, OpenSpec, or AI IDE planning
workflows for requirements interviews, decomposition, or architecture derivation.
If a helper exists later, it should only capture the narrow validation question:
what evidence must be checked before this AI-assisted change is trusted?

## What Changes

- **PARK**: Multi-skill intent interview, requirement decomposition, architecture
  generation, and evidence-check workflow.
- **KEEP AS OPTIONAL FUTURE SCOPE**: One tiny validation-intent helper that can
  record expected evidence, risk, and rerun criteria for a validation loop.
- **REMOVE FROM CRITICAL PATH**: SQUER branding, seven-question interviews,
  requirement authoring, and architecture derivation.

## Capabilities

### New Capabilities

- `validation-intent-helper`: Optional future helper for capturing expected
  validation evidence before an AI-assisted change. Not active until real user
  pull exists.

### Modified Capabilities

- `agent-skill-validation`: MAY reference the helper if it is later un-parked.

## Impact

- No implementation should begin while this change remains parked.
- If un-parked, the proposal must be rewritten as a small validation helper and
  moved out of the upstream-planning category.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #349
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/349>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
