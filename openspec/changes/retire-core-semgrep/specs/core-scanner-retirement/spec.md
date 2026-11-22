## ADDED Requirements

### Requirement: Core scans retain supported behavior without Semgrep

Core SHALL preserve supported feature, quality, and async scanning behavior through replacement checks and shall document any reviewed rule or output migration. SpecFact-owned core artifacts and standard tool paths SHALL carry no Semgrep dependency, executable, discovery or installer.

#### Scenario: Run supported scans on a clean external installation

- **GIVEN** a built wheel and an external installation with replacement prerequisites and without Semgrep
- **WHEN** supported scan entry points analyze a fixture containing findings and safe controls
- **THEN** each fixture produces the expected finding or clean completed result, compatible consumers retain structured evidence, and artifact and dependency inspection find no retired scanner graph

#### Scenario: Contract examples come from selected test source

- **GIVEN** a selected Python test with a literal HTTP request, a response body assertion and a status-code assertion
- **WHEN** the OpenAPI test converter extracts examples from source
- **THEN** it emits request, response and status for that operation without importing the test or invoking a scanner
- **AND** a requested legacy rule pack is reported with the supported source-based migration

#### Scenario: Async checks record findings and incomplete inputs

- **GIVEN** a repository with an async Python fixture containing known blocking calls, task-lifetime problems, and safe counterparts
- **WHEN** the async checker analyzes selected Python source
- **THEN** it reports rule IDs and source locations, accepts covered safe cases, and reports invalid inputs as incomplete
- **AND** a requested legacy custom policy or unsupported source fix produces a migration diagnostic without editing the project

#### Scenario: Python feature analysis retains evidence with source-only checks

- **GIVEN** Python classes with supported route, model, authentication, CRUD, and quality patterns together with clean controls
- **WHEN** the core brownfield analyzer extracts features
- **THEN** pattern evidence contributes the same categories to outcomes, themes, constraints and confidence without a scanner subprocess

### Requirement: Frozen core delivery uses the reviewed parser wheel

The frozen core dependency graph SHALL allow only the reviewed `pycparser 3.12` PyPI wheel by immutable URL and SHA-256. Existing dependency, provenance and vulnerability gates SHALL remain active. Published dependency metadata SHALL retain its existing registry requirement.

#### Scenario: Alternate parser artifacts fail the frozen checks

- **GIVEN** the official wheel with the Socket-reviewed contents
- **WHEN** the bootstrap gate checks the frozen uv lock and pip export
- **THEN** the exact wheel is admitted and an added source distribution or changed wheel URL or digest is rejected

### Requirement: Independent static analysis remains blocking

The independent CI static-analysis control SHALL preserve effective rule coverage, reviewed baseline semantics and the independent Bandit check. A required scanner failure, malformed output or incomplete input coverage SHALL produce a failed control.

#### Scenario: Existing SAST policy and baseline survive the migration

- **GIVEN** the repository baseline and a PR fixture with a seeded new security finding and a safe control
- **WHEN** the independent static-analysis gate runs with the replacement
- **THEN** it preserves reviewed baseline handling, blocks the new finding, accepts the safe control and records replacement tool and policy identity

#### Scenario: Core Python SAST produces its own complete evidence

- **GIVEN** the Git index defines the Python paths and the reviewed baseline uses existing rule identities
- **WHEN** the core SAST command parses the checkout without importing its code
- **THEN** it checks the six current Python rules on tracked paths outside `tests/` directories, preserving the current gate's test-directory scope, and rejects new findings outside the baseline
- **AND** it records the exact eligible, scanned, and excluded test paths
- **AND** parse failures or missing tracked files produce incomplete evidence and a nonzero exit

#### Scenario: Scanner evidence is incomplete

- **GIVEN** an expected scanner is unavailable or an eligible input is omitted
- **WHEN** independent static analysis runs
- **THEN** it fails with actionable evidence before successful release or merge status can be reported

#### Scenario: Independent CI invokes the replacement and retains Bandit

- **WHEN** the independent static-analysis workflow checks a candidate
- **THEN** it runs the Python SAST command with the reviewed baseline, retains Bandit at its existing severity and scope, and uploads available evidence on failure
- **AND** a new finding or incomplete input from the Python SAST command fails the job
