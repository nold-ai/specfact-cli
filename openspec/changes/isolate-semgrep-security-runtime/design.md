# Official dependency hotfix design

## Decision

Reuse the existing exact advisory register. Do not alter the audit engine,
workflow requirements, package identities or resolver behavior. Delete the
rejected fork rather than maintain inactive producer infrastructure.

## Data

One register record selects package `mcp`, version `1.29.0`, primary advisory
`CVE-2026-59951` and its `GHSA-84m7-p3x7-pcfv` alias, review/expiry dates,
rationale and mitigation. Matching is exact to the emitted primary ID. The
existing register applies across audited graphs, so document the real path
`specfact-cli[scanning/dev] -> semgrep==1.179.0 -> mcp==1.29.0`.

## Risk and mitigation

The affected SDK remains installed and imported by ordinary Semgrep startup.
The exception does not fix it or prove it unreachable. Restrict use to ordinary
scan/SAST commands and do not start an exposed stateful Streamable HTTP server.
Review official Semgrep weekly and remove the exception immediately after a
normal, compatible patched graph passes artifact, installation and audit checks.
The gate rejects the record after 2026-11-04, requiring renewed review or removal.

Keep tests proving other versions/advisories, mixed findings, skipped audit
subjects and invalid dates block. Do not remove the audit from any requirements
file. Retain inert certificate-wheel verification under trusted dependencies.

## Release boundary

The four core version sources remain 0.55.11. Future dependency-only publication
must be prepared from actual published v0.55.4, with payload comparison proving
that unreleased dev runtime changes are absent. Do not reuse the rejected-fork
release fixture. No signed module assets change. Signing remains CI/CD only.

## Superseded work

Earlier native replacement planning and the rejected producer remain in Git
history. Their tests, mappings, candidate attestations and publication approvals
do not establish acceptance for this scope. Companion-module migration is only
needed if a future change replaces/removes the official integration.
