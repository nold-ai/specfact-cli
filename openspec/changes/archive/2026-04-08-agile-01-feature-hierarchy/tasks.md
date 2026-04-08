# Tasks: agile-01-feature-hierarchy

## Status

In progress

## Overview

All tasks are GitHub operations or CHANGE_ORDER.md edits. No source code changes. Tasks are
executed primarily via `gh` CLI and the GitHub project board UI.

---

## Task 1 — Create git worktree

- [x] `git worktree add ../specfact-cli-worktrees/feature/agile-01-feature-hierarchy -b feature/agile-01-feature-hierarchy origin/dev`

---

## Task 2 — Create "Feature" label in GitHub

- [x] `gh label create "Feature" --repo nold-ai/specfact-cli --description "Feature grouping of related User Stories" --color "0052cc"`

---

## Task 3 — Create all 25 Feature issues

Create each with `gh issue create --repo nold-ai/specfact-cli --label "Feature" --label "change-proposal"`.

### Under Epic #194 — Architecture (CLI structure, modularity, performance)

- [ ] F1: Modular CLI Foundation — child stories: #193, #199, #203, #206, #207
- [ ] F2: Module Security & Schema Extensions — child stories: #208, #213
- [ ] F3: Marketplace Module Distribution — child stories: #214, #215, #327, #328, #329
- [ ] F4: Module Migration & CLI Reorganization — child stories: #315, #316, #317, #330, #338, #339
- [ ] F5: Developer Workflow & CI Pipeline — child stories: #267, #260, #276
- [ ] F6: Documentation & Discrepancy Remediation — child stories: #291, #348

### Under Epic #186 — specfact backlog

- [ ] F7: Backlog Core Commands — child stories: #116, #155, #158, #166, #173, #295, #298, #310, #337
  - Note: backlog-core-03 has no GitHub issue; omit from child list
- [ ] F8: Backlog Authentication — child stories: #340
- [ ] F9: Scrum Workflows — child stories: #168, #175, #220, #169, #170, #171
- [ ] F10: Kanban Flow Metrics — child stories: #183
- [ ] F11: SAFe & PI Planning — child stories: #184, #182

### Under Epic #187 — specfact policy

- [ ] F12: Policy Engine & Enforcement Modes — child stories: #176, #246
  - Note: #246 also listed under F20 (primary parent); add `specfact-policy` label to #246

### Under Epic #189 — specfact ceremony

- [ ] F13: Ceremony Command Layer — child stories: #185, #245
  - Note: #185 is archived; will be closed in Task 6

### Under Epic #190 — Thorough codebase validation

- [ ] F14: Deep Codebase Validation — child stories: #163

### Under Epic #256 — Architecture Layer Integration

- [ ] F15: Configuration Profiles — child stories: #237, #249, #250
- [ ] F16: Requirements Layer — child stories: #238, #239, #244
- [ ] F17: Solution Architecture Layer — child stories: #240
- [ ] F18: Full-Chain Validation & Traceability — child stories: #241, #242
- [ ] F19: Sync Engine — child stories: #243
- [ ] F20: Governance, Policy Packs & Evidence — child stories: #246, #247, #248
  - Note: #246 primary parent is F20; also carries `specfact-policy` label for #187 discoverability
- [ ] F21: OpenSpec Bridge Integration — child stories: #350

### Under Epic #257 — AI IDE Integration

- [ ] F22: Agent Skills & Instruction Files — child stories: #251, #253, #349
- [ ] F23: MCP Server — child stories: #252

### Under Epic #258 — Integration Governance and Dogfooding

- [ ] F24: End-to-End Integration Proof — child stories: #254, #255

### Under Epic #285 — Test & QA

- [ ] F25: CLI Behavior Validation Suite — child stories: #279, #280, #281, #282, #283, #284

### Singles linked directly to Epic (no Feature needed)

- [ ] Epic #188 → #177 (patch-mode-01, closed — set parent directly to Epic #188)
- [ ] Epic #191 → sidecar-01 (search for issue or confirm no public issue; link directly to #191)
- [ ] Epic #192 → #121 (bundle-mapper-01, closed — set parent directly to Epic #192)

---

## Task 4 — Set issue types and parent relationships (GitHub UI)

These steps require the GitHub project board UI (not settable via `gh` CLI):

- [ ] For each Feature issue created in Task 3: set **Type = "User Story"** in the project board
- [ ] For each Feature issue created in Task 3: set **Parent = Epic** (the Epic listed in Task 3)
- [ ] For each ~79 User Story (change-proposal) issue: set **Parent = Feature** (the Feature
      that groups it, per Task 3 mapping)
- [ ] For singles (#177, #121): set **Parent = Epic** directly (no intermediate Feature)

---

## Task 5 — Update CHANGE_ORDER.md "Parent issues (Epics)" section

- [x] Add Epics #256, #257, #258 to the table in `openspec/CHANGE_ORDER.md`

---

## Task 6 — Close orphaned/stale issues

- [ ] Close issue #185 (ceremony-cockpit-01): confirmed archived 2026-02-18, still open in GitHub
  - `gh issue close 185 --repo nold-ai/specfact-cli --comment "Archived 2026-02-18 (ceremony-cockpit-01-ceremony-aliases). Closing to match change archive status."`

---

## Task 7 — Final verification

- [ ] Run: `gh issue list --repo nold-ai/specfact-cli --label "Feature" --json number,title | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} Feature issues')"`
  - Expected: 25 Feature issues
- [ ] Run: `gh issue list --repo nold-ai/specfact-cli --label "Epic" --json number,title | python3 -c "import json,sys; print(len(json.load(sys.stdin)), 'epics')"`
  - Expected: 12 epics
- [ ] Visually confirm GitHub project board: Epic → Feature → User Story three-level hierarchy

---

## Task 8 — PR creation

- [ ] Push branch: `git push -u origin feature/agile-01-feature-hierarchy`
- [ ] Create PR targeting `dev` branch
