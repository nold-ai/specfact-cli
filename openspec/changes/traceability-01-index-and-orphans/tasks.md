# Tasks: traceability-01-index-and-orphans

## 1. Branch and dependency guardrails

- [x] 1.1 Created dedicated branch `feature/traceability-evidence-spine` from the reconciled `dev` foundation before implementation work.
- [x] 1.2 Verified requirements input contracts are implemented; optional adapters are consumed only when they supply normalized records.
- [x] 1.3 Revalidated scope on 2026-07-09: core consumes normalized artifact records; modules #170 owns persistence and runtime UX.

## 2. Spec-first and test-first preparation

- [x] 2.1 Define generic artifact, link, index, rebuild, and finding contracts plus requirements adapter mapping.
- [x] 2.2 Add tests for stable identities, deterministic ordering, incremental rebuild, dangling links, unlinked artifacts, duplicate identities, self-contradictions, and requirements mapping.
- [x] 2.3 Run targeted tests to capture failing-first behavior and record results in `TDD_EVIDENCE.md`.

## 3. Implementation

- [x] 3.1 Implement the generic artifact evidence index and deterministic rebuild output.
- [x] 3.2 Add/update contract decorators and type enforcement on public APIs.
- [x] 3.3 Implement the complete generic core index engine and integrate `requirements.inputs`; architecture remains optional and modules #170 owns persistence/query runtime.

## 4. Validation and documentation

- [x] 4.1 Re-ran targeted tests, type, clean-code, docs, contract, and security gates; all changed scenarios pass.
- [x] 4.2 Updated the validation-evidence reference and existing reference navigation; no core command or workflow was added.
- [x] 4.3 Ran `openspec validate traceability-01-index-and-orphans --strict` successfully.

## 5. Delivery

- [x] 5.1 Updated `openspec/CHANGE_ORDER.md` to record requirements as the first required adapter and all other adapters as optional.
- [x] 5.2 Updated PR [#641](https://github.com/nold-ai/specfact-cli/pull/641) from `feature/traceability-evidence-spine` to `dev` with spec/test/code/docs evidence and `Closes #242`.
