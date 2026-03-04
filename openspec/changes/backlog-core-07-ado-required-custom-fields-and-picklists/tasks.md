## 1. Branch and scope setup

- [ ] 1.1 Create worktree branch `bugfix/backlog-core-07-ado-required-custom-fields-and-picklists` from `origin/dev` using `scripts/worktree.sh create` and run all implementation commands inside that worktree.
- [ ] 1.2 Confirm GitHub issue #337 remains the source-tracked issue (no duplicate issue creation); update proposal Source Tracking status after validation and again after PR creation.
- [ ] 1.3 Run pre-flight in the worktree (`hatch env create`, `hatch run smart-test-status`, `hatch run contract-test-status`) with writable cache overrides if needed.

## 2. Specs and design (SDD first)

- [ ] 2.1 Finalize spec deltas for `backlog-map-fields` and `backlog-add`, plus new `ado-field-value-selection` spec, ensuring each requirement has at least one Given/When/Then scenario.
- [ ] 2.2 Run `openspec validate backlog-core-07-ado-required-custom-fields-and-picklists --strict` and fix any artifact format issues.

## 3. Tests first (TDD red phase)

- [ ] 3.1 Add/adjust unit tests for ADO map-fields metadata persistence (required fields and allowed-values by work item type).
- [ ] 3.2 Add/adjust unit tests for interactive add constrained-value picker behavior and fallback behavior.
- [ ] 3.3 Add/adjust unit/integration tests for non-interactive invalid constrained values and missing required custom fields.
- [ ] 3.4 Run targeted test commands and confirm failing behavior before implementation changes.
- [ ] 3.5 Record failing test evidence (commands, timestamps, short failure summaries) in `openspec/changes/backlog-core-07-ado-required-custom-fields-and-picklists/TDD_EVIDENCE.md`.

## 4. Implementation (TDD green phase)

- [ ] 4.1 Update ADO field discovery/mapping flow to persist required flags and eligible values for mapped custom fields per work item type.
- [ ] 4.2 Update add command interactive flow to render picker selection for constrained ADO field values.
- [ ] 4.3 Update non-interactive validation to reject invalid constrained values and print allowed-values hints.
- [ ] 4.4 Enforce required mapped custom fields before adapter create calls and preserve backward compatibility when metadata is absent.
- [ ] 4.5 Ensure public APIs touched by this change keep/extend `@icontract` and `@beartype` coverage.

## 5. Verification and quality gates

- [ ] 5.1 Re-run targeted tests and full related suites to confirm passing behavior for all scenarios.
- [ ] 5.2 Record passing test evidence (commands, timestamps, short summaries) in `openspec/changes/backlog-core-07-ado-required-custom-fields-and-picklists/TDD_EVIDENCE.md`.
- [ ] 5.3 Run quality gates in order: `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run yaml-lint`, `hatch run contract-test`, `hatch run smart-test`.
- [ ] 5.4 Run module signature verification: `hatch run ./scripts/verify-modules-signature.py --require-signature`; if changed module manifests fail, bump module version(s), re-sign with `hatch run python scripts/sign-modules.py --key-file <private-key.pem> <module-package.yaml ...>`, then re-verify.

## 6. Documentation, versioning, and release notes

- [ ] 6.1 Research and update affected docs (`docs/`, `README.md`, and `docs/index.md` if needed) for ADO custom required fields, constrained value picker UX, and non-interactive validation hints.
- [ ] 6.2 Apply patch version bump for this bugfix and sync versions across `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`.
- [ ] 6.3 Add `CHANGELOG.md` entry for the released version with `Fixed` notes for ADO required custom-field and constrained-value validation behavior.

## 7. Finalization

- [ ] 7.1 Re-run `openspec validate backlog-core-07-ado-required-custom-fields-and-picklists --strict` and create/update `CHANGE_VALIDATION.md` with dry-run dependency analysis results.
- [ ] 7.2 Open PR to `dev` using `.github/pull_request_template.md`, include issue #337 linkage, and update proposal Source Tracking status to reflect PR URL/state.
