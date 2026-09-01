## 1. Issue-linked isolated worktree

- [x] 1.1 Refresh `origin/dev`, create GitHub Bug #692 with required labels/project metadata, and reconstruct the issue-linked PR in an isolated worktree from current dev SHA `4fd96d6d804da70cc7ceca83b8adce21f7da561c` after the intervening #685/#700/#701 merges.
- [x] 1.2 Read repository governance, security-fix instructions, OpenSpec/TDD rules, release rules, and internal wiki blocker/dependency context without modifying C14/C15 or internal-wiki branches.

## 2. Specifications and pre-implementation validation

- [x] 2.1 Define the cache-isolation scenario in the `trustworthy-green-checks` delta and record that release narrowing, not a gate bypass, resolves PR #691's legitimate Requirements failure.
- [x] 2.2 Run `openspec validate fix-release-promotion-security-gates --strict`; resolve format or dependency findings before tests.
- [x] 2.3 Record issue #692 readiness: Bug type, assignee, labels, project/status, no parent, no blocker/blocked-by relationships, and no concurrent branch beyond this linked worktree.

## 3. Tests first and failing evidence

- [x] 3.1 Change the shared frozen-action regression to require `enable-cache: false` and prove the existing action fails it.
- [x] 3.2 Challenge and reject a Requirements fast path; keep the workflow unchanged because it would skip finalized evidence and Code Review execution.
- [x] 3.3 Add or refine tests for the two PR #691 review findings before implementation.
- [x] 3.4 Run the focused selectors against the unmodified implementation and record exact failing-before output, timestamps, environment, and legitimate controls in `TDD_EVIDENCE.md`.
- [x] 3.5 Reproduce the commit-hook index-lock race and add a failing policy
  assertion requiring the staged-index Markdown fixer to run without filename
  batching.

## 4. Minimal implementation

- [x] 4.1 Disable setup-uv cache restore/save, remove the post-fixture npm cache, and make the compatibility lane schedule-only without changing frozen synchronization.
- [x] 4.2 Narrow authority-comment exception handling and make the Bash test helper terminal path explicit, preserving their existing public/test behavior.
- [x] 4.3 Bind Code Review dependency triggers and the Pylint license exception to their exact environment.
- [x] 4.4 Permit legitimate in-change OpenSpec deletions/renames and complete
  native archives whose rewritten evidence is represented as delete+add; ignore
  function/class-local pytest plugin declarations while retaining
  module-control-flow assignments.
- [x] 4.5 Strictly validate and archive the completed `fix-retained-red-proof-provenance` change through `openspec archive`; do not manually move it.
- [x] 4.6 Raise every Semgrep tool constraint to 1.175.0, refresh the frozen
  graph to `mcp==1.29.0`, and remove the obsolete MCP exception after a failing
  policy test and targeted no-write compatibility solve; enforce both the
  Semgrep and MCP advisory floors before synchronization.
- [x] 4.7 Set `pass_filenames: false` on the stateful Markdown auto-fix hook so
  pre-commit launches one staged-index owner per commit.

## 5. Passing evidence and security challenge

- [x] 5.1 Run the focused cache, Requirements controls, and review-finding tests; record passing-after results in `TDD_EVIDENCE.md`.
- [x] 5.2 Challenge the final candidate against alternate cache/provenance paths, then obtain an independent read-only bypass/regression review and address every confirmed concrete finding.
- [x] 5.3 Run workflow/YAML lint, exact module-signature verification, CodeQL-equivalent static controls, dependency trust, Socket, pip-audit against frozen inputs, and focused package/release checks on the final tree.
- [ ] 5.4 Run repository format, lint, type, contract, focused/full pytest, code-review JSON, and all applicable quality gates on the final tree; resolve every warning/finding or document an approved exception.
- [ ] 5.5 Retain failing-before proof for the exact SUT path-policy scenarios,
  implement the compact validator without changing the four frozen anchors
  after the authenticated red source, and complete a fresh independent bypass
  and compatibility review on the exact final head.
- [x] 5.6 Retain an amendment-cycle red proof without opening another pull
  request, authenticate the prior verified #698 head, and prove later review
  findings can complete red-to-green on the same non-default-branch PR.

