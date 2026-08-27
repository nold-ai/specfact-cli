# Change Validation Report: fix-release-promotion-security-gates

**Validation Date**: 2026-08-27 (Europe/Berlin)
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: repository/GitHub boundary analysis against `origin/dev` at `3ea3d9b4492ade6ec5683fac83c5b5090b0cb547`

## Executive summary

- Breaking changes: 0 detected.
- Impact: release-blocking CI security and evidence behavior only.
- Strict OpenSpec validation: pass before tests.
- Current release version remains 0.55.2. The only additional dependency change
  is the targeted Semgrep 1.175.0 / MCP 1.29.0 security update authorized by
  #692 after the prior exception premise became obsolete.

## GitHub readiness

- Issue: [#692](https://github.com/nold-ai/specfact-cli/issues/692), open, type Bug.
- Assignee: `djm81`.
- Labels: `bug`, `openspec`, `QA`, `security`.
- Project: SpecFact CLI #1, status In Progress.
- Parent/sub-issues: none; correct for this release-blocking bugfix.
- Blocked-by/blocking: none.
- Linked branch: `bugfix/692-release-promotion-security-gates`.
- Concurrent implementation: no other issue-linked branch or worktree for #692 was found.
- Hierarchy cache: refresh command completed successfully and reported unchanged content; live issue readback supplied current state.

## Security classification

- GitHub CodeQL alerts #25-#48 are duplicate dataflow instances of the same cache-persistence class, not 24 independent vulnerabilities.
- The current module fixture is immutable at commit `69f075819be5e1ceca1446b026b0417f19e584ca` and tree `5d0b8e66c6cd467e6b1ad9d582e24c66b907e205`; no current malicious content was proven.
- External exploitability is therefore unproven and privileged-only under current controls, but the persistent cache sink is real: an intentionally approved malicious fixture could write it and a later protected release job could restore it.
- Disabling setup-uv caching removes both restore and post-job save at the shared boundary. `save-cache: false` alone is insufficient.
- The staged Markdown fixer now disables pre-commit filename batching, preventing
  concurrent full-index fixer processes from contending on `index.lock`.
- Native archive validation now accepts Git's delete+add representation for a
  heavily rewritten evidence file only when every original path has a regular
  staged counterpart in one exact dated archive and no active path remains.
- The PR Orchestrator has no manual-dispatch trigger; its advisory fixture lane is schedule-only, verifies both commit and tree, and exports the module path only after verification.
- The Requirements workflow no longer registers an npm cache hook after module-owned evidence execution.
- Retained proof now includes literal annotated and conditional module-scope plugin declarations and fails closed on computed or import-bound declarations.
- The independent review reproduced a pre-install MCP-floor P1 after the first
  candidate: an internally consistent lock/export downgrade to MCP 1.23.3
  bypassed a floor map that covered only Semgrep. The final candidate adds an
  independent `mcp>=1.28.1` floor and downgrade regression; independent
  re-review confirmed the original reproducer now fails before synchronization
  and found no surviving concrete bypass. Exhaustive proof
  against arbitrary runtime namespace or plugin-manager mutation would require
  a separately bootstrapped runtime plugin-path/digest attestation design; that
  architectural hardening is not represented as completed by this bounded AST
  fix.
- Alerts remain open until GitHub observes the corrected default branch; none will be dismissed.
- Dependabot's six MCP alert instances are now validated and remediated through
  Semgrep 1.175.0's exact `mcp==1.29.0` binding. The exception register is empty;
  the pre-install policy rejects MCP below 1.28.1, and final frozen audits report
  no vulnerabilities or waivers.

## Compatibility and documentation

- Frozen/hash-locked synchronization remains `uv sync --locked --all-extras`.
- The only expected compatibility cost is slower CI downloads.
- No public CLI/API, package metadata, dependency version, user guide, README, docs index, or navigation behavior changes.
- The internal wiki was consulted read-only. Internal wiki PR #38 and its branch remain untouched; status synchronization is a post-merge follow-up.

## Rollback

Revert the issue-linked PR before release. If 0.55.2 has already shipped, publish a normal forward patch for a regression; do not rewrite the tag or published history. Yank only a demonstrably unsafe PyPI artifact under normal release policy.

## Validation record

- `openspec validate fix-release-promotion-security-gates --strict`: pass.
- Authoritative initial failing-before run: exit 1 with 2 expected failures and 2 legitimate passing controls; see `TDD_EVIDENCE.md`.
- Review/bypass failing-before runs reproduced all applicable PR findings, including the final annotated/computed/import-bound P1.
- Changed-scope passing-after run: 211 passed; focused workflow/provenance owners: 96 passed; workflow lint: pass.
- Final full repository and pinned-fixture suite: 3066 passed, 10 skipped;
  repository lint/type checks,
  Semgrep, Bandit, frozen dependency audits, license checks, reproducible
  delivery, strict module signatures, wheel build, and Twine artifact checks
  passed.
- The exact PR Orchestrator smart-test-full command also passed with 64%
  aggregate coverage against the configured 50% threshold.
- Final staged Requirements evidence passed at `test-authored` maturity against
  the product-owner-approved change-local mapping digest.
- YAML lint no longer reports the #692 change. It still prints inherited R07/R08
  planning findings while exiting zero; those protected planning changes remain
  outside this patch and are recorded as a baseline limitation rather than
  silently treated as clean.
- Code Review reports zero errors and zero warnings. Its 13 informational
  complexity observations are pre-existing long security-policy tests and the
  explicit license-policy evaluator; no unrelated refactor was folded into this
  security patch.
- A targeted no-write solve changed only Semgrep 1.171.0 -> 1.175.0 and MCP
  1.23.3 -> 1.29.0 in the 184-package graph. The six-rule repository SAST scan
  then passed over 297 Python targets with zero findings.
- Python 3.11, 3.12, and 3.13 frozen environments all resolved the fixed
  Semgrep/MCP pair; the policy selector passed in each tested interpreter.
