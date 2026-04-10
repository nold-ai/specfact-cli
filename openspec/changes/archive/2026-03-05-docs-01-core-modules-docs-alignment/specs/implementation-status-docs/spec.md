## ADDED Requirements

### Requirement: Implementation-status docs describe core versus bundle ownership

Implementation-status and architecture status documentation SHALL explicitly describe which capabilities are owned by core runtime versus marketplace-installed bundles, and SHALL identify documentation that is still temporarily hosted in core despite belonging to bundle workflows.

#### Scenario: Reader checks ownership in status docs

- **WHEN** a reader reviews implementation-status or architecture status pages
- **THEN** the docs distinguish core lifecycle/runtime ownership from bundle workflow ownership
- **AND** temporary docs-hosting exceptions are called out so documentation location does not imply incorrect runtime ownership
