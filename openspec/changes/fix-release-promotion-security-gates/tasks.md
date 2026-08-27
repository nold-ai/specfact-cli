## 1. Issue-linked isolated worktree

- [x] 1.1 Refresh `origin/dev`, create GitHub Bug #692 with required labels/project metadata, create linked branch `bugfix/692-release-promotion-security-gates`, and attach an isolated worktree at exact dev SHA `3ea3d9b4492ade6ec5683fac83c5b5090b0cb547`.
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
- [x] 5.2 Challenge the candidate against alternate cache/provenance paths, then obtain an independent read-only bypass/regression review and address every confirmed concrete finding.
- [x] 5.3 Run workflow/YAML lint, exact module-signature verification, CodeQL-equivalent static controls, dependency trust, Socket, pip-audit against frozen inputs, and focused package/release checks.
- [x] 5.4 Run repository format, lint, type, contract, focused/full pytest, code-review JSON, and all applicable quality gates; resolve every warning/finding or document an approved exception.

## 6. Release hygiene and documentation

- [x] 6.1 Review `docs/`, `README.md`, `docs/index.md`, and navigation impact; record why no user-facing documentation change is required unless verification proves otherwise.
- [x] 6.2 Confirm 0.55.2 is still unpublished and remains the next patch after
  0.55.1; do not bump to 0.55.3, and limit added dependency metadata to the
  targeted Semgrep/MCP remediation.
- [x] 6.3 Record the internal-wiki status follow-up without modifying internal wiki PR #38 or its branch.
- [x] 6.4 Record product-owner approval for the exact change-local Requirements
  mapping digest and pass the staged gate at `test-authored` maturity.

## 7. Pull request and release continuation

- [ ] 7.1 Commit and push the issue-linked branch, create a PR to `dev` with `Fixes #692`, add required project metadata, and resolve all review threads with commit/test evidence.
- [ ] 7.2 Merge only when protected-branch policy permits; then prepare a `main`-based focused release branch whose selected security/release files exactly match the validated `dev` state.
- [ ] 7.3 Close the over-broad PR #691 only after the replacement PR exists; merge the focused release PR only when all normal main gates pass, then verify the immutable v0.55.2 tag, GitHub release, PyPI artifacts, hashes, and final pip-audit evidence.
- [ ] 7.4 After merge, update internal wiki status only outside protected PR #38 as repository policy permits, remove the implementation worktree/branch, and preserve rollback through PR reverts and normal patch/yank guidance.
