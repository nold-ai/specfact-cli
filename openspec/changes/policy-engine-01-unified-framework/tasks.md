# Tasks: Policy Engine — Unified Framework (Δ1)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply.

1. Spec deltas define behavior in `specs/policy-engine/spec.md`.
2. **Tests second**: Write tests from spec scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git branch from dev

- [ ] 1.1 Ensure on dev and up to date; create branch `feature/policy-engine-01-unified-framework`; verify.

## 2. Tests first (policy validate, suggest, config)

- [ ] 2.1 Write tests from spec: policy validate (deterministic, output format), policy suggest (confidence, no auto-write), config load.
- [ ] 2.2 Run tests: `hatch run smart-test-unit`; **expect failure**.

## 3. Implement Policy Engine

- [ ] 3.1 Implement policy config loader (`.specfact/policy.yaml`); schema for DoR/DoD/Flow/PI.
- [ ] 3.2 Implement `specfact policy validate` (deterministic, JSON + Markdown output; rule id, severity, evidence, recommended action).
- [ ] 3.3 Implement `specfact policy suggest` (AI-assisted, confidence-scored, patch-ready; no write without explicit action).
- [ ] 3.4 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [ ] 4.1 Run format, type-check, contract-test.
- [ ] 4.2 Update docs (agile-scrum-workflows, devops-adapter-integration); CHANGELOG; version sync.

## 5. Create Pull Request to dev

- [ ] 5.1 Commit, push, create PR to dev; use repo PR template.
