# entrypoint-onboarding Specification

## Purpose
TBD - created by archiving change docs-14-first-contact-story-and-onboarding. Update Purpose after archive.
## Requirements
### Requirement: One primary fast-start path

The central entry points SHALL provide one primary “start here now” path before branching into more
specialized persona or workflow guidance.

#### Scenario: User wants to try SpecFact immediately

- **WHEN** a first-time visitor reaches the primary getting-started section
- **THEN** the page SHALL provide one recommended install-and-first-run path
- **AND** that path SHALL appear before alternative personas, workflow branches, or topology details
- **AND** the path SHALL make the first value explicit rather than only listing commands

### Requirement: Choose-your-path guidance follows the first-run path

After the primary fast-start path, entry points SHALL route users into the most relevant next step
for their intent.

#### Scenario: User needs the right next path

- **WHEN** the user completes or reviews the first-run path
- **THEN** the entry point SHALL offer clear next-step options for at least:
  - greenfield or AI-assisted development that needs stronger validation
  - brownfield or legacy code understanding and reverse-engineering
  - backlog/spec/code alignment workflows
- **AND** each option SHALL describe the user outcome, not just the internal command group

### Requirement: Brownfield path explains the spec-first handoff

Brownfield onboarding SHALL explain that SpecFact helps extract trustworthy understanding from
existing systems and feed that understanding into spec-first workflows.

#### Scenario: User evaluates the brownfield path

- **WHEN** a user reads the brownfield or existing-codebase onboarding path
- **THEN** the path SHALL explain that SpecFact analyzes the codebase and sidecar context to produce
  structured insight
- **AND** it SHALL explain that this insight can be handed into spec-first tools such as OpenSpec or
  Spec-Kit to create accurate specs and reduce drift

### Requirement: Core-versus-modules handoff is explicit

The entry points SHALL explain that `docs.specfact.io` is the default starting point and
`modules.specfact.io` is the deeper module- and workflow-specific documentation surface.

#### Scenario: New user lands on modules docs

- **WHEN** a first-time visitor reaches `modules.specfact.io`
- **THEN** the page SHALL explain that module docs are the deeper workflow layer
- **AND** it SHALL direct users back to the core docs if they still need orientation or the initial
  getting-started flow
- **AND** it SHALL clarify that bundle-deep workflows build on the same validation/alignment story

#### Scenario: Core docs hand off to module-deep guidance

- **WHEN** a user outgrows the core landing guidance and needs workflow- or bundle-specific help
- **THEN** the core docs SHALL provide a clear, explicit handoff to `modules.specfact.io`
- **AND** the handoff SHALL explain what extra value the modules docs provide

