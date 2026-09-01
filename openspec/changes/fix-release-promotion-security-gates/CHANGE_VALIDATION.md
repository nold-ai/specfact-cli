# Change Validation Report: fix-release-promotion-security-gates

**Validation Date**: 2026-09-01 (Europe/Berlin)
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: repository/GitHub boundary analysis against `origin/dev` at `4fd96d6d804da70cc7ceca83b8adce21f7da561c`

## Executive summary

- Breaking changes: 0 detected.
- Impact: release-blocking CI security and evidence behavior only.
- Strict OpenSpec validation: pass before tests.
- Current dev version is 0.55.3 after the intervening module-scope patch. This
  change advances exactly the next patch, 0.55.4. The only additional dependency
  change is the targeted Semgrep 1.175.0 / MCP 1.29.0 security update authorized
  by #692 after the prior exception premise became obsolete.
- User decision: extend the existing #692 bugfix scope with the smallest complete
  execution-isolation boundary after independent review proved same-identity
  per-file sealing incomplete.

## GitHub readiness

- Issue: [#692](https://github.com/nold-ai/specfact-cli/issues/692), open, type Bug.
- Assignee: `djm81`.
- Labels: `bug`, `openspec`, `QA`, `security`.
- Project: SpecFact CLI #1, status In Progress.
- Parent/sub-issues: none; correct for this release-blocking bugfix.
- Blocked-by/blocking: none.
- Linked branch: `codex/692-computed-owner-red-proof-v2` (PR #698).
- Concurrent implementation: no other issue-linked branch or worktree for #692 was found.
- Hierarchy cache: refresh command completed successfully and reported unchanged content; live issue readback supplied current state.

## Security classification

- GitHub CodeQL alerts #25-#48 are duplicate dataflow instances of the same cache-persistence class, not 24 independent vulnerabilities.
- The current module fixture is immutable at commit `69f075819be5e1ceca1446b026b0417f19e584ca` and tree `5d0b8e66c6cd467e6b1ad9d582e24c66b907e205`; no current malicious content was proven.
- External exploitability is therefore unproven and privileged-only under current controls, but the persistent cache sink is real: an intentionally approved malicious fixture could write it and a later protected release job could restore it.
- Disabling setup-uv caching removes both restore and post-job save at the shared boundary. `save-cache: false` alone is insufficient.
- The staged Markdown fixer now disables pre-commit filename batching, preventing
  concurrent full-index fixer processes from contending on `index.lock`.
- Native archive validation accepts an active change as archived only when
  every regular source file moves byte-for-byte to the same relative path in
  one exact dated archive, no active path remains, and the archive has no extra
  files.
- Requirements evidence selection applies the same provenance proof to
  committed branch diffs and has no repository-wide review-evidence fallback.
  A fabricated, rewritten, partial, split-date, missing, extra, or non-regular
  archive remains active and fail-closed; it cannot suppress its own governed
  identity or redirect approval to another change.
- The PR Orchestrator has no manual-dispatch trigger; its advisory fixture lane is schedule-only, verifies both commit and tree, and exports the module path only after verification.
- The Requirements workflow no longer registers an npm cache hook after module-owned evidence execution.
- Retained proof is specified as a complete-history path policy: every touched
  path is stale under stock pytest, and any `mutable_after_red: true` claim
  fails closed until an explicit process-separated SUT runner exists. Restored
  paths and both rename/copy endpoints remain touched.
- All repository paths remain frozen under stock pytest. The provenance
  producer is one of those anchors, so final bytes must match the authenticated
  red source unless an exact final-producer authority authenticates the complete
  changed producer set and final blobs; no fifth anchor or self-mutable
  exception is added.
- The independent review reproduced a pre-install MCP-floor P1 after the first
  candidate: an internally consistent lock/export downgrade to MCP 1.23.3
  bypassed a floor map that covered only Semgrep. The final candidate adds an
  independent `mcp>=1.28.1` floor and downgrade regression; independent
  re-review confirmed the original reproducer now fails before synchronization
  and found no surviving concrete bypass. The compact complete-history policy
  supersedes the rejected construct-level interpreter; it does not claim to
  model arbitrary Python runtime behavior.
- Alerts remain open until GitHub observes the corrected default branch; none will be dismissed.
- Dependabot's six MCP alert instances are now validated and remediated through
  Semgrep 1.175.0's exact `mcp==1.29.0` binding. The exception register is empty;
  the pre-install policy rejects MCP below 1.28.1, and final frozen audits report
  no vulnerabilities or waivers.
- A detached mapped-test descendant can currently retain the runner identity and
  modify path-backed proof or verifier inputs after pytest returns. The validated
  boundary keeps pytest and descendants in a transient unprivileged service,
  exposes trusted inputs read-only or not at all, permits only private scratch
  and one raw-JUnit handoff, and requires cgroup-empty teardown before the
  trusted executor canonicalizes evidence. Per-file sealing and a fresh job were
  rejected as incomplete because they leave sibling trusted paths or the
  producer handoff writable before verification.

## Compatibility and documentation

- Frozen/hash-locked synchronization remains `uv sync --locked --all-extras`.
- The only expected compatibility cost is slower CI downloads.
- No public CLI/API, runtime dependency membership, user guide, README, docs index,
  or navigation behavior changes. Core package metadata advances from 0.55.3 to
  0.55.4 and the development/scanning toolchain advances only Semgrep/MCP.
- Existing mapped selectors need only read access to the checkout/module fixture
  plus private temporary files and local Bash/Git subprocesses. Network access
  is not required. The direct executor seam remains for local unit contracts;
  blocking CI explicitly requires the Linux isolation backend.
- The internal wiki was consulted read-only. Internal wiki PR #38 and its branch remain untouched; status synchronization is a post-merge follow-up.

## Rollback

Revert the issue-linked PR before release. If 0.55.4 has already shipped, publish a normal forward patch for a regression; do not rewrite the tag or published history. Yank only a demonstrably unsafe PyPI artifact under normal release policy.

## Validation record

- `openspec validate fix-release-promotion-security-gates --strict`: pass.
- Authoritative initial failing-before run: exit 1 with 2 expected failures and 2 legitimate passing controls; see `TDD_EVIDENCE.md`.
- Review/bypass failing-before runs reproduced all applicable PR findings, including the final annotated/computed/import-bound P1.
- Changed-scope passing-after run: 211 passed; focused workflow/provenance owners: 96 passed; workflow lint: pass.
- Final current-dev-rebased repository and pinned-fixture suite: 3191 passed,
  10 skipped;
  repository lint/type checks,
  Semgrep, Bandit, frozen dependency audits, license checks, reproducible
  delivery, strict module signatures, wheel build, and Twine artifact checks
  passed.
- The exact PR Orchestrator smart-test-full command also passed with 64%
  aggregate coverage against the configured 50% threshold.
- The compact path-policy mapping replaces the superseded construct-level test
  matrix. Its new digest requires product-owner approval before implementation;
  the prior mapping approval does not authorize these changed bytes.
- Compact path-policy failing-before evidence is `24 failed, 1 passed`: every
  new authority/freshness case fails under the old implementation, while the
  independent document-path option-termination regression passes.
- YAML lint no longer reports the #692 change. It still prints inherited R07/R08
  planning findings while exiting zero; those protected planning changes remain
  outside this patch and are recorded as a baseline limitation rather than
  silently treated as clean.
- The prior construct-by-construct provenance candidate failed the mandatory
  clean-code review. The compact replacement now has focused failing-before and
  passing-after evidence; the final hosted Code Review and Linux systemd smoke
  remain required on the pushed exact head.
- A targeted no-write solve changed only Semgrep 1.171.0 -> 1.175.0 and MCP
  1.23.3 -> 1.29.0 in the 184-package graph. The six-rule repository SAST scan
  then passed over 299 Python targets with zero findings.
- Python 3.11, 3.12, and 3.13 frozen environments all resolved the fixed
  Semgrep/MCP pair; the policy selector passed in each tested interpreter.
- Dry-run interface simulation found no public SpecFact CLI/API signature
  change. The affected graph is limited to the Requirements workflow, its two
  proof scripts, focused unit/workflow tests, and change-local evidence.
  Focused verification passed `116/116`; Ruff, formatting, BasedPyright,
  OpenSpec, actionlint, Bandit, Semgrep, reproducible-delivery, and lock checks
  passed. Hosted-runner compatibility still requires an actual `ubuntu-24.04`
  systemd smoke before this extension can be marked complete.
- Final mapping acceptance is the unedited repository MEMBER comment
  `https://github.com/nold-ai/specfact-cli/issues/692#issuecomment-5498165183`,
  bound to `sha256:3e4e717f4208eae1ee73614ccc3286f211f675849b2ea31a979b0269f5b4720d`.
