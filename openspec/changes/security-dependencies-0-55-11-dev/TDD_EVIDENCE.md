# Dev-first failing-before evidence

On 26 October 2026 Europe/Berlin, the unchanged production inputs at dev
`9b5ad1e78430cc0b061cb16de42f73de96f4f312` produced 15 assertion failures,
zero errors and zero skips for this change's 15 mapped cases. The exact JUnit
and execution/input receipt are retained under `requirements-proof/` as
`local-red-behavior-20261026.xml.gz` and its companion receipt. Root inspected each
failure message. The Git cases show rejection false, clone boundary reached
and one clone call, rather than a wheel-installation error.

The gzip transport decompresses to the original immutable XML bytes, SHA-256
`cdbef78a51e9bbf66e43ac826a3cfb23335b06de6092b93ed71e37606d19c407`.
Pytest's raw failure trace contains trailing whitespace. Compression preserves
that report without normalizing its contents or changing formatter rules.

The targeted local runner used Python 3.12.13, pytest 9.1.1 and the exact
hash-pinned test-tool entries extracted from dev's CI export. It loaded normal
repository conftest/configuration with third-party plugin autoload disabled.
GitPython probes installed the exact frozen GitPython/gitdb/smmap wheels with
hash checking, no dependency resolution and isolated `-I -S` execution.

The failures observe the five old package versions, both old public floors,
the old parser record, three missing exact OpenTelemetry admissions, three
metadata submodule paths reaching clone, and two existing advisory exclusions
where the required nine are expected. All recorded inputs stayed unchanged
during execution. No production edit preceded this run.

The first exploratory run had 15 failures and one passing preservation case.
It is retained privately without relabeling. The already-satisfied shared-lane
case was removed from this RED plan and remains an ordinary control. Independent
review also required per-package advisory fixtures, parser hostile-fixture
adaptation and exact deselection bounds before the corrected run. This evidence
uses the corrected tests and mapping; it does not transfer the first run's
identities.

The pinned Requirements lifecycle initially rejected the automatic floor-case
parameter IDs because comparison punctuation is not allowed in selectors.
Explicit `gitpython-floor` and `pycparser-floor` IDs corrected the metadata;
the assertions did not change. The next run had 12 intended assertion failures
and three wheel-installation CalledProcessError failures. Its total of 15
pytest failures did not establish complete behavioral RED. Independent review
caught this distinction. That raw run and receipt remain unchanged and receive
no behavioral acceptance. The separately approved network-enabled run then
produced all 15 intended assertion failures, with unchanged inputs and no
errors or skips. The actual pinned lifecycle accepts planned maturity with no
findings, mapping digest
`sha256:7025a000601cc44c1a1e6168367f2188681471d68ea5f044cfc81a94b734f8ff`
and plan digest
`sha256:dc90453d191b282ba5e47127bf067ee23b475072d7e94a0859c7c6a26677ce3a`.
That planned-only result supplies no native RED or mapping review acceptance.

This is local behavioral failing-before evidence. It is not accepted native CI
RED, an origin attestation, exact-head authority, a production acceptance or
merge readiness. Native bootstrap remains blocked before tests by the base's
expired pycparser 2.22 review. No renewal or check waiver is claimed.

Passing-after, full quality gates, genuine accepted native evidence, independent
final review, CI-only Git signatures and actual forge readiness remain pending.
