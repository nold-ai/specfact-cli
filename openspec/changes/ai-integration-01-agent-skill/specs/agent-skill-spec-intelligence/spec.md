## ADDED Requirements

### Requirement: Discover module-owned skills

The system SHALL discover versioned skill descriptors and assets through the same effective module discovery roots, priority, collision handling, and persisted enablement state used by command registration and `specfact init`, without defining module workflow content in core. Discovery SHALL include workspace modules and existing configured `SPECFACT_MODULES_ROOTS` entries and SHALL exclude disabled modules.

#### Scenario: Signed preflight module exposes a skill

- **GIVEN** the stable preflight module is installed and its descriptor identifies `specfact-preflight`
- **WHEN** skill discovery runs
- **THEN** the skill is listed with module, version, workflow, compatibility, and content-digest provenance
- **AND** core does not replace or reinterpret the workflow body.

#### Scenario: Workspace module exposes a skill

- **GIVEN** an enabled trusted module exposed by the shared effective workspace-module-root resolver provides a valid skill descriptor
- **WHEN** skill discovery runs for that workspace
- **THEN** the skill is discovered through the shared module discovery contract
- **AND** the resolved root, priority, and provenance exactly match command registration and `specfact init` without this skill contract naming a competing workspace path.

#### Scenario: Configured module root exposes a skill

- **GIVEN** an enabled trusted module under an existing root configured in `SPECFACT_MODULES_ROOTS` exposes a valid skill descriptor
- **WHEN** skill discovery runs
- **THEN** the skill is discovered through the shared module discovery contract
- **AND** a disabled module at that root is not exposed.

### Requirement: Canonical `.agents/skills` export

The system SHALL support canonical project export under `.agents/skills/<skill-id>/` with `SKILL.md` as the entrypoint and all supporting assets contained within the skill directory. Before materialization or inventory mutation, it SHALL reject absolute skill IDs or asset paths and any parent traversal, resolve the selected skill root, and verify every asset and inventory path remains within that root.

#### Scenario: Skill is exported to a project

- **GIVEN** a verified module-owned skill and a writable project target
- **WHEN** canonical export is approved
- **THEN** the exact verified assets are materialized under `.agents/skills/<skill-id>/`
- **AND** the install inventory records every path and digest.

#### Scenario: Descriptor path escapes the selected skill root

- **GIVEN** a descriptor contains an absolute skill ID or asset path, parent traversal, or a resolved asset/inventory path outside `.agents/skills/<skill-id>/`
- **WHEN** install, update, or uninstall validates the descriptor
- **THEN** the operation fails before any project or inventory write or removal
- **AND** unrelated project files remain unchanged.

### Requirement: Deterministic install and update

Skill installation and update SHALL be idempotent for identical verified input and SHALL fail safely on incompatible or user-modified assets.

#### Scenario: Identical skill is installed twice

- **GIVEN** the installed inventory and target files match the requested skill identity and digests
- **WHEN** installation runs again
- **THEN** no duplicate files or instruction blocks are created
- **AND** the result reports the installation already current.

#### Scenario: User modified an installed asset

- **GIVEN** a target file differs from its recorded installed digest
- **WHEN** update is requested without an explicit conflict decision
- **THEN** the update stops and reports the drift
- **AND** the user file remains unchanged.

### Requirement: Skill identity collisions fail closed

The system SHALL not silently install two different module skill identities under one canonical skill ID.

#### Scenario: Two modules claim one skill ID

- **GIVEN** discovered descriptors claim the same canonical skill ID with different content or owners
- **WHEN** installation is resolved
- **THEN** installation is blocked with both identities
- **AND** no arbitrary precedence is selected.

### Requirement: Safe uninstall

Uninstall SHALL remove only inventory-owned files whose current identities match the installed record.

#### Scenario: Uninstall encounters unrelated assets

- **GIVEN** the target skill directory contains an unrecorded file
- **WHEN** uninstall runs
- **THEN** the unrecorded file is preserved
- **AND** any resulting non-empty directory is reported for user review.

### Requirement: Distribution-only ownership

The installer SHALL expose module-owned skills to compatible consumers without executing validators, approving changes, generating preflight seals, or packaging external harness adapters.

#### Scenario: Preflight skill is installed

- **GIVEN** `specfact-preflight` is exported successfully
- **WHEN** installation completes
- **THEN** the result reports the installed workflow identity and supported invocation metadata
- **AND** no preflight run or source-artifact edit is triggered.
