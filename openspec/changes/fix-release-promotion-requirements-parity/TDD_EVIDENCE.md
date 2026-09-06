# TDD Evidence

## RED — 2026-09-05

The specification commit `2b2b3078` preceded test authoring. Against the
unchanged `origin/dev` implementation, the five mapped selectors failed for the
intended missing behavior:

```text
pytest -q \
  tests/unit/scripts/test_requirements_promotion_reuse.py::test_exact_protected_promotion_produces_canonical_attestation \
  tests/unit/scripts/test_requirements_promotion_reuse.py::test_lookalike_promotion_is_rejected \
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_same_named_fork_does_not_enter_promotion_path \
  tests/unit/scripts/test_requirements_promotion_reuse.py::test_incomplete_or_stale_promotion_provenance_is_rejected \
  tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_workflow_revalidates_promotion_reuse_in_all_stages

5 failed in 0.45s
```

The three validator selectors reported that the protected-promotion validator
was not implemented. Both workflow selectors reported that the promotion
checkout/validation steps were absent. Collection succeeded, so these are
behavior-level RED results rather than setup or selector failures.

Two independent read-only reviews then strengthened the same five selectors to
cover real commit-to-PR API multiplicity, same-named forks, nonempty
plan/JUnit binding, complete paginated metadata, executable central-validator
pin checks, the public CLI boundary, exact attestation byte transport, and the
unchanged main-relative aggregate planning scope. The rerun above is against
that then-current RED contract.

PR review then identified two test-contract corrections without changing any
mapped selector or requirement: GitHub artifact identifiers are opaque positive
integers, so the invalid-identifier control uses zero instead of assuming a
specific valid value; and the real-Git control excludes ambient configuration,
hooks, and templates. Each correction was committed append-only before
implementation.

Post-patch review then exercised the accepted selector against the real PR #704
evidence shape. It found that per-source mapping digests correctly differ from
the aggregate mapping digest and that the canonical report sorts selectors
while the plan and JUnit retain execution order. The existing acceptance
selector was strengthened append-only with those valid conditions and a
duplicate-selector rejection control. Before the fix, the focused accepted
promotion selector failed in `_validate_plan_sources` with
`promotion-reuse-invalid`. A second append-only test-only commit added malformed
source-name/digest and duplicate-source rejection controls under the existing
negative selector. That review-cycle RED proof is bound as follows:

- commit: `27a3d6aba5d89d4aebe79b6d83c5c31b294ad56b`
- tree: `dfaf3261083a7ae2323e128855b6c60f87df3fb1`
- GitHub Actions run: `33993567501`
- artifact: `9977366170` (`requirements-evidence`)
- evidence JSON SHA-256:
  `a7db07d98637f891d1f995f7e3999cb7f1f092c0923b9c1b48b5ceb47d98ad46`
- JUnit SHA-256:
  `5398b5ac3c2cf1d80683852a4de01a70e56030349b628a3754bc9f43842a2412`
- result: five collected tests, five intended missing-behavior failures, and
  zero provenance findings

The mandatory clean-code review then required the validator's public boundary
to group its nine authenticated inputs. The existing acceptance selector was
strengthened to require that grouped boundary and committed test-only at
`4f85630514ef91f2f5470b7e6441ac69a20ec601`. The final immutable RED proof is:

- commit: `4f85630514ef91f2f5470b7e6441ac69a20ec601`
- tree: `9a88aaf7c9ef0763a28b13c8ac44ff47525fdee9`
- GitHub Actions run: `33994253343`
- artifact: `9977565051` (`requirements-evidence`)
- evidence JSON SHA-256:
  `f6bdbb2abc7d4a78459b1b49dec03a9949dc85c306068bc436bae87a2a336708`
- JUnit SHA-256:
  `e79ca8a1dba592c119e9d9c0a9a7ff19a28cbd9b656ce69e5f5387dfc3a7daa6`
- result: five collected tests, five intended missing-behavior failures, and
  zero provenance findings

