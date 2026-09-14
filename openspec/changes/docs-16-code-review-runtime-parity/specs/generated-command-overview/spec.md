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

#### Scenario: Requirements proof exercises parity without adopting documentation source

- **GIVEN** Requirements proof retains its approved execution fixture and does not expose the documentation source context
- **WHEN** the parity mechanism is tested within that proof
- **THEN** a self-contained generated-contract fixture SHALL exercise rejection of missing paths, ordinary options, arguments and subgroup entries
- **AND** the proof SHALL execute without skipping for a missing external documentation checkout
- **AND** signed-source parity SHALL remain required in Docs Review and CLI Command Validation
