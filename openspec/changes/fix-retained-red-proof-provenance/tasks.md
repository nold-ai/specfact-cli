# Tasks: fix-retained-red-proof-provenance

## 1. Branch and governance readiness

- [x] 1.1 Refresh `origin/dev` and create issue-linked branch `bugfix/689-retained-red-proof-provenance` in a separate isolated worktree from `e3a20f20df440dff49f8c6d1f73375451bea1d8c`.
- [x] 1.2 Create issue #689 after duplicate search; verify parent #366, project, labels, assignee, and blocking relationship to #686.

## 2. Specification and failing-first proof

- [x] 2.1 Add the producer-binding spec, design, Requirements mapping, and accepted issue-linked review record before implementation.
- [x] 2.2 Add focused plugin, executor, binder, and workflow contract tests derived from the scenarios.
- [x] 2.3 Run the focused tests before production edits and record the expected failures in `TDD_EVIDENCE.md`.

## 3. Minimal implementation

- [x] 3.1 Record canonical toolchain properties through the core-owned pytest plugin.
- [x] 3.2 Add fail-closed binding of Git objects, test blobs, JUnit, and toolchain facts to the provenance utility.
- [x] 3.3 Invoke binding only after successful red reconciliation and before artifact publication.

## 4. Passing evidence and quality gates

- [ ] 4.1 Run focused tests, retained-proof legitimate/tamper controls, and a real red-to-final Requirements workflow reproduction. (Local controls and authoritative red complete; final GitHub run pending.)
- [ ] 4.2 Run format, lint, type-check, YAML/contract tests, full applicable tests, module signatures, dependency/security gates, and OpenSpec strict validation. (Local gates complete; final GitHub gates pending.)
- [ ] 4.3 Generate fresh changed/full code-review evidence, remediate all actionable findings, and close every fixed PR review thread with test evidence. (Local full-enforcement review has zero findings; PR review pending.)
- [x] 4.4 Review README, docs, landing/navigation, release, and contributor impact; keep public docs unchanged when no user-facing behavior changes.

## 5. Delivery

- [x] 5.1 Create a signed Conventional Commit series preserving spec/tests/failing evidence before production implementation.
- [ ] 5.2 Push and create the issue-linked PR to `dev`; observe required checks/reviews and merge only when policy permits.
- [x] 5.3 Keep the version at `0.55.1` in this prerequisite and let #686 perform the single planned `0.55.2` patch bump/changelog entry.

## Post-merge cleanup

- [ ] 6.1 Archive this change using `openspec archive fix-retained-red-proof-provenance`, refresh internal wiki status from its repository root, and remove the worktree when safe.
