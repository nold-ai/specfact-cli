# Tasks: Policy Engine — Unified Framework (Δ1)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply.

1. Spec deltas define behavior in `specs/policy-engine/spec.md`.
2. **Tests second**: Write tests from spec scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git worktree branch from dev

- [x] 1.1 Ensure on dev and up to date; create branch `feature/policy-engine-01-unified-framework`; verify.

## 2. Tests first (policy validate, suggest, config)

- [x] 2.1 Write tests from spec: policy validate (deterministic, output format), policy suggest (confidence, no auto-write), config load.
- [x] 2.2 Run tests: `hatch run pytest tests/integration/commands/test_policy_engine_commands.py -v`; **expect failure**.

## 3. Implement Policy Engine

- [x] 3.1 Implement policy config loader (`.specfact/policy.yaml`); schema for DoR/DoD/Flow/PI.
- [x] 3.2 Implement `specfact policy validate` (deterministic, JSON + Markdown output; rule id, severity, evidence, recommended action).
- [x] 3.3 Implement `specfact policy suggest` (AI-assisted, confidence-scored, patch-ready; no write without explicit action).
- [x] 3.4 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [x] 4.1 Run format, type-check, contract-test.
- [x] 4.2 Update docs (agile-scrum-workflows, devops-adapter-integration); CHANGELOG; version sync.

## 5. Create Pull Request to dev

- [x] 5.1 Commit, push, create PR to dev; use repo PR template.

## 6. Scope extension: policy templates and docs hints

- [x] 6.1 Add spec scenarios for `specfact policy init` template scaffolding and validate docs hints.
- [x] 6.2 Add tests for interactive/non-interactive template generation and validate error hint output.
- [x] 6.3 Implement `specfact policy init` with template selection (`--template` + interactive prompt) writing `.specfact/policy.yaml`.
- [x] 6.4 Source built-in policy templates from `resources/templates/policies/` and ensure package inclusion.
- [x] 6.5 Extend `specfact policy validate` errors to include policy format documentation hint.
- [x] 6.6 Capture failing-first and passing evidence for new scope in `TDD_EVIDENCE.md`.
