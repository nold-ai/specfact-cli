# codebase-validation-depth Specification

## Purpose
TBD - created by archiving change validation-01-deep-validation. Update Purpose after archive.
## Requirements
### Requirement: Sidecar Validation for Unmodified Code

The CLI SHALL support thorough in-depth validation of a target repository without modifying the target's source (sidecar mode).

**Rationale**: Users need to validate third-party or legacy codebases where adding contract decorators or changing code is not an option.

#### Scenario: Run Sidecar Validation on Unmodified Repo

**Given**: A repository with no contract decorators and a valid sidecar bundle name

**When**: The user runs `specfact repro --repo <path> --sidecar --sidecar-bundle <bundle>`

**Then**: SpecFact runs main repro checks (lint, semgrep, type-check, CrossHair if available) and then sidecar validation (unannotated detection, harness generation, CrossHair/Specmatic on generated harnesses) without editing the target repo

**Acceptance Criteria**:

- Sidecar runs after main repro checks when `--sidecar` and `--sidecar-bundle` are provided
- Unannotated code is detected; harnesses are generated in a no-edit path
- User receives a summary (e.g. CrossHair confirmed/not confirmed/violations) for unannotated code
- No files in the target repo are modified by sidecar validation

#### Scenario: Sidecar Optional When CrossHair Unavailable

**Given**: CrossHair is not installed in the target repo environment

**When**: The user runs `specfact repro --sidecar --sidecar-bundle <bundle>`

**Then**: Main repro checks run; sidecar is attempted and reports clearly (e.g. skipped or partial) when CrossHair or dependencies are missing, without failing the entire run if sidecar is advisory

**Acceptance Criteria**:

- Clear messaging when sidecar cannot run (tool missing, bundle invalid)
- Non-zero exit only for main check failures; sidecar failure can be advisory per existing repro behavior

---

### Requirement: Thorough Validation for Contract-Decorated Codebases

The CLI and project tooling SHALL support a documented "thorough" validation path for repositories that already use `@icontract` and `@beartype`.

**Rationale**: Existing codebases with contracts should be able to run full contract exploration and scenario tests in a single, repeatable flow.

#### Scenario: Run Full Contract-Stack Validation

**Given**: A repository with contract decorators on public APIs and a standard layout (src/, tests/)

**When**: The user runs the full contract-test stack (e.g. `hatch run contract-test-full` or equivalent: contract validation + CrossHair exploration + scenario tests)

**Then**: All layers run (runtime contract validation, CrossHair exploration, scenario/E2E tests) and results are reported; exit code reflects failures

**Acceptance Criteria**:

- `hatch run contract-test-full` (or documented equivalent) runs contracts, exploration, and scenarios
- Exploration layer uses CrossHair with configurable timeout (e.g. from `[tool.crosshair]` or env)
- Documentation states that this is the recommended "thorough" path for contract-decorated codebases
- CI can invoke this path for PR validation

#### Scenario: CrossHair Exploration with Increased Depth

**Given**: A user or CI wants deeper CrossHair analysis on critical modules

**When**: The user runs CrossHair with higher per-path timeout (e.g. via `crosshair check --per_path_timeout=60 <module>` or a documented repro/contract-test option)

**Then**: Critical modules are analyzed with longer timeout so deeper paths can be explored; results are reported

**Acceptance Criteria**:

- Documented way to run CrossHair with higher per-path timeout (CLI flag, config, or hatch script)
- Optional list of modules for "deep" exploration (e.g. config or flag) so budget is spent on critical paths
- No change to default repro budget unless user opts in

---

### Requirement: Dogfooding SpecFact CLI on Itself

The project SHALL document and support using SpecFact's own validation pipeline to verify the specfact-cli repository (dogfooding).

**Rationale**: Proves the pipeline on real complexity and catches regressions before release.

#### Scenario: Run Thorough Validation on SpecFact CLI Repo

**Given**: The specfact-cli repository with existing contracts, tests, and sidecar capability

**When**: A maintainer runs the documented dogfooding validation (e.g. `specfact repro --repo .` plus `hatch run contract-test-full`, optionally `specfact repro --sidecar --sidecar-bundle <bundle>`)

**Then**: All applicable checks run (repro: lint, semgrep, type-check, CrossHair; contract-test-full: contracts, exploration, scenarios); results are reported; exit code reflects pass/fail

**Acceptance Criteria**:

- Documentation describes the exact commands and order for dogfooding (repro + contract-test-full; optional sidecar)
- CI or release checklist can include these steps so specfact-cli validates itself before release
- No new repo-specific code required beyond existing repro and contract-test; documentation and optional CI job are sufficient

#### Scenario: Dogfooding Includes Optional Sidecar

**Given**: SpecFact CLI repo and a sidecar bundle that includes specfact-cli

**When**: Maintainer runs `specfact repro --repo . --sidecar --sidecar-bundle <bundle>`

**Then**: Main repro checks run; sidecar runs on unannotated code in specfact-cli and reports CrossHair/sidecar results

**Acceptance Criteria**:

- Sidecar can target specfact-cli repo when bundle is configured
- Documented as optional step for dogfooding to expand coverage to unannotated code

---

### Requirement: Clear Documentation of Validation Modes

The documentation SHALL describe three validation modes: (1) quick check (repro), (2) thorough contract-decorated (contract-test-full), (3) sidecar for unmodified code, and (4) dogfooding.

**Rationale**: Users need to choose the right mode for their context (unmodified repo vs. contract-decorated vs. validating SpecFact itself).

#### Scenario: User Chooses Validation Mode from Docs

**Given**: User wants to validate a codebase (own repo with contracts / third-party unmodified / specfact-cli itself)

**When**: User reads the "Thorough codebase validation" (or equivalent) section in docs

**Then**: User finds: (a) when to use sidecar (unmodified code), (b) when to use contract-test-full (contract-decorated), (c) how to dogfood specfact-cli; and the exact commands or presets

**Acceptance Criteria**:

- Single reference section or guide covering all three use cases
- Commands are copy-pasteable; any required env or config is stated
- Link from README or getting-started to this section where appropriate

