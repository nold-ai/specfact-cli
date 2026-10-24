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
It SHALL disable proxies and automatic redirects, use bounded time and response bytes,
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

### Requirement: Explicit bounded current-log continuation

The observer SHALL retain the initial API response and follow only logs redirects
with statuses 301, 302, 303, 307, or 308, using at most three fresh storage GETs.
Every Location SHALL be a single nonempty absolute HTTPS URL with a proper
subdomain of `.blob.core.windows.net` or `.actions.githubusercontent.com`.
Controls, whitespace, malformed URLs, credentials, ports, fragments, suffix
roots, IP addresses, trailing dots, deceptive suffixes, and other origins SHALL
be rejected before I/O. Every hop SHALL be revalidated. Storage requests SHALL
carry only the application's fixed User-Agent, without the API bearer, API
headers, cookies, or ambient proxies. Jobs redirects SHALL stop before logs.

#### Scenario: Redirect evidence and credentials remain separate

- **GIVEN** matching jobs and a logs redirect to permitted storage
- **WHEN** the observer follows up to three redirects
- **THEN** API requests carry the bearer and every storage request is token-free
- **AND** each response retains its own actual status, exact bytes, hash, length, Date, and request ID
- **AND** initial `current-job-logs.raw` remains separate from `current-job-logs-storage-01.raw` through `-03.raw`
- **AND** storage endpoint metadata is a fixed label, and Locations persist only as presence and digest

#### Scenario: Invalid or exhausted continuation stops with evidence

- **GIVEN** a rejected Location or a fourth logs redirect
- **WHEN** the observer evaluates that response
- **THEN** it retains the received response and exits nonzero without a request to that destination
- **AND** safe metadata contains a fixed failure code and no fabricated terminal summary

#### Scenario: Bounded payload and transport failure preserve earlier evidence

- **GIVEN** a logs continuation with earlier retained responses
- **WHEN** a terminal body reaches exactly 4 MiB
- **THEN** the complete body is retained with the actual HTTP status, including a non-200 status
- **AND** a larger body, timeout, URL error, or body-read failure exits nonzero with a fixed sanitized code and `response_retained=false`
- **AND** prior responses remain intact, incomplete bytes are not saved as a complete raw payload, every response closes, and no retry occurs
- **AND** a direct API or storage body shorter than its advertised `Content-Length`, for HTTP 200 or an HTTP-error response, exits 1 with `body-read-failed` even when the partial bytes contain the exact marker
- **AND** that incomplete response records its actual HTTP status, `response_retained=false`, and an actual local UTC body-finish timestamp without a raw payload file or terminal observation-only summary

Failure metadata SHALL attach `failure_reason` to the latest safe response
record, using `redirect-location-invalid`, `redirect-limit-exceeded`,
`response-too-large`, `transport-unavailable`, or `body-read-failed` as applicable.
An incomplete received body SHALL retain its actual status. A failure before
receipt SHALL retain null status. Neither SHALL claim a complete payload.

### Requirement: Current marker visibility remains a separate observation

After exact jobs validation, the observer SHALL print one flushed runtime marker
before requesting logs, without sleep or another jobs request. The marker SHALL
be `PR785_CURRENT_JOB_OBSERVER run=<run> attempt=<attempt> job=<job> event=<event-sha> workflow=<workflow-sha> phase=before-log-fetch`.
`marker-emission.json` SHALL record `marker` and `emitted_at_utc` after flushing.
Each completed exchange SHALL record local UTC `request_started_at_utc` and
`body_finished_at_utc` bounds without interpreting HTTP Date as ingestion delay.

#### Scenario: Exact terminal bytes determine marker count

- **GIVEN** a complete terminal response, directly from the API or through allowed storage
- **WHEN** its raw byte lines are compared with the independently constructed marker
- **THEN** only a whole bare marker or `YYYY-MM-DDTHH:MM:SS[.fraction]Z` plus one ASCII space and the whole marker counts, using ASCII digits and LF or CRLF
- **AND** substrings, trailing text, lossy decoding, and markers with different run, attempt, job, event, or workflow identity do not count
- **AND** `log_measurement` records `terminal_response`, `http_status`, `payload_retained`, and `marker_matches`, where zero is absent, one is observed once, and more than one is ambiguous
- **AND** a non-200 terminal response cannot establish visibility even if its body contains the marker

#### Scenario: Lagging steps and marker observations grant no authority

- **GIVEN** jobs report checkout in progress, observer and named future steps pending, and a post step numbered 10
- **WHEN** the observer completes its single bounded measurement
- **THEN** it preserves the full step list and numbers without normalization or polling
- **AND** authority and policy execution remain false, compatibility remains unjudged, and local marker evidence makes no current hosted availability claim
