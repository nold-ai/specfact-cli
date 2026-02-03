# Change: Add thorough in-depth codebase validation for sidecar, contract-decorated codebases, and dogfooding

## Why

Runtime bugs often slip past contract decorators and tests because: (a) contracts only fire at decorated boundaries when those paths are executed; (b) CrossHair in `specfact repro` shares a single time budget over all source and may not reach deep paths; (c) Semgrep is pattern-based and does not reason about logic. Users need a reliable way to validate codebases in three modes: (a) **Sidecar**—unmodified original code, no edits to target repo; (b) **Existing codebases**—when code already uses `@icontract`/`@beartype`, run full contract exploration and scenario tests; (c) **Dogfooding**—use SpecFact CLI to validate SpecFact CLI itself so the pipeline is proven on real complexity. Adding clear workflows, CI integration, and optional deeper CrossHair/Semgrep usage makes in-depth validation repeatable and enables production-grade confidence.

## What Changes

- **EXTEND**: Document and wire a single "thorough validation" path that supports: (1) sidecar for unmodified code (existing `specfact repro --sidecar --sidecar-bundle`), (2) contract-decorated codebases via `hatch run contract-test-full` (contracts + CrossHair exploration + scenarios), (3) dogfooding by running that path on the specfact-cli repo.
- **EXTEND**: Ensure `specfact repro` (with optional `--sidecar`) and the contract-test layers are clearly documented as the recommended in-depth validation flow; add a repro option or doc section for "deep" CrossHair (e.g. higher per-path timeout or focused modules) so users can target critical paths.
- **NEW**: Add a small validation-mode or preset (e.g. `--validation deep` or documented `specfact repro` + `hatch run contract-test-exploration` with increased timeout) so CI or local runs can explicitly request thorough validation without editing target code.
- **EXTEND**: Optional CrossHair target selection: allow repro or config to restrict CrossHair to a list of modules (e.g. critical adapters) with higher per-path timeout so budget is spent where it matters.
- **EXTEND**: Document dogfooding: how to run full validation (repro + contract-test-full or equivalent) on specfact-cli; add or reference a CI job or local checklist so specfact-cli validates itself before release.

## Capabilities

- **codebase-validation-depth**: Thorough in-depth validation supporting sidecar (unmodified code), contract-decorated codebases (full contract-test stack), and dogfooding (specfact-cli on itself) with clear workflows and optional deep CrossHair/Semgrep usage.

## Impact

- **Affected specs**: New `openspec/specs/codebase-validation-depth/spec.md` (or under existing validation/sidecar specs if preferred).
- **Affected code**: `src/specfact_cli/commands/repro.py` (optional deep-validation mode or flags), `src/specfact_cli/validators/repro_checker.py` (optional CrossHair target list / per-path timeout override), config or docs for contract-test + repro combination; possibly `pyproject.toml` or hatch scripts for a single "validate thoroughly" command.
- **Affected documentation** (<https://docs.specfact.io>): Add or extend a reference section for "Thorough codebase validation" covering: (1) sidecar for unmodified code, (2) contract-decorated codebases (contract-test-full), (3) dogfooding specfact-cli; document optional deep CrossHair and Semgrep usage; update README or getting-started if needed. No new top-level pages required if content fits in reference/validation.
- **Integration points**: Existing `specfact repro`, `specfact validate sidecar`, `hatch run contract-test-*`, CrossHair, Semgrep; CI workflows (optional new or updated job for thorough validation).
- **Backward compatibility**: Additive only; existing repro and sidecar behavior unchanged unless user opts into deep mode or new flags.

## Source Tracking

- **GitHub Issue**: #163
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/163>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
