## ADDED Requirements

### Requirement: Optional versioned decision context

The system SHALL provide a versioned RequirementDecisionContext companion to existing requirement inputs. Version 1 records SHALL retain stable record IDs, typed assumption/clarification-decision kinds, explicit disposition, original source references and source digests, and typed links to requirements, acceptance cases, components or ADRs. It SHALL reuse existing clarification question/answer/integration records rather than create a competing clarification workflow. Owner, review date and falsifying verification links SHALL remain optional in ordinary use. Records SHALL represent explicit source assertions only; unrecorded assumptions SHALL NOT be invented or claimed discovered.

#### Scenario: Legacy input has no context

- **GIVEN** a valid existing requirement input without decision context
- **WHEN** the input is parsed
- **THEN** it remains valid and no new decision fields are required.

#### Scenario: Architectural decision has no test

- **GIVEN** an explicit ADR clarification with component and ADR links but no test
- **WHEN** ordinary context normalization runs
- **THEN** the record remains valid and the available links are preserved without fabricating a test.

#### Scenario: Reuse clarification records

- **GIVEN** an existing clarification question, answer and integrated_into references
- **WHEN** it is imported as decision context
- **THEN** its source identity and disposition are retained with stable typed links and no duplicate decision workflow.

### Requirement: Separate decision context identity

Decision-relevant content SHALL have a separately versioned canonical digest over normalized IDs, kinds, dispositions, question/answer or assumption statements, typed links and explicit verification references. Source content digests SHALL bind the imported assertion to its original artifact. Historical session timestamps and other non-decision metadata SHALL NOT change the decision digest unless explicitly selected by policy. Legacy plan hashes SHALL remain unchanged and SHALL continue to exclude clarifications. A changed bound decision or source digest SHALL invalidate reuse of evidence that binds that context; an absent optional context SHALL NOT invalidate ordinary legacy evidence.

#### Scenario: Decision answer changes

- **GIVEN** evidence bound to a decision digest
- **WHEN** the bound answer, disposition or affected links change
- **THEN** its decision digest changes and context-dependent evidence cannot be reused.

#### Scenario: Historical metadata changes

- **GIVEN** a plan with unchanged decision content
- **WHEN** only a historical clarification session timestamp changes
- **THEN** its legacy plan hash and decision-content digest remain unchanged.

#### Scenario: Source assertion changes

- **GIVEN** a context record referencing a digest-addressed source
- **WHEN** the source bytes change
- **THEN** source-bound reuse is rejected even if the previously normalized record was retained.

### Requirement: Assertions and assurance authority remain distinct

Imported dispositions and answered_by/owner strings SHALL NOT authenticate approval. Ordinary evaluation SHALL report a touched unresolved recorded assumption as advisory. An explicitly selected assurance policy MAY require resolution, ownership, review date or verification links. Unavailable or ambiguous required evidence SHALL remain UNKNOWN; a reconciled behavioral contradiction SHALL remain FAIL. A trace link SHALL establish association only, not behavioral satisfaction or proof that unmapped behavior is absent.

#### Scenario: Unresolved ordinary assumption

- **GIVEN** a touched unresolved recorded assumption with no assurance policy
- **WHEN** feedback is generated
- **THEN** it produces an advisory with its source and affected obligations without blocking ordinary validation.

#### Scenario: Policy requires resolution

- **GIVEN** an explicitly selected policy requiring resolution and no verifiable disposition
- **WHEN** assurance is evaluated
- **THEN** an unmet assurance obligation retains UNKNOWN and does not become authenticated approval.

#### Scenario: Verified contradiction

- **GIVEN** current correctly bound evidence contradicts an accepted decision observable
- **WHEN** the selected required obligation is evaluated
- **THEN** the contradiction is FAIL with the evidence reference, independent of any advisory reviewer verdict.
