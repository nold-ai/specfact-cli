# Change: Adopt C14 Protected PR-Range Assurance

## Scope rescope — 2026-09-20

Optional preflight, approval seals and development checkpoints are not prerequisites. Keep independent protected-range verification, complete scope, authenticated runtime and signed producer compatibility. Use focused regression reproduction and current-run results; do not require immutable RED history, frozen selector inventories or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## Why

The signed Code Review C14 producer now emits truthful schema 1.6
`range_candidate` evidence, but core has no protected consumer that can
independently verify that evidence and promote it to effective `pr_range`.
Core issue #679 is the later C15/schema-1.7 policy adoption and cannot absorb
this missing trust-boundary work without obscuring both changes.

Without a dedicated core C14 change, a clean pull-request checkout can run the
module producer but cannot make an authoritative protected-range claim or ship
a core release that fully supports C14.

## What Changes

- **NEW**: A protected core verifier independently recomputes the unique merge
  base, governed selection, Git object/mode, diff/rename, target-tip
  policy/config, suppression-catalog, producer, artifact, and workflow
  identities required by the signed C14 handoff.
- **NEW**: A verifier-bound envelope promotes an accepted producer
  `range_candidate` to effective `pr_range`; every omitted or mismatched
  required input produces `UNKNOWN` and cannot become a green protected check.
- **NEW**: The protected PR workflow writes canonical event context under the
  runner temporary directory immediately before invocation, passes full
  base/head refs plus `--pr-context-file`, and rolls out through explicit
  shadow, warning, and enforcement phases.
- **NEW**: Execute the verifier, its imports/dependencies, policy and trust roots
  from an authenticated immutable base revision or approved release selected by
  protected workflow policy. Candidate files, workflow edits and fixture locks
  cannot select or replace that authority.
- **UPDATE**: Select a signed C14-capable publication compatible with the actual
  core candidate, verify its packaged identities, and pin the tested pair.
  The original `6a0d0b31` / module `0.49.46` / core `===0.55.1` handoff is
  historical, not a pin for current core. If no compatible signed publication
  exists, obtain one before adoption; never relax compatibility to install it.
- **UPDATE**: The existing staged pre-commit helper remains
  `explicit_files` only and consumes schema 1.6 authoritative assurance
  status/exit semantics without claiming PR authority.

## Capabilities

### New Capabilities

- `protected-code-review-range-assurance`: Protected verification and
  promotion of signed C14 `range_candidate` reports to effective `pr_range`.

### Modified Capabilities

- `pre-commit-review-gate`: Consume schema 1.6 authoritative status/exit while
  remaining a staged explicit-file check.
- `trustworthy-green-checks`: Emit a protected Code Review check only from the
  independently verified C14 envelope and fail closed on unknown evidence.

## Scope Boundary

Implementation is restricted to the following production surfaces unless a
named failing acceptance test proves one additional path is unavoidable:

- `scripts/verify_code_review_range_assurance.py` (new isolated verifier),
- `.github/workflows/pr-orchestrator.yml` (protected context and invocation),
- the existing organization-required workflow invocation policy in `nold-ai/.github`
  where needed to select the trusted verifier independently of the candidate,
- `ci/module-fixture.lock.json` (immutable signed publication identity), and
- `scripts/pre_commit_code_review.py` (schema 1.6 status/exit consumption only).

Tests are restricted to
`tests/unit/scripts/test_verify_code_review_range_assurance.py` (new),
`tests/unit/scripts/test_pre_commit_code_review.py`, and
`tests/unit/workflows/test_code_review_14_protected_range.py` (new). Tests SHALL
build temporary repositories in-process rather than adding a new shared fixture
framework. Documentation is restricted to optional
`docs/guides/code-review-protected-range-assurance.md` plus
`docs/_data/nav.yml`. Release metadata is restricted to `CHANGELOG.md`,
`pyproject.toml`, `setup.py`, `src/__init__.py`, and
`src/specfact_cli/__init__.py` when the release policy requires a version bump;
those edits are not permission to widen runtime scope.

This change MUST NOT:

- reimplement or alter module analyzers, finding classification, selection,
  sandboxing, toolchain provisioning, or report production;
- introduce schema 1.7, severity calibration, profiles, policy promotion,
  scoring, waiver/exception, autofix, or C15 behavior;
- refactor generic module discovery, installation, registry, signature, or
  package-loading abstractions;
- add Requirements behavior, evidence-graph generalization, source-to-test
  inference, new analyzer rules, or unrelated CI hardening; or
- treat review findings outside this finite C14 consumer contract as scope.

Triage every finding individually. Fix introduced or relevant defects; reject
false positives with a reason. A real pre-existing or unrelated finding needs
an individually documented, approved exception with impact and a linked
follow-up before deferral. The scope boundary is not a blanket waiver and
does not automatically authorize unrelated implementation.

## Impact

- **Affected specs**: `protected-code-review-range-assurance`,
  `pre-commit-review-gate`, `trustworthy-green-checks`.
- **Affected code**: one isolated verifier, the PR orchestrator, immutable
  module fixture, narrow staged-hook parsing, and their exact tests.
- **Release impact**: a new core release is required after implementation and
  final immutable compatibility smoke.
- **Rollback**: disable enforcement while retaining the signed C14 module,
  verifier envelope, and shadow evidence for diagnosis; the staged
  `explicit_files` hook remains available.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #680
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/680>
- **Repository**: nold-ai/specfact-cli
- **Modules implementation**: nold-ai/specfact-cli-modules#416 via PR #418
- **Historical signed publication**: nold-ai/specfact-cli-modules#419 at `6a0d0b31`
- **Downstream C15 adoption**: nold-ai/specfact-cli#679
- **Last Synced Status**: open; Todo; parent #375; blocks #679; current compatible signed pair and trusted verifier publication must be verified; implementation not started
