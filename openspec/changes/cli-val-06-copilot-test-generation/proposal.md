# Change: Copilot Test Generation for CLI Scenarios

## Why

SpecFact already has a `generate test-prompt` workflow for creating tests using IDE copilots. Extending this to generate CLI behavior scenarios means every new feature ships with end-user validation from day one — without developers manually writing YAML. This also makes the "patterns + anti-patterns as first-class artifacts" vision operationally sustainable. When the scenario format (cli-val-01) is copilot-native and CI enforces its presence (cli-val-05), the validation layer becomes self-sustaining.

## What Changes

- **NEW**: Prompt template in `resources/prompts/` that generates CLI behavior scenario YAML, anti-pattern catalog, and Markdown acceptance tests in one pass
- **EXTEND**: Existing `specfact generate test-prompt` workflow to detect CLI commands and offer the behavior scenario template alongside unit test templates
- **EXTEND**: OpenSpec convention requiring every change that adds or modifies a CLI command to include updated scenario files
- **EXTEND**: Documentation in `docs/` describing the copilot-driven scenario authoring workflow

## Capabilities

### New Capabilities

- `copilot-scenario-generation`: Prompt templates and workflow integration that enable AI copilots to generate CLI behavior scenario files (patterns + anti-patterns) for new or modified commands, making end-user validation a default part of feature development.

## Impact

- **Affected specs**: No existing specs modified
- **Affected code**: New prompt template in resources/prompts/; minor extension to generate test-prompt workflow
- **Integration points**: Consumes cli-val-01 schema (template generates compliant YAML); consumes cli-val-05 convention (CI enforces scenario presence)
- **Documentation impact**: New contributor guide page on copilot-driven scenario authoring

## Dependencies

- **Hard blocker**: cli-val-01-behavior-contract-standard (schema the templates generate)
- **Soft dependency**: cli-val-05-ci-integration (enforcement of scenario presence in CI)
- No downstream dependents

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #284
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/284
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
