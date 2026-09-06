# Tasks: preflight-03-dogfood-hardening-and-release (core dogfood)

All tasks below are future dogfood work. This planning change completes none of them and creates no dogfood or TDD evidence.

## 1. Dedicated session, worktree, and readiness

- [ ] 1.1 In a dedicated issue-linked session, create `feature/preflight-03-dogfood-hardening-and-release` from current `origin/dev` in a new core worktree before any dogfood artifact edit.
- [ ] 1.2 Refresh hierarchy metadata and verify this issue and core C14 #680 have unambiguous ownership, correct dependencies, and current project status; stop if either is concurrently active without coordination.
- [ ] 1.3 Verify core `preflight-01`, modules `preflight-02`, and core C14 #680 are delivered at the exact identities selected for dogfood.

## 2. Protocol specification and failing-first proof

- [ ] 2.1 Finalize the C14 dogfood protocol, expected-risk inventory, defect classes, evidence schema, and readiness thresholds before running the tool.
- [ ] 2.2 Add protocol/fixture tests for evidence completeness, stale identity rejection, classification, and decision aggregation.
- [ ] 2.3 Run those tests before any behavior edit, capture failing-first evidence, and create `TDD_EVIDENCE.md` only if implementation support is required.

## 3. Read-only C14 dogfood and approved refinement

- [ ] 3.1 Capture the immutable starting C14/OpenSpec/GitHub/repository snapshot without editing the existing C14 worktree.
- [ ] 3.2 Run the exact installed preflight loop and retain normalized result identities plus human output.
- [ ] 3.3 Classify every observation and present exact source-owned refinements to the C14 owner.
- [ ] 3.4 After any separately authorized refinement, capture a new snapshot and rerun the complete loop; never reuse prior approval.

## 4. Readiness decision and verification

- [ ] 4.1 Evaluate the declared go/no-go criteria and map each accepted hardening item to observed evidence and a regression case.
- [ ] 4.2 Run mapped tests and required quality gates for any dogfood-support artifact behavior; record only observed results.
- [ ] 4.3 Run `openspec status --change preflight-03-dogfood-hardening-and-release --json` and `openspec validate preflight-03-dogfood-hardening-and-release --strict`.
- [ ] 4.4 Publish the bounded readiness decision in the issue/PR without claiming universal correctness.

## 5. Delivery and post-merge cleanup

- [ ] 5.1 Verify the paired modules hardening scope contains only evidence-backed items and remains blocked on a no-go decision.
- [ ] 5.2 Open the core dogfood PR to `dev` as the final pre-merge task, linking C14 and the paired modules issue.
- [ ] 5.3 Before archive, hand accepted hardening evidence to modules #432 and verify that modules-owned signing/stable publication remains pending or complete there; then, from the repository root after merge, run `openspec archive preflight-03-dogfood-hardening-and-release`, update ordering/wiki source state, and remove the dedicated worktree and merged branch.
