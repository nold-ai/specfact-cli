## ADDED Requirements

### Requirement: Privileged dependency caches are non-persistent

Repository workflows that execute separately checked-out fixture code SHALL NOT
restore or save persistent package-manager caches in the same job. Advisory
compatibility jobs SHALL execute only from protected scheduled workflow bytes
and SHALL verify the fixture commit and tree before exporting its path.

#### Scenario: Shared frozen setup disables persistent uv caching

- **GIVEN** a required or advisory job uses the shared frozen Python setup
- **WHEN** the setup action installs the committed dependency graph
- **THEN** setup-uv SHALL have caching disabled
- **AND** later fixture execution SHALL NOT receive a persistent cache save capability.

#### Scenario: Compatibility fixture is schedule-only and immutable

- **GIVEN** the repository runs the optional dependency compatibility lane
- **WHEN** the workflow checks out the companion module fixture
- **THEN** the lane SHALL be reachable only from the scheduled event
- **AND** the checked-out commit and tree SHALL equal the committed fixture lock
- **AND** the module path SHALL be exported only after both checks pass.

#### Scenario: Post-fixture Node setup does not restore npm state

- **GIVEN** a workflow has already checked out or executed companion fixture code
- **WHEN** it installs the committed Code Review Node dependencies
- **THEN** the Node setup SHALL NOT restore or save a persistent npm cache.
