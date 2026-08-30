# Change Validation: ai-integration-03-instruction-files

## Status

**PROPOSAL READY; IMPLEMENTATION NOT STARTED.**

## Rescope Decision

- #253 retains Feature parent #372.
- Scope is limited to generated AGENTS/OpenSpec/Spec Kit and command-harness gate references with owned, idempotent sections.
- The signed module owns workflow content and validators; #251 owns installation/export; preflight-04 owns external adapter packages.

## Planning Boundary

- No production code, tests, AGENTS.md section, OpenSpec/Spec Kit file, prompt, skill, plugin, adapter, hook, workflow, manifest, signature, version, or dependency is changed.
- No `TDD_EVIDENCE.md` exists because implementation has not started.

## Dependency Review

- Parent Feature: core [#372](https://github.com/nold-ai/specfact-cli/issues/372).
- Native blocker verified: core [#251](https://github.com/nold-ai/specfact-cli/issues/251).
- Native downstream verified: modules [#433](https://github.com/nold-ai/specfact-cli-modules/issues/433).
- GitHub readback verified the retained User Story parent #372, project `SpecFact CLI` / `Todo`, assignee `djm81`, and the required labels.

## Validation Record

- `openspec status --change ai-integration-03-instruction-files --json`: PASS on 2026-08-25; all required proposal artifacts reported complete.
- `openspec validate ai-integration-03-instruction-files --strict`: PASS on 2026-08-25.
- Markdown lint limited to changed planning Markdown: PASS on 2026-08-25.
- Staged schema-v2 Requirements planning evidence: PASS on 2026-08-25 with inspection-only cases and no test selectors or execution claims.

## Decision

The rescope is decision-complete and ready for a planning-only PR. Implementation remains explicitly unstarted.
