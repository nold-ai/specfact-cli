## ADDED Requirements

### Requirement: Core docs declare current and target docs ownership boundaries

The documentation SHALL state which documentation concerns remain owned by `specfact-cli` core, which concerns belong to marketplace-installed module bundles, and that module-specific docs are temporarily still hosted in the core docs set until they are migrated to `specfact-cli-modules`.

#### Scenario: Reader checks docs ownership model

- **WHEN** a reader opens the README, docs landing page, or module architecture/development documentation
- **THEN** the docs explain that core runtime, installation, lifecycle, registry, and marketplace concepts remain documented in `specfact-cli`
- **AND** they explain that bundle-specific command and workflow docs are temporarily hosted there but are intended to migrate to `specfact-cli-modules`

### Requirement: Module-specific docs carry a migration note while hosted in core

Any live module-specific guide or reference page that remains in `specfact-cli` SHALL include a consistent note that the page is temporarily hosted in core and is planned to migrate to the modules repository.

#### Scenario: Reader opens a bundle-focused page

- **WHEN** a reader opens a module- or bundle-focused guide in the core docs set
- **THEN** the page includes a visible note about temporary hosting in `specfact-cli`
- **AND** the note points to `specfact-cli-modules` as the future long-term home for module-specific documentation