The independently reviewed test-authored mapping digest is
`sha256:9c34bb52969f9d9dd7c7caa41d686324f8f907ee0611e677e5615b27cdd21a1e`,
approved by the exact, unedited issue #692 MEMBER comment `5554670103`.

## GREEN

The canonical validator and all three workflow validation stages now satisfy
the five mapped selectors locally. The focused validator and workflow surface
passes with 29 tests on Python 3.12. The mandatory code-review run
`review-bb8895cd-2678-4578-8e71-c6c8306dc2a4` (report SHA-256
`d13641a571900b6f35a4dcb5d9bcf6a10f0e1e2cfb2bbbf66b3c51327ae1b748`)
reports no errors and no security findings. Its two contract warnings are
retained intentionally: this validator
runs in a separately provisioned, standard-library-only trust boundary, so
importing project `icontract` dependencies would couple the verifier to the
candidate environment it authenticates. The remaining informational
length/complexity suggestion is retained because the expanded attestation
assembly makes every authenticated field and output binding explicit; a
comprehension collapse would reduce auditability without changing behavior.

Verification completed on 2026-09-06 (Europe/Berlin):

- focused validator/workflow suite: 29 passed
- full Python 3.12 suite: 3,120 passed, 9 skipped, with three host-only
  failures; the runtime-discovery and reproducible-delivery controls passed on
  rerun with the immutable modules fixture, network access, and a task-local uv
  cache, while the remaining test requires a write to the user's
  `~/.specfact/metadata.json` and is deferred to the clean GitHub runner
- real PR #704 producer/execution evidence: accepted 34 selectors with distinct
  aggregate/source mapping digests and order-independent selector agreement
- frozen runtime and Code Review dependency audits: passed with no unreviewed
  vulnerabilities
- Bandit high-severity scan and six-rule Semgrep SAST scan/gate: zero findings
- strict OpenSpec validation, workflow lint, four module signatures, four-source
  `0.55.4` version consistency, Ruff, and `git diff --check`: passed
- public documentation review: no edit required because this is an internal
  protected-branch release-control correction with no CLI or user-facing
  contract change

Independent post-patch security review found no actionable P0/P1/P2. A
fresh-context reviewer challenged the use of the promotion-head validator in
all three stages; independent boundary analysis rejected an
ordinary-contributor bypass because each stage first runs the immutable central
authority, which binds the exact repository, pull request, refs, commit/tree,
unedited expiring approval, and a signer with live write/admin permission. A
malicious validator therefore also requires a privileged merge and privileged
authorization of that exact tree. The review retained three warnings without a
demonstrated privilege path: optional `run.pull_requests` hardening, Bandit's
bounded argv-only Git subprocess notices, and intentional repeated stage
plumbing for independent revalidation. The documented two-parent merge
requirement can reject squash/rebase promotions but fails closed.

Final staged-tree hooks remain pending before the implementation commit.

## Post-merge promotion-plan regression

PR #691 Requirements run `33996054082` at exact `dev` head
`5f3f506c726a8644dac23419bf557e4447ffff7b` authenticated the #714 source
merge and produced a passing aggregate report, but the producer rejected that
report because it queried the report for plan cases stored in the separate
aggregate plan artifact.

At `2026-09-05T22:53:41Z`, the mapped selector was strengthened before the
workflow correction and run with:

`python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_workflow_revalidates_promotion_reuse_in_all_stages`

Result: FAIL (`1 failed`) because producer, fresh execution, and final verdict
did not validate the aggregate report and aggregate plan through their distinct
files.

At `2026-09-05T22:55:59Z`, the assertion normalized YAML-preserved shell line
continuations and the same command remained RED (`1 failed`) against unchanged
workflow bytes.

At `2026-09-05T23:00:12Z`, PR #715 Requirements run `33997442368` retained
the same RED result at test-only head
`9eb681963ab28360a9fbaf13f07009f5ea04b28a`. Artifact `9978484067`
(`requirements-evidence`) has service digest
`sha256:526034fe72c4cdba090daa55d710be8cf25054fbe1f37c27c16143c1f4970773`;
its JUnit document has SHA-256
`0633b17b9caf535ef365f66b8b64bfc4d0981c156cbabe49609f4d8a69b07831`
and records the mapped selector as the only failure among five cases.

