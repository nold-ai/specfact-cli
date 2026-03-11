## 1. Inventory And Decision Baseline

- [ ] 1.1 Freeze the current `project` versus `codebase` ownership matrix for commands, prompts, docs, tests, and helper subsystems.
- [ ] 1.2 Record the contradictory archived references that currently place brownfield analysis internals in both `specfact-project` and `specfact-codebase`.
- [ ] 1.3 Identify active pending changes that must align with this ownership decision (`module-migration-10` minimum, plus any docs/prompt follow-ups that reference import command paths).

## 2. Spec And Design First

- [ ] 2.1 Add spec deltas for canonical `project` and `codebase` ownership boundaries.
- [ ] 2.2 Define the target public command path for code-first brownfield import and any temporary compatibility alias policy.
- [ ] 2.3 Update `openspec/CHANGE_ORDER.md` dependency notes so pending changes do not finalize conflicting import ownership assumptions.

## 3. Test-First Realignment

- [ ] 3.1 Add failing regression coverage proving code-first import is owned by the `code` surface in the target model.
- [ ] 3.2 Add failing regression coverage proving `project` is limited to project-bundle/workspace lifecycle behavior rather than code-analysis ownership.
- [ ] 3.3 Add failing validation coverage for docs/runtime ownership drift so future changes cannot silently reintroduce contradictory public paths.
- [ ] 3.4 Record the failing evidence in `TDD_EVIDENCE.md`.

## 4. Runtime And Bundle Ownership Refactor

- [ ] 4.1 Move `import from-code` runtime ownership from `specfact-project` to `specfact-codebase` (or add a bounded compatibility alias while the canonical owner changes).
- [ ] 4.2 Move or reclassify brownfield analysis internals (`analyzers`, `comparators`, relevant `parsers`, and related helpers/agents) to the canonical codebase owner.
- [ ] 4.3 Keep only true bundle/project artifact lifecycle behavior in `specfact-project`.
- [ ] 4.4 Update package dependencies, command registration, and validation inventories to match the new ownership boundary.

## 5. Alignment And Validation

- [ ] 5.1 Update active pending change artifacts that currently assume the pre-realignment import ownership model.
- [ ] 5.2 Update release-facing docs, prompts, and suggestion text to the canonical command path and ownership wording.
- [ ] 5.3 Re-run targeted runtime validation and ownership tests; record passing evidence in `TDD_EVIDENCE.md`.
- [ ] 5.4 Run `openspec validate module-migration-11-project-codebase-ownership-realignment --strict`.
