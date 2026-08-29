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

- `openspec status --change preflight-01-design-contract-core --json`: PASS on 2026-08-25; all required proposal artifacts reported complete.
- `openspec validate preflight-01-design-contract-core --strict`: PASS on 2026-08-25.
- Markdown lint limited to changed planning Markdown: PASS on 2026-08-25.
- Staged schema-v2 Requirements planning evidence: PASS on 2026-08-25 with inspection-only cases and no test selectors or execution claims.

## Decision

The proposal is ready for review and a planning-only PR. Implementation remains explicitly unstarted and must begin later in a dedicated issue-linked worktree.
