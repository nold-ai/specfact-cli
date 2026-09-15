# Required check trigger design

The missing status occurs before any job executes. Remove only `pull_request.paths` in `docs-review.yml` and `pull_request.paths-ignore` in `specfact.yml`. Preserve the explicit supported target branches and the existing push filters. Existing job success/failure behavior remains the authority; no synthetic pass job or manual dispatch substitutes for execution.

A parameterized regression parses both real workflow files. For each workflow it requires a native pull-request event without path filters, both supported branches, the existing unconditionally scheduled required job name, and its existing push filtering. The two tests fail against the unchanged workflows before implementation and pass after the trigger-only change. CI must independently observe the actual native pull-request checks.

The `.github/` paths are classified as verified implementation by the existing Requirements workflow. A new immutable RED test/mapping commit is therefore retained before applying production edits. Do not reuse or modify the prior documentation proof or change authority rules. Test and mapping bytes remain frozen between RED and GREEN.

## Review follow-up within supported PR handling

A native fork pull request has a read-only token; optional comment publication must be guarded by same-repository identity so the newly admitted required check remains usable. Preserve report creation/upload and the existing validation failure step. Supplemental regressions compare the complete unchanged push lists and require the same-repository condition on the optional comment step. These are separate from the frozen two-case Requirements proof. Record actual local failing-first evidence for the comment guard, passing evidence, and mutation evidence for complete-list preservation without claiming those supplemental cases are part of the original protected mapping. The unchanged canonical Requirements validator must accept the original retained proof after this additive follow-up.
