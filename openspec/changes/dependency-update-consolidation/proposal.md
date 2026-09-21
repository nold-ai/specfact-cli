# Change: Consolidate dependency updates and validate compatible package refresh

## Why

Open Dependabot PRs #744 (Hatchling) and #727 (docs JSON) do not constitute a complete dependency refresh. PR #744 changes two declarations without refreshing the frozen graph, while PR #727 also downgrades Jekyll. The scheduled latest/lower-bound resolver lane discovers additional updates but is advisory, currently runs on Python 3.12, and cannot establish security or supported-runtime compatibility by itself.

The repository needs one reviewed inventory covering declared dependencies, exact pins, all extras, isolated Code Review tooling, and transitives. Vulnerability and malicious-package checks must remain separate: an empty Dependabot alert list or a successful resolver does not approve new artifacts.

## What Changes

- Create a dated, complete package inventory and distinguish compatible candidates from retained packages, deferred migrations, removed transitives, and unverified evidence.
- Consolidate Hatchling's reviewed patch update with both declarations, the build-backend regression expectation, and generated frozen inputs during implementation.
- Assess latest compatible Python packages through the existing resolver mechanism, including exact pins and the isolated Code Review graph. Preserve supported constraints and defer major migrations and dependency downgrades.
- Defer PR #727 as proposed because JSON 3.x downgrades Jekyll; investigate compatible JSON 2.x releases without changing the docs framework baseline.
- Require baseline and candidate CVE/GHSA/OSV audits, separate Socket/upstream malware screening, provenance and artifact-hash review, and fresh final-graph evidence before adoption.
- Retain pycparser 2.22 until an exact-artifact review justifies another version; preserve the blocked 3.0 family and checked-in security-tool floors.
- Verify Python 3.11–3.13, minimal runtime, extras, package installation methods, frozen delivery, and affected documentation before shipping one patch release.

This PR creates planning artifacts only. It does not change dependency declarations, authoritative locks, runtime policy, signed assets, or release versions. All implementation tasks remain unchecked. Candidate metadata and audit reports are discovery evidence, not implementation or security approval.

## Capabilities

### New Capabilities

- `dependency-update-consolidation`: complete dependency inventory, compatible-update selection, independent vulnerability and malicious-package acceptance, and coherent frozen delivery evidence.

### Modified Capabilities

None. This maintenance workflow consumes the existing reproducible-delivery and dependency-trust controls; it does not redefine their enforcement or duplicate the completed #651/#686 foundations.

## Impact

- **Planning artifacts:** proposal, design, tasks, scenario specs, inventory, dated audit, and planned Requirements evidence; source tracking and change ordering.
- **Later implementation:** dependency declarations and duplicated setup/Hatch inputs, authoritative frozen graphs, build-backend test expectations, narrowly justified security-policy evidence, and patch release metadata.
- **Public interfaces:** no CLI/API/schema or Python-support changes. No new package-discovery service, runtime network dependency, bridge adapter, or plugin-registry extension.
- **Documentation:** update existing contributor dependency-refresh/security guidance if the implemented procedure changes. Rebuild Jekyll if its graph changes. README, docs landing page, and sidebar need no planned product/navigation change.
- **Cross-repository boundary:** keep companion-module fixture revisions immutable; check compatibility with the resulting core patch. Any necessary companion release is a separately tracked prerequisite, not an implicit fixture update.
- **Rollback:** revert declarations, lockfiles/exports, related policy records, test expectations, and release metadata coherently. A rollback to known-vulnerable or blocked artifacts is not an acceptable release; select a reviewed safe baseline instead.
- **Out of scope:** unrelated security-code PRs, broad Ruby modernization, major dependency migrations, and implementing the minimal-evidence/C14/C15 proposals.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->

- **GitHub Issue**: #747
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/747>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed; implementation not started
- **Parent Epic**: #194
- **Project**: SpecFact CLI #1, Todo
- **Labels**: dependencies, security, openspec, change-proposal
- **Source PRs**: #744 and #727, both target main; consolidation implementation targets dev and follows normal release promotion.
- **Completed foundations**: #651 and #686, both closed; references, not outstanding blockers.
- **Issue dependencies**: none identified for proposal creation. Missing exact-artifact malware/compatibility evidence blocks candidate adoption, not publication of this proposal.
