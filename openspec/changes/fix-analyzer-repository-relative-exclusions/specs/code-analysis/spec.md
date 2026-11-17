## ADDED Requirements

### Requirement: Repository-relative source exclusions

The analyzer SHALL match excluded directory names against whole directory
components inside the selected repository. Repository ancestors and source
names merely containing an exclusion word SHALL NOT suppress a feature.
Actual excluded child directories and test-file naming rules SHALL remain
excluded.

#### Scenario: Repository location contains an exclusion word

- **GIVEN** a documented nested service inside a repository named tmpenvabc
- **WHEN** the analyzer runs at confidence threshold 0.5
- **THEN** it discovers the service feature.

#### Scenario: Source directory merely contains an exclusion word

- **GIVEN** a production service under src/builders or src/distribution
- **WHEN** the analyzer selects source files
- **THEN** the source remains eligible.

#### Scenario: Real excluded directories remain excluded

- **GIVEN** source under a real env, build or dist child directory
- **WHEN** the analyzer selects source files
- **THEN** those files remain excluded, as do test_*.py and *_test.py.
