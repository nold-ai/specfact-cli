## Context and evidence

Issue #662 requested exact linked tests collected and passing in the current CI run. PRs #663/#666/#667/#668 expanded retained chronology into fixture/import freshness. Issue #689 records a real producer/consumer mismatch that blocked a security update. PR #674 separated the claims on paper, but live delivery retained the historical machinery.

Measured additions plus deletions in run transcripts, TDD ledgers, mappings, and review receipts: #730 2,780/4,220 lines (65.9%); #737 460/1,041 (44.2%); #738 614/886 (69.3%). Tests/verifier code are excluded. Successful current Requirements runs took minutes, so PR lifetime is not attributed entirely to CI, and no token-cost estimate is claimed. Inspection date: 2026-09-20.

## Decisions

1. MEB means current observed behavior and relevant validation context. It does not mean complete requirements coverage, absence of defects, or historical TDD compliance.
2. Keep development order: specification -> useful regression tests -> observe the relevant failure where feasible -> implementation -> passing tests. No test-only Git commit or hosted RED run is required. An impractical reproduction needs a brief reason and alternative negative control; setup/import failures do not prove sensitivity to the bug.
3. Reuse normal CI test outputs once per candidate/environment. Bind the receipt to the tested commit/tree, runner/environment identity, selection or command, counts, and artifact references. Keep detailed JUnit/logs in CI artifacts (14 days); retain release integrity records with releases. A PR validation summary normally needs five to ten authored lines, without a line-count gate.
4. A required selected acceptance case must be collected exactly once and produce an ordinary pass without `wasxfail` or equivalent xfail outcome metadata, including empty-valued markers. Failure/error/skip/XFAIL/XPASS/missing/duplicate is not proof. Ordinary full-suite skips remain separately visible under existing suite policy. Missing or malformed required output and wrong revision remain non-passing.
5. The trusted orchestration layer verifies candidate identity and required job/result provenance; project-controlled metadata cannot authorize itself. Preserve existing source/module authentication, least privilege, parser/selector bounds, signing, security, contracts, tests, and independent review. Do not run PR code with signing or repository-write credentials.
6. Build one current report and let Code Review consume it as context without verdict fusion. On dev-to-main, validate the actual promotion candidate; do not reconstruct source-PR history or reuse legacy promotion capsules.
7. Scenario associations are optional for ordinary test context. If supplied, validate them exactly. Without them, requirement coverage is not evaluated; do not report complete intent/coverage. Explicit stronger traceability/chronology policy stays opt-in and retains its stricter failure semantics.
8. Existing preflight/seal/checkpoint work is an optional product capability. Its guarantees remain meaningful inside that explicit mode. It is not a prerequisite to ship C14/C15, native execution, generic skills, or lean generated instructions.
9. R09 replaces the unimplemented R07 correction rather than duplicating its workflow. R08 remains abandoned. No new capsule, seal service, checkpoint tag protocol, AST/import closure inference, or proof-specific caching framework.

## Configured gate migration

| Existing gate | Ordinary MEB handling |
| --- | --- |
| Spec-first and useful failing-before/passing-after work | Retain development order and relevant regression reproduction; note an impractical reproduction and alternative negative control. |
| `TDD_EVIDENCE.md`, committed transcripts and hosted RED proof | Replace the mandatory authored ledger with concise validation notes and current CI artifacts. Preserve historical records and explicit legacy chronology semantics; do not fabricate missing history. |
| `.specfact/code-review.json` | Where the existing code-review gate applies, retain its fresh report for the reviewed candidate before OpenSpec completion, with each finding fixed, rejected with reasons, or covered by an individually authorized documented exception. Reuse the existing review output; no duplicate suite or new committed receipt. |
| Applicable test, contract, lint/type, independent security, signed-module and delivery checks | Retain their actual outcomes and source/authentication checks. Missing required output is not success. |
| OpenSpec validation and archival | Retain strict validation and native archival of completed changes; never apply superseded unimplemented deltas. |

This mapping adds no review run or JSON obligation to planning-only amendments.
It is enacted through the governance preparation below;
planning text alone does not change active hooks, required checks or repository
rules. Independently runnable changes use the effective governance at session
start, or an explicit owner-authorized scope exception, until that migration is
merged. They do not acquire a dependency on the complete R09 runtime rollout.

## Ownership and interfaces

Modules #481 owns current reconciliation, v3 report claims, legacy compatibility, and review-context consumption. Core owns revision selection, safe execution/original job outputs, artifact collection, trusted enforcement and platform integration. The same change ID is paired across repositories; each story owns only its repository's implementation.

