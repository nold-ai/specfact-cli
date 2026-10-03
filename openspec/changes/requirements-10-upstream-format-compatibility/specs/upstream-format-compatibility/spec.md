## ADDED Requirements

### Requirement: Pinned upstream artifact profiles

The adapter SHALL test pinned Spec Kit v1.1.0 fixtures alongside retained v0.12.18 and supported OpenSpec fixtures. Fixture metadata SHALL identify upstream tag/commit, artifact paths and content digests. Support SHALL be evaluated from the effective artifact profile, including enabled known extensions and template resolution, rather than inferred from Markdown or a claimed CLI version. The supported profile allowlist SHALL be explicit and versioned; unknown or unsupported custom profiles SHALL be rejected with an actionable diagnostic.

#### Scenario: Legacy input remains supported

- **GIVEN** a retained legacy fixture and a pinned v1.1.0 native fixture
- **WHEN** each is imported
- **THEN** both produce expected normalized requirements and readiness findings without rewriting upstream artifacts.

#### Scenario: Unknown template override

- **GIVEN** a custom or unresolved template/extension profile
- **WHEN** native import is requested
- **THEN** the import rejects the unsupported profile explicitly instead of silently treating it as the default format.

### Requirement: Extension coexistence and atomic import

A supported SpecFact extension that only adds invocation hooks SHALL NOT by its presence invalidate a supported native artifact profile. An extension that alters artifact templates SHALL require a tested effective profile. Import and readiness validation SHALL complete before persistence; any profile, parse or readiness failure SHALL leave existing imported state unchanged. Import SHALL remain offline and SHALL NOT execute upstream scripts, fetch templates or rewrite upstream inputs.

#### Scenario: SpecFact invocation extension coexists

- **GIVEN** the pinned invocation-only SpecFact extension and native upstream artifacts
- **WHEN** requirements import runs
- **THEN** the effective profile is recognized and import remains usable.

#### Scenario: Failed import preserves state

- **GIVEN** previously persisted requirements and a mixed valid/invalid new input
- **WHEN** profile or readiness validation fails
- **THEN** no partial replacement or new persisted artifact is produced and the original bytes remain unchanged.
