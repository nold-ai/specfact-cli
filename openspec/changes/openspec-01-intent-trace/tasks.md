# Tasks: OpenSpec and Spec Kit Import-First Requirement Evidence

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests MUST precede production code for any
behavior-changing task: spec deltas first, failing tests second, production
code third. Record evidence in `TDD_EVIDENCE.md`.

---

## 1. Branch and dependency guardrails

- [x] 1.1 Create dedicated worktree branch `feature/openspec-01-intent-trace` from `dev`: `scripts/worktree.sh create feature/openspec-01-intent-trace`.
- [x] 1.2 Verify `requirements-01-data-model` and `requirements-02-module-commands` are archived (shipped) in `openspec/changes/archive/`.
- [x] 1.3 Re-run change validation for the rescoped proposal and refresh `CHANGE_VALIDATION.md` (previous validation covers the retired Intent Trace scope).

## 2. Spec-first and test-first preparation

- [x] 2.1 Finalize `specs/` deltas (`openspec-speckit-evidence-adapter` NEW, `requirements-module` MODIFIED) and cross-check scenario completeness.
- [x] 2.2 Add unit tests for OpenSpec import normalization (change folder fixture → `RequirementInput` records with `openspec_change` sources, scenario → `BusinessRule` mapping, `sha256:` revision).
- [x] 2.3 Add unit tests for Spec Kit import normalization (feature folder fixture → `RequirementInput` records with `speckit_spec` sources).
- [x] 2.4 Add unit tests for gate categories: `scenario-unverified`, `stale-import`, `source-missing`, `ambiguous-mapping`, including profile severity mapping and idempotent re-import.
- [x] 2.4b Add unit tests for layered-config profile resolution: omitted profile resolves via `resolve_profile_config` (explicit flag wins); `id`, `title`, `acceptance`, and `trace_links` map to evidence fields; unsupported fields emit an advisory without making imported records incomplete.
- [x] 2.5 Run targeted tests, capture failing-first output in `TDD_EVIDENCE.md`.
- [x] 2.6 Add failing-first compatibility tests for default OpenSpec/Spec Kit
  profiles, custom OpenSpec schemas, Spec Kit template customization roots,
  and unknown Markdown markers; prove unsupported sources emit no partial
  records.

## 3. Implementation (core)

- [x] 3.1 Add import normalizers in `src/specfact_cli/requirements/` that consume `adapters/openspec_parser.py` and `importers/speckit_scanner.py`/`speckit_converter.py` output and emit `RequirementInput` records with deterministic IDs and content-hash revisions.
- [x] 3.2 Extend `requirements/context.py` validation with the four gate categories and profile-driven severity; keep existing findings intact.
- [x] 3.2b Wire layered-config profile resolution: when no explicit profile is passed, resolve the effective profile via `resolve_profile_config` (profile defaults -> org baseline -> repo overlay -> developer local); apply the four supported required-field aliases to completeness findings and emit `unsupported-profile-field` advisories for all others.
- [x] 3.3 Guarantee read-only behavior toward upstream artifact directories (contract tests: no writes under source roots).
- [x] 3.4 Contract decorators (`@beartype`, `@require`, `@ensure`) on all new public APIs.
- [x] 3.5 Add fail-closed compatibility preflight in the core import helpers:
  support only fixture-backed default profiles and return
  `unsupported-source-schema` for unknown/custom sources without emitting
  partial records.

## 4. Implementation (modules repo, paired)

- [ ] 4.1 Track runtime wiring in nold-ai/specfact-cli-modules#168: `requirements import --from-openspec [PATH] --from-speckit [PATH]` with auto-detection, plus validate/list/coverage surfacing of new gate findings including `unsupported-source-schema`.
- [ ] 4.2 Keep module runtime thin: parsing, hashing, and gate logic stay core-owned.

## 5. Validation and documentation

- [x] 5.1 Re-run tests and quality gates (`hatch run format`, `type-check`, `lint`, `contract-test`, `smart-test`) until green; record passing evidence in `TDD_EVIDENCE.md`.
- [x] 5.2 Update docs: requirements guide repositioned import-first (OpenSpec/Spec Kit as accountable authoring sources; `--from-file` as generic fallback); document gate categories and CI exit-code usage.
- [x] 5.3 Run `openspec validate openspec-01-intent-trace --strict` and resolve all issues.

## 6. Delivery

- [x] 6.1 Update `openspec/CHANGE_ORDER.md` if sequencing changed during implementation.
- [x] 6.2 Mirror material scope updates to `../specfact-cli-internal/wiki/sources/openspec-01-intent-trace.md` and rebuild the wiki graph.
- [x] 6.3 Sync GitHub issue #350 (and modules #168) title/body with the rescoped proposal.
- [ ] 6.4 Open PR from `feature/openspec-01-intent-trace` to `dev` with spec/test/code/docs evidence.
- [ ] 6.5 After the PR merges, remove the feature worktree with `scripts/worktree.sh remove feature/openspec-01-intent-trace`.
