# Change validation

The owner requested actual fixes on 2026-10-20 Europe/Berlin. This active delta
covers the immediate certifi trust-store correction. The native scanner proposal
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
No fix commit, push, audit exclusion or hook bypass followed. The staged patch
remains reviewable, while full security, final CI, merge and release stay blocked.

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
