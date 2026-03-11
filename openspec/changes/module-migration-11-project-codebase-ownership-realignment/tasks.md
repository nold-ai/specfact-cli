## 1. Inventory And Decision Baseline

- [x] 1.1 Freeze the current `project` versus `codebase` ownership matrix for commands, prompts, docs, tests, and helper subsystems.
- [x] 1.2 Record the contradictory archived references that currently place brownfield analysis internals in both `specfact-project` and `specfact-codebase`.
- [x] 1.3 Identify active pending changes that must align with this ownership decision (`module-migration-10` minimum, plus any docs/prompt follow-ups that reference import command paths).

## 2. Spec And Design First

- [x] 2.1 Add spec deltas for canonical `project` and `codebase` ownership boundaries.
- [x] 2.2 Define the target public command path for code-first brownfield import and any temporary compatibility alias policy.
- [x] 2.3 Update `openspec/CHANGE_ORDER.md` dependency notes so pending changes do not finalize conflicting import ownership assumptions.

## 3. Test-First Realignment

- [x] 3.1 Add failing regression coverage proving code-first import is owned by the `code` surface in the target model.
- [x] 3.2 Add failing regression coverage proving `project` is limited to project-bundle/workspace lifecycle behavior rather than code-analysis ownership.
- [x] 3.3 Add failing validation coverage for docs/runtime ownership drift so future changes cannot silently reintroduce contradictory public paths.
- [x] 3.4 Record the failing evidence in `TDD_EVIDENCE.md`.

## 4. Runtime And Bundle Ownership Refactor

- [x] 4.1 Move brownfield import runtime ownership from `specfact-project` to `specfact-codebase`, making `specfact code import` canonical (with a bounded compatibility alias only where needed during transition).
- [x] 4.2 Move or reclassify brownfield analysis internals (`analyzers`, `comparators`, relevant `parsers`, and related helpers/agents) to the canonical codebase owner.
- [x] 4.3 Keep only true bundle/project artifact lifecycle behavior in `specfact-project`.
- [x] 4.4 Update package dependencies, command registration, and validation inventories to match the new ownership boundary.

## 5. Alignment And Validation

- [x] 5.1 Update active pending change artifacts that currently assume the pre-realignment import ownership model.
- [x] 5.2 Update release-facing docs, prompts, and suggestion text to the canonical command path and ownership wording.
- [x] 5.3 Re-run targeted runtime validation and ownership tests; record passing evidence in `TDD_EVIDENCE.md`.
- [x] 5.4 Run `openspec validate module-migration-11-project-codebase-ownership-realignment --strict`.
