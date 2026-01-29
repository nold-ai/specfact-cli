# Design: Thorough Codebase Validation Depth

## Overview

This change adds a clear, documented path for thorough in-depth codebase validation in three modes: (a) sidecar for unmodified code, (b) contract-decorated codebases (full contract-test stack), (c) dogfooding specfact-cli on itself. No new external systems; integration is with existing repro, sidecar, and contract-test tooling.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Validation modes                                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  (1) Quick check          specfact repro [--repo PATH]                  │
│      → ruff, semgrep, basedpyright, CrossHair (budget), pytest          │
│      → Optional: --sidecar --sidecar-bundle NAME                        │
│                                                                         │
│  (2) Thorough (contracts) hatch run contract-test-full                  │
│      → contract-test-contracts + contract-test-exploration + scenarios  │
│      → Use when repo has @icontract / @beartype                         │
│                                                                         │
│  (3) Dogfooding           specfact repro --repo . && contract-test-full │
│      → Same as (1)+(2) on specfact-cli repo; optional --sidecar         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Integration Points

### Repro Checker

- **Current**: `ReproChecker.run_all_checks()` runs ruff, semgrep, basedpyright, CrossHair (with budget), optional pytest contracts/smoke. CrossHair targets: either modules with "CrossHair property test" marker or all expanded src/tools.
- **Change**: Optional "deep" mode (e.g. `--validation deep` or `--crosshair-timeout N`): when set, pass higher per-path timeout to CrossHair or restrict targets to a configurable list (e.g. critical adapters). Implementation: extend repro CLI options and pass through to `_build_crosshair_env` / CrossHair command; optional config file or env for target list.
- **Contract**: No change to default behavior; new options are additive.

### Sidecar

- **Current**: `specfact repro --sidecar --sidecar-bundle NAME` runs main checks then `run_sidecar_validation()` (unannotated detection, harness generation, CrossHair/Specmatic). No-edit path.
- **Change**: Document sidecar as the "thorough validation for unmodified code" path; ensure error messages and docs direct users to install CrossHair when sidecar is used. No code change required for sidecar itself unless we add a "deep" CrossHair option for sidecar runs (optional follow-up).

### Contract-Test Stack

- **Current**: `hatch run contract-test` (auto), `contract-test-contracts`, `contract-test-exploration`, `contract-test-scenarios`, `contract-test-full`. CrossHair timeout is configurable via STANDARD_CROSSHAIR_TIMEOUT and fast variant.
- **Change**: Document `contract-test-full` as the recommended thorough path for contract-decorated codebases. Optional: add hatch script or doc for "contract-test-exploration-deep" with higher timeout (e.g. 60s per path) for critical modules; can be a one-line script that invokes crosshair check with args. No change to contract_first_smart_test.py unless we add a "deep" exploration variant.

### CI / Dogfooding

- **Current**: CI may run repro, tests, lint separately.
- **Change**: Document dogfooding as: (1) `specfact repro --repo .`, (2) `hatch run contract-test-full` (or equivalent), (3) optional `specfact repro --sidecar --sidecar-bundle <bundle>`. Optionally add a CI job (e.g. `validate-thorough`) that runs (1)+(2) so specfact-cli validates itself on every PR or nightly. Job definition lives in `.github/workflows/`; this change can add the job or only document the commands for manual/periodic runs.

## Optional Deep CrossHair

- **Repro**: Add `--crosshair-per-path-timeout N` (default unchanged) so users can increase depth for repro runs. Implement by appending to CrossHair command in ReproChecker when building `crosshair_base`.
- **Config**: Optional `[tool.specfact]` or env (e.g. `SPECFACT_CROSSHAIR_DEEP_MODULES`) listing modules for deep-only runs; if present, repro could run CrossHair twice (normal pass + deep pass on listed modules) or once with higher timeout on listed modules. Prefer simple CLI flag first; config in a follow-up.

## Contract Enforcement

- New or modified public APIs (e.g. repro CLI options) must keep `@icontract` and `@beartype` where applicable. ReproChecker and sidecar orchestrator already have contracts; new code paths must follow the same pattern.
- No new adapters or bridge protocols; validation is local to CLI and hatch scripts.

## Risks and Mitigations

- **CrossHair timeout increase**: Longer timeouts can make CI slow. Mitigation: deep mode is opt-in; default budget unchanged; document recommended timeouts for CI vs. local.
- **Documentation drift**: Mitigation: single "Thorough codebase validation" section with copy-paste commands; link from README so it stays discoverable.

## Out of Scope

- New testing framework or external services.
- Changing default repro or contract-test behavior for users who do not opt in.
- Implementing full "validate thoroughly" as a single new CLI command (documented composition of repro + contract-test-full is sufficient for this change; a single command can be a follow-up).
