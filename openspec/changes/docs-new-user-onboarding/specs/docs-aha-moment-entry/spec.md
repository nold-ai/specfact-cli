## ADDED Requirements

### Requirement: Homepage names `code review run` as the primary entry command

The docs homepage SHALL explicitly name `specfact code review run` as the primary command for the
"review your code" use case. The command SHALL appear in the hero section before any path cards,
module system explanations, or architecture descriptions.

#### Scenario: Vibe coder arrives at the homepage

- **WHEN** a first-time visitor who heard "validate your vibe code with specfact" lands on
  docs.specfact.io
- **THEN** the homepage SHALL display a fenced code block showing:
  `uvx specfact-cli init --profile solo-developer` and
  `uvx specfact-cli code review run --path . --scope full`
  as the 2-command entry sequence
- **AND** the block SHALL appear before any path cards, architecture sections, or module links
- **AND** the expected output (scored review result with findings) SHALL be described adjacent to
  the block so the user knows what they will see before running the commands

#### Scenario: Visitor can start without navigating away

- **WHEN** a visitor reads only the homepage without clicking any link
- **THEN** they SHALL have all commands needed to run their first code review
- **AND** no prior Python or pip knowledge SHALL be required to understand or run those commands

### Requirement: Path cards name user outcomes in plain language

The "Choose your path" cards on the homepage SHALL use plain language that a non-Python-expert
can understand. Each card heading SHALL describe what the user will achieve immediately.

#### Scenario: Vibe coder reads card headings

- **WHEN** a vibe coder with no prior SpecFact knowledge reads the path card headings
- **THEN** the first card heading SHALL be oriented toward reviewing existing code immediately
  (e.g. "See what's wrong with your code right now")
- **AND** no heading SHALL use internal labels such as "Greenfield & AI-assisted delivery",
  "Brownfield and reverse engineering", "Backlog to code alignment", or "Team and policy enforcement"
  as the primary title
- **AND** each card body SHALL describe the user outcome and the key command, not the product
  architecture or module name

#### Scenario: User with no prior SpecFact knowledge selects a path

- **WHEN** a user with no prior SpecFact knowledge reads the three path cards
- **THEN** they SHALL be able to identify which card matches their immediate goal without
  understanding SpecFact's internal module or bundle architecture

### Requirement: Architectural jargon deferred below the fold

Terms describing internal platform architecture SHALL NOT appear in the above-the-fold hero content
of the homepage. They may appear in Architecture, Reference, or Module System sections lower on
the page.

#### Scenario: Above-the-fold homepage content audit

- **WHEN** the homepage is rendered at a standard viewport (1280×800)
- **THEN** the visible content SHALL NOT include any of the following terms before the user scrolls:
  "module discovery", "registry bootstrapping", "publisher trust", "mounted workflow groups",
  "runtime contracts" (used as a section label or navigation entry)
- **AND** those terms MAY appear in Architecture or Reference sections below the fold

### Requirement: Installation page promotes uvx as the no-install entry path

The installation page SHALL present the uvx invocation as the primary "try it now" path for new
users, without a "Limitations" warning that discourages its use.

#### Scenario: New user opens the installation page

- **WHEN** a first-time user opens the installation page
- **THEN** the first visible section SHALL present the uvx 2-command sequence
  (init + code review run) under a heading such as "Try it now — no install required"
- **AND** the section SHALL NOT include a "Limitations" warning about the uvx path
- **AND** pip installation SHALL appear in a clearly labelled secondary section
  ("Install for persistent use" or equivalent)

#### Scenario: User wants to find alternative installation methods

- **WHEN** a user wants to find Container or GitHub Action installation options
- **THEN** a visible section heading or anchor link SHALL allow them to jump to those options
  without reading through the uvx or pip sections first
