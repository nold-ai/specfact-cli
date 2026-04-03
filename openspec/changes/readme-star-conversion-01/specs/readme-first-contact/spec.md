## ADDED Requirements

### Requirement: README hero leads with developer outcome and runnable proof

The repository README SHALL lead with a developer-facing value proposition and a runnable quickstart
before platform, module-system, or governance explanation. A first-time visitor must be able to
understand what SpecFact does and how to try it without scrolling through architecture prose.

#### Scenario: Visitor reads only the first screen of the README

- **WHEN** a first-time visitor opens `README.md`
- **THEN** the title SHALL be followed by a short, concrete value statement for developers
- **AND** badges SHALL appear directly under the title / tagline block
- **AND** the README SHALL show a uvx-based quickstart in the first screenful
- **AND** the README SHALL include a visible CTA inviting the user to star the repo if the output is
  useful

#### Scenario: README defers enterprise framing

- **WHEN** a user scans the README from the top
- **THEN** enterprise, governance, module-marketplace, and architecture framing SHALL appear only
  after the quickstart, sample output, and concrete feature summary
- **AND** the README SHALL still preserve those deeper sections further down the page

### Requirement: README includes real sample output with reproducible evidence

The README SHALL include a sample output block derived from a real `specfact code review run`
capture, not hand-written illustrative output. The proof block SHALL help the reader mentally
simulate running the command.

#### Scenario: Visitor evaluates whether the tool feels real

- **WHEN** a visitor reads the quickstart section
- **THEN** the README SHALL display a sample output block that includes a verdict, a score or status,
  file-level findings, and an evidence bundle path
- **AND** the output SHALL be sourced from a checked-in capture artifact under
  `evidence/readme-sample-output/`
- **AND** the repo SHALL include a capture script that reproduces or refreshes the stored output

### Requirement: README explains value before deep product detail

The README SHALL include an explicit "what it does" summary for developers before it explains
organizational workflows, module ownership, or documentation topology.

#### Scenario: Visitor wants concrete reasons to care

- **WHEN** the visitor reaches the section immediately after the quickstart and proof block
- **THEN** the README SHALL summarize the product in concrete outcome bullets
- **AND** those bullets SHALL focus on developer-visible outcomes such as review, validation, drift
  detection, offline use, and backlog/code alignment
- **AND** deeper sections for pipeline story, team use, module system, and documentation topology
  SHALL appear later on the page

### Requirement: README shows adoption path beyond the hero

The README SHALL provide copy-pasteable adoption examples for local hooks and CI without forcing the
reader into the full documentation set first.

#### Scenario: Visitor wants to move from trial to workflow

- **WHEN** a developer finds the quickstart useful
- **THEN** the README SHALL include a short pre-commit or GitHub Actions snippet near the upper half
  of the document
- **AND** the README SHALL include a brief "How SpecFact is built" or equivalent trust section that
  explains the repo's OpenSpec -> TDD -> quality-gate workflow in plain language
