## ADDED Requirements

### Requirement: OpenTelemetry Active Opt-In Emitter

The system SHALL emit a summary telemetry event for every CLI invocation when telemetry is enabled, using an allowlisted PII-safe payload.

#### Scenario: Community-tier unprompted invocation stays silent before consent

- **GIVEN** a community-tier installation with no explicit telemetry configuration or recorded consent
- **WHEN** a `specfact` command runs without an interactive consent prompt
- **THEN** no telemetry event is emitted
- **AND** `specfact telemetry status` reports `disabled (source: unconfigured)`.

#### Scenario: Explicitly opted-in invocation emits a summary event

- **GIVEN** a community-tier installation with telemetry enabled by `specfact init`, first-run consent, `specfact telemetry enable`, project config, or `SPECFACT_TELEMETRY=true`
- **WHEN** any `specfact` command runs to completion
- **THEN** a single summary event is emitted containing only allowlisted fields
- **AND** the event records the five required semantic fields specified in the disclosure requirement.

#### Scenario: First interactive run asks for consent before emission

- **GIVEN** an interactive terminal with no explicit telemetry configuration or recorded consent
- **WHEN** the first `specfact` command reaches telemetry resolution
- **THEN** the CLI shows a concise telemetry disclosure before asking for consent
- **AND** the current command emits no telemetry if the user declines
- **AND** the current command MAY emit exactly one summary event after consent is recorded if the user accepts.

#### Scenario: Non-interactive first run does not prompt and remains disabled

- **GIVEN** a non-interactive terminal or CI environment with no explicit telemetry configuration or recorded consent
- **WHEN** the first `specfact` command reaches telemetry resolution
- **THEN** the CLI does not prompt
- **AND** no telemetry event is emitted.

#### Scenario: Current emitter drops non-allowlisted fields before transmission

- **GIVEN** the current `TelemetryManager._sanitize` implementation receives non-allowlisted metadata
- **WHEN** a telemetry event is built before transmission
- **THEN** non-allowlisted keys are silently dropped
- **AND** the transmitted or locally recorded event contains only allowlisted keys.

#### Scenario: Target-state validator rejects disallowed categories before transmission

- **GIVEN** the target-state emitter attempts to include a file path, repo identifier, prompt content, spec content, or
  free-form string outside the allowlist
- **WHEN** the payload is validated after the hard-fail rollout gate is enabled
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

- **GIVEN** a community-tier installation with no enterprise marker and no persisted telemetry consent
- **WHEN** a command runs with `SPECFACT_TELEMETRY=true`
- **THEN** one telemetry event is emitted if payload validation passes
- **AND** persisted configuration is not modified.

#### Scenario: Legacy telemetry opt-in overrides are honored during deprecation

- **GIVEN** `SPECFACT_TELEMETRY` is unset and `SPECFACT_TELEMETRY_OPT_IN=true`
- **WHEN** telemetry state is resolved
- **THEN** telemetry is treated as enabled for that invocation outside enterprise governance
- **AND** a runtime deprecation warning tells the user to migrate to `SPECFACT_TELEMETRY=true`.

#### Scenario: New telemetry overrides take precedence over legacy overrides

- **GIVEN** `SPECFACT_TELEMETRY=false` and `SPECFACT_TELEMETRY_OPT_IN=true`
- **WHEN** telemetry state is resolved
- **THEN** telemetry is disabled for that invocation
- **AND** a runtime conflict warning states that `SPECFACT_TELEMETRY` took precedence.

### Requirement: Telemetry Disclosure

The system SHALL disclose what telemetry tracks and rejects before consent and from the status command.

#### Scenario: Disclosure lists tracked fields and rejected categories

- **GIVEN** the user sees the `specfact init`, first-run consent, or `specfact telemetry status` disclosure
- **WHEN** telemetry disclosure is rendered
- **THEN** it lists the five required semantic fields `command`, `modules_composed`, `duration_ms`, `exit_code`, and `outcome`
- **AND** it lists optional bounded `subcommand`, `schema_version`, `run_id`, `timestamp`, Python major/minor version, and coarse platform fields
- **AND** it states that file paths, repo names, branch names, remotes, prompt content, chat transcripts, spec content, usernames, emails, hostnames, free-form logs, and raw error messages are not collected.

### Requirement: Enterprise Default-Off

The system SHALL default telemetry to disabled when an enterprise marker is present and re-enable only via a signed org-admin policy.

#### Scenario: Enterprise marker flips default

- **GIVEN** `.specfact/enterprise.yaml` is present without an enabling org policy
- **WHEN** a command runs
- **THEN** no telemetry is emitted
- **AND** `specfact telemetry status` reports `disabled (source: enterprise-default)`.

#### Scenario: Enterprise marker blocks transient environment enable without signed policy

- **GIVEN** `.specfact/enterprise.yaml` is present without an enabling org policy
- **WHEN** a command runs with `SPECFACT_TELEMETRY=true`
- **THEN** no telemetry is emitted
- **AND** `specfact telemetry status` reports `disabled (source: enterprise-default)`.

#### Scenario: Enterprise signed policy permits transient environment enable

- **GIVEN** `.specfact/enterprise.yaml` is present with a signed org policy that permits telemetry
- **WHEN** a command runs with `SPECFACT_TELEMETRY=true`
- **THEN** one telemetry event is emitted if payload validation passes
- **AND** persisted configuration is not modified.

#### Scenario: Enterprise signed policy does not override explicit transient disable

- **GIVEN** `.specfact/enterprise.yaml` is present with a signed org policy that permits telemetry
- **WHEN** a command runs with `SPECFACT_TELEMETRY=false`
- **THEN** no telemetry is emitted
- **AND** persisted configuration is not modified.

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
