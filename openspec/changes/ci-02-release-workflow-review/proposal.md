# Close release workflow authentication and evidence gaps

## Why

PR #731 executes a reviewed authentication wrapper before exposing external module sources. A wrapper edit can skip
signature checks. Native workflow JavaScript tests also rely on an undeclared Node installation. Complete push-filter
preservation tests exist outside the frozen original evidence mapping.

## What Changes

- Invoke the base checkout canonical verifier API and key directly from isolated workflow Python, before module exports.
- Preserve bootstrap compatibility when the base lacks the new wrapper, and verify every exposed source bundle.
- Pin Node setup in all jobs collecting native JavaScript regressions and document the local prerequisite.
- Record complete push-filter preservation as separate regression evidence without changing frozen proof.
- Wrap related documentation prose while preserving support and publication claims.

## Impact

No runtime API, dependency locks, module signatures, fixture locks, or product versions change. Two workflow consumers
and three test jobs change. Node setup adds a small download on cache misses; existing test scopes remain unchanged.
Rollback uses a reviewed revert and restores the known validation gaps.

## Source Tracking

Bug #736, parent Feature #355 / Epic #194, assigned djm81, existing bug/openspec/change-proposal/devops-backlog labels,
SpecFact CLI project, High priority in issue body. No prerequisite implementation blockers. This task owns In Progress.
Fresh base is origin/dev 2f9567e28e98b082801b13ff02e863933ce2f0f2. Separate docs17/#728 supplies module fixture proof.
