# docs-vibecoder-entry-path Specification

## Purpose

TBD - created by archiving change docs-new-user-onboarding. Update Purpose after archive.

## Requirements

### Requirement: Vibe-coder entry path is discoverable and runnable in under 2 commands

The documentation entry surface SHALL make it possible for a developer who has never used
SpecFact before — and who does not know Python packaging — to reach a scored `code review run`
result in 2 commands and approximately 10 seconds, without pip install or virtual environment
setup.

#### Scenario: Vibe coder runs the entry sequence for the first time

- **GIVEN** a developer with `uvx` available (via the `uv` toolchain) and a git repository
- **WHEN** they run `uvx specfact-cli init --profile solo-developer` followed by
  `uvx specfact-cli code review run --path . --scope full`
- **THEN** the first command SHALL install the required modules at user level in under 10 seconds
- **AND** the second command SHALL produce a scored code review result with categorised findings
- **AND** no additional configuration, pip install, or virtual environment setup SHALL be required

#### Scenario: Entry path is documented with expected output

- **WHEN** a visitor reads the homepage or installation page
- **THEN** the documentation SHALL show the expected output format of `code review run`
  (e.g. "Verdict: FAIL | Score: 0 | 64 findings across naming, complexity, and type checks")
  so the user knows what a successful first run looks like before they run it

### Requirement: `code review run --path .` SHALL provide actionable guidance when scope is missing

The CLI SHALL provide an actionable inline hint rather than a bare error when
`specfact code review run --path .` is run without `--scope full` and no diff output is
available.

#### Scenario: User runs `code review run --path .` without `--scope full`

- **GIVEN** the user is in a git repository with no staged or unstaged changes visible via
  `git diff HEAD`
- **WHEN** they run `specfact code review run --path .`
- **THEN** the CLI SHALL either:
  (a) default automatically to `--scope full` when no diff is available, OR
  (b) display an error that includes the exact command to run:
  `specfact code review run --path . --scope full`
- **AND** the error SHALL NOT only say "Unable to determine changed tracked files" without
  providing the corrective command

### Requirement: Module-not-found error SHALL provide an exact uvx init command

The CLI SHALL include the exact `uvx specfact-cli init` command as the suggested fix in
module-not-found errors when running in a uvx execution context.

#### Scenario: Vibe coder runs `uvx specfact-cli code review run` before init

- **GIVEN** a user running via `uvx specfact-cli` with no modules installed at user level
- **WHEN** they run `uvx specfact-cli code review run --path . --scope full`
- **THEN** the CLI SHALL display an error message that includes:
  `uvx specfact-cli init --profile solo-developer`
  as the suggested fix command
- **AND** the message SHALL NOT only reference "workflow bundles" without giving an exact command

### Requirement: Plain-language value statement precedes technical vocabulary on entry pages

The docs homepage and installation page SHALL open with a plain-language statement of what the
user will get — using vocabulary a non-Python-expert understands — before introducing any
technical terms.

#### Scenario: Non-Python developer reads the homepage

- **WHEN** a developer who primarily uses JavaScript, no-code tools, or AI-assisted coding reads
  the homepage hero section
- **THEN** they SHALL encounter at least one sentence they can understand without Python or CLI
  expertise (e.g. "Point it at your code. Get a score and a list of what to fix.")
- **AND** the first technical term they encounter SHALL be a command they can copy and run,
  not a concept they need to research first