At `2026-09-05T22:57:31Z`, the workflow correction validated the aggregate
report decision from the report file and the non-empty aggregate cases from the
separate plan file in producer, fresh execution, and final verdict. The mapped
selector passed, the focused promotion and security suite passed (`24 passed`),
and `actionlint .github/workflows/requirements-evidence.yml` passed.

## Python 3.11 compatibility regression

PR #715 check run `33998406109` exposed the same three existing late-RED proof
test failures in its Python 3.11 job `101392883500` and Python 3.12 job
`101392883489`. The new frozen dataclass was evaluated by an authenticated
dynamic loader that intentionally does not register the candidate module in
`sys.modules`; the dataclass implementation requires that registration and
failed during module evaluation. These hosted failures are the RED evidence
for replacing only the proof-scope value representation while preserving its
immutable tuple semantics and every authenticated field.

The proof scope now uses `NamedTuple`, retaining immutability and named-field
access without requiring loader-side module registration. The previously
masked selector-identity test also supplies the legacy scope that its synthetic
`verified`/`final` artifact models. The exact three failed selectors pass on
Python 3.11.15 and Python 3.12.13 (`3 passed` on each interpreter).

## Main-relative trusted-core materialization regression

After PR #715 merged, PR #691 Requirements run `33999408584`, attempt 2,
authenticated the exact promotion and passed its producer. The fresh consumer
then failed in job `101395635109` before validation because `git archive` asked
the `main` merge base for `requirements/code-review/requirements.in`, which
exists only on `dev`. The runtime uses the frozen
`requirements/code-review/locked.txt`; it never consumes the source input.
This hosted failure is the RED evidence for making both main-relative trusted
core manifests materializable without weakening the frozen review environment.
The strengthened regression executed both materialization steps against the
exact `origin/main` merge base and failed twice (`2 failed`) because that base
does not contain the Code Review source input or frozen lock.

At `2026-09-06T12:53:44Z`, both materializers passed against that same base
after adding a fail-closed bootstrap limited to base commit
`b1e517e60e669eaba15a18ecfa83ef5a9df65276` and the exact commit, tree, and two
blob identities from already-merged security commit
`3ea3d9b4492ade6ec5683fac83c5b5090b0cb547`. The focused workflow and security
surface passed (`104 passed`), the direct materialization regression passed
(`1 passed`), `actionlint .github/workflows/requirements-evidence.yml` passed,
and strict OpenSpec validation and `git diff --check` passed.

## Trusted-core source-identity review regression

CodeRabbit comment `3944012887` correctly identified that the first regression
proved only that both files materialized, not that the workflow authenticated
their exact archive source and relationship to the promotion history. The
test-authored mapping digest
`sha256:151e13b42ce1075789dd72dcea1c2f438910a7835b4d67798e4fa2149a0177d2`
was approved by exact, unedited issue #692 MEMBER comment `5559422472`.

The authorized append-only proof cycle retained these immutable commits:

- C4 commit: `21e312e5c48a5e5e6271ff609960fceb0f698249`
- C4 tree: `efca20a7f2d5e6f32593a21f40358dfc85fab6a0`
- R4 test-only commit: `415f01725c9a0451e1b8f70cdf0e1382212f8844`
- R4 tree: `efabf76f5a371cd120b4bcb8439439776afd32fb`
- GitHub Actions run: `34035393659`
- artifact: `9989994962` (`requirements-evidence`)
- service artifact digest:
  `sha256:211be475f482b91426577ba332c7720b0ebbe9a16fd31a72a012c879f95e4234`
- evidence JSON SHA-256:
  `12be4e9bbe708387b0d7f03a85abdf618d94efbbd6cec16659fa6491315ebd42`
- plan report SHA-256:
  `94254e4aaae42c483d1ad8c3d42a3e3ba91b9e84728e6e066124497510d40159`
