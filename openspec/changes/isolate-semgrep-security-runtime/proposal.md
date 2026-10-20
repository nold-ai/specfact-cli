# Change: Replace the shared Semgrep runtime without reducing security coverage

## Why

The dependency review on 2026-10-20 found that dev already contains the direct
updates requested by #762, #764, #765 and #766. JSON #777 would downgrade Jekyll
and does not resolve the remaining Python advisory. Dev freezes Semgrep 1.179.0,
whose MCP 1.29.0 dependency is affected by GHSA-84m7-p3x7-pcfv. Latest published
Semgrep 1.181.0 has the same exact dependency. An ordinary resolver rejects
Semgrep 1.181.0 together with the patched MCP range `>=1.30.0,<2`.

The owner authorized a new scoped change to isolate or replace Semgrep. This
proposal selects investigation of an independently published native scanner, with
OpenGrep as the inventoried candidate. The downstream Semgrep alternative has an
adoption cycle and an unconfigured protected producer. Replacement must prove
rule parity, independently authenticated artifacts and complete component audits.

## What Changes

- ADD a native scanner identity and component inventory, with one packaged
  execution boundary shared by repository automation and installed CLI consumers.
- MODIFY contributor, scanning-extra and Hatch installation together with all
  scanner consumers. Preserve required SAST coverage and explicit optional-tool
  behavior. Document the additional scanner preparation step.
- ADD exact-artifact publisher verification, native component/advisory coverage
  and license review alongside every existing Python audit. A clean pip-audit
  result alone cannot establish that the native replacement is safe.
- REMOVE every shared Python Semgrep declaration only after the replacement
  passes its feasibility gates. Regenerate complete locks normally, without
  overrides, package omission, baseline refresh or audit exceptions.
- KEEP #772 / PR #779 as a separate blocked alternative. This change does not
  depend on their adoption, edit their producer or approve candidate artifacts.
- REQUIRE actual scan parity, installed-wheel checks and the supported native
  Python/platform matrix before any dependency-only hotfix claim.
- INCLUDE a core patch bump in the eventual implementation PR, synchronized
  across all canonical sources, generated metadata and changelog. The next patch
  after inspected dev 0.55.10 is 0.55.11, subject to live release checks.

This PR is planning only. It changes no dependency input, application behavior,
package version, admission, audit exception, required gate or SAST baseline.
It does not close superseded dependency PRs or authorize promotion.

## Capabilities

### New Capabilities

- `isolated-scanner-runtime`: authenticated scanner preparation, one execution
  owner, complete Python/native audit coverage and consumer compatibility.

### Modified Capabilities

None in this planning PR. Implementation must reconcile existing reproducible
delivery and scanner contracts before changing them.

## Impact

- Core repository only, with explicit compatibility verification for the external
  Code Review module's scanner execution. No module implementation is assumed.
- Expected implementation paths include `pyproject.toml`, `setup.py`, `uv.lock`,
  frozen requirements, delivery/audit scripts, CI, Hatch, the three installed
  scanner consumers and installation documentation.
- Documentation research covers README.md, docs/index.md, installation/scanning
  guides and generated workflow guidance. Preserve frontmatter and navigation.
- #772 remains the downstream producer/admission owner. This change owns an
  independent upstream replacement path. Candidate proof and published hashes
  alone grant no protected artifact authority. Trusted Requirements Authority
  remains a separate required gate.
- Existing dependency maintenance #747 remains open. The old consolidation
  change and its historical evidence remain unchanged.
- Current dev contains runtime/security changes beyond main. A dependency-only
  PR to dev must not be described as a dependency-only dev-to-main release.

## Acceptance criteria

- Every installed or executed scanner dependency remains represented in the
  required security, trust and license evidence.
- Missing, forged, expired or incomplete admission fails before scanner execution.
- Required SAST retains the checked-in rules, baseline identities and failure
  semantics, with no PATH fallback or bulk baseline refresh.
- Source-checkout and installed-wheel consumers execute the same admitted scanner
  and retain their documented output and unavailable-tool behavior.
- Authored failing-before tests precede implementation. Fresh passing evidence,
  native compatibility, full review and all required gates precede adoption.
- Only after a verified implementation PR exists, link every covered duplicate
  to that PR before closure. Leave unimplemented JSON migration and unrelated
  transitive updates separately identified.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->

- **Repository**: `nold-ai/specfact-cli`.
- **GitHub Issue**: #780.
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/780>.
- **Last Synced Status**: proposed; project Todo.
- Parent: #747, dependency maintenance, under epic #194.
- Native issue blockers: none for replacement investigation; #772 is related only.
- Adoption gates: exact upstream publisher identity, complete component/license
  audits, real parity, installed-user compatibility and required protected review.
- Blocks: dependency remediation and release readiness tracked by #747 and #771;
  no native dependency edge back to the parent issue is intended.
- Status: proposed, planning only; implementation and production adoption pending.
- Owner direction: create a new scoped isolation or replacement change,
  2026-10-20 Europe/Berlin.

## Evidence and sources

Inspected dev `db5b249ec4533f6a96aca81a7de05b7ce5c47247` and main
`5262efb0881e4fac7697d629b0530250342bc656`. Sources accessed 2026-10-20.

- [MCP maintainer advisory](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-84m7-p3x7-pcfv).
- [Semgrep 1.179.0 metadata](https://pypi.org/pypi/semgrep/1.179.0/json) and
  [Semgrep 1.181.0 metadata](https://pypi.org/pypi/semgrep/1.181.0/json).
- [Downstream producer and admission issue](https://github.com/nold-ai/specfact-cli/issues/772)
  and [current candidate PR](https://github.com/nold-ai/specfact-cli/pull/779).
- [Existing promotion PR and blockers](https://github.com/nold-ai/specfact-cli/pull/771).
- [OpenGrep v1.31.0 candidate](https://github.com/opengrep/opengrep/releases/tag/v1.31.0),
  source commit `87668f6dbd28a9b97bcaf294a564fe79e0a7b56e`. Published assets
  are inventory only; signatures, components and parity are not verified here.

The reproduced normal-resolution failure is recorded in `CHANGE_VALIDATION.md`.
It is blocker evidence, not authored application RED or successful remediation.
