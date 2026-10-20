# Change validation

The owner requested actual fixes on 2026-10-20 Europe/Berlin and autonomous MCP remediation through green. On 2026-10-21 the active scope also prepares a bounded CI-produced public Semgrep distribution and corrects trusted certificate proof using exact inert wheel data. No producer output has been adopted by canonical dependencies. The certificate correction is published at 66ee3d5; the earlier validation sections below record its original checkpoint. The native scanner proposal
from commit `1a3af0cde3e3c13bdefc0de1c914d2837469a486` is preserved separately in
`openspec/parking-lot/replace-vulnerable-scanner-runtime/`, including all fourteen
unimplemented scenarios, requirements mapping and historical review evidence.
No native migration, component audit, parity or artifact admission is claimed here.

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

## Artifact proof and MCP producer scope, 2026-10-21

The trusted fresh Requirements runner uses the base dependency closure, so the
original installed-bundle test observes its old certifi rather than candidate
delivery. The new mapped test verifies the candidate tree's exact certifi wheel
SHA256, metadata and RECORD, then parses only its CA data with trusted SSL.
The original installed-runtime test remains unchanged. The verifier's dependency
closure and import roots are not weakened.

A second mapped case inspects the exact current upstream Semgrep wheel before a
producer exists, then the repository producer output after implementation. The
actual RED is the dependency mismatch `mcp==1.29.0` versus `mcp==1.30.0`, not a
missing-module error or synthetic scanner result. Certificate coverage already
passes in this new cycle. Mapping acceptance and native RED remain pending until
actually recorded for the revised mapping.

Independent review found permissive description matching. The test now requires
the recipe's exact prefix plus original upstream body, and two negative controls
reject extra prefix or suffix text. Local SpecFact review found excessive ZIP
reader complexity and vague names; these are corrected by explicit member and
RECORD boundaries and domain names. The untouched original CA test digest remains
3adb0270917811731c4972f9cbc7321f7db1d87af9457334e10a43f829b4e2a2.

The official Linux wheels lack embedded license/notice files and License-File
headers. The artifact contract preserves their exact LGPL-2.1-or-later metadata
and existing payloads; it does not pretend missing files existed or establish
complete redistribution compliance. Full source/license/component closure remains
a publication prerequisite. All seven source/output byte comparisons, 21 real
native cells, module and migration proof, complete audits, CI-only attestation,
operator publication, consumer adoption and final human authority remain open.

## Native cycle classification correction

Run 39507988136 retains the real certificate PASS and intended MCP metadata FAIL
at b61774e3, but native reconciliation rejects the revised cycle as incomplete
FINAL. The historical certifi RED does not match the new mapping. See the exact
run and artifact identities in `TDD_EVIDENCE.md`; no accepted new RED is claimed.

The fresh test/spec-only descendant adds a wrong-SHA256 download control while
preserving both mapped cases and the full plan. b61774e3 is the candidate immutable
cycle base. Any late-cycle admission requires a qualified owner-approved PR #782
trusted-policy extension and independently verified provenance. Current policy
remains enforced. Producer preparation does not supply that approval, final
exact-tree authority, package publication or canonical MCP remediation.

## Candidate producer quality dispositions

The candidate producer and runtime runner are standard-library bootstrap scripts.
They must run before candidate dependencies exist, and their boundaries explicitly
validate recipes, hashes, archives, host identity, inventory and evidence. Adding
external icontract decorators would break that bootstrap contract. Missing
`@require/@ensure` suggestions for these command implementations are an explicit
scoped exception, not permission to drop runtime checks or suppress the rule.
The workflow invokes the runner normally so its checked local producer import
resolves. Isolated matrix/uv-bootstrap probes do not prove isolated build/cell
execution. The separate producer CLI and artifact proof run with `-I -S`.

CLI JSON and uv bootstrap requirements intentionally use stdout as their machine
interface. Print-to-logging suggestions are inapplicable to those transport APIs.
The producer's metadata function names identify wheel METADATA; the naming rule's
`data` substring match does not make this domain terminology vague. Preserve those
names and the exact metadata controls. The MCP callable Protocol mirrors the
external session-manager constructor; reducing its keyword parameters would
misrepresent that contract. These exceptions are individually reviewed rather
than hidden behind lint suppressions.

The unsafe scanner positive control is inert `positive.py.txt` source data. The
runner copies its exact committed bytes into a cell-local Python target and then
scans it. It is never imported or executed. Negative data is handled identically.
The full source manifest binds both inputs, and scanner assertions still require
the expected rule, filename, line and exit codes. Bootstrap/advisory exceptions
cannot waive actual findings, missing coverage, canonical MCP remediation or
publication prerequisites.

The integrated review after corrections reports zero errors and zero type-safety
findings. Its remaining 46 warnings are 38 bootstrap-contract suggestions, four
required stdout interfaces, three metadata naming substring matches and the one
external constructor Protocol parameter count. The scoped exceptions above cover
each category; there is no new suppression or disabled review rule.

Ten informational length suggestions retain explicit security sequences.
`canonical_build` records pinned runtime, repeat builds and manifests.
`_pip_install_graph` performs an independent pip install and inventory comparison.
`prepare` resolves and installs the complete candidate graph. `_upstream_control`
proves old MCP behavior before migration. `audits` records exact installed and
upstream lineage coverage. `_verified_cell_artifacts` binds source, recipe and
canonical bytes. `execute_cell` sequences real checks and retained failure reports.
`main` exposes the unchanged command transport. The producer test's `setUp` is an
explicit inert archive fixture. `_authenticated_fixture` is the actual authenticated
MCP test server. Replacing these steps with comprehensions would hide distinct
commands, assertions or lifecycle teardown; retain their explicit sequences.

## Integrated local artifact result

The unchanged mapped artifact test file retains SHA256
d9bd7999112e5a9832f52ba9a03a4fc4d69b0326e191a02b735b6d553143ac34.
All 15 cases pass under the untouched older Hatch Python 3.12.13 when the integrated
producer selects its actual output. Producer and runner boundary tests pass all
41 cases and 66 subtests. New test-file typing diagnostics are zero. Independent
CI and producer reviews bind the final source identities before native candidate
execution. These are local preparation results, not canonical security audit,
accepted Requirements lifecycle evidence, package publication or native GREEN.
