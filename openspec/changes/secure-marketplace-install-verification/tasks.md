# Tasks: secure-marketplace-install-verification

## 1. Readiness and specification

- [x] 1.1 Confirm work occurs on a non-protected worktree branch and inspect current HEAD for the reported path.
- [x] 1.2 Add the module-installation security delta.
- [x] 1.3 Validate the OpenSpec change strictly.

## 2. Failing evidence

- [x] 2.1 Add a regression derived from the security scenario proving official verification precedes dependency installation.
- [x] 2.2 Run the focused regression before production edits and record the expected failure in `TDD_EVIDENCE.md`.

## 3. Implementation

- [x] 3.1 Require signed integrity verification for official marketplace IDs before dependency processing.
- [x] 3.2 Preserve existing dependency resolution and atomic placement after verification succeeds.

## 4. Verification and finalization

- [x] 4.1 Run focused marketplace installer tests and record passing evidence.
- [x] 4.2 Run formatting, typing, lint, YAML, contract, smart-test, independent static-analysis, and SpecFact review gates required for the touched scope; record environment/baseline failures in `TDD_EVIDENCE.md`.
- [x] 4.3 Review `docs/`, `README.md`, `docs/index.md`, and navigation for affected guidance; update the two security-flow references affected by the policy change.
- [x] 4.4 Verify module signatures; no signed module assets changed, so no module version bump or re-signing is required.
- [ ] 4.5 After merge, update `wiki/sources/secure-marketplace-install-verification.md` and run `python3 scripts/wiki_rebuild_graph.py` from the unavailable sibling `specfact-cli-internal` checkout.
- [ ] 4.6 Create the pull request after committing the completed change.
