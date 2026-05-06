## ADDED Requirements

### Requirement: OpenTelemetry Active Opt-In Emitter

The system SHALL emit a summary telemetry event for every CLI invocation when telemetry is enabled, using an allowlisted PII-safe payload.

#### Scenario: Community-tier invocation stays silent before consent

- **GIVEN** a community-tier installation with no explicit telemetry configuration or recorded consent
- **WHEN** any `specfact` command runs to completion
- **THEN** no telemetry event is emitted
- **AND** `specfact telemetry status` reports `disabled (source: unconfigured)`.

#### Scenario: Explicitly opted-in invocation emits a summary event

- **GIVEN** a community-tier installation with telemetry enabled by `specfact init`, first-run consent, `specfact telemetry enable`, project config, or `SPECFACT_TELEMETRY=true`
- **WHEN** any `specfact` command runs to completion
- **THEN** a single summary event is emitted containing only allowlisted fields
- **AND** the event records command, duration, exit code, and outcome enum.

#### Scenario: First interactive run asks for consent before emission

- **GIVEN** an interactive terminal with no explicit telemetry configuration or recorded consent
- **WHEN** the first `specfact` command reaches telemetry resolution
- **THEN** the CLI shows a concise telemetry disclosure before asking for consent
- **AND** no telemetry event is emitted unless the user accepts.

#### Scenario: Non-interactive first run does not prompt and remains disabled

- **GIVEN** a non-interactive terminal or CI environment with no explicit telemetry configuration or recorded consent
- **WHEN** the first `specfact` command reaches telemetry resolution
- **THEN** the CLI does not prompt
- **AND** no telemetry event is emitted.

#### Scenario: Disallowed fields are rejected before transmission

- **GIVEN** an emitter attempts to include a file path or free-form string
- **WHEN** the payload is validated
- **THEN** validation raises and no event is transmitted
- **AND** the rejection is logged to stderr at debug level without the offending value.

### Requirement: Telemetry Consent Surface

The system SHALL provide single-command enable/disable/status controls and environment-variable overrides honouring a deterministic resolution chain.

#### Scenario: `specfact init` records active opt-in

- **GIVEN** a user runs `specfact init` in an interactive terminal
- **WHEN** the user accepts the telemetry prompt after reading the disclosure
- **THEN** telemetry is persisted as enabled for the configured scope
- **AND** `specfact telemetry status` reports `enabled` with the consent source.

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

#### Scenario: `SPECFACT_TELEMETRY=true` enables one invocation without persisted consent

- **GIVEN** no persisted telemetry consent exists
- **WHEN** a command runs with `SPECFACT_TELEMETRY=true`
- **THEN** one telemetry event is emitted if payload validation passes
- **AND** persisted configuration is not modified.

### Requirement: Telemetry Disclosure

The system SHALL disclose what telemetry tracks and rejects before consent and from the status command.

#### Scenario: Disclosure lists tracked fields and rejected categories

- **GIVEN** the user sees the `specfact init`, first-run consent, or `specfact telemetry status` disclosure
- **WHEN** telemetry disclosure is rendered
- **THEN** it lists the tracked command/subcommand, module composition, duration, exit code, outcome enum, schema version, run ID, timestamp, Python major/minor version, and coarse platform fields
- **AND** it states that file paths, repo names, branch names, remotes, prompt content, chat transcripts, spec content, usernames, emails, hostnames, free-form logs, and raw error messages are not collected.

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

#### Scenario: Legacy `~/.specfact/telemetry.log` is migrated or dual-read

- **GIVEN** an existing audit file is present at `~/.specfact/telemetry.log` before upgrade
- **WHEN** the first telemetry-enabled command runs after upgrade
- **THEN** the system either **copies/merges** prior lines into `.specfact/telemetry/sent.log` **or** treats **both**
  `~/.specfact/telemetry.log` and `.specfact/telemetry/sent.log` as valid append/read sources until migration completes
- **AND** timestamps and OTLP endpoint identifiers are preserved across the migration path
- **AND** behavior matches the **“Transmitted payload is recorded locally”** scenario for new invocations.