- JUnit SHA-256:
  `c79b182e321a79f0cf05093b92c35637d034eee8946c36b4fb1c4249982a2bdf`
- result: six collected cases, with only the mapped trusted-core selector
  failing because the C4 tree intentionally contained one archive rather than
  the required authenticated base/source split

At `2026-09-06T13:19:08Z`, G4 restored both bootstrap blocks exactly and the
strengthened selector passed. It asserts the exact legacy base, source commit,
source tree, two source blobs, base-to-source and source-to-HEAD ancestry, both
archive source sets, and rejects a removed base-to-source relationship. The
four-file Requirements proof/workflow surface passed (`72 passed`), workflow
lint passed, strict OpenSpec validation passed, and `git diff --check` passed.

## Spec-first bootstrap recovery

Independent review found that the mapped test and RED proof preceded the exact
normative OpenSpec exception even though they preceded the implementation. The
normative scenario and task were therefore aligned at signed commit
`698694589540557c317a39a8dece6f2517a0dac0` before a new append-only proof
cycle. The mapping and its approved source digest remained unchanged.

The spec-first recovery retained these immutable commits and artifact:

- C5 commit: `90e30c33e1083945c6b26bc30e06b5b420838356`
- C5 tree: `36516710f0acd4143ce34ba883678b9702f9f21c`
- R5 test-only commit: `154bfd19fd7089aec13ec1a7473af13ea08b1035`
- R5 tree: `b606ac80e3adb4e3aa75f9543e4663f26658fc81`
- GitHub Actions run: `34036583353`
- artifact: `9990355198` (`requirements-evidence`)
- service artifact digest:
  `sha256:76a50e25c076843d4758f1af0cb09a2fb4137efac50230202bbc494ffee875a2`
- evidence JSON SHA-256:
  `257667df94d43287bbe2b757db6aa2f383ab5886a90f95c9f087d82ebe261a5e`
- plan report SHA-256:
  `94254e4aaae42c483d1ad8c3d42a3e3ba91b9e84728e6e066124497510d40159`
- JUnit SHA-256:
  `5ac750b03b62a444c0b00b9b461651958add9fb9108f3299f984841ba2bcb25b`
- result: six collected cases and exactly one failure, the mapped trusted-core
  selector, because C5 intentionally retained only the invalid single archive

R5 strengthens the same approved selector to require the base-relative default,
the disjunctive missing-input trigger, the exact immutable source identities,
both ancestry directions, and rejection of an altered default, conjunction, or
ancestry guard. At `2026-09-06T13:39:24Z`, G5 restored the reviewed production
blocks and exact PR #716 predicates. The four-file Requirements proof/workflow
surface passed (`72 passed`), workflow lint passed, strict OpenSpec validation
passed, and `git diff --check` passed.

## Late-review artifact lane regression

The normative late-review scenario was clarified at signed spec-first commit
`96672969f7c8aff4be9c087d9f6a3cfbe222f3ec`. Its direct signed test-only child
`50b2373ce87f2a5b5c92b54f989776b7cb9e3207` parameterized the existing exact
failed-selector regression over the PR #704 and PR #716 proof scopes. At
`2026-09-06T13:47:53Z`, the PR #704 case passed and the PR #716 case failed only
because the latter required `red/red` while the immutable R5 artifact and the
ordinary final Requirements lane authenticate `verified/final`.

The green correction changes only PR #716's declared maturity and run stage to
`verified/final`. It retains the exact repository, pull request, branch,
commit, tree, run, artifact, digest, test-only, failed-selector, freshness, and
final-report checks; the R5 manifest and artifact bytes remain unchanged.
The focused regression passed both proof scopes, and the four-file Requirements
proof/workflow surface passed all 73 collected cases.

Independent review then found that the first clarification touched a second
active change and its new selector was not part of the approved parity mapping.
The final append-only recovery therefore uses only the already mapped
`REQ-PROMOTION-004` selector and retains the approved mapping bytes:

