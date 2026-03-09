# Tasks: cli-val-07-command-package-runtime-validation

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for any behavior-changing task. Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last. Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
- [ ] 1.2 Create and activate a worktree-local environment, then run pre-flight checks (`hatch env create`, `hatch run smart-test-status`, `hatch run contract-test-status`).

## 2. Freeze the command inventory and validation matrix

- [x] 2.1 Inventory core command manifests from `src/specfact_cli/modules/` and official bundle manifests from `../specfact-cli-modules/packages/`.
- [x] 2.2 Enumerate nested command paths from Typer apps for every root group so no leaf command is omitted.
- [x] 2.3 Write the logical execution phases for the audit: root/core, module bootstrap/install, `project`, `spec`, `code`, `backlog`, `govern`.
- [x] 2.4 Assign a validation mode to every command path: fixture-backed, dry-run, or help-only fallback.

## 3. Test-first: add failing audit coverage

- [x] 3.1 Add or extend tests that generate the command inventory and fail when a shipped command path is missing from the matrix.
- [x] 3.2 Add or extend black-box/acceptance coverage that executes the matrix phases against bundled or local marketplace artifacts.
- [x] 3.3 Add a focused regression test for the reported startup case: running `specfact` from `<user-home>` with canonical `~/.specfact/modules` populated must not emit duplicate-module or protocol-compliance noise.
- [x] 3.4 Capture the pre-implementation failing test run and failure summary in `TDD_EVIDENCE.md`.
- [x] 3.5 Add a failing regression test for the marketplace backlog bundle accepting core backlog adapters during `backlog refine ado`.
- [x] 3.6 Add a failing regression test for `backlog map-fields` showing explicit progress after work-item-type selection and persisting required-field/picklist metadata for the selected type.
- [x] 3.7 Add failing regression coverage for `backlog add` consuming saved required-field and allowed-values metadata, including `--custom-field` validation and forwarding.
- [x] 3.8 Capture the new pre-implementation failing runs and summaries in `TDD_EVIDENCE.md`.
- [x] 3.9 Add a failing regression test proving `backlog map-fields` ignores built-in required identifiers such as `System.IterationId` and `System.AreaId`, while reporting incremental metadata-fetch progress.
- [x] 3.10 Add a failing regression test proving bundled module upgrades do not log routine already-satisfied dependencies as warnings during successful upgrade flows.
- [x] 3.11 Add a failing regression test proving bridge logger diagnostics do not leak raw log-formatted lines to the console when `--debug` is off.
- [x] 3.12 Add a failing regression test proving `specfact module upgrade` reports one upgraded module per line with `old -> new` versions.

## 4. Implement runtime-audit and output-cleanup fixes

- [x] 4.1 Implement inventory helpers or fixtures needed to execute every command family and leaf command deterministically.
- [x] 4.2 Fix canonical user-root deduplication so expected default-path discovery does not produce duplicate/shadow warnings.
- [x] 4.3 Move internal module-discovery and protocol-compliance chatter behind debug-only logging while preserving actionable warnings.
- [x] 4.4 Re-run the new validation tests and record the passing post-implementation evidence in `TDD_EVIDENCE.md`.
- [x] 4.5 Remove normal-output duplicate-command warnings for the expected `backlog-core` plus `nold-ai/specfact-backlog` overlap while preserving actionable collision diagnostics.
- [x] 4.6 Fix the backlog marketplace bundle to use the core backlog adapter contract so `backlog refine ado` works with the installed ADO adapter.
- [x] 4.7 Make `backlog map-fields` surface progress while fetching required-field and picklist metadata after work-item-type selection.
- [x] 4.8 Extend `backlog add` to consume saved required-field and allowed-values metadata, expose repeatable `--custom-field`, and fail with actionable guidance on missing or invalid required custom fields.
- [x] 4.9 Re-run the new backlog validation tests and record the passing post-implementation evidence in `TDD_EVIDENCE.md`.
- [x] 4.10 Exempt non-mappable built-in ADO hierarchy identifiers from required-field mapping failures, add incremental metadata-fetch status output, and demote already-satisfied bundled dependency upgrade messages out of warning severity.
- [x] 4.11 Re-run the new regression tests and record the failing/passing evidence in `TDD_EVIDENCE.md`.
- [x] 4.12 Keep shared bridge logger diagnostics off the normal console unless `--debug` is enabled, while preserving explicit user-facing warnings.
- [x] 4.13 Re-run the logger-output regression tests and record the failing/passing evidence in `TDD_EVIDENCE.md`.
- [x] 4.14 Make `specfact module upgrade` report per-module `old -> new` versions on separate lines for multi-module upgrades.
- [x] 4.15 Re-run the module-upgrade output regression test and record the failing/passing evidence in `TDD_EVIDENCE.md`.

## 5. Cover each package in logical order

- [x] 5.1 Validate root/core commands: `specfact`, `init`, `init ide`, `module init/install/uninstall/enable/disable/search/list/show/upgrade`, and `upgrade`.
- [x] 5.2 Validate the exported `project` bundle surface: `project`, `project version`, `project sync`, `project import`, and project lifecycle leaf commands mounted on the public group.
- [x] 5.3 Validate the exported `spec` bundle surface: `spec`, `spec validate`, `spec backward-compat`, `spec generate-tests`, and `spec mock`.
- [x] 5.4 Validate `code` bundle commands and subgroups: `code analyze`, `code drift`, `code validate`, `code validate sidecar`, and `code repro`.
- [x] 5.5 Validate `backlog` bundle commands and subgroups: `backlog`, `backlog ceremony`, `backlog auth`, `backlog refine`, `backlog daily`, `backlog init-config`, and `backlog map-fields`.
- [x] 5.6 Validate `govern` bundle commands and subgroups: `govern enforce`, `govern enforce stage`, `govern enforce sdd`, and `govern patch apply`.
- [x] 5.7 Re-run the installed `specfact` and hatch-env backlog validations for `backlog refine ado`, `backlog map-fields`, and `backlog add` against the fixed bundle/core combination and capture findings.

## 6. Documentation and release-validation guidance

- [x] 6.1 Update docs for contributor/release workflows with the command-package audit procedure and command coverage expectations.
- [x] 6.2 Update docs/reference guidance for clean normal output versus `--debug` diagnostics if command-output behavior changes.

## 7. Quality gates

- [x] 7.1 `hatch run format`
- [x] 7.2 `hatch run type-check`
- [x] 7.3 `hatch run lint`
- [x] 7.4 `hatch run yaml-lint`
- [x] 7.5 `hatch run contract-test`
- [x] 7.6 `hatch run smart-test`
- [x] 7.7 `openspec validate cli-val-07-command-package-runtime-validation --strict`

## 8. Delivery

- [x] 8.1 Update `openspec/CHANGE_ORDER.md` and `CHANGE_VALIDATION.md` with final implementation status and validation evidence.
- [ ] 8.2 Stage and commit using a conventional commit message for this validation/fix scope.
- [ ] 8.3 Push the branch and open a PR against `dev`.

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout and remove the dedicated worktree for `feature/cli-val-07-command-package-runtime-validation`.
- [ ] Delete the local branch after merge and prune stale worktree metadata.
