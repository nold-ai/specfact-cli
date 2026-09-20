# Tasks: cli-val-07-code-review-gate-adoption

## Scope rescope — 2026-09-20

Keep the signed C14/C15, profile, policy and exception-authority prerequisites. Optional preflight is not an indirect prerequisite. Use meaningful regression reproduction, current test results and independent review; no immutable RED history or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## 1. Worktree and readiness

- [x] 1.1 Create `feature/cli-val-07-code-review-gate-adoption` from core `dev` in the required sibling worktree.
- [x] 1.2 Create public issue [#679](https://github.com/nold-ai/specfact-cli/issues/679) and verify parent #375, labels, assignee, User Story type, SpecFact CLI/Todo project metadata, and all six native blocked-by relationships from live GitHub.
- [ ] 1.3 Verify C14 protected adoption and the signed C15 schema 1.7 module release are available.
- [ ] 1.4 Verify the paired modules issue is not concurrently in progress elsewhere.
- [ ] 1.5 Stop production implementation if any readiness item is incomplete.

## 2. Spec and compatibility freeze

- [x] 2.1 Add proposal, design, tasks, and schema/consumer delta specs.
- [x] 2.2 Cross-link both repository change orders and the paired source tracking.
- [ ] 2.3 Import the released producer/consumer matrix and pin signed module, schema, profile, and exception identities.
- [x] 2.4 Update the internal wiki source page and rebuild the graph.
- [x] 2.5 Run `openspec validate cli-val-07-code-review-gate-adoption --strict`.

## 3. Tests first

- [ ] 3.1 Add failing helper tests for explicit changed/bug-hunt invocation and authoritative report exit propagation.
- [ ] 3.2 Add failing tests for PASS, FAIL, UNKNOWN, NOT_APPLICABLE, shadow exit, malformed fields, and contradictory status/exit pairs.
- [ ] 3.3 Add failing tests proving schema 1.6 is shadow-only and cannot satisfy protected enforcement.
- [ ] 3.4 Add failing protected-consumer tests for approved trusted-base waiver, candidate self-approval, expiry, scope mismatch, and profile/module digest mismatch.
- [ ] 3.5 Observe meaningful regression failures before production edits and summarize the command and result briefly; no committed output transcript is required.

## 4. Implementation

- [ ] 4.1 Implement strict schema 1.7 report projection and invariant validation.
- [ ] 4.2 Update the pre-commit command and remove severity-count/subprocess-status fallback authority.
- [ ] 4.3 Extend the released C14 protected verifier to validate C15 policy and waiver identities.
- [ ] 4.4 Update workflow/config rollout to shadow first, then enforcing only after measurement acceptance.
- [ ] 4.5 Re-run focused tests and record passing evidence.

## 5. Validation and delivery

- [ ] 5.1 Dogfood the released signed module on core in shadow; remediate or obtain approved time-bound exceptions for every error.
- [ ] 5.2 Run format, type-check, lint, yaml, contracts, smart/full tests, independent static analysis, and fresh SpecFact review evidence.
- [ ] 5.3 Run strict OpenSpec validation and the complete schema compatibility matrix.
- [ ] 5.4 Update contributor/CI documentation and changelog/version surfaces required by release policy.
- [ ] 5.5 Merge only after the modules precision target and core protected-consumer evidence pass; archive only after paired completion.
