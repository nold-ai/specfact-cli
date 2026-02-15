## MODIFIED Requirements

### Requirement: Profile Config Layering
The system SHALL merge domain overlays after central profile resolution and before developer-local overrides.

#### Scenario: Overlay precedence is enforced
- **GIVEN** base enterprise profile and domain overlay define conflicting requirement schema rules
- **WHEN** profile resolution executes
- **THEN** overlay rules win over base profile rules
- **AND** developer-local overrides can still adjust non-locked keys.

#### Scenario: Unknown overlay is rejected
- **GIVEN** requested overlay name is not available
- **WHEN** initialization runs
- **THEN** command fails with clear overlay-not-found diagnostics
- **AND** available overlays are listed.
