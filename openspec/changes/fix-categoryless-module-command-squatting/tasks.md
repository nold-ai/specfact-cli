# Tasks: fix-categoryless-module-command-squatting

## TDD / SDD order (enforced)

Specification deltas precede scenario-derived tests; tests must fail on vulnerable HEAD before production code changes. Production code is implemented only after failing evidence is recorded.

## 1. Worktree and readiness

- [x] 1.1 Confirm work occurs on a non-protected branch in an attached git worktree.
- [x] 1.2 Verify the vulnerability against current registration code and check for overlapping active OpenSpec scope.
- [x] 1.3 Create and link public GitHub issue #718 under module-security feature #352 with required labels.
- [x] 1.4 Validate this change strictly before implementation.
- [ ] 1.5 Add issue #718 to the organization project with a token that has project access; implementation is blocked until this metadata gate is complete.
- [ ] 1.6 Update `specfact-cli-internal/wiki/sources/fix-categoryless-module-command-squatting.md` and rebuild the internal wiki graph when the sibling checkout is available.

## 2. Specification and failing evidence

- [x] 2.1 Add delta scenarios for fail-closed grouped mode and explicit legacy compatibility.
- [ ] 2.2 Add focused registry tests derived from both scenarios.
- [ ] 2.3 Run the focused tests against vulnerable HEAD and record failing-before evidence.

## 3. Implementation

- [ ] 3.1 Skip category-less package command registration when grouping is enabled.
- [ ] 3.2 Preserve categorized registration and explicitly disabled grouping behavior.

## 4. Verification and documentation review

- [ ] 4.1 Run focused registry and category-routing tests and record passing evidence.
- [ ] 4.2 Run formatting, type, lint, YAML, contract, smart-test, Semgrep, and Bandit gates required for the touched scope.
- [ ] 4.3 Refresh `.specfact/code-review.json`, resolve all findings, and record the result.
- [ ] 4.4 Review `README.md`, `docs/`, `docs/index.md`, and sidebar navigation for impact; update only if documented behavior changes.
- [ ] 4.5 Confirm no signed module assets or manifests changed; otherwise bump and re-sign affected modules and run signature verification.
- [ ] 4.6 Validate the OpenSpec change strictly after implementation.

## 5. Release and pull request

- [ ] 5.1 Apply the required patch version bump across canonical version files and add a Security changelog entry.
- [ ] 5.2 Commit with a Conventional Commit message and push the branch.
- [ ] 5.3 Create a pull request to `dev` using the repository template and link the OpenSpec change and GitHub issue.

## Post-merge cleanup

- [ ] Archive the completed change with `openspec archive fix-categoryless-module-command-squatting` after merge.
- [ ] Remove the implementation worktree and prune the local branch after merge.
