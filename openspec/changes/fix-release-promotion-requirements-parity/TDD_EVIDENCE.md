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
