# Bind documentation to corrected portable pytest evidence

## Why

The documentation module fixture registers the portable review commands, but its native pytest adapter can accept
skipped or expected-failure tests and incomplete production coverage without the required error findings. Documentation
must consume a signed module whose actual behavior supports the documented review policy.

## What Changes

- Add six prospective native pytest/adapter scenarios against the independently authenticated documentation lock.
- Establish a new protected RED/GREEN cycle before changing that lock to the accepted CI-signed module source.
- Preserve the entire docs-16 change, its 38 mapped tests and retained proof, and the separate Requirements fixture.
- Update documentation and generated command artifacts only if the accepted module changes their current content.

## Impact

The eventual production change selects a different immutable documentation module source. This is a dependency-selection
requirement, separate from docs-16 command registration. It adds no runtime implementation to core and does not replace
the Linux external-repository capsule acceptance gate. The fresh cycle starts at synchronized dev
`2f9567e28e98b082801b13ff02e863933ce2f0f2`.

## Source Tracking and Readiness

**GitHub Issue**: #728

**Repository**: nold-ai/specfact-cli

Parent Feature #356 within Epic #194; assignee djm81; SpecFact CLI project In Progress is this ongoing authorized task.
Labels: bug, documentation, openspec, change-proposal, code-review. Native blocker relationships are empty. The issue's
acceptance criteria were refreshed for this proof cycle before implementation. Related modules #473, #477 and PR #478;
core release PR #731 consumes the resulting completed source proof. No reverse dependency blocks module publication.

Rollback is a reviewed documentation fixture change, retaining immutable earlier module assets and proof records.
