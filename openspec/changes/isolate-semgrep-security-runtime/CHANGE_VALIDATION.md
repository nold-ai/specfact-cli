# Scope validation

Checked 2026-10-22 Europe/Berlin against main 5262efb0 in the dedicated release
worktree. This phase implements issue #780 release preparation, with parent #747.
The coordinating agent verified Todo status, labels, project, and hierarchy.
The dev change was read as context. Its admission artifacts and dev-only CI
changes are excluded. Genuine main native RED is required before production edits.
That initial status is historical. The 23-case correction was subsequently accepted
and authenticated native RED ran at 8cce44f449e9559d0100064d629c81991784ab41.

The owner explicitly approved the virtualenv correction on 2026-10-22. The
coordinator rechecked issue #780 as OPEN/Todo with labels, project, and hierarchy
intact, and updated the internal wiki mirror and rebuilt its graph. The corrected
release selects nine changed Python packages relative to main. That correction received independent acceptance and native RED.

The owner separately approved GitPython 3.2.1 and the exact opentelemetry-api
1.37.0 exception on 2026-10-22. Fresh independent mapping acceptance for this new correction is recorded in
requirements-proof/advisory-mapping-review.md. Only new native RED remains pending. All twelve saved production paths
were verified and backed up before restoration to HEAD. The four independently
reviewed fixture corrections are retained unchanged. The coordinating agent owns
the matching internal wiki update and has reported its graph rebuild complete.