- Spec-only commit `24218c7eceb125dc2107c1348389bd44fd6179de`
  (tree `5b96d8cc5c07dcf81d0f274aff08d6a124ede220`) removes the second-change
  delta and adds the final-lane semantic to the mapped parity scenario.
- Cycle-base commit `f7accc92223a4184af3c9eb5728007ae22a8d51d`
  (tree `75ae13c95c0da357edd24c5855122b553fc33780`) temporarily restores only
  PR #716's mismatched `red/red` scope.
- Its direct test-only child
  `cc9097ddd777c97865547fa848cdd239b416a2ac` (tree
  `aa2b14d2b267f5d685d4379f52d7c6f96c8dbe1e`) strengthens the existing
  mapped promotion-stage selector and removes the superseded unmapped
  parameter case. The mapped selector failed only on the exact missing
  `verified/final` scope; the unchanged selector-order control passed.

The green candidate restores only PR #716's `verified/final` values. No mapping,
review evidence, immutable manifest, or retained artifact byte changed.
The mapped regression and unchanged selector-order control passed, followed by
all 72 cases in the four-file Requirements proof/workflow surface.

## Fresh mapped final-lane proof

The mapped test change correctly made the older R5 artifact stale, so the final
candidate does not reuse or relax that proof. A new append-only cycle retained:

- C8 commit `22e458f0a28d708c1287dbf62a30184c6f8b7523` with tree
  `79e4a1b03741e3537bb762ef138366ce0647b342`, which temporarily removed
  the old manifest and mapped assertion and restored only PR #716's `red/red`
  mismatch.
- Its direct test-only child
  `4858b3a863c433a0ce5496bb8a1a4e2d6b736b20` with tree
  `c052de7c6aba2d76be7865b1d3667c34bb796df0`, which restored only the
  existing mapped `REQ-PROMOTION-004` assertion.
- Requirements Evidence run `34037707935` and immutable artifact `9990694902`
  with service digest
  `sha256:cfffe81dfceea8357b76b9474257caa9ecff0db49ec8bbfc3560655fd36aae3a`.
- Report, plan-report, and JUnit digests respectively
  `sha256:5d074828304a81c00ffad3cd79ea851c07f346c9eecfa7778ac53d76ebf9fee3`,
  `sha256:94254e4aaae42c483d1ad8c3d42a3e3ba91b9e84728e6e066124497510d40159`,
  and `sha256:ee269ead68a195e30eda1be5bd6dfd330b8983f4eb89c07996bdb2951b70a505`.

The run collected all six approved selectors with exactly the mapped promotion
stage selector failing and zero errors or skips. The final candidate restores
PR #716's `verified/final` scope, retains the mapped test bytes, and binds this
fresh artifact without changing the approved mapping or review evidence.

## Reviewed final-lane proof

The fresh final run exposed one blocking `CC18` finding in the trusted-core
test helper. Four information-only bloat suggestions and two type-check
warnings were classified as non-blocking and intentionally left unchanged.
The required helper refactor split identity, ordering, and archive assertions
without altering any assertion or selector behavior; Radon reduced the wrapper
from complexity 18 to 1 and the highest extracted helper to 12.

The post-review append-only cycle retained:

- C9 commit `f502f28e4f13dc6a5e0e7d1c58de3d1b0a49a5dc` with tree
  `e5ac7624669128c46f8c2be6ca9672f3c94451dc`, containing the CC18-only
  test refactor plus the temporary manifest removal, mapped assertion removal,
  and PR #716 `red/red` proof configuration.
- Its direct test-only child
  `7b51700a7f10f25ce908f55d0b652c0d709b4a72` with tree
  `556302e49d80c06cfb0b5eaf9c6950a77eb02ae4`, restoring only the mapped
  `REQ-PROMOTION-004` assertion.
- Requirements Evidence run `34038160697` and artifact `9990828779` with
  service digest
  `sha256:43a3bb17b610e174f96457f3fca58266d1e8b7c9bb29dd834bcdf4bd7b82cbcb`.
