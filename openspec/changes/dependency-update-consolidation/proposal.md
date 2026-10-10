# Change: Consolidate compatible security dependency PRs

## Why

The owner authorized the remaining security and compatible package updates on
2026-10-10 Europe/Berlin, including all five existing PRs #744, #727, #752, #754
and #753. Their shared locks and outdated bases need sequential reconciliation.
The earlier focused repair #756 merged into dev on 2026-10-09; its specifications,
tests and historical proof remain part of this change and must be preserved.

## What Changes

- EXTEND #744 with GitPython 3.1.62 and Hatchling 1.32.4, synchronized declarations,
  build expectation, generated Python lock and hash-protected CI export.
- MODIFY #727 into compatible JSON hardening: declare `>=2.21.2,<3`, keep JSON
  2.21.2 and Jekyll 4.4.1, and strengthen the existing security-floor test.
- EXTEND #752/#754 with redirect-from 0.17.0 and feed 0.18.0 security fixes;
  verify unsafe redirect and feed escaping boundaries alongside ordinary output.
- EXTEND #753 with relative-links 0.9.1 and navigation/base-URL compatibility proof.
- ADD one 0.55.5 bugfix release, subject to the live PyPI-ahead check, with all
  canonical version sources, generated metadata and changelog synchronized.
- MODIFY the existing PR branches into
  `dev <- #744 <- #727 <- #752 <- #754 <- #753`, retaining numbers, captured heads,
  signed commits and explicit force-with-lease protection. Register a native
  GitHub stack when available; otherwise retain the linked branch chain.
- MODIFY conflicting planning PR #748 and the internal wiki to reflect completed
  #756 work, the selected stack and deferred broader inventory work.

JSON 3 migration and all unrelated dependency upgrades remain deferred. No module
fixture, security policy, trusted authority, gate relaxation or workflow runtime
implementation is included. Keep #747 open and do not archive the whole change.
Close an older duplicate only after verifying its relevant fixes are covered and
linking its replacement; none was found in the inspected open PR inventory.

## Capabilities

### New Capabilities

- `dependency-update-consolidation`: extends the existing #747 maintenance slices.

### Modified Capabilities

None. Existing delivery, signature and Requirements controls remain authoritative.

## Impact

- Affected specs: dependency-update-consolidation; prior #756 requirements retained.
- Affected inputs: pyproject.toml, setup.py, uv.lock, requirements/ci/locked.txt,
  docs/Gemfile and docs/Gemfile.lock, canonical package versions and CHANGELOG.md.
- Integration points: GitPython consumers, Hatchling wheel builds, Jekyll output,
  immutable module fixtures, frozen audits, trust/Socket, quality and Requirements.
- Review scope: each PR carries only its parent-relative layer; the final head
  must pass the complete accumulated validation. Rebase invalidates head-bound proof.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->

- **GitHub Issue**: #747, <https://github.com/nold-ai/specfact-cli/issues/747>
- **Parent Epic**: #194
- **Project**: SpecFact CLI #1, In Progress; ownership explicitly approved.
- **Labels**: dependencies, security, openspec, change-proposal
- **Native dependencies**: no blockers/blocking edges at refreshed readback.
- **Planning PR**: #748; broader accepted work remains open.
- **Completed repair**: #756, merge cb417b5dd5d58fbe9ce50b62cb8a75868caa5ef2.
