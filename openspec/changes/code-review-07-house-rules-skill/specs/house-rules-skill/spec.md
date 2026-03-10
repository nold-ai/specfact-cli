## ADDED Requirements

### Requirement: ai-integration-01 Compliant House Rules Skill File
The system SHALL provide `skills/specfact-code-review/SKILL.md` with valid ai-integration-01 YAML frontmatter, DO/DON'T rules, and an auto-managed TOP VIOLATIONS section, within a 35-line hard cap.

#### Scenario: SKILL.md has valid ai-integration-01 YAML frontmatter
- **GIVEN** `skills/specfact-code-review/SKILL.md` exists
- **WHEN** the frontmatter is parsed
- **THEN** `name`, `description`, and `allowed-tools` fields are present and valid

#### Scenario: Skill file is within 35 line cap
- **GIVEN** the SKILL.md in its default or updated state
- **WHEN** line count is measured
- **THEN** line count is at most 35

#### Scenario: TOP VIOLATIONS section is auto-managed and other sections preserved
- **GIVEN** SKILL.md contains the auto-managed TOP VIOLATIONS marker
- **WHEN** `specfact code review rules update` runs
- **THEN** only the TOP VIOLATIONS section is modified and DO/DON'T sections are unchanged

#### Scenario: SKILL.md creation does not modify CLAUDE.md
- **GIVEN** `specfact code review rules init` is run
- **WHEN** all files created or modified are inspected
- **THEN** `CLAUDE.md` is not in the list of modified files

#### Scenario: rules init creates default SKILL.md for new project
- **GIVEN** no `skills/specfact-code-review/SKILL.md` exists
- **WHEN** `specfact code review rules init` is run
- **THEN** SKILL.md is created with default DO/DON'T rules within 35 lines
