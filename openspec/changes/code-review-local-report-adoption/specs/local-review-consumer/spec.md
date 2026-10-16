## ADDED Requirements

### Requirement: Explicit report schema dispatch

Core SHALL dispatch only through explicitly supported report contracts and versions, support historical 1.6 only where supported, and reject any unrecognized version, including an unsupported minor version within a known major. A numeric >=1.6 branch SHALL NOT classify schema 2.0 as 1.6. Consumers governed by the separate C15 contract SHALL retain explicit schema 1.7 dispatch and C15 enforcement until its owner authorizes a separate retirement cutover. This change SHALL NOT enable C15 or alter its acceptance.

#### Scenario: Select the schema 2.0 consumer

- **GIVEN** a valid local schema 2.0 report
- **WHEN** an ordinary core consumer reads the report
- **THEN** it selects the schema 2.0 contract and does not apply historical 1.6 semantics

#### Scenario: Bound historical support

- **GIVEN** a historical 1.6 report at a consumer that supports it
- **WHEN** the consumer dispatches by version
- **THEN** it uses only supported historical semantics

#### Scenario: Preserve separate C15 dispatch

- **GIVEN** a schema 1.7 report reaches a consumer governed by the C15 contract
- **WHEN** ordinary schema 2.0 adoption is evaluated before a separately authorized C15 retirement
- **THEN** the consumer retains schema 1.7 dispatch and C15 enforcement without treating the report as schema 1.6 or schema 2.0 evidence
- **AND** this local adoption does not enable C15 or change its owners, prerequisites, status or acceptance

#### Scenario: Reject unsupported same-major schemas

- **GIVEN** an ordinary consumer supports only the released local 2.0 and bounded historical 1.6 contracts, and is not governed by C15
- **WHEN** it receives schema 1.7, an unknown 1.x version or an unrecognized 2.x version
- **THEN** it rejects that version without routing it through 1.6 or 2.0 semantics or claiming successful assurance

#### Scenario: Reject unsupported evidence

- **GIVEN** an unsupported major version or malformed required report data
- **WHEN** the consumer parses the report
- **THEN** it rejects the input without claiming successful assurance

### Requirement: Preserve authoritative local truth

Core SHALL consume producer assurance and completeness independently of score and fixability. Shadow mode SHALL preserve adverse truth and SHALL NOT claim protected PR authority.

#### Scenario: Preserve incomplete shadow results

- **GIVEN** producer failure, uncertainty, or incomplete evidence in shadow mode
- **WHEN** core renders the local result
- **THEN** the summary and machine evidence retain the adverse truth even when enforcement is non-blocking

#### Scenario: Reject score based success

- **GIVEN** a favorable score or fixability alongside adverse assurance or contradictory process evidence
- **WHEN** core decides the local result
- **THEN** it does not replace producer assurance and completeness with success

### Requirement: Separate installed CLI and project runtime

Core SHALL preserve externally installed CLI and project Python separation, supported installation tooling, signed compatibility, and project-runtime descriptor semantics. Ordinary local invocation SHALL use the project-aware local runner without capsule acquisition or execution. Once required signed artifacts and execution prerequisites are provisioned and locally verified, ordinary local review SHALL run without requiring network access.

#### Scenario: Run an externally installed CLI

- **GIVEN** a supported signed core/module pair installed by pipx, uv tool, or uvx and a different project Python
- **WHEN** ordinary local review runs
- **THEN** core loads the compatible module while modules resolve the trusted project runtime without injecting dependencies into the project environment

#### Scenario: Run ordinary local review without capsules

- **GIVEN** a supported externally installed signed CLI/module pair, a selected project environment and no capsule runtime, catalog or acquisition service
- **WHEN** the customer invokes ordinary trusted local review
- **THEN** core invokes the project-aware local runner and selected checks execute without capsule provisioning, a sandbox broker or a legacy host orchestrator
- **AND** protected and C15 consumers retain their separately governed contracts

#### Scenario: Run from verified local artifacts offline

- **GIVEN** an externally installed compatible CLI/module pair, valid locally verified signed modules, a prepared project environment and all selected check tools are available locally
- **WHEN** networking is disabled and ordinary local review runs
- **THEN** loading and invocation use those artifacts without requiring a registry or package-index lookup and the selected checks execute
- **AND** missing local prerequisites remain actionable preparation failures rather than claimed offline bootstrap support

#### Scenario: Handle uvx without pip

- **GIVEN** a uvx tool environment without pip
- **WHEN** installation compatibility provisions required tool dependencies
- **THEN** it uses supported external tooling or declarations rather than unmanaged mutation

#### Scenario: Preserve the runtime descriptor

- **GIVEN** a supported --project-runtime descriptor
- **WHEN** core invokes the module
- **THEN** it forwards descriptor semantics without treating the value as an interpreter path

### Requirement: Keep protected contracts and independent gates separate

Core SHALL retain protected #680 and C15 #679/modules #417 contracts and independent security/signature gates. Local adoption SHALL NOT introduce blanket optional-addon blockers.

#### Scenario: Retain separate protected acceptance

- **GIVEN** a local schema 2.0 report
- **WHEN** a protected #680 or C15 #679 consumer is considered
- **THEN** local evidence does not satisfy the protected capsule contract or change C15 owners, status, or acceptance

#### Scenario: Retain independent security and signatures

- **GIVEN** ordinary local adoption and optional downstream consumers
- **WHEN** implementation readiness is evaluated
- **THEN** signing and independent security gates remain while optional preflight, architecture, and Requirements addons create no blanket blockers
