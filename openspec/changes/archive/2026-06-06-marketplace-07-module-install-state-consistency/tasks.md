## 1. Regression Tests and Evidence

- [x] 1.1 Add a regression test where a module artifact exists but `modules.json` marks the manifest module id disabled, then `specfact module install <module-id>` reports or repairs disabled state instead of only "already installed".
- [x] 1.2 Add a regression test where a known command group is unavailable because its module is disabled, and the CLI prints installed-but-disabled guidance.
- [x] 1.3 Add a regression test for installed-but-skipped diagnostics covering at least one local skip reason: missing dependency, incompatible core version, schema mismatch, or integrity failure.
- [x] 1.4 Add a regression test for bare/legacy/marketplace module identity normalization against a manifest id such as `nold-ai/specfact-codebase`.
- [x] 1.5 Add a regression test where project and user scope contain the same module and diagnostics identify the active project origin plus the shadowed user copy.
- [x] 1.6 Add a regression test where `specfact init --repo <repo> --profile <profile>` discovers project modules relative to `<repo>` while preserving unrelated lifecycle state.
- [x] 1.7 Run the focused tests before implementation and record the failing-before output in `TDD_EVIDENCE.md`.

## 2. Availability Classification

- [x] 2.1 Add a metadata-only module availability classifier that accepts a requested module id or command group and returns absent, available, disabled, shadowed, skipped, or ambiguous status.
- [x] 2.2 Reuse existing discovery, state merge, dependency, compatibility, schema, and integrity helpers where practical so classification matches runtime registration decisions.
- [x] 2.3 Add canonical module identity resolution for bare names, legacy namespace names, marketplace ids, and manifest ids.
- [x] 2.4 Cover the classifier with unit tests that do not import module command app code eagerly.

## 3. Install and Missing-Command UX

- [x] 3.1 Route `specfact module install` already-present checks through the availability classifier before returning success.
- [x] 3.2 Make install report or repair installed-but-disabled modules according to the final implementation decision documented in tests.
- [x] 3.3 Make install report installed-but-unavailable reasons for compatibility, dependency, schema, and integrity skips when those reasons are locally derivable.
- [x] 3.4 Update known missing-command help to show installed-but-disabled, installed-but-skipped, or truly-not-installed messages.
- [x] 3.5 Ensure normal non-debug command output remains concise and free of duplicate shadow warnings.

## 4. Init/Profile State Refresh

- [x] 4.1 Make `specfact init --repo <repo>` pass the selected repository path into project-scope module discovery for state refresh and prompt audits.
- [x] 4.2 Change init/profile state writes to merge discovered rows with existing lifecycle state rather than replacing unrelated rows blindly.
- [x] 4.3 Preserve explicit disabled states for rediscovered modules unless the user directly requests enablement.
- [x] 4.4 Ensure profile-selected installed-but-disabled modules cannot remain in a contradictory not-installed/already-installed state without actionable output.

## 5. Documentation and Source Tracking

- [x] 5.1 Review and update affected user docs: `docs/module-system/installing-modules.md`, `docs/module-system/module-marketplace.md`, `docs/reference/README.md`, and `docs/core-cli/init.md` if command output or recovery guidance changes.
- [x] 5.2 Keep GitHub issue #533 linked to the synced user story and OpenSpec change in source tracking comments or issue body.
- [x] 5.3 Update `/home/dom/git/nold-ai/specfact-cli-internal/wiki/sources/marketplace-07-module-install-state-consistency.md` and run `python3 scripts/wiki_rebuild_graph.py` from the internal repo root when scope, dependency, or status changes.

## 6. Verification

- [x] 6.1 Run focused unit tests for module registry, module discovery, init module state, and missing-command diagnostics.
- [x] 6.2 Run `openspec validate marketplace-07-module-install-state-consistency --strict`.
- [x] 6.3 Run the repository quality gates required by the touched scope, including code review JSON generation.
- [x] 6.4 Record passing-after verification output in `TDD_EVIDENCE.md`.
