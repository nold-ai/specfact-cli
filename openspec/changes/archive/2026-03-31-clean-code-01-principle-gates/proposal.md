# Change: Clean Code Principle Gates for specfact-cli

## Why

SpecFact CLI already has a growing review toolchain, but the repository still lacks one governed change that turns the 7 clean-code principles into explicit repo-level gates for the public instruction surfaces and the repo's own review workflow. The 2026-03-22 clean-code implementation plan splits that work into two phases: the review engine expansion lives in `specfact-cli-modules`, and specfact-cli then consumes those new rule categories to harden its own charter, CI gate, and contributor guidance. This change is the specfact-cli half of that sequence.

## What Changes

- **NEW**: `agent-instruction-clean-code-charter` capability that defines how specfact-cli instruction surfaces reference or embed the 7-principle clean-code charter across `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/clean-code-principles.mdc`, `.codex` skill surfaces, and `.github/copilot-instructions.md`.
- **NEW**: `clean-code-compliance-gate` capability that requires specfact-cli to run the expanded `specfact review` categories from `clean-code-02-expanded-review-module` and hold zero clean-code regressions before merge.
- **NEW**: `clean-code-loc-nesting-check` capability that consumes the review module's LOC, nesting-depth, and parameter-count checks under Phase A thresholds first, with the stricter Phase B thresholds explicitly deferred until cleanup is complete.
- **EXTEND**: `code-review-zero-findings` remains the prerequisite dogfood gate and is extended with a clean-code self-compliance phase after the baseline zero-finding pass is achieved.
- **EXTEND**: `ai-integration-03-instruction-files` receives a narrow delta so generated IDE aliases reference the canonical clean-code skill without duplicating the charter verbatim.

## Capabilities

### New Capabilities

- `agent-instruction-clean-code-charter`: specfact-cli instruction surfaces consistently reference the 7-principle clean-code charter and keep one canonical source of truth for reviewers and AI copilots.
- `clean-code-compliance-gate`: specfact-cli consumes the expanded review module and blocks clean-code regressions in repo-local review and CI workflows.
- `clean-code-loc-nesting-check`: specfact-cli adopts the review module's LOC, nesting-depth, and parameter-count checks using the staged Phase A threshold rollout.

### Modified Capabilities

- `dogfood-self-review`: Extended to require zero clean-code category regressions before the repo claims a zero-finding self-review state.
- `cross-platform-instructions`: Extended to carry a one-line clean-code alias reference instead of inlining the full charter into every generated instruction file.

## Impact

- **Affected specs**: new change-local specs for clean-code charter, clean-code compliance gating, and staged LOC/nesting thresholds; delta updates to `code-review-zero-findings`, `ai-integration-03-instruction-files`, `policy-02-packs-and-modes`, `profile-01-config-layering`, `governance-01-evidence-output`, `governance-02-exception-management`, `validation-02-full-chain-engine`, `dogfooding-01-full-chain-e2e-proof`, and `cli-val-01-behavior-contract-standard`.
- **Affected code**: instruction surfaces, CI/review orchestration, and docs in specfact-cli only after the prerequisite module change lands.
- **Dependencies**: blocked by `code-review-zero-findings` and cross-repo change `clean-code-02-expanded-review-module` in `nold-ai/specfact-cli-modules`.
- **Documentation**: update `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/clean-code-principles.mdc`, `.github/copilot-instructions.md`, and any contributor docs that explain repo review gates or AI instruction setup.
- **Rollback**: if the expanded review categories prove too noisy, specfact-cli can temporarily keep the charter/reference surfaces while leaving the clean-code gate in advisory mode via the policy-pack override path owned by `policy-02-packs-and-modes`.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #434
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/434>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
