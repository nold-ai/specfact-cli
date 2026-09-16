## ADDED Requirements

### Requirement: Documentation fixture preserves portable pytest evidence

The documentation pipeline SHALL select an immutable publisher-authenticated module source whose real portable pytest
adapter records nonpassing outcomes and incomplete production coverage as error findings. Native execution and module
authentication SHALL be established independently before behavioral assertions. Acquisition or execution failures SHALL
remain distinct setup errors and SHALL NOT count as behavioral RED evidence. The separate Requirements execution fixture
and prior command-registration proof SHALL remain unchanged.

#### Scenario: Native skipped test remains a review error

- **GIVEN** a real passing test and a real skipped test with complete production-source coverage
- **WHEN** the selected documentation module consumes the native observation
- **THEN** it emits an error `TEST_OUTCOME_NOT_PASS` finding

#### Scenario: Native expected failure remains a review error

- **GIVEN** a real passing test and an actual XFAIL with complete production-source coverage
- **WHEN** the selected documentation module consumes the native observation
- **THEN** it emits an error `TEST_OUTCOME_NOT_PASS` finding

#### Scenario: Native unexpected pass remains a review error

- **GIVEN** a real passing test and a successful non-strict xfail-marked test with a reason
- **WHEN** the selected documentation module consumes their actual outcomes and complete production coverage
- **THEN** it emits an error `TEST_OUTCOME_NOT_PASS` finding

#### Scenario: Empty reason does not erase an unexpected pass

- **GIVEN** a successful non-strict xfail-marked test whose reason is empty
- **WHEN** the selected documentation module consumes actual outcomes and complete production coverage
- **THEN** it emits an error `TEST_OUTCOME_NOT_PASS` finding

#### Scenario: Missing reviewed source coverage remains incomplete

- **GIVEN** real passing tests with nonempty coverage for another module and no row for the reviewed production source
- **WHEN** the selected documentation module consumes the native observation
- **THEN** it emits an error tool diagnostic identifying missing source coverage

#### Scenario: Native zero floor does not weaken review coverage policy

- **GIVEN** real passing tests covering less than 80 percent of the reviewed production source and a native zero floor
- **WHEN** the selected documentation module consumes the native observation
- **THEN** it emits an error `TEST_COVERAGE_LOW` finding
