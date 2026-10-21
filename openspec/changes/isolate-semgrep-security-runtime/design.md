# Official dependency hotfix design

## Decision

Reuse the existing exact advisory register. Do not alter the audit engine, package identities or resolver behavior.
The owner separately authorized narrowly scoped Requirements admission and
core CI integration on 2026-10-21. Delete the
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

## Scoped CI admission

Policy PR #4 owns one live evaluator in immutable protected policy code. Core
invokes it at the producer, fresh and final Requirements reconciliation
boundaries. Its output is audit data only. Every boundary independently reads
the live exact-head grant, permission, current subject and retained evidence.
No consumer trusts an earlier sidecar as a bearer credential.

The domain has distinct NativeProvenance, HumanApprovedLateCycle and Refused
outcomes. Admission preserves the byte-identical failed native report, including
incomplete maturity and missing historical RED. Code Review consumes that real
failed report through its existing signed schema-2 interface. Its own failures
remain blocking. No signed module changes are required.

The canonical separate grant binds repository, the live numeric direct follow-up PR, issue780, change, dev
base, head branch/commit/tree, immutable policy revision, exact eleven dependency selectors and three admission controls,
source/aggregate mapping and plan identities, native run/attempt/artifact and
raw hashes, authenticated executed producer source, explicitly missing native
RED, the exact allowed provenance finding and expiry. It is unedited, unique,
issued by a currently authorized write/admin human, and at most seven days old.
The current execution independently passes every selector and matches semantic
plan/mapping identities. Historical and current byte hashes remain separate.

All JSON, archive, XML and network inputs are bounded. Duplicate/unknown fields,
unsafe archive members, malformed or skipped tests, extra findings, changed
subject/policy, stale/revoked authority, network uncertainty and expiry refuse.
No API run head SHA is claimed to prove executed workflow revision. Use verified
GitHub CI provenance when the API does not authenticate that identity. Signing
and attestation generation occur only in CI/CD. No local signing is permitted.

The implementation is prepared and reviewed before protected activation. It
must refuse before owner-approved deployment and the distinct final human grant.
Rollback disables the scoped protected policy and restores refusal while keeping
all native reports and ordinary CI gates. The generic exact-head authority and
the MCP advisory register remain separate capabilities.

Implementation sequence is updated specification, behavioral failing workflow
fixture, policy/core implementation, passing hostile-input and native-path
controls, independent review, normal hooks and CI. No immutable failed artifact
is relabelled RED or rewritten. The final deployment packet records exact code
revisions, new evidence, approval payloads, rollback and remaining owner actions.

The owner merged dependency PR #782 before this CI implementation was ready,
then authorized a separate follow-up. Current subject is the unique open dev PR
on `codex/dependency-hotfix-admission`, independently obtained through GitHub.
Its numeric PR identity is an exact canonical grant field. It inherits no old
head/tree authority. The still-open issue #780 and this active change retain
scope and tracking. The merged dependency payload remains separate from the
CI control continuation.
