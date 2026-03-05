## ADDED Requirements

### Requirement: Live docs reflect lean-core and grouped bundle command topology
The live documentation set SHALL describe the current command surface as a lean core plus marketplace-installed grouped bundle commands, and SHALL NOT present the former flat all-commands topology as the primary current UX.

#### Scenario: Reader checks command examples
- **WHEN** a reader follows command examples in README or published docs
- **THEN** core commands are shown as always available from `specfact-cli`
- **AND** bundle commands are shown through grouped command paths and marketplace installation context
- **AND** stale flat-command examples are removed, corrected, or clearly marked as historical compatibility context

### Requirement: Marketplace guidance is discoverable and non-duplicative
Marketplace, bundle installation, dependency, trust, and publishing documentation SHALL be available through clear entry points and SHALL avoid contradictory or duplicate guidance across README, landing pages, guides, and reference pages.

#### Scenario: Reader looks for marketplace workflow guidance
- **WHEN** a reader wants to install, trust, publish, or understand official bundles
- **THEN** the docs provide a discoverable path from README or docs landing into marketplace-specific pages
- **AND** terminology, command examples, and workflow descriptions are consistent across those pages

### Requirement: Command reference reflects ownership and package boundaries
The command reference documentation SHALL distinguish permanent core commands from marketplace-delivered bundle commands and SHALL organize module command coverage by package/category ownership instead of one legacy flat command inventory.

#### Scenario: Reader checks command reference
- **WHEN** a reader opens command reference documentation
- **THEN** the reference identifies which commands belong to core and which are provided by installed bundles
- **AND** bundle command coverage is grouped by category or package boundary
- **AND** readers can navigate from command docs to the relevant marketplace/module docs without ambiguity

### Requirement: Markdown quality workflow auto-fixes low-risk issues before enforcement
The documentation workflow SHALL automatically fix low-risk Markdown issues during pre-commit checks before enforcing markdown lint failures for non-fixable or higher-risk issues.

#### Scenario: Contributor stages Markdown changes with trivial spacing issues
- **WHEN** a contributor stages Markdown files and runs the repository pre-commit checks
- **THEN** the workflow attempts safe markdown auto-fixes first using the configured markdown lint tooling
- **AND** any auto-fixed Markdown files are re-staged automatically
- **AND** markdown lint still runs afterward to fail on remaining non-fixable issues
