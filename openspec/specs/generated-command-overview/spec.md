# generated-command-overview Specification

## Purpose
TBD - created by archiving change tester-cli-reliability. Update Purpose after archive.
## Requirements
### Requirement: Generated Command Overview Is The Authoritative Command Contract

The repository SHALL generate deterministic command overview artifacts from the actual core and official module command tree.

#### Scenario: Core command overview artifacts are generated

- **GIVEN** the command overview generator runs in the core repository
- **WHEN** it writes artifacts
- **THEN** it produces `llms.txt`, `docs/reference/commands.generated.md`, and `docs/reference/commands.generated.json`
- **AND** every command record includes command path, owning repo, owning package or module, install prerequisite, short help, arguments/options, subcommands, source import path when known, and hidden/deprecated status
- **AND** generated output is stable for the same source tree.

#### Scenario: Generated artifacts are freshness-checked

- **GIVEN** CLI source, module manifests, docs, prompts, or command validation scripts change
- **WHEN** the command overview check runs in pre-commit or CI
- **THEN** it fails if generated artifacts are stale
- **AND** it tells the developer which generator command refreshes the artifacts.

### Requirement: Docs And Guidance Validate Against Generated Command Contract

Docs, prompt, template, and code guidance validation SHALL use the generated command contract instead of prefix-only help checks.

#### Scenario: Legacy command references fail validation

- **GIVEN** a Markdown file, prompt, Jinja2 template, YAML/JSON/text resource, or Python guidance string contains an obsolete command such as `specfact sync bridge`
- **WHEN** command guidance validation runs
- **THEN** the validator fails unless the reference is inside an explicitly marked migration/deprecation context
- **AND** the finding includes file path, line number, observed command, and canonical replacement when known.

#### Scenario: Invalid option placement fails validation

- **GIVEN** documentation contains `specfact code import <bundle> --repo .`
- **WHEN** command guidance validation runs
- **THEN** the validator rejects the example because the generated command contract does not support that option placement
- **AND** it reports the canonical supported invocation.

