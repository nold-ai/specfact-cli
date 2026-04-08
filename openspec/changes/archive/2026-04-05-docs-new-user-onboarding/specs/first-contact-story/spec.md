## MODIFIED Requirements

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
