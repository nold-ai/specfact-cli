# Change: Adopt the Signal-Calibrated Code Review Gate

## Scope rescope — 2026-09-20

Keep the signed C14/C15, profile, policy and exception-authority prerequisites. Optional preflight is not an indirect prerequisite. Use meaningful regression reproduction, current test results and independent review; no immutable RED history or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## Why

The core pre-commit helper currently counts error findings itself and then
returns the nested process status. A report can therefore contain errors while
the helper returns zero when the producer's status and severity diverge. Core
also needs an authoritative schema 1.7 consumer before protected CI can trust
the modules-side calibrated gate and approved exception evidence.

## Dependency and Readiness Status

This change is paired with modules change
`code-review-15-signal-calibrated-blocking-gate`. It is downstream of the signed
C14 module release and C14 protected core adoption, then the signed C15 module
release. Production implementation SHALL NOT consume a feature-branch module
or infer schema 1.7 fields from older reports.

The identifier uses `cli-val-07` because `cli-val-06` is already assigned to the
parked Copilot test-generation change.

## What Changes

- **NEW**: Core-owned schema 1.7 consumer contract for assurance status,
  authoritative exit code, signed policy/profile identity, occurrence evidence,
  and authenticated waiver evidence.
- **CHANGED**: `scripts/pre_commit_code_review.py` invokes review with explicit
  `--enforcement changed --bug-hunt` and returns the validated report exit code.
- **CHANGED**: Contradictory or malformed schema 1.7 status/exit fields fail
  closed instead of falling back to severity counting or subprocess status.
- **NEW**: Protected CI requires the approved signed module/schema/profile and
  trusted-base exception identity before accepting a waived error.
- **COMPATIBILITY**: Schema 1.6 remains readable only in shadow compatibility
  mode for one migration release; it cannot satisfy protected blocking policy.

## Capabilities

### New Capabilities

- `code-review-gate-consumer`: authoritative local and protected consumption of
  schema 1.7 code-review evidence.

### Modified Capabilities

- `trustworthy-green-checks`: code-review green status is derived from validated
  report truth rather than a fallback severity count.
- `ci-integration`: protected review enforcement pins the signed module, schema,
  policy, and exception authority.

## Impact

- **Code**: pre-commit code-review helper and the C14 protected consumer/workflow
  integration point after it exists.
- **Tests**: unit consumer matrix plus protected-CI acceptance/rejection fixtures.
- **Compatibility**: enforcing consumers require schema 1.7; shadow mode can
  read 1.6 during the migration release.
- **Documentation**: contributor and CI-gate guidance on authoritative status,
  approved waivers, rollout, and rollback.
- **Rollback**: set code-review policy to shadow while retaining schema 1.7
  evidence; do not restore severity-count fallback.

## Non-Goals

- Core does not implement analyzer rules, severity calibration, source
  suppression parsing, finding deduplication, or module-side policy execution.
- Core does not replace C14 protected range verification.
- Candidate policy or exception files never become approval authority.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: [#679](https://github.com/nold-ai/specfact-cli/issues/679)
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/679>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: GitHub metadata verified; blocked on signed prerequisite releases
- **Parent Feature**: [#375](https://github.com/nold-ai/specfact-cli/issues/375)
- **Paired Modules Change**: [nold-ai/specfact-cli-modules#417](https://github.com/nold-ai/specfact-cli-modules/issues/417) / `code-review-15-signal-calibrated-blocking-gate`
