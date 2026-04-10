# Change: Validation — Deep Codebase Validation (Sidecar, Contract, Dogfooding)

## Why

Runtime bugs often slip past contract decorators and tests because: (a) contracts only fire at decorated boundaries when those paths are executed; (b) CrossHair in `specfact repro` shares a single time budget over all source and may not reach deep paths; (c) Semgrep is pattern-based and does not reason about logic. Users need a reliable way to validate codebases in three modes: (a) **Sidecar** — unmodified original code; (b) **Existing codebases** — when code already uses `@icontract`/`@beartype`, run full contract exploration and scenario tests; (c) **Dogfooding** — use SpecFact CLI to validate SpecFact CLI itself.

This change extends the existing core validation capabilities. It does **not** require a new module; it extends the `specfact repro` and `specfact validate sidecar` commands already in the CLI core.

## Scope Note (Module Architecture)

This change affects the **core CLI** and **validation module** (`modules/validation/` or core `src/specfact_cli/validators/`) — not the new backlog/agile modules. The validation capabilities pre-date the module architecture and are part of the core CLI contract-first toolchain.

If the existing validation code lives in `src/specfact_cli/validators/`, no module migration is required for this change; it extends existing core validators.

## Scope Note (Module Architecture)

This change affects the **core CLI** and **validation module** (`modules/validation/` or core `src/specfact_cli/validators/`) — not the new backlog/agile modules. The validation capabilities pre-date the module architecture and are part of the core CLI contract-first toolchain.

If the existing validation code lives in `src/specfact_cli/validators/`, no module migration is required for this change; it extends existing core validators.

## What Changes

- **EXTEND**: Document and wire a single "thorough validation" path that supports:
  1. Sidecar for unmodified code (existing `specfact repro --sidecar --sidecar-bundle`)
  2. Contract-decorated codebases via `hatch run contract-test-full` (contracts + CrossHair exploration + scenarios)
  3. Dogfooding by running that path on the specfact-cli repo
- **EXTEND**: Ensure `specfact repro` (with optional `--sidecar`) and the contract-test layers are clearly documented as the recommended in-depth validation flow; add a repro option or doc section for "deep" CrossHair (e.g. higher per-path timeout or focused modules) so users can target critical paths.
- **NEW**: Add a validation mode or preset (e.g. `--validation deep` or documented `specfact repro` + `hatch run contract-test-exploration` with increased timeout) so CI or local runs can explicitly request thorough validation without editing target code.
- **EXTEND**: Optional CrossHair target selection: allow repro or config to restrict CrossHair to a list of modules (e.g. critical adapters) with higher per-path timeout so budget is spent where it matters.
- **EXTEND**: Document dogfooding: how to run full validation (repro + contract-test-full or equivalent) on specfact-cli; add or reference a CI job or local checklist so specfact-cli validates itself before release.

## Capabilities

- **codebase-validation-depth**: Thorough in-depth validation supporting sidecar (unmodified code), contract-decorated codebases (full contract-test stack), and dogfooding (specfact-cli on itself) with clear workflows and optional deep CrossHair/Semgrep usage.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #163
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/163>
- **Last Synced Status**: proposed
- **Sanitized**: false
