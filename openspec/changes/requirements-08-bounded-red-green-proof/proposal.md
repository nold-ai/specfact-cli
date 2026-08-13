# Change: Add Bounded Red-to-Green Replay Evidence

## Why

A retained failing-first result is useful only if its claim is precise and reproducible. PRs #665–#671 showed that trying to infer every Python, pytest, plugin, configuration, and data dependency after the fact is unbounded and produces alternating false-green and false-stale cases.

SpecFact can prove a smaller and stronger statement mechanically: exact declared selectors failed at an explicit red commit, passed at the final commit, and only declared implementation touchpoints changed between them.

## What Changes

- Introduce an explicit three-commit boundary: merge base B, red commit R, and final head H, with B ancestor of R and R a strict ancestor of H.
- Require B..R to contain no governed implementation change and R..H to change only explicitly mapped implementation touchpoints.
- Replay identical exact selectors at R and H during the same trusted CI run in the same pinned environment.
- Bind Git, plan, selector, JUnit, runner, environment, policy, and verifier identities in one attestation.
- Produce `unproven` and fail strict policy whenever scope, history, execution, identity, or artifacts cannot be established.
- Establish a verifier-promotion boundary: a candidate replay verifier cannot authorize itself.

## Capabilities

### New Capabilities

- `requirements-bounded-red-green-proof`: Produce an attested, replayable red-to-green claim under an explicit Git mutation policy.

## Impact

- Planning scope only; no implementation, workflow, tests, fixture pins, or released schemas change in this commit.
- Depends on the paired modules R08 report/attestation contract and a signed module release.
- Later implementation should simplify or replace prior-red provenance code rather than extend it.
- Rollback: disable the R08 profile and retain R07 current-run evidence; both claims remain independent.

## Explicit Non-Goals

- Infer a complete Python or pytest dependency closure.
- Reuse an old GitHub Actions artifact instead of replaying R in the strongest mode.
- Prove stakeholder-intent completeness, overall correctness, code quality, or absence of defects.
- Replace full tests, contracts, security analysis, or Code Review.
- Define the global evidence status schema owned by governance changes.
- Repair generic Code Review PR-scope semantics.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **Origin**: forensic review of [#665](https://github.com/nold-ai/specfact-cli/pull/665) through [#671](https://github.com/nold-ai/specfact-cli/pull/671)
- **Extends**: corrected `requirements-07-runtime-proof-delivery`
- **Paired Modules Change**: `requirements-08-bounded-red-green-proof`
- **Planning date**: 2026-08-13

