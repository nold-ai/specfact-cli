## Context

This change wires the CLI validation layer (snapshots, anti-patterns, acceptance tests) into the existing CI pipeline. It extends `pr-orchestrator.yml` with new jobs and steps, and adds a snapshot update workflow.

## Goals / Non-Goals

**Goals:**

- Add snapshot validation as a hard gate in the existing tests job
- Add black-box acceptance testing as a new job with wheel installation
- Define and document tiered gating (hard vs advisory)
- Add snapshot update workflow for developers
- Extend contract-test system with CLI behavior contract tier

**Non-Goals:**

- No new test creation (those are cli-val-01 through cli-val-04)
- No production CLI code changes
- No changes to existing test behavior — only CI pipeline configuration

## Decisions

- Snapshot tests run in the existing `tests` job for speed (no separate job overhead)
- Black-box acceptance tests run in a new `cli-acceptance` job that builds and installs the wheel first — true black-box isolation
- The `cli-acceptance` job depends on `tests` (fast path validates first; no point running slow black-box if fast path fails)
- Snapshot update workflow is `workflow_dispatch` only (manual trigger) — prevents accidental automated updates
- Hypothesis edge cases are advisory, not hard gates — avoids blocking PRs on non-deterministic fuzz results
- CLI behavior contracts are added as a new tier in `tools/contract_first_smart_test.py` — fits the existing tiered architecture

## CI Job Dependency Chain

```
tests (existing) → cli-acceptance (new, hard gate) → package-validation (existing)
     ↓
 snapshot check (step in tests, hard gate)
 anti-pattern safety (step in tests, hard gate)
 hypothesis fuzz (step in tests, advisory)
```

## Risks / Trade-offs

- [Black-box tests add CI runtime] -> Mitigation: only 3-5 flagship chain tests + YAML scenarios; bounded to ~60s
- [Snapshot updates add PR friction] -> Mitigation: clear workflow documentation; snapshot update job is one-click
- [dev-to-main PR skip may bypass new gates] -> Mitigation: new gates run on all PRs to dev; main skip applies only to already-validated code

## Migration Plan

1. Add snapshot check step to `tests` job in pr-orchestrator.yml
2. Add cli-acceptance job to pr-orchestrator.yml
3. Create snapshot update workflow file
4. Extend contract_first_smart_test.py with CLI contract tier
5. Add combined hatch script
6. Test CI changes on a feature branch PR

## Open Questions

- Whether to add the CLI acceptance gate to specfact.yml as well (dedicated contract validation workflow)
- Whether dev-to-main PRs should run the full CLI validation or rely on dev-branch validation
