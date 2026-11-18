## ADDED Requirements

### Requirement: Official managed modules match the incident cutoff

The CLI SHALL install and load an official module only when its identity, version and computed artifact bytes match the pinned release inventory. Archive admission SHALL verify bytes before extraction, and filesystem admission SHALL verify installed content before it can be used. A legacy signature SHALL NOT authorize a version or artifact absent from the inventory.
Workspace module registration SHALL compare its metadata with the manifest bytes covered by the verified tree digest.

#### Scenario: Previously published artifacts remain installable

- **WHEN** a published official archive or bundled module matches the pinned inventory
- **THEN** the managed install and load paths SHALL continue to accept those bytes
- **AND** the current interpreter SHALL continue to load approved source when another supported interpreter has left a standard cache for that source

#### Scenario: A changed or newer artifact is refused

- **WHEN** an official module version or its computed bytes do not match the inventory
- **THEN** the CLI SHALL reject it before extracting an untrusted archive or running module code
