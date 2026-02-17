# Tasks: Backlog Kanban — Flow Metrics (Δ4)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply.

1. Spec deltas define behavior in `specs/kanban-flow/spec.md`.
2. **Tests second**: Write tests from spec scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git worktree branch from dev

- [ ] 1.1 Ensure on dev and up to date; create branch `feature/backlog-kanban-01-flow-metrics`; verify.

## 2. Tests first (flow command, config, output)

- [ ] 2.1 Write tests from spec: backlog flow command (WIP, aging, output format), kanban config load, JSON/Markdown output.
- [ ] 2.2 Run tests: `hatch run smart-test-unit`; **expect failure**.

## 3. Implement Kanban Flow

- [ ] 3.1 Implement `.specfact/kanban.yaml` loader (columns, WIP limits, aging thresholds).
- [ ] 3.2 Implement `specfact backlog flow` (WIP per column, aging, optional cycle time/throughput/blocked); JSON and Markdown output.
- [ ] 3.3 Integrate with Policy Engine (#176) for Kanban entry/exit policies when config present.
- [ ] 3.4 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [ ] 4.1 Run format, type-check, contract-test.
- [ ] 4.2 Update docs (agile-scrum-workflows); CHANGELOG; version sync.

## 5. Create Pull Request to dev

- [ ] 5.1 Commit, push, create PR to dev; use repo PR template.
