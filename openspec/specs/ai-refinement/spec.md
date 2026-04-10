# ai-refinement Specification

## Purpose

TBD - created by archiving change add-template-driven-backlog-refinement. Update Purpose after archive.

## Requirements

### Requirement: AI-Powered Backlog Refinement

The system SHALL generate prompts for IDE AI copilots to refactor non-matching backlog items into target template format while preserving original intent and scope. SpecFact CLI does NOT directly invoke LLM APIs.

**Architecture Note**: SpecFact CLI follows a CLI-first architecture:

- SpecFact CLI generates prompts/instructions for IDE AI copilots (Cursor, Claude Code, etc.)
- IDE AI copilots execute those instructions using their native LLM
- IDE AI copilots feed results back to SpecFact CLI
- SpecFact CLI validates and processes the results

#### Scenario: AI refinement prompt generation

- **WHEN** a backlog item doesn't match any template and AI refinement is requested
- **THEN** the system generates a refinement prompt for IDE AI copilot, displays it to the user, and waits for refined content to be pasted back

#### Scenario: AI refinement with high confidence

- **WHEN** an IDE AI copilot returns refined content that matches the target template format
- **THEN** the system validates the refined content and assigns confidence >= 0.75

#### Scenario: AI refinement preserves intent

- **WHEN** AI refines a backlog item
- **THEN** the refined content preserves original requirements, scope, and technical details without adding new features

#### Scenario: AI refinement marks missing information

- **WHEN** AI cannot determine required information from original item
- **THEN** the system marks missing information with [TODO: describe what's needed] markers

#### Scenario: AI refinement flags ambiguities

- **WHEN** AI detects conflicting or ambiguous information
- **THEN** the system adds a [NOTES] section at the end explaining the ambiguity

### Requirement: Refinement Confidence Scoring

The system SHALL compute confidence scores for AI-refined content based on completeness, clarity, and validation checks.

#### Scenario: High confidence for complete refinement

- **WHEN** refined content contains all required sections, no TODO markers, and no NOTES section
- **THEN** the system assigns confidence >= 0.85

#### Scenario: Medium confidence with minor gaps

- **WHEN** refined content contains all required sections but has 1-2 TODO markers
- **THEN** the system assigns confidence 0.6-0.85 (base 1.0, deduct 0.1 per TODO marker)

#### Scenario: Low confidence with significant gaps

- **WHEN** refined content has missing sections, multiple TODO markers, or NOTES section
- **THEN** the system assigns confidence < 0.6

#### Scenario: Confidence deduction for NOTES section

- **WHEN** refined content includes a [NOTES] section
- **THEN** the system deducts 0.15 from base confidence score

#### Scenario: Confidence deduction for size increase

- **WHEN** refined body size increases significantly (possible hallucination)
- **THEN** the system deducts 0.1 from base confidence score

### Requirement: Post-Refinement Validation

The system SHALL validate AI-refined content against template requirements before presenting to users.

#### Scenario: Validate required sections present

- **WHEN** AI refinement completes
- **THEN** the system checks that all required template sections are present in refined content

#### Scenario: Reject malformed refinement

- **WHEN** refined content is missing critical sections or is malformed
- **THEN** the system marks the refinement for human review or re-attempts with adjusted prompt

#### Scenario: Detect scope changes

- **WHEN** AI refinement adds features or changes requirements beyond original scope
- **THEN** the system flags the refinement for review and reduces confidence score
