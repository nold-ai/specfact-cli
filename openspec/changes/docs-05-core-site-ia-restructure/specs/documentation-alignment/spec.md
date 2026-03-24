# Delta: documentation-alignment

Extends the existing `documentation-alignment` capability with core-only site focus and module redirect policy.

## New Scenarios

### Scenario: Core docs site excludes module-specific workflow content

- **GIVEN** the core docs site at docs.specfact.io
- **WHEN** a reader browses guides and tutorials
- **THEN** module-specific tutorials (backlog quickstart, standup, refine) are NOT present in the core site
- **AND** those topics link to the canonical modules site at modules.specfact.io

### Scenario: Core site landing page delineates core vs modules

- **GIVEN** the docs.specfact.io landing page (index.md)
- **WHEN** a reader arrives at the docs home
- **THEN** the page clearly separates core platform concerns from module-specific workflows
- **AND** provides direct links to modules.specfact.io for bundle-specific guidance

### Scenario: Getting Started section focuses on platform bootstrap

- **GIVEN** the Getting Started section of the core docs
- **WHEN** a new user follows the getting started path
- **THEN** it covers installation, quickstart, and profiles/IDE setup
- **AND** does NOT include module-specific tutorials as inline content
- **AND** links to modules.specfact.io for module workflow tutorials
