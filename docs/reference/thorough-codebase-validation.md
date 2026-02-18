---
layout: default
title: Thorough Codebase Validation
permalink: /reference/thorough-codebase-validation/
description: How to run in-depth validation (quick check, contract-decorated, sidecar, dogfooding).
---

# Thorough Codebase Validation

This reference describes how to run thorough in-depth validation in different modes: quick check, contract-decorated codebases, sidecar for unmodified code, and dogfooding SpecFact CLI on itself.

## Validation Modes

| Mode | When to use | Primary command(s) |
|------|-------------|---------------------|
| **Quick check** | Fast local/CI gate (lint, type-check, CrossHair with default budget) | `specfact repro --repo <path>` |
| **Thorough (contract-decorated)** | Repo already uses `@icontract` / `@beartype`; run full contract stack | `hatch run contract-test-full` |
| **Sidecar (unmodified code)** | Third-party or legacy repo; no edits to target source | `specfact repro --repo <path> --sidecar --sidecar-bundle <bundle>` |
| **Dogfooding** | Validate the specfact-cli repo with the same pipeline | `specfact repro --repo .` + `hatch run contract-test-full` (optional sidecar) |

## 1. Quick check (`specfact repro`)

Run the standard reproducibility suite (ruff, semgrep if config exists, basedpyright, CrossHair, optional pytest contracts/smoke):

```bash
specfact repro --repo .
specfact repro --repo /path/to/external/repo --verbose
```

- **Time budget**: Default 120s; use `--budget N` (advanced) to change.
- **Deep CrossHair**: To increase per-path timeout for CrossHair (e.g. for critical modules), use `--crosshair-per-path-timeout N` (seconds; N must be positive). Default behavior is unchanged when not set.

```bash
specfact repro --repo . --crosshair-per-path-timeout 60
```

Required env: none. Optional: `[tool.crosshair]` in `pyproject.toml` (e.g. from `specfact repro setup`).

## 2. Thorough validation for contract-decorated codebases

When your repo already has `@icontract` and `@beartype` on public APIs, use the full contract-test stack:

```bash
hatch run contract-test-full
```

This runs:

- Runtime contract validation (`contract-test-contracts`)
- CrossHair exploration (`contract-test-exploration`)
- Scenario tests with contract references (`contract-test-scenarios`)

Exploration timeout can be configured via `[tool.crosshair]` or env (e.g. `STANDARD_CROSSHAIR_TIMEOUT`). For deeper CrossHair analysis on critical paths, run CrossHair directly with a higher per-path timeout:

```bash
crosshair check --per_path_timeout=60 src/your_critical_module/
```

Document this as the recommended thorough path for contract-decorated code; CI can invoke `hatch run contract-test-full` for PR validation.

## 3. Sidecar validation (unmodified code)

For repositories you cannot or do not want to modify (no contract decorators added):

```bash
specfact repro --repo <path> --sidecar --sidecar-bundle <bundle-name>
```

- Main repro checks run first (lint, semgrep, type-check, CrossHair if available).
- Then sidecar validation runs: unannotated detection, harness generation, CrossHair/Specmatic on generated harnesses. No files in the target repo are modified.
- If CrossHair is not installed or the bundle is invalid, sidecar is skipped or partial with clear messaging; non-zero exit only for main check failures (sidecar can be advisory).

See [Sidecar Validation Guide](/guides/sidecar-validation/) for setup and bundle configuration.

## 4. Dogfooding (SpecFact CLI on itself)

Maintainers can validate the specfact-cli repository with the same pipeline:

1. **Repro + contract-test-full** (recommended minimum):

   ```bash
   specfact repro --repo .
   hatch run contract-test-full
   ```

2. **Optional sidecar** (to cover unannotated code in specfact-cli):

   ```bash
   specfact repro --repo . --sidecar --sidecar-bundle <bundle-name>
   ```

Use the same commands in a CI job or release checklist so specfact-cli validates itself before release. No repo-specific code is required beyond existing repro and contract-test tooling.

## Copy-paste summary

| Goal | Commands |
|------|----------|
| Quick gate | `specfact repro --repo .` |
| Deep CrossHair (repro) | `specfact repro --repo . --crosshair-per-path-timeout 60` |
| Full contract stack | `hatch run contract-test-full` |
| Unmodified repo | `specfact repro --repo <path> --sidecar --sidecar-bundle <name>` |
| Dogfooding | `specfact repro --repo .` then `hatch run contract-test-full`; optionally add `--sidecar --sidecar-bundle <name>` to repro |

Required env/config: optional `[tool.crosshair]` in `pyproject.toml`; for sidecar, a valid sidecar bundle and CrossHair installed when sidecar CrossHair is used.
