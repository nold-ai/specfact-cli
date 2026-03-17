## ADDED Requirements

### Requirement: House Rules Auto-Update Algorithm with Frequency Thresholds and Line Cap
The system SHALL implement an update algorithm that surfaces rules with >= 3 hits in last 20 runs, prunes rules with 0 hits for 10+ consecutive runs, enforces a 35-line hard cap, and increments the version header.

#### Scenario: Rule appearing 3+ times in last 20 runs is surfaced
- **GIVEN** ledger data showing rule `C901` appeared 5 times in the last 20 runs
- **WHEN** `update_house_rules(skill_path, ledger_data)` is called
- **THEN** `C901` is present in the TOP VIOLATIONS section of the updated SKILL.md

#### Scenario: Rule appearing fewer than 3 times is not surfaced
- **GIVEN** rule `T201` appeared only twice in the last 20 runs
- **WHEN** `update_house_rules(...)` is called
- **THEN** `T201` is NOT added to TOP VIOLATIONS

#### Scenario: Rule with 0 hits for 10 consecutive runs is pruned
- **GIVEN** SKILL.md lists `W0702` in TOP VIOLATIONS and `W0702` has 0 hits in last 10 runs
- **WHEN** `update_house_rules(...)` is called
- **THEN** `W0702` is removed from TOP VIOLATIONS

#### Scenario: Version header increments on each update
- **GIVEN** SKILL.md has `# House Rules — AI Coding Context (v3)`
- **WHEN** `update_house_rules(...)` is called
- **THEN** the version becomes `v4` and the `Updated:` timestamp reflects the current date

#### Scenario: 35 line cap enforced by pruning lowest-frequency entries
- **GIVEN** updating would exceed the 35-line budget
- **WHEN** `update_house_rules(...)` is called
- **THEN** lowest-frequency entries are removed first and the result is at most 35 lines

#### Scenario: DO and DON'T sections unchanged after update
- **GIVEN** DO and DON'T sections have specific content
- **WHEN** `update_house_rules(...)` is called
- **THEN** DO and DON'T sections remain byte-identical to their pre-update state
