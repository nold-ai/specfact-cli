## ADDED Requirements

### Requirement: Metadata-only final review needs no artifact

The required Requirements workflow SHALL record when final changed-path
discovery finds no existing changed Python target and SHALL NOT require a final
Code Review artifact for that intentional no-review outcome.

#### Scenario: Metadata-only final review needs no artifact

- **GIVEN** final changed-path discovery succeeds
- **AND** no existing changed `*.py` or `*.pyi` target is present
- **WHEN** the final Code Review stage completes
- **THEN** it SHALL record that review was not required
- **AND** it SHALL NOT require a final Code Review artifact.

### Requirement: Python final review requires strict artifact

The required Requirements workflow SHALL declare final Code Review mandatory
before it invokes the reviewer for one or more existing changed Python targets,
and SHALL fail if the expected review artifact is absent.

#### Scenario: Python final review requires strict artifact

- **GIVEN** final changed-path discovery identifies at least one existing Python
  target
- **WHEN** the final Code Review stage starts review execution
- **THEN** it SHALL record that review is required before invoking the reviewer
- **AND** the final artifact upload SHALL fail if the expected report is absent.

### Requirement: Final review failure blocks Requirements

The required Requirements workflow SHALL retain final review output when
available and SHALL keep the Requirements verdict non-green whenever final Code
Review fails.

#### Scenario: Final review failure blocks Requirements

- **GIVEN** final Code Review is required
- **WHEN** review execution fails
- **THEN** the workflow SHALL attempt to retain the final report
- **AND** the final Requirements verdict SHALL remain non-green
- **AND** neither conditional upload nor a missing output SHALL suppress verdict
  enforcement.
