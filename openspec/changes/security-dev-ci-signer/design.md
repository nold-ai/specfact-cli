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

Source S must resolve to T. Complete dev-tree and T leaf inventories must prove
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

Only POST /git/commits and POST /git/refs may mutate. The first request has
exactly tree, parents and message, omitting author/committer/signature. Message
is message_stem followed by a blank line and Intent, Executor, Run, Attempt
lines. The only parent is dev. Require POST and GET commit agreement, valid
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
never upgrades uncertainty to published. No retry, PATCH, DELETE, recovery,
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
