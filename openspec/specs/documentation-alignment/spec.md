# documentation-alignment Specification

## Purpose
TBD - created by archiving change arch-08-documentation-discrepancies-remediation. Update Purpose after archive.
## Requirements
### Requirement: Module system status in docs

The published architecture documentation SHALL state that the module system is production-ready (e.g. since v0.27) and SHALL NOT describe it as "transitioning" or "experimental."

#### Scenario: Reader checks module system status
- **GIVEN** the published architecture documentation (e.g. docs/reference/architecture.md, docs/architecture/module-system.md)
- **WHEN** a reader looks for the current state of the module system
- **THEN** the docs state production-ready status
- **AND** do not use "transitioning" or "experimental" for the module system

### Requirement: BridgeAdapter interface documented

The adapter documentation SHALL include the full BridgeAdapter interface: detect, import_artifact, export_artifact, load_change_tracking, save_change_tracking (or equivalent), with current behavior and contracts.

#### Scenario: Developer implements BridgeAdapter
- **GIVEN** the adapter documentation
- **WHEN** a developer implements or extends a BridgeAdapter
- **THEN** the documented interface includes all methods above
- **AND** contracts and usage are described

### Requirement: Architecture layers match codebase

The architecture overview SHALL describe the actual layers (Specification, Contract, Enforcement, and where relevant Adapter, Analysis, Module layers) so they match the codebase structure.

#### Scenario: Reader learns layer structure
- **GIVEN** the architecture overview
- **WHEN** a reader learns the high-level layer structure
- **THEN** the docs describe actual layers present in code
- **AND** do not omit Adapter, Analysis, or Module layers where they exist

### Requirement: Operational modes clarity

The documentation for CI/CD and CoPilot modes SHALL clarify current mode detection and any limitations (e.g. mode-specific behavior as planned), and SHALL NOT imply full mode implementations that do not exist.

#### Scenario: Reader checks mode implementation
- **GIVEN** the documentation for CI/CD and CoPilot modes
- **WHEN** a reader checks what is implemented
- **THEN** current detector behavior is stated
- **AND** planned vs implemented behavior is distinguished

### Requirement: CommandRegistry and module structure documented

The architecture or module docs SHALL describe lazy loading, metadata caching, and the required module package structure (e.g. module-package.yaml, src/<name>/main.py) and naming conventions.

#### Scenario: Developer needs registry or module layout details
- **GIVEN** the architecture or module docs
- **WHEN** a developer needs implementation details for the command registry or module layout
- **THEN** lazy loading and metadata caching are described
- **AND** required module package structure and naming are documented

### Requirement: ToolCapabilities and error handling documented

The ToolCapabilities model and adapter selection SHALL be documented; error handling patterns (custom exceptions, logging) SHALL be described in reference or adapter documentation.

#### Scenario: Developer looks for capabilities or error handling
- **GIVEN** the reference or adapter documentation
- **WHEN** a developer looks for adapter capabilities or error handling
- **THEN** ToolCapabilities and adapter selection are documented
- **AND** error handling patterns are described

### Requirement: Terminology and version consistency

The documentation set SHALL use consistent terminology (e.g. Project Bundle, Plan Bundle) and SHALL standardize or remove version references that cause confusion.

#### Scenario: Same concept referenced across docs
- **GIVEN** the documentation set
- **WHEN** the same concept is referenced
- **THEN** terminology is consistent
- **AND** version references are standardized or removed where confusing

### Requirement: Diagrams reference only existing or planned components

Any Mermaid or component diagram in the docs SHALL show only components that exist in the codebase or are clearly marked as planned; non-existent components (e.g. unimplemented "DevOps Adapters") SHALL be removed or relabeled.

#### Scenario: Reader interprets diagram
- **GIVEN** any Mermaid or component diagram in the docs
- **WHEN** a reader interprets the diagram
- **THEN** only existing or clearly planned components are shown
- **AND** non-existent components are removed or relabeled

### Requirement: Performance metrics current or removed

Any stated performance or timing in the docs SHALL reflect current benchmarks or SHALL be removed if outdated.

#### Scenario: Docs publish performance claims
- **GIVEN** any stated performance or timing (e.g. "typical execution: < 10s")
- **WHEN** the docs are published
- **THEN** metrics reflect current benchmarks or are removed if outdated

### Requirement: Live docs reflect lean-core and grouped bundle command topology

The live documentation set SHALL describe the current command surface as a lean core plus marketplace-installed grouped bundle commands, and SHALL organize navigation around a stable split between docs home, core docs, and modules docs.

#### Scenario: Reader checks command examples and navigation

- **WHEN** a reader follows command examples in README or published docs
- **THEN** core commands are shown as always available from `specfact-cli`
- **AND** bundle commands are shown through grouped command paths and marketplace installation context
- **AND** the top-level docs navigation exposes clear entry points for `Docs Home`, `Core CLI`, and `Modules`.

### Requirement: Marketplace guidance is discoverable and non-duplicative

Marketplace, bundle installation, dependency, trust, and publishing documentation SHALL be available through clear entry points and SHALL avoid contradictory or duplicate guidance across README, landing pages, guides, and reference pages.

#### Scenario: Reader looks for marketplace workflow guidance

- **WHEN** a reader wants to install, trust, publish, or understand official bundles
- **THEN** the docs provide a discoverable path from README or docs landing into marketplace-specific pages
- **AND** they provide a clear path into the modules docs site for bundle-specific deep guidance
- **AND** terminology, command examples, and workflow descriptions are consistent across those pages.

### Requirement: Command reference reflects ownership and package boundaries

The command reference documentation SHALL distinguish permanent core commands from marketplace-delivered bundle commands and SHALL organize module command coverage by package/category ownership instead of one legacy flat command inventory.

#### Scenario: Reader checks command reference

- **WHEN** a reader opens command reference documentation
- **THEN** the reference identifies which commands belong to core and which are provided by installed bundles
- **AND** bundle command coverage is grouped by category or package boundary
- **AND** readers can navigate from command docs to the relevant modules docs without ambiguity.

### Requirement: Markdown quality workflow auto-fixes low-risk issues before enforcement
The documentation workflow SHALL automatically fix low-risk Markdown issues during pre-commit checks before enforcing markdown lint failures for non-fixable or higher-risk issues.

#### Scenario: Contributor stages Markdown changes with trivial spacing issues
- **WHEN** a contributor stages Markdown files and runs the repository pre-commit checks
- **THEN** the workflow attempts safe markdown auto-fixes first using the configured markdown lint tooling
- **AND** any auto-fixed Markdown files are re-staged automatically
- **AND** markdown lint still runs afterward to fail on remaining non-fixable issues

