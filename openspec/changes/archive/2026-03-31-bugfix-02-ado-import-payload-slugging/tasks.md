## 0. GitHub sync

- [x] 0.1 Export or sync this change to a `[Change]` GitHub issue in `nold-ai/specfact-cli`
- [x] 0.2 Update `proposal.md` Source Tracking with the synced issue number, URL, repository, and status
- [x] 0.3 Ensure the synced change issue has labels `enhancement`, `openspec`, and `change-proposal`
- [x] 0.4 Add the synced change issue to the `SpecFact CLI` GitHub project
- [x] 0.5 Link the synced change issue under parent feature `#357` (epic lineage `#186`)
- [x] 0.6 Record the relation back to originating bug `#425`

## 1. Branch and baseline

- [x] 1.1 Create worktree: `scripts/worktree.sh create bugfix/bugfix-02-ado-import-payload-slugging`
- [x] 1.2 Bootstrap Hatch in the worktree: `hatch env create`
- [x] 1.3 Reproduce the current selective ADO import failure and record the failing command/output in `openspec/changes/bugfix-02-ado-import-payload-slugging/TDD_EVIDENCE.md`
- [x] 1.4 Audit adjacent import paths that use `fetch_backlog_item()`, `extract_change_proposal_data()`, or `import_backlog_item_as_proposal()` and record the scoped call sites before code changes

## 2. Write failing tests from spec scenarios

- [x] 2.1 Add unit tests in `tests/unit/adapters/test_ado.py` proving selective `fetch_backlog_item()` preserves the native ADO payload with populated `fields`
- [x] 2.2 Add unit tests in `tests/unit/adapters/test_ado.py` proving imported ADO change IDs derive from title slugs when no OpenSpec metadata exists
- [x] 2.3 Add collision tests proving duplicate title slugs append a deterministic source-ID suffix instead of degrading to numeric-only names
- [x] 2.4 Add bridge/import contract tests in the selective import path (`tests/unit/specfact_cli/sync/` or adjacent bridge tests) proving `fetch_backlog_item()` output remains valid input for proposal import
- [x] 2.5 Add or extend audit coverage for similar adapter commands so nearby `fetch_backlog_item()` implementations are checked for the same contract assumption
- [x] 2.6 Run targeted tests and capture the failing results in `TDD_EVIDENCE.md`

## 3. Implement payload preservation and title-first slugging

- [x] 3.1 Update `src/specfact_cli/adapters/ado.py` so selective ADO fetch returns the native work item payload while preserving compatibility summary keys
- [x] 3.2 Add shared title-first change-ID normalization in `src/specfact_cli/adapters/backlog_base.py` or a nearby shared helper used by proposal import
- [x] 3.3 Update ADO proposal extraction/import flow to use the shared normalizer and keep numeric source IDs in source tracking instead of primary naming
- [x] 3.4 Patch any adjacent adapter or bridge call sites found in the audit where the same summary-vs-native payload mistake or numeric-only fallback can occur
- [x] 3.5 Improve diagnostics or guard rails so missing native payload structure is reported clearly if an adapter violates the import contract in future

## 4. Verify and evidence

- [x] 4.1 Re-run the targeted adapter and bridge tests; record passing results in `TDD_EVIDENCE.md`
- [x] 4.2 Run `hatch run format`
- [x] 4.3 Run `hatch run type-check`
- [x] 4.4 Run `hatch run lint`
- [x] 4.5 Run `hatch run yaml-lint`
- [x] 4.6 Run `hatch run contract-test`
- [x] 4.7 Run `hatch run smart-test`

## 5. Documentation research and update

- [x] 5.1 Review affected docs in `docs/`, `README.md`, and command references for selective bridge import and ADO adapter behavior
- [x] 5.2 Update the relevant ADO sync/import documentation to describe the corrected selective import behavior and title-based change-ID fallback
- [x] 5.3 If new or moved docs are required, verify front matter and sidebar navigation entries in `docs/_layouts/default.html`

## 6. Module signing, version, and changelog

- [x] 6.1 Run `hatch run ./scripts/verify-modules-signature.py --require-signature`
- [x] 6.2 If any module manifests changed, bump module versions and re-sign before re-running verification
- [x] 6.3 Bump patch version across the required version files
- [x] 6.4 Add a `CHANGELOG.md` entry for the bugfix release describing the ADO import contract fix and title-based slugging correction

## 7. PR and cleanup

- [x] 7.1 Open a PR from `bugfix/bugfix-02-ado-import-payload-slugging` to `dev`
- [x] 7.2 Ensure CI passes and the PR links both the synced change issue and bug `#425`
- [x] 7.3 After merge, remove the worktree and delete the local branch
