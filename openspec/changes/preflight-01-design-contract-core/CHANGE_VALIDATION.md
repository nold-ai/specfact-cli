# Change Validation: preflight-01-design-contract-core

## Status

**PROPOSAL READY; IMPLEMENTATION NOT STARTED.**

## Planning Boundary

- Proposal-stage governance artifacts only.
- No production code, tests, runtime scaffold, generated contract, seal, skill, plugin, workflow, package, manifest, signature, version, or dependency change exists in this planning change.
- No `TDD_EVIDENCE.md` exists because implementation and failing-first work have not started.

## Scope and Ownership Review

- Core owns durable contract, role-classified scope, component/risk/verification intent, validation-result, canonical digest, seal, and verifier interfaces.
- Modules owns executable validators, CLI, persistence, rendering, and bundled workflow content.
- Existing Requirements verification cases/selectors/plans, architecture, governance evidence, traceability, and OpenSpec/Spec Kit import changes remain upstream inputs.

## Dependency Review

- Parent Feature: core [#681](https://github.com/nold-ai/specfact-cli/issues/681).
- Native downstream edge verified: modules [#431](https://github.com/nold-ai/specfact-cli-modules/issues/431) is blocked by core #682.
- GitHub readback verified User Story type, parent #681, project `SpecFact CLI` / `Todo`, assignee `djm81`, and the required labels.

## Validation Record

- `gh issue view 682 --repo nold-ai/specfact-cli --json number,title,state,updatedAt,url`: PASS on 2026-08-29; source identity was `nold-ai/specfact-cli#682`, open, updated `2026-08-29T19:56:04Z`.
- `openspec status --change preflight-01-design-contract-core --json` and `openspec validate preflight-01-design-contract-core --strict`: PASS on 2026-08-29 for this change only.
- `SPECFACT_MODULES_REPO=/private/tmp/specfact-modules-fixture-69f07581 hatch run pre-commit run`: PASS on 2026-08-29 against the complete staged planning diff. This command ran the repository YAML, Markdown fix/lint, schema-v2 Requirements planning-evidence, diff-scope, contract, and code-review gates; the sidecar remained inspection-only and claimed no test execution.
- `git diff --check`: PASS on 2026-08-29 for the complete planning diff.

## Decision

The proposal is ready for review and a planning-only PR. Implementation remains explicitly unstarted and must begin later in a dedicated issue-linked worktree.
