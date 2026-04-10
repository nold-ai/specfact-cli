# first-contact-story Specification

## Purpose

TBD - created by archiving change docs-14-first-contact-story-and-onboarding. Update Purpose after archive.

## Requirements

### Requirement: Canonical first-contact product story

The repository and documentation entry points SHALL present one canonical product story that answers
the first-contact questions for both vibe coders and experienced developers. The hero statement SHALL
use plain language that works for a developer who does not know Python packaging — not just for
someone already familiar with contracts, modules, and runtimes.

The canonical answer to "what is SpecFact?" SHALL describe what the user gets immediately
("a score and a list of what to fix") before explaining how it is achieved internally.

#### Scenario: Vibe coder reads the homepage hero

- **WHEN** a developer who primarily uses AI-assisted or no-code tools reads the homepage hero
- **THEN** the first sentence SHALL describe an outcome they will recognise
  (e.g. "Point it at your code. Get a score and a list of what to fix.")
- **AND** the hero SHALL NOT open with "validation and alignment layer", "runtime contracts",
  or any other phrase that requires prior familiarity with the product

#### Scenario: User compares repo and docs entry points

- **WHEN** a user reads the repo README and the core docs homepage
- **THEN** both SHALL describe the same core product identity
- **AND** they SHALL NOT give conflicting first impressions about whether SpecFact is primarily
  a CLI, a module platform, an AI tool, or a backlog tool

#### Scenario: Hero statement pairs identity with a concrete, time-bounded outcome

- **WHEN** a first-time visitor reads the hero on the docs homepage or README
- **THEN** the primary headline or subheadline SHALL communicate a concrete achievable outcome
  with a time signal (e.g. "See what's wrong with your code in 10 seconds")
- **AND** the outcome statement SHALL appear before any explanation of internal architecture,
  module system, or platform topology
- **AND** the hero SHALL include or link directly to the runnable 2-command uvx sequence

### Requirement: First-contact story explains the four product pressures

The first-contact story SHALL explain why SpecFact exists by grounding it in the main delivery
pressures it addresses.

#### Scenario: User asks why SpecFact exists

- **WHEN** a first-time visitor reads the “why” section of the README or core docs landing page
- **THEN** the page SHALL explain that SpecFact addresses:

  - AI-assisted or vibe-coded changes that need stronger validation
  - brownfield systems that need reverse-engineered understanding
  - backlog/spec/code drift that causes “I wanted X but got Y”
  - team and enterprise policy inconsistency across developers and CI
- **AND** the wording SHALL present those pressures as reasons the product exists, not as an
  unstructured feature list

### Requirement: Headline and proof-point separation

First-contact surfaces SHALL keep the primary identity statement separate from supporting proof
points. Platform-internal vocabulary SHALL NOT appear in the hero or primary identity statement.
The hero SHALL work for a non-Python-expert; advanced vocabulary may appear in proof-point
sections below the hero.

#### Scenario: User scans the first screen

- **WHEN** a user scans the first screen of the README or docs homepage
- **THEN** the primary message SHALL fit in a short headline/subheadline structure
- **AND** secondary capability claims (contracts, SDD/TDD, brownfield, module extensibility)
  SHALL appear as proof points after the hero, not as headline overload
- **AND** platform-internal architectural terms SHALL NOT appear in the above-the-fold hero

#### Scenario: Experienced developer also finds their next step

- **WHEN** an experienced Python developer reads the homepage after the hero section
- **THEN** they SHALL find links to the pip installation path, profile options, and deeper
  technical documentation without needing to search for them
- **AND** the progressive depth SHALL be clearly layered: vibe-coder entry → developer setup →
  advanced configuration

### Requirement: Future enterprise direction reinforces seriousness without narrowing adoption

First-contact messaging SHALL describe centralized policy management as a scale-up path for teams and
enterprises without implying that SpecFact only makes sense for large organizations.

#### Scenario: User scans enterprise and governance messaging

- **WHEN** a visitor reads first-contact copy that mentions policy enforcement or future account/back-end support
- **THEN** the copy SHALL present that capability as an extension of the same validation/alignment story
- **AND** it SHALL preserve the message that solo developers and smaller teams can adopt SpecFact immediately

### Requirement: Repo metadata reinforces the same story

GitHub-facing repository metadata SHALL reinforce the same first-contact story used in the README and
docs landing pages.

#### Scenario: User sees the repository before opening the README

- **WHEN** a visitor sees the repository description, topics, badges, and other above-the-fold repo
  cues
- **THEN** those cues SHALL reinforce the same core identity as the README hero
- **AND** they SHALL not emphasize internal topology ahead of user value

Cross-repo traceability note: `modules.specfact.io` and the
`nold-ai/specfact-cli-modules` `docs/index.md` SHALL either present the same first-contact story or
provide an explicit handoff to the core docs. See `documentation-alignment/spec.md` for ownership
and cross-site wording guidance.