- Report, plan-report, and JUnit digests respectively
  `sha256:f893ab930e794b1d1445702f36053c99c8377dccb8354569722425ab27739645`,
  `sha256:94254e4aaae42c483d1ad8c3d42a3e3ba91b9e84728e6e066124497510d40159`,
  and `sha256:ad28dc8dad83f2238a33df993f32d5ddd1dda8191b5016b959cc602a3e564e36`.

All six approved selectors ran; five passed and only the mapped final-lane
selector failed, with zero errors or skips. The final candidate restores
`verified/final`, preserves the reviewed helper and mapped test bytes, and
binds the post-review artifact without changing mapping or review evidence.

## Mixed trusted-input fail-closed regression

CodeRabbit comment `3944088952` identified a valid trust-boundary defect: both
materializers entered the legacy bootstrap when either Code Review input was
missing. A mixed base could therefore replace the one base-relative input that
was present. The existing specification already required every mixed state to
fail closed, so no normative scope or approved mapping changed.

At `2026-09-06T14:32:00Z`, the exact local RED command was:

```shell
/Users/dom/.codex/worktrees/323f/specfact-cli/.venv/bin/python -m pytest -q tests/unit/workflows/test_requirements_promotion_trusted_core.py
```

It collected one mapped test and failed because the workflow lacked the new
presence probes and explicit pair-state dispatch. The final append-only hosted
proof retains:

- C11 commit `ed3fe4d0cca8641d1169fbdb692fc1c76c41b7f8` with tree
  `c9f9b3fecda1728087ce4fcd053f5315ad2a172e`, retaining the temporarily
  unreachable 17 PR #716 late-RED predicates and recording the approved review
  threshold
- its direct test-only child
  `ce5d09d355ba705aa9f861e377515f5b82a063c1` with tree
  `1d528effda913eb7d432010bae41881a7afac64e`, which finalized only the
  approved `REQ-PROMOTION-004B` selector and passed Code Review with zero
  findings
- Requirements Evidence run `34039534709` and artifact `9991241676`, created
  at `2026-09-06T14:34:08Z`, with service digest
  `sha256:60b006ac943352551c15a159aab13685ba7ec9cada3ac235ab0e0309fec4009b`
- report, plan-report, and JUnit digests respectively
  `sha256:916f6bee520b0e224f4821502b68c51b00b8b56f9c3e578224ecbfa59d1f06f5`,
  `sha256:94254e4aaae42c483d1ad8c3d42a3e3ba91b9e84728e6e066124497510d40159`,
  and `sha256:84d620083f18fdebefeed30a74f8ec799556c995eb11ae0d5ce12bb0440e5029`

The hosted JUnit collected all six approved selectors, with five passing and
only `REQ-PROMOTION-004B` failing; it recorded zero errors and zero skips. The
green implementation probes both inputs independently, permits only the
complete pair and exact legacy absent pair, rejects both mixed permutations,
and rejects any unexpected state. Both materializers retain the exact base,
source, tree, blob, ancestry, and archive-source checks. At
`2026-09-06T14:37:00Z`, the exact passing commands were:

```shell
/Users/dom/.codex/worktrees/323f/specfact-cli/.venv/bin/python -m pytest -q tests/unit/workflows/test_requirements_promotion_trusted_core.py
/Users/dom/.codex/worktrees/323f/specfact-cli/.venv/bin/python -m pytest -q tests/unit/workflows/test_requirements_evidence_delivery_workflow.py tests/unit/workflows/test_requirements_promotion_trusted_core.py
```

They passed `1/1` and `27/27` tests respectively, with the final test bytes
identical to R11. The 17 late-RED predicates were restored exactly. CodeRabbit
comment `3944074309`, requesting retroactive command detail for older proof
cycles, is minor documentation cleanup and was explicitly dispositioned as
non-blocking rather than expanding this security fix further.

## Authenticated final-context handoff regression

PR #691 run `34040421417` exposed the same fail-closed defect at two promotion
boundaries: fresh execution copied its aggregate planning report over the
verified consumer report, and final verification repeated that replacement.
Code Review correctly rejected the resulting report because its
`execution_proof.run_stage` was not `final`. The existing specification and
approved mapping already require both stages to validate reuse independently,
so no mapping or review-evidence bytes changed.

