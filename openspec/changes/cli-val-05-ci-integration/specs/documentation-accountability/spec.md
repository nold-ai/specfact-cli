## ADDED Requirements

### Requirement: Official module documentation accountability SHALL derive from source authority

The documentation-accountability contract SHALL derive the set of official
module package ids and grouped command roots from the checked-out
`specfact-cli-modules` manifests and marketplace registry. It SHALL reject a
missing, unreadable, or internally inconsistent modules source rather than
falling back to a hard-coded core package list.

#### Scenario: Requirements module is an official source record

- **GIVEN** the modules source contains the official
  `nold-ai/specfact-requirements` manifest and registry entry
- **WHEN** the documentation-accountability contract builds its inventory
- **THEN** the inventory contains package id
  `nold-ai/specfact-requirements` and root command `requirements`
- **AND** the generated command overview and runtime command contract include
  that package and root.

#### Scenario: Modules source is unavailable or inconsistent

- **GIVEN** `SPECFACT_MODULES_REPO` and the documented sibling checkout cannot
  provide a valid official-module manifest and registry source
- **WHEN** the documentation-accountability contract runs locally or in CI
- **THEN** it exits non-zero with an actionable source-resolution error
- **AND** it does not silently skip validation or reuse a stale hard-coded list.

### Requirement: Core catalogues SHALL cover every official module

The documentation-accountability contract SHALL require every designated core
package catalogue, command reference, install overview, and repository-layout
page to represent every official module package and its grouped command root
where that page describes command topology. The contract SHALL report the
missing package, expected root, file, and location.

#### Scenario: A catalogue omits a shipped official module

- **GIVEN** a designated core catalogue lists other official packages but omits
  `nold-ai/specfact-requirements`
- **WHEN** the documentation-accountability contract runs
- **THEN** it exits non-zero
- **AND** identifies the catalogue file and omitted package.

### Requirement: Core and modules documentation ownership SHALL be consistent

Core overview and architecture pages SHALL accurately distinguish permanent
core runtime/lifecycle ownership from module-owned grouped command and deep
workflow documentation. They SHALL not classify an installed official grouped
command as a removed or non-canonical core surface, and required handoffs SHALL
target the canonical modules documentation path.

#### Scenario: Core architecture contradicts an installed module command

- **GIVEN** a core architecture or ownership page states that an official
  grouped command such as `specfact requirements ...` is not canonical
- **WHEN** the documentation-accountability contract runs
- **THEN** it exits non-zero and identifies the conflicting ownership claim.

### Requirement: Documentation accountability SHALL block locally and in PR CI

The same documentation-accountability command SHALL run from the always-run
local pre-commit path and from a required pull-request workflow job whenever
documentation, command-contract, module-discovery, module manifest, or
workflow inputs change.

#### Scenario: Accountability failure prevents delivery

- **GIVEN** a staged or pull-request change leaves a catalogue, generated
  command artifact, or ownership handoff inconsistent with the official-module
  inventory
- **WHEN** pre-commit or PR CI runs
- **THEN** the relevant gate exits non-zero
- **AND** the pull request cannot satisfy its required documentation check.
