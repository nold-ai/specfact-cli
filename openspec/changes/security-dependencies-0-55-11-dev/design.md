# Design

The data contract is the reviewed package/version table, two public dependency
floors and two distinct advisory records. The existing frozen refresh and audit
implementations remain the source of behavior. No new dependency resolver or
advisory engine is needed.

Use a new change root because Requirements selects the complete mapping for
each changed root. Editing the delivered `isolate-semgrep-security-runtime`
mapping would incorrectly demand new RED for cases already passing on dev.
Keep that root and all historical evidence byte-identical.

Tests inspect the canonical lock/export and metadata, invoke the existing audit
gate with concrete hostile inputs, and exercise the frozen GitPython API with
the clone boundary observed. Passing preservation and negative controls run
alongside the selected genuinely failing cases but are not labeled RED.

Only scoped hunks may enter existing dev files. Preserve its third audit,
runtime-smoke graph, native artifact transport, trusted planning/proof bases and
all other runtime behavior. Reuse reviewed official artifact metadata, then
regenerate and verify the lock/export with normal tooling. Never hand-edit the
generated dependency lists to force a resolver result.

CI-only Git signing must bind the reviewed tree, exact dev parent and a new
create-only branch using existing permissions. It grants no shared-history
rewrite, protected ref change or merge. The test-only prefix must remain
separate from later production commits.

Native bootstrap is an explicit open delivery dependency. The base's expired
parser record prevents test execution; changing that production record in the
RED prefix is not a native proof fix. The concrete trusted bootstrap or exact
admission prerequisite needs independent review and any separate protected
deployment approval before adoption. No implementation is claimed here.

Rollback before merge is disposal of the unmerged candidate branch. A later
merged dependency correction can be reverted through an ordinary reviewed PR.
