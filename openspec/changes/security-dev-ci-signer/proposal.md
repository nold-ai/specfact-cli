# Create-only dev security CI signer

## Why

The reviewed dev security snapshot needs a fresh CI service signature before a
blocked draft can be opened. Historical PR785 signing evidence grants no new
scope. This auxiliary executor must never become the target tree.

## What changes

Add one bounded `publish_once(intent_file, expected, context)` operation.
Authenticate an uploaded source commit/tree and its entire dev-relative leaf
delta. Create one signed commit with the frozen dev SHA as its sole parent,
then create the initially absent fixed destination ref. Preserve partial and
uncertain outcomes without retries or cleanup.

This auxiliary change contains the reviewed specifications, synthetic tests and
implemented bounded runtime. Root froze source 3752d92a9c895eef726ec336c3ae212f06e2dc52,
tree baeb88acf0d2a5015810ad12dbfccfa7fdf9a21e and the exact 17-path test-only
delta in frozen-test-source.json, and prepared the auxiliary intent. Remote
executor review, freshness checks and real CI delivery remain pending. This
artifact establishes neither native acceptance nor runtime readiness.

## Dependencies and limits

Root owns input freezing, GitHub metadata readiness, normal checks, independent
remote executor/intent review, the single real CI invocation, live verification
and raw fetched-object comparison. Native bootstrap remains separately blocked.
The internal wiki mirror and change-order registration are root follow-ups
outside this delegate's exclusive paths. No claim is made that either is done.
