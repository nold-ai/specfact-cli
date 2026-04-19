## ADDED Requirements

### Requirement: OpenTelemetry Default-On Emitter

The system SHALL emit a summary telemetry event for every CLI invocation when telemetry is enabled, using an allowlisted PII-safe payload.

#### Scenario: Default community-tier invocation emits a summary event

- **GIVEN** a community-tier installation with no explicit telemetry configuration
- **WHEN** any `specfact` command runs to completion
- **THEN** a single summary event is emitted containing only allowlisted fields
- **AND** the event records command, duration, exit code, and outcome enum.

#### Scenario: Disallowed fields are rejected before transmission

- **GIVEN** an emitter attempts to include a file path or free-form string
- **WHEN** the payload is validated
- **THEN** validation raises and no event is transmitted
- **AND** the rejection is logged to stderr at debug level without the offending value.

### Requirement: Telemetry Opt-Out Surface

The system SHALL provide a single-command opt-out and an environment-variable opt-out honouring a deterministic resolution chain.

#### Scenario: `specfact telemetry disable` persists across invocations

- **GIVEN** a user runs `specfact telemetry disable`
- **WHEN** any subsequent `specfact` command runs
- **THEN** no telemetry event is emitted
- **AND** `specfact telemetry status` reports `disabled (source: user)`.

#### Scenario: `SPECFACT_TELEMETRY=false` overrides persisted enable

- **GIVEN** telemetry is enabled in project config
- **WHEN** a command runs with `SPECFACT_TELEMETRY=false`
- **THEN** no event is emitted for that invocation
- **AND** persisted configuration is not modified.

### Requirement: Enterprise Default-Off

The system SHALL default telemetry to disabled when an enterprise marker is present and re-enable only via a signed org-admin policy.

#### Scenario: Enterprise marker flips default

- **GIVEN** `.specfact/enterprise.yaml` is present without an enabling org policy
- **WHEN** a command runs
- **THEN** no telemetry is emitted
- **AND** `specfact telemetry status` reports `disabled (source: enterprise-default)`.

### Requirement: Local Redacted Audit Log

The system SHALL append every transmitted payload to a local audit log so users can inspect what was sent.

#### Scenario: Transmitted payload is recorded locally

- **GIVEN** telemetry is enabled and an exporter is configured
- **WHEN** a command completes
- **THEN** the exact transmitted payload is appended to `.specfact/telemetry/sent.log`
- **AND** each log line includes the transmission timestamp and OTLP endpoint identifier.
