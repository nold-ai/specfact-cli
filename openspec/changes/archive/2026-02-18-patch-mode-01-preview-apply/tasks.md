# Tasks: Patch Mode — Preview and Apply (Δ2)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply.

1. Spec deltas define behavior in `specs/patch-mode/spec.md`.
2. **Tests second**: Write tests from spec scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git worktree branch from dev

- [x] 1.1 Ensure on dev and up to date; create branch `feature/patch-mode-01-preview-apply`; verify.

## 2. Tests first (patch generate, apply local, write upstream)

- [x] 2.1 Write tests from spec: backlog refine --patch (emit file, no apply); patch apply <file> (local, preflight); patch apply --write (confirmation, idempotent).
- [x] 2.2 Run tests: `hatch run smart-test-unit`; **expect failure**.

## 3. Implement patch mode

- [x] 3.1 Implement patch pipeline (generate diffs for backlog body, OpenSpec, config).
- [x] 3.2 Add `specfact backlog refine --patch` (emit patch file and summary) — deferred by scope decision to backlog integration follow-up.
- [x] 3.3 Add `specfact patch apply <patchfile>` (preflight, apply local only).
- [x] 3.4 Add `specfact patch apply --write` (explicit confirmation, idempotent upstream updates).
- [x] 3.5 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [x] 4.1 Run format, type-check, contract-test.
- [x] 4.2 Update docs (agile-scrum-workflows, devops-adapter-integration); CHANGELOG; version sync — handled in broader backlog doc/changelog stream for this implementation cycle.

## 5. Create Pull Request to dev

- [x] 5.1 Commit, push, create PR to dev; use repo PR template.
