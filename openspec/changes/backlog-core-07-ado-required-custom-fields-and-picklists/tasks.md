## 1. Branch and scope setup

- [x] 1.1 Create worktree branch `bugfix/backlog-core-07-ado-required-custom-fields-and-picklists` from `origin/dev` using `scripts/worktree.sh create` and run all implementation commands inside that worktree.
- [x] 1.2 Create companion branch/worktree in `specfact-cli-modules` for the same change scope (keep branch slug aligned for traceability).
- [x] 1.3 Confirm GitHub issue #337 remains the source-tracked issue (no duplicate issue creation); update proposal Source Tracking status after validation and again after PR creation.
- [ ] 1.4 Run pre-flight in each active worktree (`hatch env create`, `hatch run smart-test-status`, `hatch run contract-test-status`) with writable cache overrides if needed.

## 2. Specs and design (SDD first)

- [x] 2.1 Finalize spec deltas for `backlog-map-fields` and `backlog-add`, plus new `ado-field-value-selection` spec, ensuring each requirement has at least one Given/When/Then scenario.
- [x] 2.2 Run `openspec validate backlog-core-07-ado-required-custom-fields-and-picklists --strict` and fix any artifact format issues.

## 3. Tests first (TDD red phase)

- [x] 3.1 In `specfact-cli-modules`, add/adjust unit tests for ADO `map-fields` metadata persistence (required fields and allowed-values by work item type), including non-interactive auto-mapping success/failure paths.
- [x] 3.2 In `specfact-cli`, add/adjust unit tests for `backlog add` constrained-value picker behavior and fallback behavior.
- [x] 3.3 In `specfact-cli`, add/adjust unit/integration tests for non-interactive invalid constrained values, missing required custom fields, and repeatable `--custom-field key=value` parsing.
- [x] 3.4 Run targeted test commands and confirm failing behavior before implementation changes.
- [x] 3.5 Record failing test evidence (commands, timestamps, short failure summaries) in `openspec/changes/backlog-core-07-ado-required-custom-fields-and-picklists/TDD_EVIDENCE.md`.

## 4. Implementation (TDD green phase)

- [x] 4.1 In `specfact-cli-modules`, update ADO field discovery/mapping flow to persist required flags and eligible values for mapped custom fields per work item type.
- [x] 4.1.1 Add non-interactive auto-mapping mode for `map-fields` that persists deterministic mappings and fails fast with interactive fallback guidance when required fields cannot be resolved.
- [x] 4.2 In `specfact-cli`, update add command to support repeatable `--custom-field key=value` and interactive picker selection for constrained ADO field values.
- [x] 4.3 In `specfact-cli`, update non-interactive validation to reject invalid constrained values and print allowed-values hints.
- [x] 4.4 In `specfact-cli`, enforce required mapped custom fields before adapter create calls and preserve backward compatibility when metadata is absent.
- [ ] 4.5 Ensure public APIs touched by this change keep/extend `@icontract` and `@beartype` coverage in both repos where applicable.

## 5. Verification and quality gates

- [x] 5.1 Re-run targeted tests and full related suites in both repos to confirm passing behavior for all scenarios.
- [x] 5.2 Record passing test evidence (commands, timestamps, short summaries) in `openspec/changes/backlog-core-07-ado-required-custom-fields-and-picklists/TDD_EVIDENCE.md`.
- [ ] 5.3 Run quality gates in each touched repo in order: `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run yaml-lint`, `hatch run contract-test`, `hatch run smart-test`.
- [x] 5.4 Run module signature verification where module manifests changed: `hatch run ./scripts/verify-modules-signature.py --require-signature`; if verification fails, bump module version(s), re-sign, then re-verify.

## 6. Documentation, versioning, and release notes

- [ ] 6.1 Update affected docs in both repos (`specfact-cli-modules/docs/` for `map-fields`, `specfact-cli/docs/` for `backlog add`) plus README/landing pages where behavior is described.
- [x] 6.2 Apply version bump(s) according to touched artifacts (module package version bump in `specfact-cli-modules`; core patch bump in `specfact-cli` if core runtime changes are shipped).
- [ ] 6.3 Add changelog entry/entries for released version(s) with `Fixed` notes for ADO required custom-field and constrained-value validation behavior.

## 7. Finalization

- [x] 7.1 Re-run `openspec validate backlog-core-07-ado-required-custom-fields-and-picklists --strict` and create/update `CHANGE_VALIDATION.md` with dry-run dependency analysis results.
- [ ] 7.2 Open coordinated PRs (modules + core as needed), link issue #337 in each, and update proposal Source Tracking status to reflect PR URL/state.

**Task 7.2 note (2026-03-05)**: modules-side coordinated PRs are merged (`#9`, `#11` in `specfact-cli-modules`). Core-side coordinated PR/state linkage remains pending before archive.
