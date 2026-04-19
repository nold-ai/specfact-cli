# Tasks: knowledge-01-distillation-engine

## 1. Branch and dependency guardrails

- [ ] 1.1 Create worktree branch `feature/knowledge-01-distillation-engine` from `dev`.
- [ ] 1.2 Confirm telemetry-01 is landed (emitter consumes knowledge outcomes).
- [ ] 1.3 Reconfirm scope — this change owns schema + engine; bundle runtime lives in modules repo.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/knowledge-distillation/spec.md`.
- [ ] 2.2 Write pydantic schema tests for evidence/learning/rule frontmatter.
- [ ] 2.3 Write 500-token rule enforcement test (fail first).
- [ ] 2.4 Write distill pipeline tests (below-threshold no-op; above-threshold learning + dry-run diff).
- [ ] 2.5 Write promotion-gate tests including supersedes chain.
- [ ] 2.6 Write MemoryBackend protocol contract tests.
- [ ] 2.7 Capture failing-first output in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement pydantic models in `src/specfact_cli/memory/schema.py` with `@icontract`/`@beartype`.
- [ ] 3.2 Implement markdown-graph backend in `src/specfact_cli/memory/backends/markdown_graph.py`.
- [ ] 3.3 Implement fingerprint + PII-redaction helper in `src/specfact_cli/memory/fingerprint.py`.
- [ ] 3.4 Implement curator prompt loader (`prompts/curator_v1.md`) with version pinning.
- [ ] 3.5 Implement `specfact memory distill` command (dry-run only).
- [ ] 3.6 Implement `specfact memory promote` command (human-gated).
- [ ] 3.7 Implement `specfact memory status` surface (pending / ready / promoted counts).

## 4. Validation and documentation

- [ ] 4.1 Re-run tests; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Document schema in `docs/agent-rules/knowledge-schema.md`.
- [ ] 4.3 Document distill / promote workflow in user-facing docs.
- [ ] 4.4 Run `openspec validate knowledge-01-distillation-engine --strict`.
- [ ] 4.5 Run full quality gate: format, type-check, contract-test, tests with coverage.

## 5. Delivery

- [ ] 5.1 Mirror to `specfact-cli-internal/wiki/sources/knowledge-01-distillation-engine.md`; rebuild graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` — dependents: knowledge-02, enterprise-03.
- [ ] 5.3 Open PR to `dev`.
