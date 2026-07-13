# Tasks: OpenSpec and Spec Kit Import-First Requirement Evidence

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests MUST precede production code for any
behavior-changing task: spec deltas first, failing tests second, production
code third. Record evidence in `TDD_EVIDENCE.md`.

---

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/openspec-01-intent-trace` from `dev`: `scripts/worktree.sh create feature/openspec-01-intent-trace`.
- [ ] 1.2 Verify `requirements-01-data-model` and `requirements-02-module-commands` are archived (shipped) in `openspec/changes/archive/`.
- [ ] 1.3 Re-run change validation for the rescoped proposal and refresh `CHANGE_VALIDATION.md` (previous validation covers the retired Intent Trace scope).

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/` deltas (`openspec-speckit-evidence-adapter` NEW, `requirements-module` MODIFIED) and cross-check scenario completeness.
- [ ] 2.2 Add unit tests for OpenSpec import normalization (change folder fixture → `RequirementInput` records with `openspec_change` sources, scenario → `BusinessRule` mapping, `sha256:` revision).
- [ ] 2.3 Add unit tests for Spec Kit import normalization (feature folder fixture → `RequirementInput` records with `speckit_spec` sources).
- [ ] 2.4 Add unit tests for gate categories: `scenario-unverified`, `stale-import`, `source-missing`, `ambiguous-mapping`, including profile severity mapping and idempotent re-import.
- [ ] 2.5 Run targeted tests, capture failing-first output in `TDD_EVIDENCE.md`.

## 3. Implementation (core)

- [ ] 3.1 Add import normalizers in `src/specfact_cli/requirements/` that consume `adapters/openspec_parser.py` and `importers/speckit_scanner.py`/`speckit_converter.py` output and emit `RequirementInput` records with deterministic IDs and content-hash revisions.
- [ ] 3.2 Extend `requirements/context.py` validation with the four gate categories and profile-driven severity; keep existing findings intact.
- [ ] 3.3 Guarantee read-only behavior toward upstream artifact directories (contract tests: no writes under source roots).
- [ ] 3.4 Contract decorators (`@beartype`, `@require`, `@ensure`) on all new public APIs.

## 4. Implementation (modules repo, paired)

- [ ] 4.1 Track runtime wiring in nold-ai/specfact-cli-modules#168: `requirements import --from-openspec [PATH] --from-speckit [PATH]` with auto-detection, plus validate/list/coverage surfacing of new gate findings.
- [ ] 4.2 Keep module runtime thin: parsing, hashing, and gate logic stay core-owned.

## 5. Validation and documentation

- [ ] 5.1 Re-run tests and quality gates (`hatch run format`, `type-check`, `lint`, `contract-test`, `smart-test`) until green; record passing evidence in `TDD_EVIDENCE.md`.
- [ ] 5.2 Update docs: requirements guide repositioned import-first (OpenSpec/Spec Kit as accountable authoring sources; `--from-file` as generic fallback); document gate categories and CI exit-code usage.
- [ ] 5.3 Run `openspec validate openspec-01-intent-trace --strict` and resolve all issues.

## 6. Delivery

- [ ] 6.1 Update `openspec/CHANGE_ORDER.md` if sequencing changed during implementation.
- [ ] 6.2 Mirror material scope updates to `../specfact-cli-internal/wiki/sources/openspec-01-intent-trace.md` and rebuild the wiki graph.
- [ ] 6.3 Open PR from `feature/openspec-01-intent-trace` to `dev` with spec/test/code/docs evidence.
- [ ] 6.4 Sync GitHub issue #350 (and modules #168) title/body with the rescoped proposal.
