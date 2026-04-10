# module-docs-ownership Specification

## Purpose

TBD - created by archiving change docs-01-core-modules-docs-alignment. Update Purpose after archive.

## Requirements

### Requirement: Core docs declare current and target docs ownership boundaries

The documentation SHALL state which documentation concerns remain owned by `specfact-cli` core, which concerns belong to marketplace-installed module bundles, and that module-specific deep docs are canonically owned by `specfact-cli-modules` once published there.

#### Scenario: Reader checks docs ownership model

- **WHEN** a reader opens the README, docs landing page, or module architecture/development documentation
- **THEN** the docs explain that core runtime, installation, lifecycle, registry, and marketplace concepts remain documented in `specfact-cli`
- **AND** they explain that bundle-specific command and workflow docs are canonically owned by `specfact-cli-modules`
- **AND** they do not describe the core docs set as the permanent home for module-specific deep guidance.

### Requirement: Module-specific docs carry a migration note while hosted in core

Any live module-specific guide or reference page that remains in `specfact-cli` SHALL either provide core-owned overview context or a clear handoff to the canonical modules docs page.

#### Scenario: Reader opens a bundle-focused page in core docs

- **WHEN** a reader opens a module- or bundle-focused guide in the core docs set
- **THEN** the page states whether it is a core-owned overview or a temporary handoff page
- **AND** the page links the reader to the canonical modules docs destination when module-specific deep guidance lives there.

### Requirement: Canonical modules URLs are discoverable from core docs

The core documentation set SHALL include a short reference page that explains the core vs modules URL relationship and points to the authoritative contract on `modules.specfact.io`.

#### Scenario: Contributor looks up how to link to modules

- **WHEN** a contributor needs to add or verify a cross-site link
- **THEN** they can open `docs/reference/documentation-url-contract.md` in this repository for obligations and a link to the full contract on the modules site
