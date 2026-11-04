# Bounded signer contract

The domain is a frozen intent, dispatch expectation, live run context and six
truthful outcomes. One public operation owns validation and both writes.
Private `_request(method, path, body)` is the sole transport seam. It returns
HTTP status and raw JSON bytes so tests can distinguish definite 404 from
transport errors and exercise strict JSON decoding. Tests replace that seam;
no public stage API or generic signing framework is introduced.

Intent JSON has exactly repository_id, repository_full_name, actor,
triggering_actor, dev, main, source_commit, source_tree, delta, auxiliary_ref,
destination and message_stem. Actor objects have exactly id/login. Delta
objects have exactly path/before/after; each non-null entry is [mode, blob SHA].
Reject duplicate or unknown keys at every intent object level, wrong primitive
types (including bool-as-int), invalid hashes, unsafe/duplicate paths and modes.
Only the exact reviewed changed paths in D are eligible; production, auxiliary
signer and workflow changes are forbidden. Unchanged production/executable
leaves and directory entries are valid in the authenticated complete trees. The exact intent digest binds the complete approved path set.

Source S must resolve to T and have exactly the sole parent
`4ae6175a4d337296d0347e73b66c9da1f0e43f7f`. Complete dev-tree and T leaf inventories must prove
the exact delta including additions, deletions, blob changes and mode changes.
Reject truncated or malformed inventories. Source ancestry never enters the
created commit. Tests include complete recursive inventories with directory records; complete
traversal is a valid later implementation alternative.

Before and after each mutation verify numeric/full repository identity; workflow
204352514 at .github/workflows/specfact.yml; workflow_dispatch; exact actor and
triggering actor numeric/login identities; run ID, attempt 1, in_progress and E;
auxiliary ref E; frozen dev/main; destination absence before creation and exact
created SHA afterward. Ref objects must name the requested ref and be commits.
A complete workflow run listing must rule out another dispatch for E or a prior
attempt. Any incomplete observation refuses. Workflow concurrency configuration
and independent actual run SHA review remain root-owned requirements.

At every existing guard boundary PR786 must remain open, non-draft and without
auto-merge; its head SHA must equal the fixed reviewed parent on the intended
feature ref/repository, and its base must remain dev at the frozen dev SHA in
the intended repository. The frozen dev baseline remains
`9b5ad1e78430cc0b061cb16de42f73de96f4f312`; frozen main remains intent-bound.
The new auxiliary/destination refs and exact 19-path allowlist are specified in
the proposal. Old refs and unreviewed deltas refuse. No schema, public API,
workflow, permission or pinned runtime change is included.

Only POST /git/commits and POST /git/refs may mutate. The first request has
exactly tree, parents and message, omitting author/committer/signature. Message
is message_stem followed by a blank line and Intent, Executor, Run, Attempt
lines. The only parent is the frozen reviewed PR786 head
`4ae6175a4d337296d0347e73b66c9da1f0e43f7f`, in both API data and signed payload. Require POST and GET commit agreement, valid
GitHub verification, nonempty signature and exact signed payload. Author is
github-actions[bot]/41898282/Bot with Git name github-actions[bot] and email
41898282+github-actions[bot]@users.noreply.github.com. Committer is
web-flow/19864447/User with Git name GitHub and email <noreply@github.com>.
Signed headers contain exactly tree, parent, author, committer, with decimal
timestamps and signed four-digit offsets. API attribution must match roles.

Receipt outcomes are published, refused, object_only, uncertain_commit,
uncertain_ref and created_ref_with_drift. Receipts retain intent digest,
executor/run identity, known commit SHA, observed ref SHA, signature/payload
and reason where available. Known commit with later verification/guard failure
is object_only. A write timeout or ambiguous response is uncertain, even if a
subsequent read observes the expected object/ref. Read-only reconciliation
never upgrades uncertainty to published. No mutating request retry, PATCH, DELETE, recovery,
rollback or tree-construction fallback exists. Drift after known ref creation
is created_ref_with_drift and requires review.

