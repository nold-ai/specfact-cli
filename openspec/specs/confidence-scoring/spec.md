# confidence-scoring Specification

## Purpose

TBD - created by archiving change bundle-mapper-01-mapping-strategy. Update Purpose after archive.

## Requirements

### Requirement: Explicit Label Signal

The system SHALL score explicit bundle labels (e.g., "bundle:xyz", "project:abc") with highest priority and 100% confidence when bundle exists.

#### Scenario: Explicit label with valid bundle

- **WHEN** item has tag "bundle:backend-services" and bundle exists
- **THEN** the system assigns score 1.0 (100% confidence) to that bundle

#### Scenario: Explicit label with invalid bundle

- **WHEN** item has tag "bundle:nonexistent" and bundle doesn't exist
- **THEN** the system ignores the label and uses other signals

#### Scenario: Multiple explicit labels

- **WHEN** item has multiple bundle labels
- **THEN** the system uses the first matching label

### Requirement: Historical Mapping Signal

The system SHALL score historical mappings based on frequency of similar items mapped to the same bundle.

#### Scenario: Strong historical pattern

- **WHEN** 10+ similar items (same assignee, area, tags) were mapped to "backend-services"
- **THEN** the system assigns high confidence (normalized count / 10, capped at 1.0)

#### Scenario: Weak historical pattern

- **WHEN** 1-2 similar items were mapped to a bundle
- **THEN** the system assigns low confidence (count / 10)

#### Scenario: No historical pattern

- **WHEN** no similar items exist in history
- **THEN** the system returns None for historical signal

#### Scenario: Item key similarity matching

- **WHEN** item keys share at least 2 of 3 components (area, assignee, tags)
- **THEN** the system considers them similar for historical lookup

### Requirement: Content Similarity Signal

The system SHALL score content similarity between item text and existing specs in bundles using keyword matching.

#### Scenario: High keyword overlap

- **WHEN** item title/body shares many keywords with specs in a bundle
- **THEN** the system assigns high similarity score (Jaccard similarity)

#### Scenario: Low keyword overlap

- **WHEN** item title/body shares few keywords with specs in a bundle
- **THEN** the system assigns low similarity score or ignores bundle

#### Scenario: No keyword overlap

- **WHEN** item text has no keywords in common with bundle specs
- **THEN** the system assigns score 0.0 for that bundle

#### Scenario: Conflicting content signal does not increase confidence

- **GIVEN** explicit or historical scoring selected a primary bundle
- **AND** top content similarity points to a different bundle
- **WHEN** final confidence is calculated
- **THEN** the content contribution is not added to the selected primary bundle confidence

#### Scenario: Tokenization for matching

- **WHEN** content similarity is computed
- **THEN** the system tokenizes text (lowercase, split by non-alphanumeric) for comparison

### Requirement: Confidence Thresholds

The system SHALL use configurable confidence thresholds for routing decisions.

#### Scenario: Auto-assign threshold

- **WHEN** confidence >= auto_assign_threshold (default 0.8)
- **THEN** the system auto-assigns to bundle (with optional user confirmation)

#### Scenario: Confirm threshold

- **WHEN** confidence >= confirm_threshold (default 0.5) and < auto_assign_threshold
- **THEN** the system prompts user for confirmation

#### Scenario: Reject threshold

- **WHEN** confidence < confirm_threshold (default 0.5)
- **THEN** the system requires explicit bundle selection

#### Scenario: Configurable thresholds

- **WHEN** user configures custom thresholds in `.specfact/config.yaml`
- **THEN** the system uses custom thresholds instead of defaults

#### Scenario: Malformed thresholds fall back to defaults

- **WHEN** config contains non-numeric threshold values
- **THEN** mapper initialization does not fail
- **AND** default threshold values are used
