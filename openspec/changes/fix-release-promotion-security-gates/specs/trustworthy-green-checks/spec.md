## ADDED Requirements

### Requirement: Privileged dependency caches are non-persistent

Repository workflows that execute separately checked-out fixture code SHALL NOT
restore or save persistent package-manager caches in the same job. Advisory
compatibility jobs SHALL execute only from protected scheduled workflow bytes
and SHALL verify the fixture commit and tree before exporting its path.

#### Scenario: Shared frozen setup disables persistent uv caching

- **GIVEN** a required or advisory job uses the shared frozen Python setup
- **WHEN** the setup action installs the committed dependency graph
- **THEN** setup-uv SHALL have caching disabled
- **AND** later fixture execution SHALL NOT receive a persistent cache save capability.

#### Scenario: Compatibility fixture is schedule-only and immutable

- **GIVEN** the repository runs the optional dependency compatibility lane
- **WHEN** the workflow checks out the companion module fixture
- **THEN** the lane SHALL be reachable only from the scheduled event
- **AND** the checked-out commit and tree SHALL equal the committed fixture lock
- **AND** the module path SHALL be exported only after both checks pass.

#### Scenario: Post-fixture Node setup does not restore npm state

- **GIVEN** a workflow has already checked out or executed companion fixture code
- **WHEN** it installs the committed Code Review Node dependencies
- **THEN** the Node setup SHALL NOT restore or save a persistent npm cache.

### Requirement: Proof and review execute across a clean authenticated boundary

Requirements proof execution SHALL NOT inherit GitHub credentials. The workflow
SHALL run final Code Review in a separate fresh job and runner from candidate
proof execution. That review job SHALL clean-checkout and authenticate the exact
pull-request head, recreate and validate its frozen review environment before
downloading proof data, and consume the producer artifact by immutable artifact
identity.

#### Scenario: Proof tests cannot mutate the later review toolchain

- **GIVEN** candidate proof tests run before Code Review
- **WHEN** the proof step completes
- **THEN** the workflow SHALL persist only the expected evidence files and start a fresh review runner
- **AND** SHALL clean-checkout and authenticate the exact head commit before synchronizing the frozen review environment
- **AND** SHALL install frozen tools before downloading the producer output by immutable artifact identity
- **AND** SHALL verify the immutable module fixture and fail closed if changed-path enumeration fails before Code Review.

#### Scenario: Proof execution has no credential-bearing ancestor

- **WHEN** one-time bootstrap metadata requires GitHub API access
- **THEN** a separate bounded step MAY retrieve the fixed metadata with a token
- **AND** the proof-producing step and its child processes SHALL NOT receive `GH_TOKEN` or `GITHUB_TOKEN`.

#### Scenario: Proof validators cannot inherit repository startup hooks

- **GIVEN** the checked-out repository and its selected tests are untrusted proof inputs
- **WHEN** the workflow starts the proof executor, provenance validator, or bootstrap-authority validator
- **THEN** Python site startup, `.pth` files, and `sitecustomize` SHALL be disabled before repository bytes execute
- **AND** installed proof dependencies SHALL be added explicitly without processing repository-controlled startup hooks
- **AND** any isolated install from `requirements/ci/locked.txt` SHALL follow successful proof that it is the exact reproducible closure of `uv.lock`.

#### Scenario: Candidate tests cannot replace prefetched external evidence

- **GIVEN** retained proof or one-time authority bytes are fetched before candidate tests execute
- **WHEN** those bytes are consumed after the test process returns
- **THEN** the workflow SHALL verify their exact prefetched digests immediately before consumption
- **AND** retained red proof SHALL be authenticated against the completed failing Requirements workflow run for the same repository and pull-request branch
- **AND** SHALL download exactly one unexpired Requirements artifact by its immutable artifact identity
- **AND** the workflow run head, artifact run/head metadata, and proof source commit SHALL match exactly
- **AND** any missing or changed byte or identity SHALL fail closed.

#### Scenario: Governed paths remain exact across local and external history checks

- **GIVEN** Git permits paths containing tabs or other characters that text output quotes
- **WHEN** bootstrap history or staged pre-commit paths are classified
- **THEN** every Git record SHALL be status-checked and parsed as NUL-delimited bytes
- **AND** bootstrap red history containing a merge commit SHALL fail closed
- **AND** every staged Python path SHALL reach both lint and Code Review classification.

#### Scenario: Required Requirements context cannot be manually minted

- **GIVEN** branch protection requires the `Requirements evidence` GitHub Actions context
- **WHEN** the Requirements workflow is invoked
- **THEN** only a `pull_request` event targeting `dev` or `main` SHALL be able to emit that context
- **AND** no manual caller-controlled base branch SHALL be accepted by the required workflow.
