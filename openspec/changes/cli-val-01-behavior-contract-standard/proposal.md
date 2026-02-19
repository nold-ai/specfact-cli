# Change: CLI Behavior Contract Standard

## Why

Every SpecFact CLI feature should have a single artifact that answers: "What does this command do, and what happens when you use it wrong?" Today this knowledge lives scattered across 73+ test files, docstrings, and docs pages. When a user reports unexpected behavior, there is no single source of truth to check the expected CLI behavior against. A machine-readable behavior contract per command group — recording exact argv, expected exit codes, output patterns, and filesystem side effects — closes this gap and becomes the foundation for all downstream validation (snapshot tests, acceptance runners, anti-pattern suites, CI gates).

## What Changes

- **NEW**: YAML schema definition for CLI behavior scenarios (`tests/cli-contracts/schema/cli-scenario.schema.yaml`) — defines the contract format for command groups
- **NEW**: Scenario files for pilot command groups stored in `tests/cli-contracts/` — one YAML file per command group recording patterns (happy paths) and anti-patterns (misuse/invalid input)
- **NEW**: Schema validation utility (`tools/validate_cli_contracts.py`) that validates scenario YAML files against the schema
- **EXTEND**: `openspec/config.yaml` context to reference CLI behavior contracts as a recognized artifact type
- **EXTEND**: Documentation in `docs/` to describe the CLI behavior contract format and authoring guidelines

## Capabilities

### New Capabilities

- `cli-behavior-contracts`: A YAML-based schema and authoring standard for declaring CLI command behavior expectations — exact argv, required context, expected exit class (success/failure), stdout/stderr patterns, and filesystem diff expectations — separated into patterns (happy paths) and anti-patterns (misuse).

## Impact

- **Affected specs**: No existing specs modified; new spec delta defines the schema and authoring process
- **Affected code**: New schema file and validation tool only; no production CLI code changes
- **Integration points**: Consumed by cli-val-03 (anti-patterns), cli-val-04 (acceptance runner), cli-val-06 (copilot generation)
- **Documentation impact**: New page in `docs/` describing the CLI behavior contract format for contributors

## Dependencies

- No hard blockers — this is the foundation change with no prerequisites
- Downstream dependents: cli-val-03-misuse-safety-proof, cli-val-04-acceptance-test-runner, cli-val-06-copilot-test-generation

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #279
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/279
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
