## ADDED Requirements

### Requirement: Documentation uses its own immutable module source

Core Docs Review SHALL use a dedicated reviewed module repository, commit and tree identity for command generation, independently of the approved Requirements execution fixture.

#### Scenario: Documentation adopts an additive module command release

- **GIVEN** a reviewed immutable module source adds documented command paths or options
- **WHEN** Docs Review materializes its documentation source
- **THEN** it SHALL verify the repository, full commit and tree before importing module source
- **AND** it SHALL generate and freshness-check core JSON, Markdown and llms command artifacts against that source
- **AND** the Requirements fixture and its independently approved commit/tree SHALL remain unchanged

#### Scenario: Documentation fixture does not match its declaration

- **GIVEN** documentation module source has a mutable reference or mismatched repository, commit or tree
- **WHEN** Docs Review verifies its input
- **THEN** it SHALL fail before executing the command generator
- **AND** it SHALL NOT fall back to an unverified source checkout

### Requirement: Code Review command parity includes options and subgroups

Core documentation validation SHALL compare the Code Review command surface with its reviewed module source, including command paths, arguments, ordinary options and subgroup names.

#### Scenario: Portable runtime entries are omitted from the core contract

- **GIVEN** the selected Code Review module exposes runtime inspect/prepare and review run project-config/project-runtime options
- **WHEN** any corresponding entry is absent or differs in the core generated contract
- **THEN** the core documentation validation SHALL fail with the mismatched command
- **AND** legitimate standalone versus mounted Typer completion switches SHALL NOT count as ordinary command drift

#### Scenario: CLI documentation validation uses the same reviewed source

- **GIVEN** core CLI Command Validation checks generated command documentation
- **WHEN** the job selects its module source
- **THEN** it SHALL use the independent documentation fixture and verify its repository, commit, tree and clean checkout before importing source
- **AND** Docs Review and CLI Command Validation SHALL require explicit documentation source context and run command parity and freshness checks
- **AND** unrelated test and Requirements jobs using the approved execution fixture SHALL NOT compare newer documentation with that older source

#### Scenario: Positional arguments survive Click and Typer parameter representations

- **GIVEN** a command declares optional or required positional arguments, including variadic file selection
- **WHEN** the core generator inspects Click or Typer command parameters
- **THEN** its contract SHALL preserve each argument's display name, required status and arity
- **AND** the presence of an internal opts attribute on an argument SHALL NOT cause its omission
- **AND** options SHALL NOT appear as positional arguments

#### Scenario: Local documentation generation retains separate Requirements authority

- **GIVEN** a local commit uses the approved Requirements execution fixture and separately selects SPECFACT_DOCS_MODULES_REPO
- **WHEN** command artifacts are generated, freshness-checked or validated against live command behavior
- **THEN** the generator and command contract validator SHALL use only the explicitly selected documentation module source
- **AND** an empty, unavailable or invalid explicit documentation source SHALL fail instead of using the Requirements fixture
- **AND** callers without an explicit documentation source SHALL retain existing module-source discovery

#### Scenario: Mandatory CI exercises parity without adopting documentation source

- **GIVEN** ordinary test jobs retain the approved execution fixture and do not expose the documentation source context
- **WHEN** mandatory CI tests the parity mechanism
- **THEN** a self-contained generated-contract fixture SHALL exercise rejection of missing paths, ordinary options, arguments and subgroup entries
- **AND** these self-contained controls SHALL execute without skipping for a missing external documentation checkout
- **AND** passing preservation controls and parity fault-injection controls SHALL remain mandatory CI checks independently of the failing-first Requirements selector mapping
- **AND** signed-source parity SHALL remain required in Docs Review and CLI Command Validation

### Requirement: Documentation CI authenticates external module payloads before imports

Docs Review and CLI Command Validation SHALL verify publisher signatures and filesystem payload checksums for every external module source they expose, using the canonical verifier and public key from a separate immutable core base checkout. Local generator source discovery and the approved Requirements execution fixture SHALL remain unchanged.

#### Scenario: An immutable documentation fixture lacks authentic payload evidence

- **GIVEN** the external fixture matches its declared repository, commit and tree and has a clean checkout
- **WHEN** either documentation CI job prepares to export or import its module source
- **THEN** it SHALL reject absent or invalid signatures, wrong signing keys, changed filesystem payloads and missing required bundle manifests
- **AND** verification SHALL require signatures, filesystem payload hashing and checksums even when relaxed PR signature-policy environment variables are present
- **AND** the verifier and public key SHALL come from the core base checkout rather than the selected external source
- **AND** source export and command imports SHALL occur only after that verification succeeds

#### Scenario: Valid signed documentation source is admitted without changing execution authority

- **GIVEN** all expected imported bundles have valid signatures and matching filesystem payloads
- **WHEN** documentation CI authenticates them against its separate trusted core verifier and public key
- **THEN** the jobs SHALL admit that fixture for command parity and freshness checks
- **AND** the Requirements fixture and its approval authority SHALL remain unchanged
