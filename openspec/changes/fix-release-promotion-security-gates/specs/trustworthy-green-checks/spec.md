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
identity. Mapped tests and the production code they intentionally import SHALL be
review-trusted and assumed not to deliberately tamper with the same-process
pytest runner, its exit status, or its JUnit channel. This requirement SHALL NOT
claim sandbox containment of intentionally hostile Python executed by pytest.

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

#### Scenario: Fresh reconciliation executes the trusted plan independently of producer results

- **GIVEN** producer-side executors, proof plugins, dependency graphs, and uploaded JUnit are untrusted inputs
- **AND** the approved mapped tests and imported production code follow the documented non-hostile same-process assumption
- **WHEN** the required Requirements context evaluates final mapped proof
- **THEN** the fresh consumer SHALL derive and validate the exact plan with authenticated base-branch proof code
- **AND** SHALL independently execute every selected test with installed pytest and the authenticated base-branch proof plugin
- **AND** SHALL disable candidate conftest discovery, candidate pytest configuration, and candidate `addopts`
- **AND** SHALL bound proof execution time
- **AND** SHALL reconcile only the consumer-generated JUnit so producer-uploaded pass results alone cannot mint the final verdict.

#### Scenario: Fresh reconciliation selects the producer's active change

- **GIVEN** multiple active changes contain accepted review-evidence records
- **WHEN** one active change is amended without rewriting its accepted review-evidence record
- **THEN** the fresh consumer SHALL select that change from the same changed active OpenSpec paths as the producer
- **AND** SHALL reject zero or multiple changed active changes before consuming review evidence.

#### Scenario: Every frozen-graph verification uses an isolated trusted interpreter

- **GIVEN** candidate repository startup paths can affect ordinary Python invocation
- **WHEN** the fresh consumer verifies the frozen closure before either isolated install
- **THEN** each verification SHALL use the same explicit `-I -S` bootstrap and trusted dependency directory
- **AND** no direct candidate-context Python execution SHALL perform a closure verification.

#### Scenario: Late review amendments retain exact test-first evidence

- **GIVEN** a mapped review correction is added after production commits already exist on the pull request
- **WHEN** an ordinary same-branch RED report is classified as final against the original base
- **THEN** one expiring member authority MAY bind the exact final pull-request commit and tree
- **AND** a final-tree-bound manifest SHALL bind the exact repository, issue, pull request, branch, cycle base, RED commit, run, artifact, service digest, file digests, mapping, plan, and failed selectors
- **AND** SHALL revalidate all live identities, linear ancestry, test-only history, artifact bytes, and selected test freshness before reconciliation
- **AND** all unbound, changed, nonlinear, non-test, or expired amendment evidence SHALL fail closed.

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

#### Scenario: Local version checks preserve one patch release across follow-up commits

- **GIVEN** a change branch already contains one complete synchronized version bump and changelog entry relative to its fetched target branch
- **WHEN** a later commit updates package metadata without changing the declared version
- **THEN** the staged version gate SHALL validate the complete change against that target branch
- **AND** SHALL NOT require another version increment for the same unreleased change
- **AND** a later staged version change SHALL still be a strict increment over the branch HEAD
- **AND** staged deletion of release evidence SHALL fail rather than reuse committed bytes
- **AND** CI SHALL fail closed if its explicit base revision cannot be resolved.