At `2026-09-06T15:41:00Z`, the exact local RED command was:

```shell
/Users/dom/.codex/worktrees/323f/specfact-cli/.venv/bin/python -m pytest -q tests/unit/scripts/test_requirements_promotion_reuse.py::test_exact_protected_promotion_produces_canonical_attestation tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_workflow_revalidates_promotion_reuse_in_all_stages
```

Both mapped selectors failed against unchanged production code. The first
hosted evidence attempt retained:

- C12 commit `82adb14babf699381a50601e2c7c5c79703d1d39` with tree
  `f80d3e4d3403a0514053a02f52a034c9a2c423fb`, clarifying the existing
  authenticated-report transport requirement
- its direct signed test-only child
  `65facaa2788b5809ab7b48cf6ef69c9756ae8991` with tree
  `9ecacd5c48ef6ff6311af5bc7b29787a1db1f8a1`
- Requirements Evidence run `34043136896` and artifact `9992286643`, created
  at `2026-09-06T15:42:10Z`, with service digest
  `sha256:fa851f93d2ededdf7533b35ef57ef1d3f2c8863521b6dffa0fd84f1d55e07661`
- report, plan-report, and JUnit digests respectively
  `sha256:7702fe9dbe0921301ed95572dba0254222ddefb14c2906e307506deaf775033d`,
  `sha256:94254e4aaae42c483d1ad8c3d42a3e3ba91b9e84728e6e066124497510d40159`,
  and `sha256:5c9be9e09b94d718f90c98aa25bc97d375042bc1504b648b4a09c93441dd40a6`

The hosted JUnit collected all six approved selectors, with the two affected
selectors failing and the four unchanged security controls passing, with zero
errors or skips. The green implementation returns the exact verified producer
report bytes from the same authenticated archive read and writes them only
after the expected promotion attestation matches. Fresh execution and final
verification pass those bytes to Code Review and retain their independent
planning checks.

At `2026-09-06T15:48:00Z`, all 30 promotion validator, workflow, and trusted-core
tests passed locally, including both mapped regressions and all lookalike,
stale-provenance, main-relative, and fail-closed controls.

The proof normalizer then correctly rejected that first attempt because an
intermediate append-only commit had changed and later restored one selected
test file. Since freshness considers every path touched after RED, exact byte
restoration cannot erase that history. No history was rewritten and the proof
check was not relaxed.

The freshness-preserving recovery cycle uses:

- C13 commit `14726b9274a586f591899bf941f7081458dec027` with tree
  `8797eec7f4f6e9ed654611997535516642fd1531`, temporarily restoring only the
  two defective report handoffs and redirecting only the 17 PR #717 late-RED
  branch predicates to an unreachable branch
- its direct signed test-only child
  `3cb4ed08c051302c23830a2471cadbb40f33b638` with tree
  `96b8791dc6282ff47a21fa7da953d998dfa5310c`, strengthening the mapped
  validator selector to require `execution_proof.run_stage == final`
- Requirements Evidence run `34044017472` and artifact `9992549271`, created
  at `2026-09-06T15:59:36Z`, with service digest
  `sha256:33699997a9426e758894b08882b56a68269cddb0c1a35e8ed4c640cfc9efa8d3`
- report, plan-report, and JUnit digests respectively
  `sha256:7051e4c40cdaa51381b4d5c74faacf56c2418bfe432836e755e4f0502fdc8075`,
  `sha256:94254e4aaae42c483d1ad8c3d42a3e3ba91b9e84728e6e066124497510d40159`,
  and `sha256:52141cdb93e21b4766eb16ddd6974d9ecfad6c7a17697f8d5fc5e77e20992446`

The R13 report records `required_maturity=verified` and
`execution_proof.run_stage=final`. Its hosted JUnit again contains exactly the
two expected mapped failures and four passing controls, with zero errors or
skips. The final child restores the two handoffs and all 17 exact branch
predicates, binds the R13 artifact, and does not modify either selected test
file.
