# Tasks: fix-categoryless-module-command-squatting

## TDD / SDD order (enforced)

Specification deltas precede scenario-derived tests; tests must fail on vulnerable HEAD before production code changes.
Production code is implemented only after failing evidence is recorded.

## 1. Worktree and readiness

- [x] 1.1 Confirm work occurs on a non-protected branch in an attached git worktree.
- [x] 1.2 Verify the vulnerability against current registration code and check for overlapping active OpenSpec scope.
- [x] 1.3 Create and link public GitHub issue #718 under module-security feature #352 with required labels.
- [x] 1.4 Validate this change strictly before implementation.
- [x] 1.5 Verify current issue #718 project/Todo, parent #352, labels and empty native dependency lists; earlier
project-access block is resolved.
- [x] 1.6 Update `specfact-cli-internal/wiki/sources/fix-categoryless-module-command-squatting.md` and rebuild the
internal wiki graph when the sibling checkout is available.

## 2. Specification and failing evidence

- [x] 2.1 Add delta scenarios for fail-closed grouped mode and explicit legacy compatibility.
- [x] 2.2 Add focused registry tests derived from both scenarios.
- [x] 2.3 Run the focused tests against vulnerable HEAD and record failing-before evidence.

## 3. Implementation

- [x] 3.1 Skip category-less project package registration in grouped mode; reserve permanent core commands for resolved
built-in paths in both modes.
- [x] 3.2 Preserve categorized routing, non-project legacy sources and explicit unreserved flat registration.

## 4. Verification and documentation review

- [x] 4.1 Run focused registry and category-routing tests and record passing evidence.
- [x] 4.2 Run formatting, type, lint, YAML, contract, smart-test, Semgrep, and Bandit gates required for the touched
scope.
- [x] 4.3 Refresh `.specfact/code-review.json`, resolve all findings, and record the result.
- [x] 4.4 Review `README.md`, `docs/`, `docs/index.md`, and sidebar navigation for impact; update only if documented
behavior changes.
- [x] 4.5 Confirm no signed module assets or manifests changed; otherwise bump and re-sign affected modules and run
signature verification.
- [x] 4.6 Validate the OpenSpec change strictly after implementation.

## 5. Release and pull request

- [x] 5.1 Apply the required patch version bump across canonical version files and add a Security changelog entry.
- [x] 5.2 Commit with a Conventional Commit message and push the branch.
- [x] 5.3 Create a pull request to `dev` using the repository template and link the OpenSpec change and GitHub issue.

## Post-merge cleanup

- [ ] Archive the completed change with `openspec archive fix-categoryless-module-command-squatting` after merge.
- [ ] Remove the implementation worktree and prune the local branch after merge.

## 6. Current review corrections

- [x] 6.1 Extend spec deltas before tests for official category roots and rejected-package import isolation.
- [x] 6.2 Capture actual failing tests against facb690 before implementation.
- [x] 6.3 Record human acceptance of mapping a9ba0dfd and corrected native authored RED (run 38176059675); final
e550f23e acceptance/proof remains tracked by 6.7.
- [x] 6.4 Reject packages before all registration side effects and preserve effective built-in discovery.
- [ ] 6.5 Run focused/full/quality gates, restack, and verify final current-head review and Requirements.

- [x] 6.6 Add executable reserved-flat-name controls and reconcile the ended spec shim requirement.
- [ ] 6.7 Obtain exact final mapping acceptance, regenerate authored/final proof after prerequisite #760, and validate
the final stack.

- [x] 6.8 Reproduce category-builder imports during eligibility and use the existing static category map before side
effects.

## 7. Protected-base validation cycle after #761

- [x] 7.1 Refresh protected dev and capture all existing stack heads and the approved candidate.
- [x] 7.2 Preserve owner acceptance for exact mapping e550f23e; record earlier validation as historical.
- [ ] 7.3 Publish signed specification and authored tests before implementation; retain fresh native RED.
- [ ] 7.4 Restore the approved security correction, synchronize 0.55.8 artifacts, and verify final exact-head gates.
- [ ] 7.5 Restack both planning children, issue authorized signed-head grants and validate scoped-token proof reuse.
- [ ] 7.6 Resolve only validated findings and leave the final three PRs unmerged.

## 8. Protected-base cycle after #767

- [x] 8.1 Verify protected merge c6af68a0 and retain previously green heads as historical evidence.
- [x] 8.2 Publish signed specification and unchanged accepted tests; retain genuine current-base native RED.
- [ ] 8.3 Restore the accepted guard, synchronize 0.55.9 and validate all current-head required gates.
- [ ] 8.4 Restack both planning children and verify independent protected-context proof reuse.
- [ ] 8.5 Close only verified findings and leave all three target PRs unmerged.
