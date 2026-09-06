## 1. Worktree and specification

- [x] 1.1 Confirm implementation runs on the dedicated non-protected `work` branch/worktree.
- [x] 1.2 Add the repository-confined IDE prompt export specification and design.
- [x] 1.3 Create and link public issue #720 with parent, labels, assignment, project status, and blocker metadata.

## 2. Tests and failing evidence

- [x] 2.1 Add tests derived from both specification scenarios: external export-root symlinks fail without mutation, and normal exports preserve unrelated directories.
- [x] 2.2 Run the focused tests before production changes and record failing output in `TDD_EVIDENCE.md`.

## 3. Implementation

- [x] 3.1 Add a small internal containment guard for IDE export roots.
- [x] 3.2 Apply the guard before cleanup and prompt export filesystem mutations.

## 4. Verification and delivery

- [x] 4.1 Re-run focused tests and record passing output in `TDD_EVIDENCE.md`.
- [x] 4.2 Run formatting, type-checking, lint, YAML lint, contract tests, smart tests, independent static analysis, and SpecFact code review gates; record unrelated/environment limitations in `TDD_EVIDENCE.md`.
- [x] 4.3 Review `README.md`, `docs/`, `docs/index.md`, and navigation for documentation impact; no update is required.
- [x] 4.4 Bump the patch version in all canonical files and add the security fix to `CHANGELOG.md`.
- [x] 4.5 Verify signed module manifests remain valid; no signed module asset changed.
- [x] 4.6 Record the internal wiki mirror/rebuild follow-up because the sibling checkout is unavailable.
- [ ] 4.7 Commit the completed change and create a pull request to `dev`.

## 5. Post-merge cleanup

- [ ] 5.1 After merge, run `openspec archive security-01-confine-ide-prompt-exports` and perform worktree cleanup.
