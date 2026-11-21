# Change validation

The owner explicitly rescoped PR #782 on 2026-10-21 Europe/Berlin to official
packages only, removal of the rejected fork, and an exact temporary MCP advisory
exception if the upstream pin prevents a compatible upgrade. The certificate
correction remains published at 66ee3d5. Earlier sections below retain certificate
checkpoints and their original limitations. The superseded scanner plans remain
in Git history rather than in this hotfix. No fork adoption or publication is
claimed or authorized.

The original frozen audit reports certifi 2026.7.22 / GHSA-6q48-6c7w-9gw2 and
MCP 1.29.0 / CVE-2026-59951. The reviewed certifi advisory recommends >=2026.10.19.
The old hash-verified bundle contains the compromised CA fingerprint; the patched
bundle excludes it. Authored test evidence must be recorded before dependency edits.
The same test and canonical frozen checks must pass after refresh. Full security
audit remains blocked until MCP is actually remediated.

Sources accessed 2026-10-20.

- [Reviewed certifi advisory](https://github.com/advisories/GHSA-6q48-6c7w-9gw2).
- [Failed frozen audit](https://github.com/nold-ai/specfact-cli/actions/runs/39492552089/job/118869420960).
- [Certifi release metadata](https://pypi.org/pypi/certifi/2026.10.19/json).

## Actual bounded implementation

The working tree now requires certifi >=2026.10.19 in both runtime declarations,
regenerates the complete frozen lock/export normally, and synchronizes all four
core version sources to 0.55.11 with a Security changelog entry. The lock retains
184 package records; only certifi and the project version change. Native scanner
code, audit coverage, exception manifests and signature policy remain unchanged.

The old installed CA test fails on the compromised fingerprint; the refreshed
frozen installation passes the same test. Native run 39498007620 retains genuine
failing-first proof at d6d8f908. See `TDD_EVIDENCE.md` for identities and limits.
Independent scope/mapping review and separate final dependency review accepted
this bounded unit. Neither acceptance supplies human authority or aggregate green.

Normal commit hooks passed signature scope, synchronized versions and dependency
trust, then failed `frozen-cve-audit` solely on MCP 1.29.0 / CVE-2026-59951.
At that earlier checkpoint no fix commit, push, audit exclusion or hook bypass followed. The owner subsequently approved one exact local frozen-audit hook exception. It was consumed for published commit 66ee3d58959e7798a6a7a5a1ed5c41d1db37fbc0. Other hooks and all required CI remained enforced. This does not renew the exception or waive the still-failing MCP audit. Merge and release remain blocked.

## Review triage for the existing release-security test

The 0.55.11 bump exposed the existing fixed 0.55.10 release assertion. Updating
that single expected constant preserves every original cross-source assertion.
The release/security test file and new CA test then passed all 20 selected tests.
An independent reviewer accepted this correction and the evidence updates.

Whole-file SpecFact review reports a naming warning for
`test_invalid_utf8_authority_is_stable_metadata_failure`. The actual rule uses a
substring regex containing `data`, which matches the domain word `metadata`.
The existing test name specifically identifies malformed UTF-8 authority input
and its stable failure result. This is a false naming finding, retained with this
explicit disposition rather than renaming an unrelated security control.

Two informational length suggestions concern the existing fresh-consumer test
and malformed-authority CLI argument fixture. Their assertions and explicit
argument list make the security controls reviewable. A comprehension or shared
fixture abstraction would not improve these tests. Retain them without suppressing
rules or changing protected verification behavior. These three whole-file
findings are dispositions, not claims that the raw review report is empty.

## Final local quality results

The final `hatch run smart-test` exits 0 with 3429 passed, 11 skipped and two
dependency deprecation warnings. Full Ruff format/lint, explicit-interpreter type
checking, documentation/command contracts and the contract gate pass. Contract
selection reports no changed contract inputs and reuses its cached result.
The source-bearing patch and fixed release expectation have separate independent
PASS verdicts. No accepted new review defect remains; whole-file suggestions have
the explicit dispositions above. Final CI and authority still require a published
fix commit, which the MCP audit currently prevents.

## Corrected scope and current verification

Retain official Semgrep 1.179.0 and MCP 1.29.0. Latest official Semgrep 1.182.0
still exact-pins the same affected MCP, confirmed in actual artifact metadata
and a fresh normal resolver failure. The owner-authorized register entry
selects only MCP 1.29.0 / CVE-2026-59951 and its GHSA alias, with review
2026-10-21 and inclusive expiry 2026-11-04. Every other advisory and strict
audit error remains blocking. The scanner still imports affected MCP, so
reviewed automation avoiding server startup is mitigation rather than proof
of unreachability. Review weekly and remove the exception upon a verified
official compatible fix.

The rejected workflow, producer, manifests, runtime patches and their tests
are removed. Certificate artifact verification remains. Requirements mappings
now cover certificate trust and bounded exception behavior. Prior candidate
review acceptance is withdrawn and cannot transfer to this map.

The actual audit fails before the entry and all three strict audits pass after
it, visibly reporting the exact waived finding. Gate tests additionally prove
other versions/advisories, mixed findings, skipped subjects and expiry fail.
See TDD_EVIDENCE.md for exact logs and counts. No audit engine or required CI
workflow was modified. Signing is CI/CD only.

A future dependency-only release must start from published v0.55.4 commit
d579970565530c3fd7b98bad4de90cf874c2a99d. Unreleased dev runtime changes must
not be promoted as part of that hotfix. The old rejected-fork release fixture
is not adoption evidence for this scope. No release or merge is performed.

## Current gate and review checkpoint

The pinned Requirements consumer accepts the corrected three-case plan. A fresh
independent technical reviewer, Codex agent `/root/official_scope_acceptance`,
accepts mapping digest
`sha256:9400b195f3c46b54c8fafbd8461de73716aeeb17318f5c39e54863091e3c39f3`.
This is mapping review, not human authority or final native lifecycle admission.
The frozen-artifact requirement deliberately tests candidate wheel bytes rather
than the trusted verifier's installed certifi. The retained installed test runs
in the candidate environment as supplemental delivery evidence.

Ruff formatting/lint, BasedPyright type/lint, YAML, contract, license and Bandit
gates exit 0. The scoped smart-test command exits 0 with 53 selected unit tests
passing. Its raw pytest coverage report is 5 percent and emits a threshold
message that the scoped wrapper documents as expected. This is not a full-suite
coverage pass. Required full delivery CI remains enforced.

Normal frozen regeneration changes no dependency selection beyond the existing
certifi correction. Reproducibility, `uv lock --check` and version-source checks
pass. Actual official Semgrep SAST reports zero findings against a zero-finding
baseline. SpecFact review identified test complexity/parameter-count issues,
which must be fixed before commit. No review error is waived.

## Bounded review findings and dispositions

The two new test complexity/parameter-count findings require correction rather
than a waiver. The scenario inputs use a named record, and lock inventory and
exception fields use exact collection comparisons. All nine adversarial test
IDs and both mapped selectors remain unchanged.

Whole-file review also emits 44 reportUnknownMemberType warnings on the existing
dynamically loaded audit fixture at unchanged lines before the new scenario
record. Focused type checking finds no warning in the changed functions. These
pre-existing fixture warnings are retained as a narrow documented exception to
whole-file cleanup, because rewriting every existing fixture is unrelated to
the dependency hotfix. No type rule or severity threshold is suppressed. The
existing naming false positive and two informational length suggestions retain
the earlier explicit dispositions above. Required error-level type checking
and clean-code checks remain enforced.

Final bounded review by Codex agent `/root/bounded_policy_final_review` accepts
the test refinement. The final SpecFact report is PASS_WITH_ADVISORY with zero
errors and no introduced warning. Its remaining 44 fixture type warnings, one
existing naming warning and two existing informational findings have the
bounded dispositions above. No complexity finding remains on changed tests.

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
