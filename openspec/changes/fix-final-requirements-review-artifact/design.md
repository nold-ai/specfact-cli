# Design: Final Requirements review artifact handling

## Decision

The final Code Review step writes a fixed `review-required` output. It defaults
to `false` before changed Python paths are inspected and changes to `true` only
after at least one existing `*.py` or `*.pyi` target is collected and before the
review command executes.

The existing R07 boundary remains unchanged: Requirements reconciliation owns
the authenticated add/modify/delete/rename diff, while file-oriented Code
Review receives only paths present in the checked-out head. A deletion-only
change therefore has no final review target; a mixed change reviews every
remaining present Python target.

The artifact upload runs with `always()` only when that output is exactly
`true`. Its existing `if-no-files-found: error` remains unchanged. The later
verdict-enforcement step also remains unchanged.

This creates three explicit outcomes:

1. No existing Python targets, including metadata-only and deletion-only diffs:
   review succeeds, output remains `false`, and no report is expected or
   uploaded.
2. Existing Python targets, including the present side of mixed diffs, and a
   successful review: output is `true`, and the report is required and uploaded.
3. Existing Python targets and failed review: output is already `true`, so any
   produced report is retained; a missing report and the failed review both
   remain blocking.

If changed-path discovery or another pre-target operation fails, the review step
fails and the existing enforcement step blocks the job even though no artifact
was declared required. This does not convert operational failure into a pass.

## Alternatives

- Changing `if-no-files-found` to `ignore` or `warn` was rejected because it
  would accept missing evidence for real Python review targets.
- Creating an empty report on metadata-only pull requests was rejected because
  it would represent a review execution that did not occur.
- Adding an artificial Python change to PR #706 was rejected because it would
  enlarge release scope and merely hide the workflow defect.
- Inferring artifact necessity again in the upload step was rejected because
  the review step already owns the exact filtered target set.
- Blocking deleted paths was rejected because it contradicts the accepted R07
  file-oriented review contract and would make legitimate deletion-only and
  mixed pull requests unmergeable.

## Security and compatibility

Only fixed literal values are written to `GITHUB_OUTPUT`; no repository path or
candidate-controlled value is emitted. The existing changed-path validation,
trusted toolchain, isolated review context, artifact action pin, strict missing
file behavior, and final verdict enforcement remain intact.

GitHub Actions step outputs are the narrow control channel between the review
and upload steps. The condition compares the output to the exact string `true`;
missing or different values cannot authorize an artifact upload or suppress a
failed review verdict.

## Rollback

Revert the workflow and test commit. No data migration, published artifact
rewrite, dependency rollback, or package version change is required.