Synthetic transport tests specify contract behavior. Until implemented, scaffold
failures establish missing implementation only. They do not prove
GitHub signature creation or cryptographic validity. Root must retain live
GitHub valid verification and independently fetch and compare the raw commit
SHA, tree, sole parent, message, signature and reconstructed unsigned payload.

## Normal-gate correction

Normal Code Review rejected the unimplemented scaffold as an unused transport
and missing public runtime contract. The spec/test/failing-evidence order is
already retained; a separate scaffold commit is not accepted or bypassed.
The implemented utility will use the already-reviewed exact five-package CI
contract-tool closure from the earlier auxiliary signer. This supplies real
icontract and beartype checks without bootstrapping the subject graph or adding
a hook exception. The source tree delivered to dev excludes this auxiliary
closure and executor. Final independent review must assess this design delta.

## Owner-selected 0.55.12 binding refresh

The existing finite signer remains the only publication owner. Root its source/output chains at accepted CI-signed R3 d77209f4b13c386e29391f93e1f1c58d7fd8622f. Add only src/__init__.py and src/specfact_cli/__init__.py to the existing changed-path allowlist because the unchanged version gate requires both canonical version constants for0.55.12. Preserve every other path restriction, all checkpoint/schema/message/delta/signature/actor/ref/run/uncertainty/resource guards and HTTP operations. Do not add a mode, API, wildcard, launcher or framework.

COPY keeps exactly four authenticated actual native36 members, separate from fixture metadata. Pin metadata SHA256 e491e7ce89edf6a5c4299dc0d723cb9a3ff90573c062b45269da13f963a65617 and synchronize the existing fixed COPY artifact label to native36 in signer and consumers. These fixture bytes are from accepted original artifact13269307808/run41715861806; no new native execution or origin credit follows. Keep runtime lockbc64 byte-identical and the existing unused auxiliary/destination ref names.

First update the existing Synthetic API fixtures and add two public publication cases for these exact initializer paths. Require their before result to refuse the unreviewed path before any API write. Then normal TEST, three finite program binding edits plus the two paths and COPY label, all existing preservation cases, fresh independent exact review and normal hooks. The intent stays explicitly UNBOUND until complete normal source history and actual API messages exist. This candidate grants no dispatch, protected integration, final-head provenance, publication/release or merge authority.

## Bounded observation after acknowledged ref creation

Run 41788765186 remains failed and consumed. Its authenticated receipt records
fourteen verified service objects, an acknowledged exact ref creation and an
immediate missing-ref observation. A later read found the expected ref. This
does not identify a cache or replica cause and cannot promote the old receipt.

In a new invocation, retain the existing first ref observation after HTTP201
and its exact response-schema check. Only a definite HTTP404, represented by
None, permits one 60-second wait and exactly one additional GET of that same
ref. Then require the exact expected SHA, final signature/attribution readback
and every final live guard. A second missing observation still fails.

Do not wait or repeat an observation after a wrong SHA, malformed response,
non404 status, read exception or uncertain POST. Never repeat a POST. This is
a finite observation policy, not a guarantee of service visibility. Keep the
30-second request timeout, ten-minute job limit and all other caps unchanged.
The maximum added wait and request time is 90 seconds.

The correction stays inline in publish_once. The existing_ref, _request,
outcome schema, public signatures, workflow and runtime remain unchanged.
Patch standard-library time.sleep in the two existing Synthetic fixtures so
test setup succeeds before the production import exists. Record actual
before failures at finite.publish, then pass the same cases after CODE.

Any later operation uses new exact refs and a new frozen intent. Preserve
every consumed ref, object, artifact and source checkpoint. Bind the corrected
program digest and new exact refs in the existing core owner, its shared
workflow branch literal and existing integration fixtures. Keep all eight
native proof inputs identical to R3. No new framework or waiver is included.

The forward correction uses the fresh exact executor ref `refs/heads/codex/dev786-complete-ci-signer-20261104` and destination `refs/heads/codex/security-dev-complete-candidate-20261104`. Both older operation refs remain consumed and immutable. These are finite bindings within the existing source/authority contract, not a new mode or a retry of the failed operation. Source data remains UNBOUND until the reviewed complete core and its actual API messages are frozen.
