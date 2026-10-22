# Certificate trust-store regression

## Failing before dependency changes

On 2026-10-20 Europe/Berlin, the existing frozen lock was installed with
`uv sync --locked --all-extras` into an isolated environment using Python 3.13.14.
It installed certifi 2026.7.22. No dependency input had been edited.

Command from this worktree:

```bash
/private/tmp/specfact-dependency-audit-20261020/certifi-tools/bin/python -m pytest tests/unit/security/test_certificate_trust_store.py -q --no-cov
```

The actual SSL trust-store comparison failed as intended:

```text
Extra items in the left set:
'86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b'
1 failed in 0.06s
```

The installed bundle still trusted the compromised emSign ECC Root CA - G3.
The full local capture is
`/private/tmp/specfact-dependency-audit-20261020/certifi-root-red.log`.
The frozen audit independently reported GHSA-6q48-6c7w-9gw2 and the separate MCP
finding. Passing-after evidence must use the same test against the refreshed
frozen installation. This local record does not replace native CI execution proof.

## Native CI failing-first proof

The typed test was published at commit
`d6d8f9089bb55f8e834a55dfcac43a8a5e4c61ca` before dependency changes.
[Requirements run 39498007620](https://github.com/nold-ai/specfact-cli/actions/runs/39498007620)
retained artifact `12297219535`, digest
`sha256:10fefe0c9b89815a6a7b29cbe5bca56680fe0fed3aefae693328dfbe6e5406e8`.
The actual JUnit records one intended fingerprint failure, no errors and no skips
on Python 3.12.15. Native reconciliation reports `observed_maturity: red`,
`gate_decision: pass`, and `implementation_evidence: failing-first-proven`.
The run's delivery checks remain blocked at this intermediate failing-test stage.
This is not final implementation or authority evidence.

## Passing after frozen refresh

The canonical `hatch run refresh-frozen-delivery` regenerated the Python lock and
hash-protected CI export after the certifi minimum and 0.55.11 metadata changes.
`uv sync --locked --all-extras` then installed the exact graph in the isolated
environment. The same typed test passed on Python 3.13.14 with certifi 2026.10.19:

```text
1 passed in 0.05s
```

The lock retains 184 packages. Only certifi 2026.7.22 to 2026.10.19 and the project
0.55.10 to 0.55.11 changed version. The installed store has 120 roots and excludes
the compromised fingerprint. Delivery/export parity, lock consistency, license,
dependency trust, synchronized versions, strict PyPI-ahead and Bandit checks pass.
The full audit still fails solely on MCP 1.29.0 / CVE-2026-59951. Both other frozen
exports pass their actual audits. No audit exclusion or resolver override exists.

These passing-after observations describe the local implementation working tree.
Final commit-bound CI evidence and new exact-head authority remain required.
The local logs and package accounting are in
`/private/tmp/specfact-dependency-audit-20261020/certifi-fix-result.txt`.

## Release verification corrections

The broader smart-test attempt had 3427 passes and two failures. Its launcher
selected the Requirements fixture instead of the separately pinned smoke fixture.
Using the exact smoke fixture, then warming the new hash-locked certifi wheel for
its offline child, made the real launcher pass. The first failed results remain
in the local trail and are not reported as passes.

The other failure was the existing release test's fixed 0.55.10 expectation against
the required 0.55.11 patch. Updating only that expected value preserves all original
assertions. All 20 release/security and CA tests then passed. The final full
smart-test rerun is recorded separately after completion; targeted passes do not
turn the earlier failed run into a green gate.

## Final local smart gate

With the separately pinned smoke fixture and frozen cache prepared,
`hatch run smart-test` exited 0. Its actual result was:

```text
3429 passed, 11 skipped, 2 warnings in 262.82s
```

The two warnings are dependency deprecations, not failed tests. The earlier failed
run remains retained. Final local success does not waive MCP, final native CI or
exact-head human authority. Normal dependency commit remains blocked by the
unchanged `frozen-cve-audit` failure.

## Official-only correction, 2026-10-21

The owner rejected the producer/fork and authorized an exact temporary MCP
exception when official Semgrep prevents patched MCP. Superseded producer
evidence remains in Git at 46970dc1 and the private operator archive. It is not
current acceptance evidence and supplies no publication or authority approval.

Latest official Semgrep 1.182.0 wheel metadata requires MCP 1.29.0. A fresh
normal `uv pip compile` with `semgrep==1.182.0` and `mcp>=1.30.0,<2` fails:

```text
Because semgrep>=1.182.0 depends on mcp==1.29.0 ...
your requirements are unsatisfiable.
```

The original strict frozen audit exits 1 for MCP 1.29.0 / CVE-2026-59951.
Before adding the register entry, the new exact-policy and gate tests record
6 failed and 4 passed, including the intended empty-register policy mismatch
and unwaived approved findings. After adding the owner-authorized entry,
all 41 audit/policy tests pass. Twelve unchanged certificate artifact and
adversarial-input tests pass using real hash-pinned official wheel downloads.

All three unchanged strict audit commands then exit 0. The CI graph visibly
reports `WAIVED: mcp==1.29.0 vuln=CVE-2026-59951`; the other two graphs contain
no unreviewed findings. This is accepted temporary risk, not remediation.

Local evidence is retained under
`/private/tmp/specfact-dependency-audit-20261020/official-only/` in
`latest-compatible.log`, `security-before.log`, `exception-tests-red.log`,
`exception-tests-green.log`, `certificate-tests.log` and `security-after.log`.
The gate implementation and all required workflow checks are unchanged.
Normal commit hooks, final CI and exact-head human authority remain pending.

## Native official-only verification and selector correction

At b3bf7cf5, native run 39572650717 passes Security Audit with the exact
reviewed MCP exception. Native Requirements run 39572650571 records 11 tests
with zero failures, errors or skips. Its reconciliation rejects both the
missing prior-RED admission and the unexpanded parametrized selector.

The mapping now names all nine parameter IDs explicitly. Fresh independent
review by `/root/expanded_selector_map_review` confirms the 11 unique selectors
match actual native JUnit and accepts mapping digest
`sha256:9be3a10b220655e55c299b9b3d69c2be0c0b029b1db1c0942abfea1ea6c4f86d`.
This supersedes the earlier three-case mapping acceptance. The prior native
report remains immutable evidence of its original failure. Prior-RED admission
and exact-head human authority are still required. Neither local test evidence
nor technical mapping acceptance fabricates those protected approvals.

Direct yamllint on the changed mapping passes. The repository-wide wrapper
prints unrelated baseline errors while returning success, already tracked by
issue #781. No wrapper behavior is changed in this dependency hotfix.

## Owner-authorized scoped admission implementation, 2026-10-21

The owner authorized actual implementation in policy PR #4 and core PR #782,
with an explicit pause before protected deployment or merging. This supersedes
the previous documentation-only policy checkpoint. Native historical proof
remains missing. No original failed artifact is relabelled RED or modified.

The new workflow wiring test was authored after the updated specification and
before implementation. It extracts and executes the actual final reconciliation
shell from requirements-evidence.yml with a synthetic policy-boundary adapter.
The adapter isolates workflow routing; it does not claim authentic GitHub
approval or signing. The raw failed native packet must remain byte-identical.

The pre-code command was `python -m pytest -q
 tests/unit/scripts/test_requirements_late_cycle_workflow.py` in the existing
full tools environment. Actual result was 1 failed. The behavioral disagreement
was `assert 1 == 0` with stderr:

```text
Final reconciliation requires authenticated red or legacy evidence.
```

This is evidence of the real early-refusal branch, not a missing-module/import
failure. The complete retained log is
`/private/tmp/specfact-dependency-audit-20261020/official-only/implementation/workflow-red.txt`.
The protected policy baseline independently passes all 66 existing tests before
new implementation. Hostile-input policy tests and all three workflow paths are
separate required verification. Final CI and new exact-head grants remain open.

## Separate follow-up verification, 2026-10-21

After PR #782 merged, the owner authorized a separate CI-only core follow-up
with policy PR #4. The fourteen exact mapped selectors pass, including the
actual frozen certifi artifact test. The protected policy suite passes all
179 tests. Its historical-attempt regression first failed against the old
collector and then passed after explicit approved-attempt binding.

The shell tests execute each actual producer, fresh and final boundary using
transport and policy doubles. They prove preserved raw native bytes, ordinary
success, enforced policy refusal, scope guards and isolated CI origin wiring.
They do not prove authentic GitHub attestation or human approval. The final
clean-code review of the refactored test reports zero findings. A fresh
independent reviewer accepted the final fourteen-case mapping under its own
identity in requirements-proof/review-evidence.json.

All three strict frozen audits pass with only the owner-approved MCP exception.
The required contract command exits zero with no modified source detected.
This is a CI-only change; that command does not establish contract execution.
Actual mapped test and policy results are retained separately. Full smart-test,
normal hooks, final native CI origin verification, protected deployment and
new exact-head human approvals remain separate gates.

Policy revision pinned in the workflow is `ea0509fc5261e394cbc8de918b85ea02ac5f4126`.
It remains inactive until separately authorized protected deployment.
Native failed reports remain immutable and missing historical RED stays missing.

### Normal-hook and existing contract corrections

The normal commit hook first rejected job.workflow_sha because the pinned
workflow linter does not recognize that new context. This origin job is directly
defined in the workflow. GitHub's context reference documents the equivalent
github.workflow_sha for this case. An added assertion first failed on the old
context, then all three shell controls passed with the supported declaration.
The final normal commit hooks passed, including zero findings for the new test.

The first full follow-up smart suite recorded 7 failed, 3447 passed and 10
skipped. Every failure was an existing workflow contract tied to the replaced
enforcement name or previous exact read-permission set. The two existing test
files now preserve their original mapped parameter IDs, exercise native/admission
exit combinations in all three lanes, retain upload ordering and independently
require both Code Review failure guards. The targeted suite passes all 30 cases.

Narrow baseline quality exception: reviewing the two existing test files reports
four pytest.mark/parametrize unknown-member typing warnings and four fixture-length
informational findings. An actual unchanged-HEAD helper run records the same
severity, rule and message for every finding. No new warning or information
finding remains. The unchanged expanded fixture builders express authenticated
artifact/run contracts and remain outside this focused CI admission correction.
No suppression or tool configuration change is introduced. This exception covers
only these eight baseline findings, not future regressions.

Evidence is retained in the implementation audit as origin-context-red.log,
origin-context-green.log, core-commit-hooks-final.log, followup-smart-final.log,
existing-workflow-tests-red.log, existing-workflow-tests-green.log and the actual
baseline/current review JSON files. The final full-suite rerun remains separately
required; the targeted result does not turn the earlier failed run into a pass.

### Full-suite pass and fork-attester review fix

At core head 89bf62e8, the corrected full smart suite exited zero with 3455
passed, 9 skipped and 2 dependency-deprecation warnings in 251.58 seconds.
The final-head native origin job also succeeded. The actual protected-policy
historical collector and official gh verifier authenticated its origin bundle,
exact workflow revision, native ZIP and fourteen passing selectors. The only
native finding is prior-red-proof-missing. This authenticates the observed
failed report; it does not supply historical RED or a human grant.

PR #784 review identified that the new attester could start on fork PRs without
the required write permissions. The exact scoped-job contract first failed
because its same-repository, pull-request, dev-base and branch guards were absent.
The job now requires the same exact subject as late-cycle admission. It remains
always() after producer failure but skips forks and unrelated subjects. No
permission change, separate CI status check or artifact mutation is used to
address the finding.
The focused new and existing workflow suite passes all 33 tests after the fix.
Evidence is retained in origin-scope-red.log and origin-scope-green.log.

### Actual rerun retention check

Review claimed that fixed artifact names conflict across workflow reruns.
The exact locked artifact client documents reruns as a supported duplicate-name
case. A controlled retry of Requirements run 39588065523 on 21 October 2026
confirmed the actual backend behavior. Attempt 2 successfully uploaded the same
requirements-evidence name as new artifact 12341235127 and the same producer
audit name as new artifact 12341410036. The original native artifact 12339828168
and origin artifact 12340872780 remained accessible and unexpired.

After the run advanced to attempt 2, the actual reviewed historical collector
and official gh verifier again authenticated attempt 1's original signed origin
and native ZIP. Its bytes, fourteen selectors and sole missing-RED finding were
unchanged. The existing consumers bind explicit artifact IDs. No overwrite,
deletion or artifact naming change is required. The retry remains refused for
the absent distinct human grant. Successful uploads do not admit provenance.

The exact retry job is
<https://github.com/nold-ai/specfact-cli/actions/runs/39588065523/job/119186574654>.
Evidence is retained in pr784-after-rerun-artifacts.json,
pr784-rerun-producer.log and pr784-retained-attempt1-verification.log.

### Exact-ID artifact transfer correction, 2026-10-21 (Europe/Berlin)

Specification was amended before the local behavioral probe and implementation.
The actual pinned download-action runtime at
`3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` applies `filterLatest` before explicit
ID filtering. A Node probe executed that function verbatim against the six-record
authenticated REST fixture for run `39589983181`. Requested producer artifact
`12341352657` exists, but older same-name `12341630570` has the larger numeric ID.
The explicit-ID assertion failed with selected `[]`, `0 !== 1`, and exit 1 before
production edits at `d88310de977bfc5d080e7e03c75256434ed937ea`.
This retains genuine selection failure, not a missing-helper or empty-step error.

Retained local evidence under
`/private/tmp/specfact-dependency-audit-20261020/official-only/implementation/`:
`artifact-design/reproduce-selection-red.js`, `selection-red.log` and
`selection-red-report.md` (the latter two in the same artifact-design directory),
and `review/artifact-download-rerun-sources/` with the source and REST fixture.
Source SHA-256:
`f4a6b7046eb834bed98bb687f6d08feb0bfe6fb32570e9da7de0707884c08b31`.
Fixture SHA-256:
`91bf7c28202053d63a64feb5562486b27f2507e0b110bd49308b8aa916ca55b3`.
The real producer ZIP digest is
`2d857d60225b8e0e1073488936d7fc62cee43a58283072ae67ae07c78f05b927`.

The correction uses one YAML scalar with two aliases, invoked through
`/usr/bin/python3 -I -S`. Tests execute that actual resolved Python body with
transport-only doubles. The three names/destinations and the fourteen-case
mapping remain unchanged. Existing workflow tests now inspect the equivalent
exact-ID environment binding instead of obsolete action inputs.

Passing command (Python 3.13.14, pytest 9.1.1, established run-hatch environment):

```sh
sh /private/tmp/specfact-dependency-audit-20261020/official-only/run-hatch.sh   python -m pytest -o addopts='' -q -p no:cacheprovider   tests/unit/workflows/test_exact_artifact_transfer.py   tests/unit/workflows/test_requirements_evidence_delivery_workflow.py   tests/unit/security/test_release_promotion_security_gates.py   tests/unit/scripts/test_requirements_late_cycle_workflow.py
```

Result: **114 passed**, with no warnings, retained in
`artifact-design/focused-tests.log`. Controls cover both exact requested IDs,
independent execution digest, metadata association/type/expiry/size/digest,
duplicate JSON, refusal statuses, truncation, HTTPS redirects and credential
stripping across redirect chains, total deadline, digest-before-ZIP ordering,
flat paths, raw NUL, encryption, links/devices/directories, CRC failure, member and
expansion limits, existing and concurrent collisions, symlink parents, fresh
exclusive destinations and preservation of unrelated context. Ruff checks pass
for the three touched test files. Strict OpenSpec validation passes.

The parent independently executed the real workflow program with local
`/usr/bin/python3` 3.9.6 against authenticated live GitHub endpoints, verifying
producer `12341352657` in both producer roles (6,582 ZIP bytes; four files;
70,093 expanded bytes). Retained execution artifact `12302080806` from run
`39502448590`, head `66ee3d58959e7798a6a7a5a1ed5c41d1db37fbc0`, restored two flat
files (1,913 ZIP bytes; 4,102 expanded bytes) with independent digest
`0e20e44875b9a43c4653940ca90a788d541e9ed085fa5c613648f1c41ae9abe5`.
Byte comparisons and unrelated context preservation passed. Evidence is
`live-exact-transfer-proof.json` and `.log`; the parent refreshes it if the
workflow body changes. Historical execution proves transport/layout, not
current-head native success. Existing grants remain historical. Fresh grants,
normal hooks, independent review and current-head CI remain delivery gates.

The program keeps verified compressed bytes in bounded memory rather than a
private ZIP temporary file; extraction still stages every validated member on
the destination filesystem before exclusive publication. Each file publishes
atomically; whole-set atomicity is not claimed. Interruption or a late collision
may leave partial new evidence, and retry refuses it. Existing evidence is never
overwritten. Rollback is reverting the workflow correction; no artifact deletion,
protected-policy change, signing or dependency changes are required.

### Final transport review and local gates

Independent reviewer `Codex:/root/artifact_transfer_security_review` returned
PASS for exact program SHA-256
`f9a09798fed949615bbd8845fca26044ca53a16fe95c85853ad04590f67e6b8a`.
It independently passed 114 focused tests, eight additional hostile probe groups,
compared all workflow YAML outside the three changed steps with the base, and
compared the live restored files with genuine ZIPs. The review and evidence are
retained in `review/artifact-transfer-security.md` and adjacent machine records
under the local evidence root above. No grant, deployment or merge authority is
implied by that technical review.

The new test file has zero SpecFact findings. The full affected-file review has
one warning and six informational findings in unchanged existing functions.
The same independent reviewer explicitly accepted a narrow exception for exactly
those baseline diagnostics. It compared both complete source and AST against
`git show d88310de:<path>`, independently of the parent's comparison. The warning
is `banned-generic-public-names` on
`test_invalid_utf8_authority_is_stable_metadata_failure`. The six
`ai-bloat.loc-vs-complexity` findings concern that same function,
`test_fresh_consumer_reexecutes_trusted_plan`, `_write_late_red_artifact`,
`_write_late_red_metadata`, `_late_red_fixture`, and
`test_workflow_revalidates_promotion_reuse_in_all_stages`. No rule, threshold,
suppression or function body was changed to accept them. The explicit exception
is limited to these unchanged symbols for this correction; it permits no new
finding or changed body. Evidence is `artifact-transfer-self-review.json`,
`artifact-transfer-baseline-findings.json`, and the reviewer's independent
`review/artifact-transfer-security-baseline.json`.

The review used the committed pinned BasedPyright runner with the actual Hatch
Python path. The global pyenv shim previously could not resolve pytest and
produced false unknown-member diagnostics. The isolated executable adapter
preserves every caller argument and adds only the correct `--pythonpath`; it
changes no repository configuration or check. The required authoritative full
project type run reports zero errors and 1,456 warnings, exactly the baseline.

Required formatter passed with all 1,128 files unchanged. Full lint, YAML lint,
actual pinned actionlint 1.7.11, strict OpenSpec validation and stable fourteen-case
mapping/plan identity checks passed. The smart-test gate passed its selected 111
workflow/security tests; its unit-scope coverage notice is not a full-suite
coverage result. The contract gate exited zero with no modified source scope,
using its cached result. Fresh complete CI remains required at the new head.

The comment review's two private docstrings and changed-line type suppression
were removed. Its only kept comment explains redaction of signed URLs emitted
by the external urllib exception formatter. No production change followed the
final live transfer proof or independent security verdict. The core dependency,
version and signed-module inputs remain unchanged. Signing stays in CI/CD.

### Equivalent signed synthetic merge origin, 2026-10-21 (Europe/Berlin)

Normal-hook commit `4b25241ef5548d29b6ad78be6cd2d26dda6afa77` published the
reviewed exact-ID transfer. All ordinary CI checks passed at that head. The
new native artifact `12344301975` and signed origin `12342973880` in run
`39595683488`, attempt 1, retain fourteen passing cases and the sole missing-RED
finding. The canonical request operation refused with `origin-source` before
any new human request was issued.

Authenticated GitHub commit records show actual attested workflow revision
`21cca82b7d32c567bbea6f496184cbdf633cab13` and current PR merge revision
`6636108be140545670ab348e503187102dded6e7`. Both have the exact reviewed tree
`c131fc747fa4cd827a06ffd6a1ec164e146a986c`, the ordered parents
`3cf72e848a2b5a233d3f599898d6983319d375de` and the current head, and valid
signatures. Their signed payloads encode author/committer time zones differently.
The deployed literal source-ID guard rejects this equivalent signed merge.
No origin or artifact was rewritten to work around that refusal.

The specification preceded the scoped policy regression. The new test
`test_historical_equivalent_signed_merge_preserves_attested_source` first failed
with `late_cycle_admission.Refused: origin-source`. Two subsequent ordered-parent
negative controls first failed with `DID NOT RAISE Refused` before the candidate
was tightened to a distinct first parent and exact current-head second parent.
The final policy suite passed 264 tests, independently repeated by
`Codex:/root/policy_identity_security_review`. Its exact source SHA-256 is
`bdd671842d0f0c1d252a759a7aa8230b2b94d6d97e44bebc760b9b13e7c967f0`.
Formatting/lint, comment review and diff checks passed. The independent technical
verdict permits normal commit/publication, not protected deployment or grants.

The candidate accepts a different signed merge only when both authenticated
full identities match their requests, both signatures are valid, both trees
match the exact reviewed head tree, and both ordered two-parent lists agree
as distinct base/current-head. It retains workflow-byte equality and verifies
the actual original signer/source digest through official gh. All native,
selector, immutable-artifact, live subject/permission/expiry and deployment checks
remain unchanged.

Parent technical verification called the real candidate historical collector
against the actual API and signed origin, without replacing its official gh
verifier. It accepted the genuine native ZIP and sole missing-RED finding, while
retaining the original workflow revision. This was evidence verification only;
no request, grant or decision was issued. The unchanged `deployed()` restriction
continues to refuse an unmerged candidate.

The policy correction is proposed as
<https://github.com/nold-ai/.github/pull/5>, exact commit
`5cd61c45303bc5da174a39ff79945fafad77ea3b`. Core now pins that immutable revision
for all three existing evaluator calls. This pin is inactive for admission until
the owner explicitly approves protected deployment and the revision is reachable
from policy main. The earlier policy4 deployment approval does not apply to this
new change. No policy5 deployment, new human grant, core merge or local signing
has occurred. Fresh core evidence and separate exact owner grants remain required
following approved deployment. Reverting the pin and policy correction restores
the prior refusal without altering retained evidence.

Local evidence is under the previously identified implementation directory,
`policy-identity/`: `actual-deployed-red.log`, `regression-red.log`,
`ordered-parent-red.log`, `final-tests.log`, `security-review.md`,
`candidate-live-origin-proof.json` and its producer script in the parent directory.
The original authenticated synthetic commit responses and origin manifest are
retained adjacent to those records.
