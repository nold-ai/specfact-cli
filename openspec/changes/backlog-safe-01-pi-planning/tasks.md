# Tasks: Backlog SAFe — PI Planning (Δ5)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply.

1. Spec deltas define behavior in `specs/safe-pi/spec.md`.
2. **Tests second**: Write tests from spec scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git worktree branch from dev

- [ ] 1.1 Ensure on dev and up to date; create branch `feature/backlog-safe-01-pi-planning`; verify.

## 2. Tests first (pi-summary, config, WSJF)

- [ ] 2.1 Write tests from spec: pi-summary command (scope, commitments, ROAM), safe config load, WSJF calculation and confirmation.
- [ ] 2.2 Run tests: `hatch run smart-test-unit`; **expect failure**.

## 3. Implement SAFe PI

- [ ] 3.1 Implement `.specfact/safe.yaml` loader (PI/iteration/ART); Policy Engine PI readiness hook.
- [ ] 3.2 Implement `specfact backlog pi-summary` (scope, commitments, dependency contracts, ROAM); JSON and Markdown output.
- [ ] 3.3 Implement WSJF assistance (calculation, AI-assisted missing fields, confirmation; no silent write).
- [ ] 3.4 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [ ] 4.1 Run format, type-check, contract-test.
- [ ] 4.2 Update docs (agile-scrum-workflows); CHANGELOG; version sync.

## 5. Create Pull Request to dev

- [ ] 5.1 Commit, push, create PR to dev; use repo PR template.
