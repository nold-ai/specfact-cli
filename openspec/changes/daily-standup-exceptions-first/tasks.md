# Tasks: Daily standup exceptions-first (E1 delta)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. **Spec deltas** define behavior in `openspec/changes/daily-standup-exceptions-first/specs/daily-standup/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git branch from dev

- [ ] 1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
- [ ] 1.2 Create branch: `git checkout -b feature/daily-standup-exceptions-first`
- [ ] 1.3 Verify branch: `git branch --show-current`

## 2. Tests first (exceptions-first order, --mode, patch hook)

- [ ] 2.1 Write tests from spec: exceptions-first section order, --mode scrum|kanban|safe, patch hook when available.
- [ ] 2.2 Run tests: `hatch run smart-test-unit`; **expect failure**.

## 3. Implement exceptions-first and mode

- [ ] 3.1 Implement default section order: blockers → policy failures → aging → normal (when data available).
- [ ] 3.2 Add `--mode scrum|kanban|safe` to `specfact backlog daily`; adjust defaults per mode.
- [ ] 3.3 Integrate patch hook when patch-mode-preview-apply available and `--patch` set.
- [ ] 3.4 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [ ] 4.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [ ] 4.2 Run contract test: `hatch run contract-test`.
- [ ] 4.3 Update docs: agile-scrum-workflows.md, devops-adapter-integration.md (exceptions-first, --mode).
- [ ] 4.4 Add CHANGELOG entry; sync version.

## 5. Create Pull Request to dev

- [ ] 5.1 Commit and push: `git add .` then `git commit -m "feat(backlog): daily standup exceptions-first and --mode scrum|kanban|safe"` and `git push origin feature/daily-standup-exceptions-first`
- [ ] 5.2 Create PR to dev using repo PR template; reference this change ID.
