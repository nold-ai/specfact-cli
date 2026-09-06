# Change: Fix retained red-proof provenance production

## Why

The released Requirements Evidence workflow creates red reports that its own
provenance validator cannot accept. Reconciliation records the source commit,
selectors, JUnit digest, and runner stage, but omits the source tree, merge base,
selected-test digests, and toolchain identity required by the validator. Every
later final run therefore rejects a genuine retained red artifact as
`prior-red-proof-invalid`, blocking issue-linked TDD delivery including security
PR #688.

## What Changes

- **ADD** trusted producer-side binding of every required Git, test-byte, JUnit,
  and toolchain identity to red Requirements evidence before artifact upload.
- **ADD** toolchain facts to each JUnit case through the existing core-owned pytest
  plugin so provenance comes from the actual proof process.
- **MODIFY** the Requirements workflow to bind only a successfully reconciled red
  report and fail closed when binding cannot be completed.
- **ADD** an isolated, hash-locked Code Review tool environment so the final
  review runs its declared BasedPyright and Pylint checks instead of reporting
  tool-availability warnings.
- **PRESERVE** all validator rejection behavior for incomplete, stale, tampered,
  tracked, or chronologically invalid evidence.

## Capabilities

### Modified Capabilities

- `requirements-runtime-proof-delivery`: ensure a runner-produced red artifact
  contains every immutable provenance binding required for later retention.

## Impact

- **Affected code**: `scripts/requirements_proof_pytest_plugin.py`,
  `scripts/requirements_proof_provenance.py`, and the Requirements Evidence
  workflow, plus the isolated Code Review tool lock and its audit wiring.
- **Affected tests**: focused plugin, executor, provenance, and workflow contracts.
- **Compatibility**: no public CLI/API, runtime dependency, module fixture, or
  evidence-validator relaxation. Pylint is CI-only in an isolated environment;
  BasedPyright continues to use the repository's committed npm lock. Existing
  complete reports remain valid.
- **Documentation**: contributor-facing OpenSpec/TDD evidence only; README, public
  guides, landing page, and navigation are unaffected.
- **Release**: this prerequisite is included in the already planned `0.55.2`
  security patch owned by #686; it does not independently consume another version.
- **Rollback**: revert the prerequisite PR before the patch release. After release,
  correct through a forward patch; never rewrite a published tag.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #689
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/689>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open; parent #366; blocks #686; project SpecFact CLI status Todo; assigned to djm81; labels bug/QA/openspec

## Dependencies

- Baseline: `origin/dev@e3a20f20df440dff49f8c6d1f73375451bea1d8c`.
- #686/#688 depends on this repair. Its signed dependency/security commits remain
  a distinct merge parent, but live required checks force the two scopes to ship
  through #690: #688 cannot pass the released producer, while #690 cannot pass the
  validated baseline CVE audit without #686.
- Requirements 08 remains independent and is not modified.
