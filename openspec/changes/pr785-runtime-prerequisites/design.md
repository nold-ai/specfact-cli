# Bound the prerequisite observation

## Accepted source and scope

The accepted private proposal was reviewed on 24 October 2026, Europe/Berlin.
Its observer SHA-256 is
`97fb5ece29bef1ed62c92754f86503edfff46517934376cf908162dc5b09b2f1`.
Its workflow SHA-256 is
`6365d76590ba5804e4ae98c51ab7f70ed2eb62f487d1c30dd9cef8ec63d31ab4`.
The coordinator retains the independent review and formatting reconciliation.
This test/spec unit adds neither accepted production artifact yet.

One disposable job uses the existing Actions-read token. Its only service
operations are one attempt-specific jobs GET and at most one logs GET for the
selected current job. There is no policy reader, protected runtime, package
installation, namespace operation, signer, deployment, or authority consumer.

## Workflow contract

The workflow has only `workflow_dispatch`, empty top-level permissions, and one
`platform-prerequisites` job on `ubuntu-24.04` with a five-minute timeout.
Job permissions are exactly contents/actions read. There is no workflow input,
job environment, service, matrix, container, or elevated permission.

Four explicit steps preserve the observed future-step boundary:

1. `Checkout immutable observer` pins checkout to
   `df4cb1c069e1874edd31b4311f1884172cec0e10`, uses `github.sha`, and disables
   persisted credentials, submodules, and LFS.
2. `Observe current job boundary` receives only the existing token as its explicit
   step environment and runs
   `/usr/bin/python3 -I -S -B scripts/pr785_runtime_prerequisite.py`.
3. `Future step marker` prints the fixed observation-only marker.
4. `Upload prerequisite observations` always attempts the pinned upload action
   `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`, uploads only
   `platform-prerequisite-observations/`, and fails when no files exist.

The artifact name includes actual run ID, attempt, and event commit. Upload
success means persistence was attempted successfully. It does not judge the
response evidence. These workflow invariants are the local tests' complete
claim. Their initial failures are structural contract mismatches against normal
validation, not a reproduced GitHub service failure.

## Request and observation contract

The fixed context requires repository `nold-ai/specfact-cli`, event
`workflow_dispatch`, job `platform-prerequisites`, and workflow reference
`nold-ai/specfact-cli/.github/workflows/specfact.yml@refs/heads/codex/pr785-runtime-prerequisites`.
Run and attempt are bounded positive decimal identities. Event commit and
workflow revision are independently validated 40-hex values and remain distinct
in the output, with equality recorded only as an observation.

The observer disables environment proxies and does not follow redirects. It
uses only `https://api.github.com/`, a 30-second request timeout, and a 4 MiB
response-body limit. It never retries or polls. The jobs response must identify
exactly one matching current in-progress job, with the actual run, attempt,
event commit, empty conclusion, and positive integer job ID before selecting
the logs endpoint. Invalid or unavailable jobs evidence prevents that request.

`jobs.raw` and `current-job-logs.raw` retain bounded received response bytes.
`responses.json` binds each received response to endpoint, status, request ID,
date, byte count, and SHA-256. Redirect location is presence and digest only.
No token, Authorization value, signed redirect URL, or exception text is output.
Pre-response transport failure records `http_status=null`,
`transport=unavailable`, and `response_retained=false`, then exits nonzero.
Oversized responses and failures during body reading are process failures and
cannot be claimed as complete retained response evidence.

After selecting the current job and observing its logs endpoint,
`observation-only.json` records run, attempt, job, both revisions, fixed context,
raw observed steps, and the two expected future-step names. Its kind is
`platform-prerequisite-observation`, compatibility is `unjudged`, authority is
false, and policy execution is false. These labels describe the result. The
absence of policy execution and authority paths enforces the boundary.

## Verification and limits

Two local tests read the actual workflow with PyYAML's BaseLoader. They assert
manual/read-only/bounded configuration and the isolated invocation plus durable
upload contract. They require neither candidate import nor application fixtures.
They do not test the observer's HTTP internals with constructed responses.