## 6. Release hygiene and documentation

- [x] 6.1 Review `docs/`, `README.md`, `docs/index.md`, and navigation impact; record why no user-facing documentation change is required unless verification proves otherwise.
- [x] 6.2 Confirm GitHub/PyPI still publish 0.55.1 while current dev sources are
  0.55.3; bump exactly the next repository patch to 0.55.4 and limit added
  dependency metadata to the targeted Semgrep/MCP remediation.
- [ ] 6.3 After merge, update the internal wiki mirror summary for the compact
  path-policy scope and rebuild its graph without modifying internal wiki PR #38
  or its branch.
- [x] 6.4 Record product-owner approval for the exact final change-local Requirements
  mapping digest and pass the staged gate at `test-authored` maturity.

## 7. Pull request and release continuation

- [x] 7.1 Commit and push the issue-linked branch, create a PR to `dev` with `Fixes #692`, add required project metadata, and resolve all review threads with commit/test evidence.
- [ ] 7.2 Merge only when protected-branch policy permits; then prepare a `main`-based focused release branch whose selected security/release files exactly match the validated `dev` state.
- [ ] 7.3 Close the over-broad PR #691 only after the replacement PR exists; merge the focused release PR only when all normal main gates pass, then verify the immutable v0.55.4 tag, GitHub release, PyPI artifacts, hashes, and final pip-audit evidence.
- [ ] 7.4 After merge, update internal wiki status only outside protected PR #38 as repository policy permits, remove the implementation worktree/branch, and preserve rollback through PR reverts and normal patch/yank guidance.

## 8. Consolidated PR #698 review remediation

- [x] 8.1 Complete an exact `origin/dev...PR #698` security and clean-code review with independent security-boundary, provenance, dependency, and bypass passes.
- [x] 8.2 Record the review-driven compact SUT path-policy delta before changing
  tests or implementation; preserve external authority, linear ancestry,
  test-only red, exact archive protocol, and repeatable amendment cycles.
- [x] 8.3 Derive focused regressions from each compact path-policy scenario,
  including exact mutable SUT success, restored/renamed/copied paths, frozen
  harness and anchor rejection, ambiguous mapping rejection, and unmapped-path
  rejection; record failing-before evidence before implementation.
- [x] 8.4 Update the exact regular-file Requirements mapping, leave every
  touchpoint immutable under stock pytest, obtain product-owner approval of the
  resulting digest, and capture acceptance before implementation. The later
  boundary review superseded the proposed same-process mutable-SUT authority.
- [x] 8.5 Replace the oversized construct-by-construct interpreter with the
  compact complete-history path validator at the externally authenticated red
  boundary; do not add a fifth trust anchor or general mutable/process bypass.
- [ ] 8.6 Record passing-after evidence, run focused and repository-wide gates,
  and require the mandatory clean-code review to pass with no unresolved
  warning or error before pushing.
- [ ] 8.7 Run one independent candidate bypass/regression review against the
  exact final tree and resolve every applicable PR review thread with commit and
  verification evidence.
- [x] 8.8 Extend the existing security-gate specification and design with the
  approved transient-UID, read-only-mount, private-scratch, and cgroup-teardown
  boundary; record compatibility and rollback constraints before tests.
- [x] 8.9 Add failing regressions for exact blocking-workflow isolation,
  detached-descendant teardown, protected trusted inputs, and legitimate
  temporary Bash/Git fixture behavior before changing the executor.
- [x] 8.10 Implement the smallest hosted-Linux isolation backend around only
  the mapped pytest process; keep canonicalization and every later verifier in
  the trusted host process and fail closed rather than falling back.
- [ ] 8.11 Run focused adversarial and legitimate controls, hosted-runner smoke
  evidence, all applicable quality/security gates, and one fresh independent
  bypass/regression review before requesting final mapping/producer authority.
- [ ] 8.12 Reject every `mutable_after_red` claim under stock pytest, remove
  construct-specific plugin discovery, and reserve post-red mutation for a
  future explicit process-separated SUT runner.
