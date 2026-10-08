# Change: Repair the frozen security graph and versioning test fixture

## Why

Core PR #755 fails required checks on unchanged dev dependencies and a fixture that
stages Git metadata. The owner explicitly authorized the focused #747 repair and cleared
concurrent ownership on 2026-10-09 Europe/Berlin.

## What Changes

- Implement the first security slice of existing dependency-update-consolidation: PyJWT,
  urllib3, virtualenv and resolver-required Semgrep/python-discovery updates.
- Preserve caller-owned JWT options, expiry enforcement and supported signed-token padding.
- Restrict versioning fixture staging to generated project files; preserve real assertions.
- Isolate the ephemeral smoke fallback's seed cache and disable periodic updates so an
  older virtualenv's persisted unverified wheel cannot cross into this launcher.
- Update the exact Semgrep lock sentinel while preserving its floor and MCP waiver checks.
- Generate coherent frozen inputs after exact-artifact review and retain authentic RED/final proof.

This branch contains only the focused slice. Original #748's broader inventory/build/Ruby/
release plan and branch remain untouched and need later reconciliation. Do not close #747
or archive the consolidation after this slice. No policy waiver, module pin, release bump,
CI gate change or planned workflow runtime implementation is included.

## Capabilities

### New Capabilities

- `dependency-update-consolidation`: focused security slice of existing #747.

### Modified Capabilities

None. Existing delivery, signature and Requirements controls remain authoritative.

## Impact

Frozen lock/export, JWT/cache regression tests, smoke fallback and versioning fixture;
production analyzer is unchanged. Independent artifact, license, security, consumer, Python and quality gates
remain required. A passing advisory audit alone cannot establish safe adoption.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->

- **GitHub Issue**: #747
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/747>
- **Parent Epic**: #194
- **Project**: SpecFact CLI #1, In Progress; focused ownership explicitly approved.
- **Labels**: dependencies, security, openspec, change-proposal
- **Native dependencies**: no blockers/blocking edges at refreshed readback.
- **Existing planning PR**: #748, broader scope remains open and unchanged.
- **Unblocks**: baseline failures on #755, without inventing a native dependency edge.
