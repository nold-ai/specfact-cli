# Tasks: security-02-eu-gdpr-baseline

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/security-02-eu-gdpr-baseline` from `origin/dev` (per `AGENTS.md`).
- [ ] 1.2 Run `hatch env create` in the worktree and confirm the Hatch environment exists before implementation.
- [ ] 1.3 Run `hatch run smart-test-status` and `hatch run contract-test-status` (or the repo’s standard health checks)
  and resolve failures before deeper work.
- [ ] 1.4 Perform the `AGENTS.md` self-check (worktree-only implementation, protected branches untouched).
- [ ] 1.5 If bundled modules or signed manifests are touched: run module-signing verification per `openspec/config.yaml`.
- [ ] 1.6 Confirm `security-01-unified-findings-model` remains the authority for the shared finding schema.
- [ ] 1.7 Coordinate with module-side companions `security-03-module-pii-gdpr-eu` and `enterprise-01-policy-resolution-extension`.

## 2. Spec-first and test-first preparation

- [ ] 2.0 Re-run the section 1 pre-flight commands if the branch was idle for more than a day (keep CI/git health green
  before spec edits).
- [ ] 2.1 Finalize `specs/security-gdpr-baseline/spec.md` and the `policy-engine` delta.
- [ ] 2.2 Write policy parsing tests for lawful-basis, residency allowlist, retention, and data subject request keys.
- [ ] 2.3 Write validation tests for advisory vs hard enforcement on GDPR findings.
- [ ] 2.4 Capture failing-first evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Extend the policy engine to parse and validate a `security.gdpr` namespace.
- [ ] 3.2 Implement baseline pack loading for lawful basis, residency, retention, deletion, and breach handling.
- [ ] 3.3 Wire GDPR-specific metadata into the unified security finding pipeline.
- [ ] 3.4 Ensure profile enforcement modes and future exception hooks can consume the baseline without bundle-specific logic.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests until all spec scenarios pass; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Update docs covering privacy posture, residency defaults, and exception flow.
- [ ] 4.3 Run `openspec validate security-02-eu-gdpr-baseline --strict`.
- [ ] 4.4 Run quality gates for touched scope, including `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, `hatch run smart-test`, and fresh `.specfact/code-review.json`.

## 5. Delivery

- [ ] 5.1 Mirror the change into `specfact-cli-internal/wiki/sources/security-02-eu-gdpr-baseline.md` and rebuild the internal wiki graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` with downstream dependencies.
- [ ] 5.3 Open PR from `feature/security-02-eu-gdpr-baseline` to `dev`.
- [ ] 5.4 After merge, remove the worktree branch and prune stale worktree state.
