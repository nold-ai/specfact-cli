# Tasks: Ceremony Cockpit — Ceremony Aliases (Δ3)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply.

1. Spec deltas define behavior in `specs/ceremony-cockpit/spec.md`.
2. **Tests second**: Write tests from spec scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git branch from dev

- [ ] 1.1 Ensure on dev and up to date; create branch `feature/ceremony-cockpit-01-ceremony-aliases`; verify.

## 2. Tests first (ceremony aliases, mode, order)

- [ ] 2.1 Write tests from spec: ceremony standup/refinement/planning delegate to backlog; --mode passed through; exceptions-first order when data exists.
- [ ] 2.2 Run tests: `hatch run smart-test-unit`; **expect failure**.

## 3. Implement Ceremony Cockpit

- [ ] 3.1 Add command group `specfact ceremony` with subcommands standup, refinement, planning (delegate to backlog daily, refine, sprint-summary).
- [ ] 3.2 Add `--mode scrum|kanban|safe` at ceremony level; pass through to backlog commands.
- [ ] 3.3 Wire exceptions-first default section order for standup when Policy Engine or flow data available.
- [ ] 3.4 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [ ] 4.1 Run format, type-check, contract-test.
- [ ] 4.2 Update docs (agile-scrum-workflows); CHANGELOG; version sync.

## 5. Create Pull Request to dev

- [ ] 5.1 Commit, push, create PR to dev; use repo PR template.
