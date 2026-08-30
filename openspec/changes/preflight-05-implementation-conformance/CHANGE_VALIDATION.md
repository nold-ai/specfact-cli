# Change Validation: preflight-05-implementation-conformance (core)

## Status

**PROPOSAL READY; IMPLEMENTATION NOT STARTED.**

## Planning Boundary

- Proposal-stage governance artifacts only.
- No production code, tests, generated snapshot/result, runtime command, module, skill, adapter, manifest, signature, version, or dependency is created.
- No `TDD_EVIDENCE.md` exists because implementation has not started.

## Scope and Ownership Review

- Core owns worktree/index/range snapshot, obligation mapping, checkpoint/conformance result, finding, authority, and side-effect-free verifier interfaces.
- The paired modules story owns Git extraction, pytest/review execution, remediation packets, bounded agent workflow, rendering, persistence, release, and policy orchestration.
- This work follows the stable preflight release and precedes generic installation, generated instructions, and adapters.

## Dependency Review

- Parent Feature: core [#681](https://github.com/nold-ai/specfact-cli/issues/681).
- Native blocker verified: stable modules [#432](https://github.com/nold-ai/specfact-cli-modules/issues/432).
- Native downstream verified: paired modules [#434](https://github.com/nold-ai/specfact-cli-modules/issues/434).
- GitHub readback verified User Story type, parent #681, project `SpecFact CLI` / `Todo`, assignee `djm81`, and the required labels.

## Validation Record

- `gh issue view 684 --repo nold-ai/specfact-cli --json number,title,state,updatedAt,url`: PASS on 2026-08-29; source identity was `nold-ai/specfact-cli#684`, open, updated `2026-08-29T19:56:04Z`.
- `openspec status --change preflight-05-implementation-conformance --json` and `openspec validate preflight-05-implementation-conformance --strict`: PASS on 2026-08-29 for this change only.
- `SPECFACT_MODULES_REPO=/private/tmp/specfact-modules-fixture-69f07581 hatch run pre-commit run`: PASS on 2026-08-29 against the complete staged planning diff. This command ran the repository YAML, Markdown fix/lint, schema-v2 Requirements planning-evidence, diff-scope, contract, and code-review gates; the sidecar remained inspection-only and claimed no test execution.
- `git diff --check`: PASS on 2026-08-29 for the complete planning diff.
- Review follow-up on 2026-08-30: interface additions, deletions, and both rename endpoints now require provenance-bound absent-side tombstones so expected nonexistence is distinguishable from missing evidence.
- Second review follow-up on 2026-08-30: the planning evidence explicitly covers immutable lineage origin, origin-to-head ancestry, and exact delivery-head observables; invalid absence aggregates through `unverifiable` to `UNKNOWN`; the parked R08 archive gate now repeats its complete implementation-through-approved-promotion prerequisite.

## Decision

The proposal is ready for review and a planning-only PR. Checkpoint and final conformance implementation remain explicitly unstarted.
