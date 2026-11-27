# Tasks: preflight-03-dogfood-hardening-and-release (core dogfood)

## Scope rescope — 2026-09-20

Seal, checkpoint, frozen mapping, successor approval, and historical RED/GREEN requirements in this issue apply only when an explicitly selected assurance policy requests them. They are not prerequisites for ordinary implementation, Code Review, release promotion, skill installation, or generated instructions. Keep the internal optional-feature dependency chain and source/signature integrity. Missing optional chronology is not a failed current-execution claim. No runtime policy changes in this planning update. The dogfood exercise requires both core C14 #680 and modules runtime #431; record both native prerequisites now that C14 no longer depends on #431.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../requirements-09-minimal-evidence/proposal.md).

Implementation discipline: use focused regression/reproduction and current-run results. Any task requiring immutable hosted RED, frozen test authoring or approval receipts merely to implement this feature is superseded; tests of an explicitly selected optional seal feature remain in scope.

All tasks below are future dogfood work. This planning change completes none of them and creates no dogfood or TDD evidence.

## 1. Dedicated session, worktree, and readiness

- [ ] 1.1 In a dedicated issue-linked session, create `feature/preflight-03-dogfood-hardening-and-release` from current `origin/dev` in a new core worktree before any dogfood artifact edit.
- [ ] 1.2 Refresh hierarchy metadata and verify this issue and core C14 #680 have unambiguous ownership, correct dependencies, and current project status; stop if either is concurrently active without coordination.
- [ ] 1.3 Verify core `preflight-01`, modules `preflight-02`, and core C14 #680 are delivered at the exact identities selected for dogfood.

## 2. Protocol specification and failing-first proof

- [ ] 2.1 Finalize the C14 dogfood protocol, expected-risk inventory, defect classes, evidence schema, and readiness thresholds before running the tool.
- [ ] 2.2 Add protocol/fixture tests for evidence completeness, stale identity rejection, classification, and decision aggregation.
- [ ] 2.3 Run those tests before any behavior edit and summarize meaningful failures briefly using existing local or CI results; no authored TDD ledger is required under the effective lean policy.

## 3. Read-only C14 dogfood and approved refinement

- [ ] 3.1 Capture the delivered C14 planning snapshot for read-only pre-implementation review replay; never edit shipped history or make #680 wait for dogfood.
- [ ] 3.2 Run the exact installed preflight loop and retain normalized result identities plus human output.
- [ ] 3.3 Classify every observation and present fixture corrections or separately scoped product follow-ups to the C14 owner.
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
