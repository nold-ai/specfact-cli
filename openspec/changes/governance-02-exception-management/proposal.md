# Change: Exception Management — Time-Bound, Tracked Policy Exceptions

## Why




Enterprises always need exceptions — a legacy service can't comply with the new API versioning policy until migration completes, a regulatory deadline grants a 6-month grace period. But untracked exceptions defeat governance: they become permanent workarounds. Explicit, tracked, time-bound exceptions in config — with automatic expiry, monthly digests, and audit trail — make governance flexible without losing accountability.

## Ownership Alignment (2026-04-08)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: exception schema, expiry semantics, and scope-suppression rules consumed by sibling governance changes.
- Bundle-owned follow-up required: the user-facing exception commands and policy-runtime integration below must be implemented by the canonical bundle owner rather than by `specfact-cli` core.
- Target modules-repo follow-up issue: [#167](https://github.com/nold-ai/specfact-cli-modules/issues/167) in `nold-ai/specfact-cli-modules`
- Implementation MUST NOT assume a core-owned exception command surface until a narrower retained-core delta is defined.

## What Changes




- **NEW**: Exception declaration in `.specfact/exceptions.yaml`:
  ```yaml
  exceptions:
    - id: EXC-1234
      policy: clean-code-principles/banned-generic-public-names
      scope: service:legacy-reporting
      reason: "Migration in progress, target Q4 2026"
      expires_at: 2026-12-31
      approved_by: "CIO"
      created_at: 2026-02-15
  ```
- **NEW**: `specfact exceptions list` — show all active, approaching expiry, and expired exceptions
- **NEW**: `specfact exceptions add --policy <name> --scope <scope> --reason <reason> --expires <date> --approved-by <name>` — add a tracked exception
- **NEW**: `specfact exceptions check` — verify all exceptions are still valid (not expired); flag expired exceptions as hard failures
- **NEW**: Behavior during validation:
  - Active exception: treated as warning locally, non-blocking in CI
  - Approaching expiry (configurable threshold, default 30 days): elevated warning with reminder
  - Expired exception: hard failure — same as if exception never existed
- **NEW**: Monthly digest generation: `specfact exceptions digest` — summary of approaching expirations for governance review
- **EXTEND**: Evidence output (governance-01) includes exception status in evidence artifacts
- **EXTEND**: Policy engine respects exception scope during validation — matching exceptions suppress the specific policy rule for the specific scope only, including clean-code pack rules
- **NEW**: Ownership authority — this change is authoritative for exception-scope suppression and expiry semantics; evidence schema remains owned by governance-01.

## Capabilities
### New Capabilities

- `exception-management`: Time-bound, tracked policy exceptions with automatic expiry, scope-limited suppression, approaching-expiry warnings, monthly digest generation, and audit trail in evidence artifacts.

### Modified Capabilities

- `policy-engine`: Extended to respect exception scope during validation (suppress specific policy for specific scope)
- `exception-management`: Extended so clean-code exceptions are expressed by policy rule ID, not by introducing a parallel `principle` exception schema
- `governance-evidence-output`: Extended to include exception status in evidence artifacts


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #248
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/248>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#167
- **Paired Modules Scope**: runtime exception management and enforcement
- **Last Synced Status**: proposed
- **Sanitized**: false
