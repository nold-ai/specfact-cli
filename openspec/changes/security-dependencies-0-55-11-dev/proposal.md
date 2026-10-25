# Change: Complete the 0.55.11 security dependencies on dev

## Why

The owner requires the security patch to enter `dev` before a release PR can
reach `main`. Dev commit `9b5ad1e78430cc0b061cb16de42f73de96f4f312` already
contains merged #784, core 0.55.11, the certificate correction and the current
Requirements controls. Five reviewed dependency updates and their supporting
records remain absent. PR #785 contains an incomplete test-only release prefix
and is not a replacement for this dev follow-up.

## What Changes

- Select official GitPython 3.2.1, packaging 26.3, pycparser 3.12,
  python-discovery 1.6.1 and virtualenv 21.14.12 in the frozen graph/export.
- Require GitPython >=3.2.1 and pycparser >=3.12, excluding the blocked 3.0
  family, in both public dependency declarations.
- Replace the expired pycparser 2.22 provenance record with the reviewed exact
  official 3.12 artifact. Do not renew the expired record.
- Add the separately owner-approved OpenTelemetry API 1.37.0 advisory record,
  distinct from MCP 1.29.0. Both end on 4 November 2026 inclusive.
- Exercise GitPython submodule creation against metadata paths and ordinary
  checkout controls through the exact frozen wheels.
- Exclude only frozen-version assertions from the scheduled advisory resolver
  lanes. Keep ordinary negative tests and every blocking job selected.
- Preserve dev runtime changes, portable smoke fixtures, all three strict
  audits, existing version 0.55.11 and all delivered Requirements controls.

## Capabilities

### New Capabilities

- `dev-security-dependencies`: the remaining reviewed dependency selection,
  provenance, bounded advisory treatment and compatibility controls.

### Modified Capabilities

None. The existing admission capability and its original evidence stay intact.

## Impact

This follow-up changes dependency inputs, their records and verification. It
does not change application source or module manifests. The frozen graph's
PyJWT remediation is not a claim about every public resolver outcome.

Native CI currently rejects the base's expired parser record before tests.
Local failing tests alone cannot replace native provenance. A legitimate
trusted bootstrap or separately approved exact admission must resolve that
boundary before production history is adopted. No old PR #785 or #784 grant
transfers to this change, branch, PR, plan, head or tree.

No merge, publication, protected deployment, local signing, access expansion,
check waiver, new CVE exception or exception renewal is authorized. A later
dependency-only release must retain the published v0.55.4 application payload;
this dev PR does not authorize wholesale dev promotion.

## Source Tracking

- Repository: nold-ai/specfact-cli.
- Issue: <https://github.com/nold-ai/specfact-cli/issues/780>.
- Parent: #747. Live status on 25 October 2026 is Todo.
- Open blockers #783 and #523 remain recorded; this proposal does not close them.
- Supersedes no delivered change or historical proof.

## Acceptance Criteria

- Every selected new RED case fails for its specified missing behavior, without
  errors or skips, before dependency/workflow edits.
- Frozen refresh is generated normally and changes only the reviewed dependency
  closure and declared metadata.
- Exact artifact, audit, GitPython compatibility and preservation controls pass.
- Native producer, fresh/final consumers, signatures, Code Review and every
  required check pass for the actual final head under fresh authority.
- The dev PR is reviewable and forge-ready. No merge occurs.
