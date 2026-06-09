# Tasks: cli-removed-flat-alias-diagnostics

## 1. Readiness and source tracking

- [x] 1.1 Create the GitHub User Story issue under parent `#594` with labels `enhancement`, `openspec`, `change-proposal`, and `module-system`.
- [x] 1.2 Update `proposal.md` Source Tracking with the created issue URL and final sync status.
- [x] 1.3 Validate the OpenSpec change with `openspec validate cli-removed-flat-alias-diagnostics --strict`.

## 2. Failing evidence

- [ ] 2.1 Add a regression that invokes removed flat aliases such as `specfact validate --help` and `specfact plan --help`.
- [ ] 2.2 Add a regression fixture with both user-scope and project-scope copies of the same marketplace modules installed.
- [ ] 2.3 Confirm the current failure emits module install/shadowing diagnostics for removed aliases and record evidence.

## 3. Implementation

- [ ] 3.1 Remove removed flat aliases from root known-command diagnostic sets.
- [ ] 3.2 Remove removed flat aliases from root token to marketplace-module diagnostic mappings.
- [ ] 3.3 Keep canonical grouped command diagnostics for supported root groups such as `code` and `project`.
- [ ] 3.4 Audit tests and generated command references for stale expectations around removed flat aliases.

## 4. Verification

- [ ] 4.1 Verify `specfact code validate --help` and other canonical grouped commands still work with project-scope modules.
- [ ] 4.2 Verify removed aliases no longer emit installed/disabled/skipped/shadowed module diagnostics.
- [ ] 4.3 Run targeted CLI unit tests and the module command registration tests.
- [ ] 4.4 Record passing evidence in `TDD_EVIDENCE.md`.
