## ADDED Requirements

### Requirement: Isolated manual read-only prerequisite workflow

The auxiliary diagnostic SHALL execute only by manual dispatch, with one
five-minute job on `ubuntu-24.04`, empty workflow permissions, and job-scoped
contents/actions read. It SHALL have no policy, installation, signing,
deployment, write permission, or authority path.

#### Scenario: Isolated manual read-only prerequisite workflow

- **GIVEN** the isolated `codex/pr785-runtime-prerequisites` diagnostic branch
- **WHEN** Actions evaluates its `specfact.yml`
- **THEN** only an input-free manual dispatch can start one `platform-prerequisites` job
- **AND** the job has the fixed runner, five-minute timeout, and exactly contents/actions read permissions

### Requirement: Immutable observation invocation and durable upload

The diagnostic SHALL use immutable checkout/upload action pins, checkout the
event commit without persisted credentials, and invoke isolated platform Python.
Its complete four-step sequence SHALL retain two explicit future steps. It SHALL
always attempt upload of the observation directory using an identity containing
the actual run, attempt, and event commit, with missing files treated as an error.

#### Scenario: Immutable observation invocation and durable upload

- **GIVEN** a manually dispatched diagnostic job
- **WHEN** Actions executes its steps
- **THEN** immutable checkout precedes the sole isolated observer invocation
- **AND** the fixed future marker and immutable upload follow that invocation
- **AND** upload always attempts `platform-prerequisite-observations/` under the run/attempt/commit artifact identity and fails if no files exist

### Requirement: Bounded current-job evidence has no authority

The observer SHALL validate the fixed repository, event, job, workflow reference,
and distinct event/workflow revisions. It SHALL make one attempt-specific jobs
GET and at most one matching current-job logs GET using existing read access.
It SHALL disable proxies and redirects, use bounded time and response bytes,
and perform no retry or polling. Received response records SHALL bind retained
bytes to their endpoints and metadata without serializing secrets or redirect
URLs. Transport failure before a response SHALL remain distinct from an HTTP
response. Results SHALL preserve raw step observations and remain unjudged.

#### Scenario: Bounded current-job evidence has no authority

- **GIVEN** the exact fixed manual context and the existing read-only token
- **WHEN** the observer requests the attempt jobs and, only after a matching in-progress job, its logs
- **THEN** it retains each bounded received response with status, request ID, date, byte count, and digest
- **AND** any pre-response transport failure records null status and no retained response, then exits nonzero
- **AND** the observation identifies actual run, attempt, job, both revisions, raw steps, and expected future steps without a compatibility or authority verdict
- **AND** a redirect, missing evidence, upload success, or future-step list establishes no policy execution, admission, or deployment readiness
