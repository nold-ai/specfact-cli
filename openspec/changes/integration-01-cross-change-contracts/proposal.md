# Change: Integration Umbrella for Cross-Change Contracts and Ownership

## Why




The architecture integration wave introduces many parallel changes that touch shared files and interfaces (`ProjectBundle` extensions, backlog adapters, policy engine outputs). Without one umbrella integration contract, implementation drift and merge collisions are likely. This change creates a single authoritative contract and ownership model so all dependent changes can compose into one end-to-end system.

## What Changes




- **NEW**: Define a cross-change integration contract for shared interfaces:
  - ProjectBundle extension namespaces and merge order
  - Backlog adapter extension protocol boundaries
  - Policy engine result envelope consumed by governance/evidence layers
- **NEW**: Define ownership boundaries and change authority rules for overlapping files:
  - `policy-02-packs-and-modes` owns policy mode execution core
  - `governance-01-evidence-output` owns evidence schema and CI envelope
  - `governance-02-exception-management` owns exception-scope suppression behavior
  - `requirements-01-data-model` owns base requirements schema
  - `architecture-01-solution-layer` owns architecture-specific bundle extension namespace
- **NEW**: Add compatibility rules for all architecture-plan changes before implementation starts (required pre-implementation checklist)
- **NEW**: Add integration acceptance gate definition for Wave 6+ and Wave 8 closure

## Capabilities
### New Capabilities

- `cross-change-integration-contract`: A single integration contract that defines interface boundaries, ownership authority, and compatibility rules across all architecture integration changes.

### Modified Capabilities

(none)


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #254
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/254>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: e677449c87a4f951 -->