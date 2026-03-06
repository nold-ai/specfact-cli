## 1. Ownership Inventory And Spec Setup

- [ ] 1.1 Freeze the backlog ownership matrix: commands, prompts, templates, helpers, tests, and docs currently split between core and `specfact-backlog`.
- [ ] 1.2 Add spec deltas covering module-only backlog command ownership and backlog-owned prompt/template resources.
- [ ] 1.3 Capture the expected keep-in-core list for shared contracts/models/provider infrastructure.

## 2. Test-First Cleanup

- [ ] 2.1 Add failing tests proving core no longer directly owns backlog command surfaces that belong to `nold-ai/specfact-backlog`.
- [ ] 2.2 Add failing tests proving backlog prompts/templates are no longer exported from core resource paths after migration.
- [ ] 2.3 Add failing regression coverage proving duplicate backlog overlap handling is no longer required in normal registration.
- [ ] 2.4 Record the failing evidence in `TDD_EVIDENCE.md`.

## 3. Production Refactor

- [ ] 3.1 Remove or retire `modules/backlog-core` command ownership from `specfact-cli`.
- [ ] 3.2 Remove or retire core backlog command/group shims that still expose backlog feature commands directly.
- [ ] 3.3 Move backlog-specific prompts, templates, and backlog-only helpers into `specfact-backlog`.
- [ ] 3.4 Retain only approved shared contracts/models/provider infrastructure in core.
- [ ] 3.5 Remove duplicate-overlap toleration that exists only for split backlog ownership.

## 4. Validation

- [ ] 4.1 Re-run the new ownership tests and record passing evidence in `TDD_EVIDENCE.md`.
- [ ] 4.2 Re-run the active CLI runtime validation for backlog command registration.
- [ ] 4.3 Run `openspec validate backlog-module-ownership-cleanup --strict`.
