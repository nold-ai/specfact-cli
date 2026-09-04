# Tasks: fix-release-promotion-security-gates

## 1. Branch and governance

- [x] 1.1 Refresh `origin/dev` and create isolated branch `bugfix/692-security-patch-clean-replay` at `4fd96d6d804da70cc7ceca83b8adce21f7da561c`.
- [x] 1.2 Verify issue #692 metadata and explicit same-session concurrency authorization.
- [x] 1.3 Merge the trusted organization workflow, activate the no-bypass ruleset for `dev` and the default branch, and verify its immutable source.

## 2. Specification and tests first

- [x] 2.1 Archive completed change #689 with `openspec archive` and inspect the generated permanent spec.
- [x] 2.2 Author compact spec deltas for the dependency, cache, archive, license, and proof boundaries.
- [x] 2.3 Add focused tests derived from every scenario and record failing-before evidence against the unmodified implementation.
- [x] 2.4 Generate the test-authored Requirements mapping and obtain one approval only after its digest is stable.
- [x] 2.5 Add one mapped review-amendment cycle for the remaining P1/P2 findings and retain its exact RED artifact.
- [x] 2.6 Add a mapped namespace-scope regression for the final release-PR provenance finding and record its failing-before result before implementation.
- [x] 2.7 Add mapped malformed-license-scope and module-release-publication regressions and record their failing-before results.

## 3. Minimal implementation

- [x] 3.1 Disable persistent caches, remove manual dispatch, and authenticate fixture commit/tree before export.
- [x] 3.2 Upgrade Semgrep/MCP frozen inputs and remove the obsolete vulnerability waiver.
- [x] 3.3 Bind Code Review lock/trust/license policy to the exact isolated environment and regenerated closure.
- [x] 3.4 Make archive selection and Git error handling fail closed; preserve legitimate active edits and native archives.
- [x] 3.5 Apply the narrow authority diagnostic, pytest bootstrap, credential-free proof, fresh-runner exact-head review handoff, and `rg --` fixes.
- [x] 3.6 Disable Python site startup for proof validators, bind prefetched inputs across test execution, and make authority/pre-commit Git path parsing NUL-safe.
- [x] 3.7 Re-execute the authenticated plan on the fresh consumer and reconcile only its consumer-generated JUnit.
- [x] 3.8 Bind the late RED artifact to live GitHub metadata and the expiring exact-tree member authority without importing the superseded amendment subsystem.
- [x] 3.9 Restore candidate `src/` imports after trusted pytest initialization and document the approved non-hostile same-process proof boundary.
- [x] 3.10 Pin isolated pytest to the authenticated repository root so JUnit retains canonical repository-relative selector identities.
- [x] 3.11 Upgrade the GitPython runtime floor and frozen graph to 3.1.61 after the final audit reported four newly published 3.1.58 advisories.
- [x] 3.12 Make the local version gate reuse the complete branch-level release bundle only for unchanged-version follow-ups, while rejecting later downgrades, deleted evidence, and invalid explicit CI bases.
- [x] 3.13 Restrict literal `pytest_plugins` discovery to module bindings while retaining explicit-global assignments.
- [x] 3.14 Reject non-string license scopes through the stable diagnostic path.
- [ ] 3.15 Publish and checksum-verify tag-qualified bundled module release assets before updating snapshot metadata.

## 4. Passing evidence and review

- [x] 4.1 Run focused legitimate/bypass controls and record passing-after evidence.
- [x] 4.2 Run format, lint, type, YAML/workflow, OpenSpec, contract, full test, module-signature, dependency, license, audit, SAST, Code Review, package, and release gates.
- [x] 4.3 Run final pip-audit against both frozen sets and prove all three MCP and four GitPython CVEs no longer reproduce.
- [x] 4.4 Obtain independent security-diff and code review on the exact final tree; resolve every P1/P2 or documented false positive.
- [x] 4.5 Review docs, README, landing page, and navigation; update only dependency trust and release notes because no public behavior changes.
- [x] 4.6 Re-run independent security bypass review and the full applicable gates after the consumer-proof correction.
- [x] 4.7 Re-run independent review and all applicable gates after the final review-amendment correction.
- [x] 4.8 Re-run independent review and all applicable gates after the canonical-selector compatibility correction.
- [x] 4.9 Recover immutable RED proof for the final clean-code refactors, then re-run independent review and all applicable gates without changing mapped selector identities.
- [x] 4.10 Resolve the remaining release-PR evidence and test-quality findings, then re-run independent review and all applicable gates.
- [x] 4.11 Normalize parameterized Requirements selectors, recover the final definition-time plugin RED proof, and restore the PR #704 late-RED path.
- [x] 4.12 Bind parameter values to stable exact selectors, recover their immutable RED proof, and preserve independent per-case reconciliation.

## 5. Release and delivery

- [x] 5.1 Bump all four version sources from 0.55.3 to 0.55.4 and add the 2026-09-02 changelog entry.
- [ ] 5.2 Push the signed linear commits, create the issue-linked PR to `dev`, and verify the trusted workflow fails without and passes only with the exact authority comment.
- [ ] 5.3 Merge only under repository policy, then promote and verify the `v0.55.4` GitHub/PyPI release.
- [ ] 5.4 Refresh PR #685 security status, close superseded PR #698 with evidence, close completed issues, and report the exact C14 baseline commit/tag.
