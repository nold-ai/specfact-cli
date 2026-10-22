# Change: Patch certificate trust using official dependencies

## Why

PR #782 must remain a dependency-only hotfix. On 2026-10-21 Europe/Berlin the
owner rejected owning or publishing a Semgrep fork and explicitly requested its
removal. The owner authorized a temporary MCP exception if official Semgrep
prevents a compatible upgrade. Official Semgrep 1.182.0 still requires
`mcp==1.29.0`; normal resolution with `mcp>=1.30.0,<2` is unsatisfiable.

## What Changes

- Retain official certifi >=2026.10.19 and coherent core patch version 0.55.11.
- Remove the rejected scanner producer, recipe, workflow, runtime patches and
  fork-specific tests and Requirements mappings. Preserve history in Git.
- Keep the existing official Semgrep 1.179.0 / MCP 1.29.0 frozen pair. Updating
  Semgrep to 1.182.0 would retain the same advisory and expand this hotfix.
- Use the existing vulnerability register for only MCP 1.29.0 /
  CVE-2026-59951 (GHSA-84m7-p3x7-pcfv), reviewed 2026-10-21 and expiring
  2026-11-04 inclusive. Remove it as soon as a verified compatible upstream
  release exists. Expiry, unrelated advisories and other versions fail closed.
- Preserve strict audits of all three committed requirement graphs, independent
  SAST, module signatures, protected authority and CI/CD-only signing.
- Implement the owner-requested scoped late-cycle admission in policy PR #4 and
  its CI-only core integration. Keep the failed native report intact. A separate
  exact-head human grant may admit only missing historical failing-first proof
  for the eleven dependency scenarios and three new admission control cases. It grants no dependency-audit waiver,
  native RED claim, merge, release or local signing.
- Authenticate the retained native evidence and execute the same immutable
  protected evaluator at producer, fresh and final reconciliation. Every
  consumer independently verifies live scope, approval, permission and expiry.
  Policy activation, protected deployment and merging require owner approval.

## Capabilities

### New Capabilities

- `isolated-scanner-runtime`: certificate artifact safety and temporary exact
  advisory treatment for the unchanged official scanner graph.

### Modified Capabilities

- CI Requirements admission for only issue #780 and the direct admission follow-up to merged PR #782. Application runtime
  and the ordinary native-provenance path retain their existing contracts.

## Impact

No application behavior, scanner implementation, module manifest or publisher
changes. Ordinary base installs do not declare MCP or Semgrep. Opt-in scanning
still delivers affected MCP. Reviewed automation invokes ordinary scans rather
than an MCP server; this does not establish universal unreachability. Users must
not expose a stateful Streamable HTTP MCP server while this exception applies.
The advisory concerns session-memory exhaustion, not an established package
compromise.

A later hotfix release must start from published v0.55.4 commit
`d579970565530c3fd7b98bad4de90cf874c2a99d`, not include unreleased dev runtime
changes. This PR prepares dependencies/versioning on dev; no release, merge or
promotion is authorized. Final commit/tree authority remains separate.

## Source Tracking

- **Source Repository**: nold-ai/specfact-cli
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/780>
- **Last Synced Status**: Todo, confirmed 2026-10-21.

## Acceptance Criteria

- Frozen and installed certifi exclude compromised emSign ECC Root CA - G3 DER
  SHA256 `86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b`.
- No rejected fork implementation, production workflow or adoption plan remains.
- Normal official dependency metadata and a fresh resolver prove the MCP pin.
- Only the exact reviewed MCP finding is waived before expiry. Every other
  advisory, audit error, skipped dependency or expired record remains blocking.
- Required quality, review, CI and human authority gates remain enforced.
- Scoped admission is distinct from native proof, refuses all extra findings and
  cannot transfer across heads, trees, policies, mappings or expired approvals.
- Genuine pre-code failures and adversarial controls verify the new admission
  implementation separately from the dependency scenarios being admitted.

Sources checked 2026-10-21: [official Semgrep metadata](https://pypi.org/pypi/semgrep/json),
[upstream MCP advisory](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-84m7-p3x7-pcfv).

## Direct follow-up after dependency merge

On 2026-10-21 the owner merged dependency PR #782 as dev commit
`3cf72e848a2b5a233d3f599898d6983319d375de`, then explicitly authorized a
separate core admission follow-up alongside policy PR #4. This continuation
uses branch `codex/dependency-hotfix-admission`, the same still-open issue #780,
and the exact numeric follow-up PR from live GitHub metadata. Its separate
human grant must bind that PR's own head/tree and authentic evidence. The old
PR #782 grant cannot transfer. The follow-up changes CI controls and their
verification, without changing merged dependency pins or application runtime.
