## ADDED Requirements

### Requirement: Entry-point messaging hierarchy is documented

Contributor-facing documentation SHALL define the required messaging hierarchy for first-contact
surfaces so README and homepage edits preserve the same structure over time.

#### Scenario: Contributor updates an entry-point page

- **WHEN** a contributor edits `README.md`, `docs/index.md`, or other designated entry-point copy
- **THEN** the guidance SHALL require them to preserve the ordering of:
  - product identity
  - why it exists
  - user value
  - how to start
  - deeper topology and branching guidance
- **AND** the guidance SHALL define validation/alignment as the product core, with “keep backlog,
  specs, tests, and code in sync” expressed as the user-visible result

### Requirement: Cross-site handoff copy stays aligned

Documentation alignment rules SHALL require core-docs and modules-docs entry points to describe the
same ownership split and onboarding handoff.

#### Scenario: Contributor edits core or modules landing copy

- **WHEN** a contributor updates landing-page copy that references `docs.specfact.io` or
  `modules.specfact.io`
- **THEN** the wording SHALL preserve the same explanation of what belongs to the core docs versus
  the modules docs
- **AND** cross-site links SHALL direct users to the intended next step rather than only the raw site
  URL

### Requirement: First-contact copy encodes the key user questions

Contributor guidance SHALL require entry-point copy to answer the key first-contact questions
explicitly enough that maintainers can review the page against them.

#### Scenario: Maintainer reviews a rewritten entry-point page

- **WHEN** a maintainer reviews changes to an entry-point page
- **THEN** they SHALL be able to verify that the page clearly answers:
  - what SpecFact is
  - why it exists
  - why a user should use it
  - what the user gets
  - how the user gets started
- **AND** the page SHALL not bury those answers underneath topology or implementation details
