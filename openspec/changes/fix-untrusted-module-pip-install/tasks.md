## 1. Branch and specification

- [x] 1.1 Confirm work occurs on the dedicated `work` worktree branch.
- [x] 1.2 Add trust-boundary and requirement-policy spec deltas.
- [x] 1.3 Validate the OpenSpec change strictly.

## 2. Test-first proof

- [x] 2.1 Add unit tests derived from every security scenario.
- [x] 2.2 Run focused tests before production edits and record failing evidence.

## 3. Implementation

- [x] 3.1 Add PEP 508 named-requirement validation before pip subprocesses.
- [x] 3.2 Restrict resolution/install input to selected marketplace metadata.
- [x] 3.3 Verify marketplace artifacts before dependency side effects.
- [x] 3.4 Record passing focused-test evidence.

## 4. Verification and delivery

- [x] 4.1 Review README, `docs/`, `docs/index.md`, and navigation impact; no update required because CLI syntax and documented workflows are unchanged.
- [x] 4.2 Run formatting, typing, lint, YAML, contract, smart-test, Semgrep, Bandit, and module-signature gates; record pre-existing/environment limitations.
- [x] 4.3 Refresh `.specfact/code-review.json`; it contains zero findings but UNKNOWN analyzer evidence because the verified OCI cache is unavailable, documented in TDD evidence.
- [x] 4.4 Bump the patch version in all four authorities and add a changelog security entry.
- [ ] 4.5 Commit the completed change.
- [ ] 4.6 Create the pull request to `dev` without publicly reproducing exploit details.
- [ ] 4.7 After merge, archive with `openspec archive fix-untrusted-module-pip-install` and clean up the worktree.
