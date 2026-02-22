# documentation-alignment Specification

Documentation accurately reflects current implementation so that contributors and users are not misled.

## ADDED Requirements

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
