## ADDED Requirements

### Requirement: Coverage gates SHALL be blocking

PR quality gates SHALL enforce the repository coverage threshold configured in `pyproject.toml` and SHALL fail when measured coverage is below that threshold.

#### Scenario: Coverage below threshold blocks PR

- **GIVEN** the test job publishes `coverage.xml`
- **AND** `tool.coverage.report.fail_under` is `50`
- **WHEN** the quality-gates job evaluates line coverage below 50 percent
- **THEN** the job exits non-zero
- **AND** the emitted check is named `Quality Gates`
- **AND** the output does not describe the result as advisory.

### Requirement: Independent static analysis SHALL block separately from self-review

CI SHALL run Semgrep and Bandit as a blocking job that is independent from `specfact code review`.

#### Scenario: Semgrep or Bandit fails

- **WHEN** Semgrep or Bandit reports a blocking finding or exits non-zero
- **THEN** the `Independent Static Analysis` job fails
- **AND** raw Semgrep JSON and Bandit output are uploaded when present
- **AND** the result does not depend on `.specfact/code-review.json`.

### Requirement: Package runtime matrix SHALL validate built artifacts before merge

PR validation SHALL build a wheel and validate supported runtime launchers before merge when runtime, packaging, module discovery, command docs, or workflow inputs change.

#### Scenario: Runtime-affecting PR runs package matrix

- **WHEN** a pull request changes CLI runtime, packaging, command docs, module discovery, CI smoke scripts, or workflow files
- **THEN** CI builds the package wheel
- **AND** validates hatch/source, pip wheel, pipx, uv run, and uvx launch paths
- **AND** each launcher checks root help, unknown-command guidance, module list, representative official module help, and a non-destructive init flow.

### Requirement: Release parity fast path SHALL keep release-safety gates

`dev -> main` parity skips SHALL skip only duplicate expensive validation and SHALL still run release-safety checks.

#### Scenario: Dev to main parity PR

- **WHEN** a `dev -> main` pull request proves commit parity
- **THEN** duplicate full suite, contract exploration, and editable CLI validation may be skipped
- **AND** strict module signature verification, version sync, package validation, and minimal installed-wheel smoke still run.

#### Scenario: Direct-to-main PR changes bundled modules

- **WHEN** a pull request targets `main` without coming through the regular `dev -> main` release path
- **AND** it changes signed bundled module assets or manifest inputs
- **THEN** PR orchestration runs strict module signature verification with `VERIFY_MODULES_STRICT`
- **AND** unsigned, stale, or incorrectly signed manifests block before merge.

### Requirement: Cross-platform smoke SHALL be staged

CI SHALL run macOS runtime smoke for PRs affecting runtime/package paths and Windows runtime smoke on schedule or manual dispatch until promoted.

#### Scenario: Runtime PR hits macOS smoke

- **WHEN** a PR changes runtime, packaging, module discovery, or smoke scripts
- **THEN** the macOS runtime smoke job runs and blocks failures
- **AND** Windows smoke remains scheduled/manual with uploaded logs.

### Requirement: Critical resolver paths SHALL have generative and mutation evidence

Critical resolver and installer paths SHALL have property-based tests, and scheduled mutation testing SHALL publish a baseline report.

#### Scenario: Critical path correctness probes run

- **WHEN** PR validation runs for dependency resolver or module installer changes
- **THEN** Hypothesis property tests exercise dependency constraints, version satisfaction, malformed manifests, registry identity, and circular dependency surfaces
- **AND** scheduled mutation testing targets dependency resolver, module installer, module package parsing, marketplace selection, and upgrade/version detection.
