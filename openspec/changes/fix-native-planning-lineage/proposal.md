# Change: Validate native planning lineage separately from trust

## Why

After merged #761, #743's producer authenticates inherited #719 proof and selects planned maturity.
Independent execution fails before reconciliation: native stack CI exposes dev as its review base,
while the workflow requires the newer planning parent to be an ancestor of that protected review base.
Actual run 38295529623 reproduces the failure. Both bases are valid but serve different purposes.

## What Changes

- Preserve the authenticated protected proof base as verifier and review trust authority.
- Require that proof base to be an ancestor of the immutable review merge base.
- Require the authenticated planning/evidence parent to be an ancestor of the candidate source.
- Preserve the ordinary lane, exact-root check/run/authority authentication, scope whitelist,
  object equality, plan/context equality, independent execution and every protected gate.
- Add actual shell/Git controls for valid native planning ancestry and forged trust/candidate lineage.

## Capabilities

### New Capabilities

- requirements-native-stack-lineage: independent consumer lineage validation for native planning.

### Modified Capabilities

None. Provider semantics and inherited-proof eligibility are unchanged.

## Impact

Only the independent execution preflight, focused controls, evidence and coherent bugfix metadata.
Reviewed protected integration is required before planning children consume changed workflow objects.
No runtime module or deferred roadmap implementation.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- Existing issue #760; parent #355; SpecFact CLI/Todo; bug, security and change-proposal labels.
- Native dependency lists are empty. Prerequisite #761 is merged at protected c4ee5be8.
- Owner requests continued validation and forbids weakening security/stability gates.
- New exact mapping acceptance, authorized signed-head grants and protected merge remain required.