Modules add `current` as the default reconciliation stage; explicit legacy `red`/`final` remains supported. V3 separates `current_execution` and `red_green_chronology`; current-only operation reports chronology not evaluated. V2 is read through the explicit legacy path, never inferred from missing v3 fields. No new general profile framework is required for this rollout.

## Bootstrap and rollout

First update and review contributor governance, agent rules, templates and
pre-commit guidance under the owner-authorized MEB migration, before behavior
tests or code. Do not make the migration prove the historical process it removes. Implement and review regression tests under existing code/security checks; use the owner-authorized MEB scope for these changes. If the old required authority gate prevents integration, prepare and review the exact organization/core policy change first and apply the coordinated policy cutover as an explicit migration step. Never add a per-PR bypass or unconditional success job.

The delivery order is reviewed governance preparation -> signed modules #481
publication -> core adoption and trusted pilot -> coordinated repository/organization
cutover, with the module/workflow/policy rollback kept together. Open and integrate
bounded PRs as each slice becomes reviewable; trusted pilot execution uses that
reviewed integrated source. Finalization records those PRs rather than opening
the first PR after deployment.

Run the replacement non-blocking on representative ordinary, bugfix, executable-doc, dependency, fork, and promotion candidates. Verify current checks and trust boundaries before switching both repository and organization enforcement. Do not leave duplicate old/new test execution running for every PR after cutover.

Rollback restores prior module pin, workflow, and required-policy configuration together. Reader incompatibility, missing required checks, and incorrect current-result acceptance are rollback triggers. Historical records remain readable; rollback cannot relabel current-only evidence as chronology.

## Verification and value check

Keep the real defects visible: missing-JUnit (#666), producer/consumer mismatch (#689), skipped/XFAIL/XPASS/coverage acceptance (#737), and independent source authentication (#738). Add integration coverage for a normal PR completing without historical records or authority comments and for independent verdict propagation.

Across ten representative PRs inspect existing GitHub data: proof-only reruns, duplicate execution, manual approvals, artifact-only churn, and detected regressions. Target aggregation under 60 seconds excluding tests/queueing, as an optimization target only. No mandatory cost telemetry or new dashboard.

## Research basis

- [DORA test automation](https://dora.dev/capabilities/test-automation/): useful, reliable automated tests and feedback within ten minutes.
- [NIST SSDF 1.1, PW.8](https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-218.pdf): risk-based testing, retained regressions and documented outcomes.
- [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations): provenance describes origin/build, not correctness or security.

Accessed 2026-09-20. The MEB policy is a repository design decision informed by these sources, not a claim that they prescribe this exact implementation.

## Execution-unit selection

Exactly once is per canonical selector within the current selected candidate/environment/logical suite-or-shard/job-attempt unit, not globally across the matrix. Core derives the required unit set and current designated attempts from trusted CI metadata; each unit must satisfy its expected selector set. Do not cherry-pick older passing attempts when the current designated attempt is pending, failed, cancelled or unavailable. Ambiguous selection or duplicates inside one unit remain non-passing. Modules only compares supplied unit identities alongside the existing plan/source/environment binding. Reuse existing CI metadata and outputs; no historical transcript, extra suite or new approval protocol is introduced.

The shared execution-unit identity SHALL be a compact UTF-8 JSON array with
this fixed field order:
`[candidate_binding, environment_binding, matrix_lane, suite_or_shard, provider, run_id, run_attempt, job_id]`.
Candidate and environment bindings SHALL preserve their existing report/plan
values, types and normalization; the remaining six fields SHALL be strings.
The tuple SHALL NOT replace the existing binding checks.
Matrix lane and suite/shard SHALL use stable configured identifiers, never
ambiguous display names; an absent matrix lane is the empty string. For GitHub,
provider is `github-actions` and run ID, run attempt and actual job execution ID
are canonical decimal strings from trusted metadata (job ID is the actual
execution ID, not the logical `GITHUB_JOB` name); reruns retain distinct
attempt/job identities. Local execution uses provider `local`, the current
invocation ID, attempt `1` and the selected command's configured job ID, without
claiming CI authority. Core selection and module comparison SHALL use exact
ordered-field equality after parsing this same representation, using existing
binding normalization and ignoring object-member order and JSON whitespace. Missing or ambiguous required identity SHALL remain non-passing.
This reuses existing bindings and execution metadata; no new hash, registry,
receipt, extra execution or approval protocol is required.

## Current-run consumer boundary

Current reconciliation requires no prior session receipt and preserves independent producer outcomes. Local progress cannot establish chronology or protected CI authority. Executors remain outside the pure Requirements reconciler, which performs no Git, test or network operations.
