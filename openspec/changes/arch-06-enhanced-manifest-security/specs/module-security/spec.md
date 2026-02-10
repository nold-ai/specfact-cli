# Spec: Module Security

## ADDED Requirements

### Requirement: Module artifacts SHALL be verified for integrity before installation

The system SHALL verify module artifact checksums before extraction or registration.

#### Scenario: Checksum verification succeeds

- **WHEN** installer receives a module artifact and expected checksum
- **THEN** checksum verification SHALL pass when values match
- **AND** installation SHALL continue to next verification stage.

#### Scenario: Checksum verification fails

- **WHEN** artifact checksum does not match expected checksum
- **THEN** installation SHALL fail with a security error
- **AND** module SHALL NOT be extracted or registered.

### Requirement: Signature verification SHALL be supported for signed modules

The system SHALL support signature verification for modules that provide signature metadata.

#### Scenario: Signed module verification succeeds

- **WHEN** module manifest includes signature and trusted key metadata
- **THEN** signature verification SHALL validate artifact provenance
- **AND** installation SHALL proceed.

#### Scenario: Signature verification fails

- **WHEN** signature validation fails against trusted key material
- **THEN** installation SHALL fail with explicit signature error details
- **AND** module SHALL NOT be enabled.

### Requirement: Unsigned module installation SHALL require explicit opt-in

The system SHALL require explicit allow-unsigned policy override when strict trust mode is enabled.

#### Scenario: Unsigned module blocked by default policy

- **WHEN** strict trust mode is active and module has no signature metadata
- **THEN** installer SHALL reject the module by default
- **AND** output SHALL explain how to opt in explicitly.

#### Scenario: Unsigned module allowed via explicit override

- **WHEN** user sets allow-unsigned override
- **THEN** installer MAY continue after checksum validation
- **AND** system SHALL emit warning/audit logs.
