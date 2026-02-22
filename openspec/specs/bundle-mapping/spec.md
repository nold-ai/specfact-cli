# bundle-mapping Specification

## Purpose
TBD - created by archiving change verification-01-wave1-delta-closure. Update Purpose after archive.
## Requirements
### Requirement: Confidence-Based Routing

The system SHALL route bundle mappings based on confidence thresholds: auto-assign (>=0.8), prompt user (0.5-0.8), require explicit selection (<0.5).

#### Scenario: Refine/import `--auto-bundle` executes runtime mapping flow

- **GIVEN** `bundle-mapper` module is installed and a user runs backlog refine/import with `--auto-bundle`
- **WHEN** items are processed for OpenSpec bundle assignment
- **THEN** `BundleMapper` confidence scoring is executed for each item
- **AND** confidence routing behavior is enforced (auto/prompt/explicit selection) instead of placeholder or no-op import messaging
- **AND** resulting mapping decision is persisted via configured mapping history/rules storage.

### Requirement: Bundle Mapping Engine

The system SHALL provide a `BundleMapper` that computes mapping from backlog items to OpenSpec bundles with confidence scoring.

#### Scenario: Compute mapping with explicit label

- **WHEN** a backlog item has tag "bundle:backend-services"
- **THEN** the system returns mapping with bundle_id="backend-services" and confidence >= 0.8

#### Scenario: Compute mapping with historical pattern

- **WHEN** similar items (same assignee, area, tags) were previously mapped to a bundle
- **THEN** the system returns mapping with that bundle_id and confidence based on historical frequency

#### Scenario: Compute mapping with content similarity

- **WHEN** item title/body contains keywords matching existing specs in a bundle
- **THEN** the system returns mapping with that bundle_id and confidence based on keyword overlap

#### Scenario: Weighted confidence calculation

- **WHEN** multiple signals contribute to mapping
- **THEN** the system calculates final confidence as: 0.8 × explicit + 0.15 × historical + 0.05 × content

#### Scenario: No mapping found

- **WHEN** no signals match any bundle
- **THEN** the system returns mapping with primary_bundle_id=None and confidence=0.0

### Requirement: Mapping History Persistence

The system SHALL persist mapping rules learned from user confirmations.

#### Scenario: Save user-confirmed mapping

- **WHEN** a user confirms a bundle mapping
- **THEN** the system saves the mapping pattern to config history for future use

#### Scenario: Historical mapping lookup

- **WHEN** a new item matches historical pattern (same assignee, area, tags)
- **THEN** the system uses historical mapping frequency to boost confidence score

#### Scenario: Historical mapping ignores stale bundle ids

- **GIVEN** history contains bundle ids that are no longer present in available bundles
- **WHEN** historical scoring is computed
- **THEN** stale bundle ids are ignored
- **AND** returned historical bundle ids are always members of current available bundles

#### Scenario: Mapping rules from config

- **WHEN** config file contains mapping rules (e.g., "assignee=alice → backend-services")
- **THEN** the system applies these rules before computing other signals

#### Scenario: History key encoding is unambiguous

- **WHEN** item keys are serialized for history matching
- **THEN** field delimiters and tag-value delimiters do not collide
- **AND** round-trip parsing preserves all tag values without truncation

### Requirement: Interactive Mapping UI

The system SHALL provide an interactive prompt for bundle selection with confidence visualization and candidate options.

#### Scenario: Display high confidence suggestion

- **WHEN** mapping confidence >= 0.8
- **THEN** the system displays "✓ HIGH CONFIDENCE" with suggested bundle and reason

#### Scenario: Display medium confidence suggestion

- **WHEN** mapping confidence 0.5-0.8
- **THEN** the system displays "? MEDIUM CONFIDENCE" with suggested bundle and alternative candidates

#### Scenario: Display low confidence warning

- **WHEN** mapping confidence < 0.5
- **THEN** the system displays "! LOW CONFIDENCE" and requires explicit bundle selection

#### Scenario: Show all available bundles

- **WHEN** user selects "S" option
- **THEN** the system displays all available bundles with descriptions

#### Scenario: Skip item

- **WHEN** user selects "Q" option
- **THEN** the system skips the item without mapping

