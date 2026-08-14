# Change: Add Bounded Red-to-Green Replay Evidence

## Why

A retained failing-first result is useful only if its claim is precise and reproducible. PRs #665–#671 showed that trying to infer every Python, pytest, plugin, configuration, and data dependency after the fact is unbounded and produces alternating false-green and false-stale cases.

SpecFact can prove a smaller and stronger statement mechanically: exact declared selectors failed at an explicit red commit R, passed at a green implementation checkpoint H, and remained passing at the delivered head D. Only declared implementation touchpoints may change from R to H; only named delivery-evidence records may change from H to D.

## What Changes

- Introduce three proof commits—merge base B, red commit R, and green implementation checkpoint H—plus delivered head D, with B ancestor of R, R a strict ancestor of H, H ancestor of or equal to D, and D equal to the current delivery identity.
- Require every B..R path and rename endpoint to be an explicitly mapped red-setup touchpoint with an allowed requirement/specification/test, accepted proof-mapping, or failing-before TDD-evidence role; reject implementation, dependency, workflow, verifier, policy, other generated artifacts, and unclassified paths.
- Require R..H to change only explicitly mapped implementation touchpoints.
- When H differs from D, require H..D to change only exact mapped `delivery_evidence_touchpoints` for the governed change's `TDD_EVIDENCE.md` and `CHANGE_VALIDATION.md`; reject implementation, tests, configuration, mappings, policy, workflow, schema, generated runtime inputs, and unclassified paths.
- Replay identical exact selectors at R and H, and again at D when D differs from H, during the same trusted CI run in the same pinned environment with enforced network isolation for strict proof.
- Have core produce a versioned replay capsule binding B/R/H/D Git identities, all transition manifests, plan, selector, red/green/delivery JUnit, runner, environment, network-policy, policy, verifier, and signed-module identities.
- Have the signed Requirements module validate the capsule schema, hash links, transition facts, selector outcomes, and verifier epoch without executing Git or tests.
- Produce `unproven` and fail strict policy whenever scope, history, execution, identity, or artifacts cannot be established.
- Establish a verifier-promotion boundary: a candidate replay verifier cannot authorize itself.

## Capabilities

### New Capabilities

- `requirements-bounded-red-green-proof`: Produce an attested, replayable red-to-green claim under an explicit Git mutation policy.

## Impact

- Planning scope only; no implementation, workflow, tests, fixture pins, or released schemas change in this commit.
- Depends on the paired modules R08 versioned replay-capsule contract accepting the delivery binding D and a signed immutable module release/fixture. Core owns Git/worktree/test execution and capsule production; the Requirements module owns capsule validation and chronology status without executing Git or tests.
- Later implementation should simplify or replace prior-red provenance code rather than extend it.
- Documentation impact: create or update the Requirements evidence adoption guide and docs navigation so users can distinguish `current_execution`, bounded chronology, `unproven`, and remediation.
- Rollback: disable the R08 profile and retain R07 current-run evidence; both claims remain independent.

## Explicit Non-Goals

- Infer a complete Python or pytest dependency closure.
- Reuse an old GitHub Actions artifact instead of replaying R, H, and the distinct delivered head D in the strongest mode.
- Prove stakeholder-intent completeness, overall correctness, code quality, or absence of defects.
- Replace full tests, contracts, security analysis, or Code Review.
- Define the global evidence status schema owned by governance changes.
- Repair generic Code Review PR-scope semantics.

## Source Tracking

- **GitHub Issue**: #675
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/675
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #374 — End-to-End Integration Proof
- **Parent Epic**: #258 — Integration Governance and Dogfooding
- **Paired Modules Change**: nold-ai/specfact-cli-modules#412
- **Related Code Review Change**: nold-ai/specfact-cli-modules#413
- **Superseded benchmark source**: #671
- **Planning date**: 2026-08-13