Transport restrictions, context validation, and output fields need independent
source inspection. Actual current-job availability, response status/body,
future-step representations, and action markers need one separately coordinated
hosted observation with authenticated source, workflow, run, attempt, job, and
artifact readback. Those checks remain open after local GREEN.

A 302 is a redirect observation. It supplies no downloaded logs or action
markers. Missing or denied evidence leaves the prerequisite unestablished.
Neither a future-step list nor any diagnostic success establishes compatibility,
namespace support, actual-P execution, closure, admission, or deployed readiness.

The auxiliary workflow deliberately differs from native validation. Existing
native-trigger tests remain unchanged and must not be weakened to accommodate
it. This branch is not a protected-branch workflow replacement.

## Failure modes and rollback

Unavailable current-job logs leave the reader prerequisite unresolved. Preserve
the actual status and bytes, then revise the observable design without waivers.
An incomplete step list leaves the future-step prerequisite unresolved. Compare
it independently with the full authenticated workflow. A source or context
mismatch stops the observation before the logs request.

Abandon the isolated branch or revert it through normal review. No installed
runtime or host mount needs cleanup because this diagnostic creates neither.

## Test-first continuation addendum on 24 October 2026, Europe/Berlin

The original request description above is historical. The newly agreed command
contract preserves the explicit no-redirect urllib opener and adds a logs-only
loop over at most three validated storage destinations. Every response has its
own bounded raw file. The response state separates actual status and bytes from
transient Location and Location count. Marker visibility is a separate result.
No workflow edit, generic redirect callback, policy client, retry, or delay is
part of this unit.

The exact destination, body, marker, metadata, and failure contracts are in the
new requirements in `specs/pr785-runtime-prerequisites/spec.md`. Additive output
fields are `marker` and `emitted_at_utc` in `marker-emission.json`, per-response
`request_started_at_utc` and `body_finished_at_utc`, and the four fields under
`log_measurement`. A fixed `failure_reason` annotates the latest safe response
record. Received incomplete bodies retain actual status while failures before
receipt retain null status. Early failures leave no completed summary.

The new tests call the existing `_main` entry. Only HTTPSConnection is replaced
with a recorder that returns real HTTPResponse objects parsed from wire bytes.
The actual opener, Request, handlers, and HTTPError chain remain in use. Tests
assert outbound headers, raw files, hashes, counts, timestamps, and summaries.
Their first regression assertion requires the missing storage request before
checking the new marker metadata. New helper symbols are never imported.
Native pytest uses the existing canonical-selector plugin exactly once.

A non-200 terminal body may contain an exact marker and report its byte count of
matches. Its actual HTTP status remains non-200, so it cannot prove visibility.
A 200 payload with zero matches remains absent, and multiple matches remain
ambiguous. All summaries retain authority false, policy execution false, and
compatibility unjudged. Step statuses and post-step numbers are preserved.

## Short advertised body amendment on 24 October 2026, Europe/Berlin

The shared response-read boundary must distinguish complete bounded bytes from
a body shorter than its advertised `Content-Length`. This applies to ordinary
responses and HTTP-error wrappers on both direct API and storage routes.
A successful bounded read alone does not establish completeness. The incomplete
response must exit 1 with `body-read-failed`, preserve its actual status and local
UTC body-finish timestamp, and keep `response_retained=false`. Earlier complete
responses remain intact. No incomplete raw file or terminal observation-only
summary may be written, even when the bytes contain an exact marker.

The existing real HTTPResponse wire fixture gains only an optional explicit
`declared_length` integer. Its default preserves `Content-Length=len(body)`.
One append-only selector covers direct 200 and 404 plus storage 200 and 404
after an authenticated API 302. The actual urllib opener and HTTPError path stay
in use. No response-read method is replaced. Existing fixture reads enforce the
4 MiB plus one-byte bound, and existing checks enforce response closure and
secret-free output. The twelve earlier transport selectors and two workflow
selectors retain their assertions and loop cases.

Root first runs the frozen fifteen-case baseline against the unchanged observer.
The intended first failure is the new completeness assertion. Existing mapping
review evidence remains historical until fresh independent acceptance. Local
results establish synthetic behavior only. Hosted dispatch remains separately
gated, and the earlier fourteen-case passing evidence remains immutable.
