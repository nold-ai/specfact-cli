# Tasks: Patch mode (Δ2)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply.

1. Spec deltas define behavior in `specs/patch-mode/spec.md`.
2. **Tests second**: Write tests from spec scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git branch from dev

- [ ] 1.1 Ensure on dev and up to date; create branch `feature/patch-mode-preview-apply`; verify.

## 2. Tests first (patch generate, apply local, write upstream)

- [ ] 2.1 Write tests from spec: backlog refine --patch (emit file, no apply); patch apply <file> (local, preflight); patch apply --write (confirmation, idempotent).
- [ ] 2.2 Run tests: `hatch run smart-test-unit`; **expect failure**.

## 3. Implement patch mode

- [ ] 3.1 Implement patch pipeline (generate diffs for backlog body, OpenSpec, config).
- [ ] 3.2 Add `specfact backlog refine --patch` (emit patch file and summary).
- [ ] 3.3 Add `specfact patch apply <patchfile>` (preflight, apply local only).
- [ ] 3.4 Add `specfact patch apply --write` (explicit confirmation, idempotent upstream updates).
- [ ] 3.5 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [ ] 4.1 Run format, type-check, contract-test.
- [ ] 4.2 Update docs (agile-scrum-workflows, devops-adapter-integration); CHANGELOG; version sync.

## 5. Create Pull Request to dev

- [ ] 5.1 Commit, push, create PR to dev; use repo PR template.
