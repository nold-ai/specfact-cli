## ADDED Requirements

### Requirement: AI Refinement Writeback Preserves Provider Field Semantics

The system SHALL parse structured refinement output into canonical fields before provider writeback so provider-specific fields are updated correctly rather than storing prompt labels verbatim in description/body.

#### Scenario: ADO writeback splits label-style refined output into canonical fields

- **GIVEN** a user runs `specfact backlog refine ado --write`
- **AND** the refined output uses label-style sections such as `Description:`, `Acceptance Criteria:`, `Story Points:`, `Business Value:`, and `Priority:`
- **WHEN** the refinement is accepted
- **THEN** SpecFact parses those sections into canonical fields
- **AND** writes `description` content to ADO description field
- **AND** writes `acceptance_criteria`, `story_points`, `business_value`, and `priority` to their mapped ADO fields when present
- **AND** does not write the entire labeled structure verbatim as ADO description.

#### Scenario: GitHub writeback normalizes label-style refined output to structured markdown

- **GIVEN** a user runs `specfact backlog refine github --write`
- **AND** the refined output uses label-style sections rather than markdown headings
- **WHEN** the refinement is accepted
- **THEN** SpecFact normalizes the output into canonical markdown sections
- **AND** updates issue body and related canonical fields consistently
- **AND** avoids duplicating or flattening structured fields into a single unparsed description block.

#### Scenario: Heading-style narrative sections are preserved during writeback parsing

- **GIVEN** a user runs `specfact backlog refine <provider> --write`
- **AND** the refined output uses markdown headings like `## Notes` and `## Dependencies`
- **WHEN** the refinement output is parsed into canonical fields for writeback
- **THEN** `body_markdown` keeps those narrative sections
- **AND** canonical numeric/provider metadata sections (for example `## Story Points`, `## Business Value`, `## Priority`, `## Provider`) are not duplicated into narrative body text.

#### Scenario: Heading-style narrative sections are matched case-insensitively

- **GIVEN** a user runs `specfact backlog refine <provider> --write`
- **AND** the refined output uses uppercase narrative headings like `## NOTES` and `## DEPENDENCIES`
- **WHEN** the refinement output is parsed into canonical fields for writeback
- **THEN** `body_markdown` preserves those narrative sections as normalized `## Notes` / `## Dependencies` sections
- **AND** writeback does not silently drop narrative context because of heading case differences.

#### Scenario: Label-only field blocks without Description do not leak raw labels into body/description

- **GIVEN** a user runs `specfact backlog refine <provider> --write`
- **AND** the refined output contains label-style field blocks (for example `Acceptance Criteria:`, `Story Points:`, `Priority:`) but no `Description:` block
- **WHEN** the refinement output is parsed into canonical fields for writeback
- **THEN** canonical fields (for example acceptance criteria and numeric fields) are extracted
- **AND** parser fallback does not keep the entire raw labeled payload as `description`
- **AND** `body_markdown` does not contain prompt labels verbatim.

#### Scenario: Mixed heading and inline label formatting preserves description narrative

- **GIVEN** a refined output that uses heading-style sections such as `## Description` and `## Acceptance Criteria`
- **AND** the `## Description` section contains an inline label like `**Notes**:`
- **WHEN** SpecFact parses the refinement output for writeback
- **THEN** text before the inline label in `## Description` is preserved in `body_markdown`
- **AND** label-capture does not swallow subsequent heading sections.

#### Scenario: Prompt format contract includes canonical scaffold and metadata omission rule

- **GIVEN** SpecFact generates a refinement prompt for IDE Copilot
- **WHEN** prompt text is rendered for backlog refine
- **THEN** it includes an explicit expected output scaffold (ordered canonical sections)
- **AND** it instructs Copilot to omit unknown metadata fields (for example area/iteration path) instead of placeholders like "unspecified" or "provide ...".

#### Scenario: Mixed heading description does not duplicate inline notes block

- **GIVEN** a refined output with `## Description` narrative
- **AND** an inline label block like `**Notes**:` appears inside that description section
- **WHEN** SpecFact parses the refinement output for writeback
- **THEN** description narrative is preserved without raw inline label markup
- **AND** notes content appears only once in normalized `## Notes` output.

#### Scenario: Label-style notes preserves internal non-boundary headings

- **GIVEN** a label-style `Notes:` section includes internal headings such as `## Risks`
- **WHEN** SpecFact parses notes/dependencies label blocks
- **THEN** internal headings that are not canonical section boundaries are preserved as notes content
- **AND** parser does not truncate notes at the internal heading line.

#### Scenario: Refine command orchestration remains behaviorally consistent after decomposition

- **GIVEN** `specfact backlog refine` supports initialization, filtering, export/import, interactive refinement, writeback, and summary flows
- **WHEN** the command implementation is decomposed into smaller helper methods
- **THEN** observable CLI behavior and writeback semantics remain unchanged for equivalent inputs
- **AND** command complexity in the top-level `refine` function is reduced to keep the implementation readable and maintainable.
