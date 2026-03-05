# Change Proposal: agile-01-feature-hierarchy

## Status

Active

## Date

2026-03-05

## Priority

Medium

## Purpose

Complete the GitHub agile hierarchy from two levels (Epic → User Story) to three levels
(Epic → Feature → User Story) so the project board supports coherent sprint-planning groupings
below the Epic level.

---

## Problem

The repo has 12 Epics and ~79 User Story (change-proposal) issues but zero Feature-tier issues.
This means the project board is flat below the Epic level: sprint planners cannot see which
cluster of User Stories delivers a coherent user-facing or architectural slice of value. There
is no natural grouping unit for mid-level roadmap planning, velocity tracking per theme, or
cross-team scoping conversations.

Additionally, Epics #256 (Architecture Layer Integration), #257 (AI IDE Integration), and #258
(Integration Governance and Dogfooding), created as part of the 2026-02-15 architecture
integration plan, are not recorded in `openspec/CHANGE_ORDER.md`'s "Parent issues (Epics)"
section, leaving the change order document out of sync with GitHub.

---

## Proposed Change

1. Create a "Feature" label in GitHub.
2. Create 25 Feature issues (F1–F25), each linked to its parent Epic and listing the child
   User Story issues it groups.
3. Set issue type to "User Story" on Feature issues and set the Feature's parent = Epic via
   the GitHub project board (requires GitHub UI).
4. Set parent (User Story → Feature) for all ~79 change-proposal issues via the GitHub
   project board.
5. Update `openspec/CHANGE_ORDER.md` to add Epics #256, #257, #258 to the "Parent issues"
   section.
6. Close issue #185 (ceremony-cockpit-01), confirmed archived 2026-02-18, which remains open
   in GitHub.
7. Verify the project board shows a correct three-level hierarchy.

---

## Scope

- No source code changes.
- No OpenSpec spec or design artifacts (no behaviour changes, no API contracts).
- Tasks only: GitHub operations + one CHANGE_ORDER.md update.

---

## Impact

- Project board: three-level Epic → Feature → User Story hierarchy visible.
- Sprint planning: team can select Features as sprint-level planning units.
- Roadmap: Features group User Stories into coherent architectural slices.
- CHANGE_ORDER.md: stays in sync with all 12 Epics.

---

## Files Modified

- `openspec/CHANGE_ORDER.md` — add #256, #257, #258 to "Parent issues (Epics)" section.

## Files Created

- `openspec/changes/agile-01-feature-hierarchy/proposal.md` (this file)
- `openspec/changes/agile-01-feature-hierarchy/tasks.md`
