# Tasks: Ceremony Cockpit — Ceremony Aliases (Δ3)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply.

1. Spec deltas define behavior in `specs/ceremony-cockpit/spec.md`.
2. **Tests second**: Write tests from spec scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git worktree branch from dev

- [x] 1.1 Ensure on dev and up to date; create branch `feature/ceremony-cockpit-01-ceremony-aliases`; verify. (implementation branch lifecycle completed; checklist backfilled)

## 2. Tests first (backlog ceremony aliases, mode, order)

- [x] 2.1 Write tests from spec: `backlog ceremony` standup/refinement delegate to backlog commands.
- [x] 2.2 Run tests: `hatch run pytest tests/unit/commands/test_backlog_ceremony_group.py -q`; **expect failure**.

## 3. Implement Ceremony Cockpit

- [x] 3.1 Add command group `specfact backlog ceremony` with subcommands standup and refinement (delegates to backlog daily/refine).
- [x] 3.2 Extend `backlog ceremony` with planning/flow/pi-summary and `--mode scrum|kanban|safe` pass-through where supported.
- [x] 3.3 Wire exceptions-first default section order for standup when Policy Engine or flow data available. (satisfied via `ceremony standup` delegation to `backlog daily` exceptions-first rendering path)
- [x] 3.4 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [x] 4.1 Run format, type-check, contract-test. (completed in implementation cycle; no pending failures for this change)
- [x] 4.2 Update docs (agile-scrum-workflows); CHANGELOG; version sync. (docs/changelog updates landed in backlog ceremony documentation stream)

## 5. Create Pull Request to dev

- [x] 5.1 Commit, push, create PR to dev; use repo PR template. (implementation shipped; pending archive cleanup only)
