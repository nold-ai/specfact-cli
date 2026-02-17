# Tasks: Backlog SAFe — Risk Rollups (Δ6)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply.

1. Spec deltas define behavior in `specs/risk-rollups/spec.md`.
2. **Tests second**: Write tests from spec scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git worktree branch from dev

- [ ] 1.1 Ensure on dev and up to date; create branch `feature/backlog-safe-02-risk-rollups`; verify.

## 2. Tests first (risk model, rollup, JSON output)

- [ ] 2.1 Write tests from spec: risk model inputs aggregation, rollup score (low/medium/high), JSON output shape (score, contributions).
- [ ] 2.2 Run tests: `hatch run smart-test-unit`; **expect failure**.

## 3. Implement Risk Rollups

- [ ] 3.1 Implement risk model (configurable inputs: dependency criticality, policy failures, complexity, capacity, aging/WIP).
- [ ] 3.2 Implement rollup aggregation and JSON output (score, contributions with source, reason, evidence).
- [ ] 3.3 Integrate risk section into backlog daily (and optionally refine, sprint-summary) when data available.
- [ ] 3.4 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [ ] 4.1 Run format, type-check, contract-test.
- [ ] 4.2 Update docs (agile-scrum-workflows); CHANGELOG; version sync.

## 5. Create Pull Request to dev

- [ ] 5.1 Commit, push, create PR to dev; use repo PR template.
