# OpenSpec change order by module and implementation dependency

Changes are grouped by **module** and prefixed with **`<module>-NN-`** so implementation order is explicit. Implement **01** before **02** within a module; cross-module dependencies are listed under "Blocked by" below.

## Naming convention

- **Folder**: `<module>-<NN>-<suffix>` (e.g. `backlog-core-01-dependency-analysis-commands`).
- **Module** may be compound: `backlog-core`, `backlog-scrum`, `backlog-kanban`, `backlog-safe`, `policy-engine`, `patch-mode`, `bundle-mapper`, `ceremony-cockpit`.
- **Order**: 01, 02, … within a module group; lower numbers are implemented first where dependencies require it.

---

## Implementation status

### Implemented (archived)

| Change | Archived |
|--------|----------|
| arch-01-cli-modular-command-registry | 2026-02-04 |
| arch-02-module-package-separation | 2026-02-06 |
| arch-03-module-lifecycle-management | 2026-02-06 |
| arch-04-core-contracts-interfaces | 2026-02-08 |
| arch-05-bridge-registry | 2026-02-10 |
| backlog-scrum-01-standup-exceptions-first | 2026-02-11 |
| backlog-core-03-refine-writeback-field-splitting | 2026-02-12 |
| sidecar-01-flask-support | 2026-02-12 |

### Pending

All entries in the table below are pending implementation.

---

## Module groups and change folders

### Architecture (platform foundation)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| arch | 06 | arch-06-enhanced-manifest-security | [#208](https://github.com/nold-ai/specfact-cli/issues/208) | arch-05 ✅ |
| arch | 07 | arch-07-schema-extension-system | [#213](https://github.com/nold-ai/specfact-cli/issues/213) | arch-04 ✅ |

### Marketplace (module distribution)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| marketplace | 01 | marketplace-01-central-module-registry | [#214](https://github.com/nold-ai/specfact-cli/issues/214) | #208 |
| marketplace | 02 | marketplace-02-advanced-marketplace-features | [#215](https://github.com/nold-ai/specfact-cli/issues/215) | #214 |

### Cross-cutting foundations (no hard dependencies — implement early)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| policy-engine | 01 | policy-engine-01-unified-framework | [#176](https://github.com/nold-ai/specfact-cli/issues/176) | — |
| patch-mode | 01 | patch-mode-01-preview-apply | [#177](https://github.com/nold-ai/specfact-cli/issues/177) | — |
| validation | 01 | validation-01-deep-validation | [#163](https://github.com/nold-ai/specfact-cli/issues/163) | — |
| bundle-mapper | 01 | bundle-mapper-01-mapping-strategy | [#121](https://github.com/nold-ai/specfact-cli/issues/121) | — |

### backlog-core (required by all backlog-* modules)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| backlog-core | 01 | backlog-core-01-dependency-analysis-commands | [#116](https://github.com/nold-ai/specfact-cli/issues/116) | — |
| backlog-core | 02 | backlog-core-02-interactive-issue-creation | [#173](https://github.com/nold-ai/specfact-cli/issues/173) | #116 (optional: #176, #177) |

### backlog-scrum

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| backlog-scrum | 02 | backlog-scrum-02-sprint-planning | [#170](https://github.com/nold-ai/specfact-cli/issues/170) | #116 (optional: #176, #182) |
| backlog-scrum | 03 | backlog-scrum-03-story-complexity | [#171](https://github.com/nold-ai/specfact-cli/issues/171) | #116 (optional: #177) |
| backlog-scrum | 04 | backlog-scrum-04-definition-of-done | [#169](https://github.com/nold-ai/specfact-cli/issues/169) | — (optional: #176) |

### backlog-kanban

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| backlog-kanban | 01 | backlog-kanban-01-flow-metrics | [#183](https://github.com/nold-ai/specfact-cli/issues/183) | #116 (optional: #176) |

### backlog-safe

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| backlog-safe | 01 | backlog-safe-01-pi-planning | [#184](https://github.com/nold-ai/specfact-cli/issues/184) | #116 (optional: #176) |
| backlog-safe | 02 | backlog-safe-02-risk-rollups | [#182](https://github.com/nold-ai/specfact-cli/issues/182) | #184 (optional: #116, #176, #170, #171, #183) |

### ceremony-cockpit

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| ceremony-cockpit | 01 | ceremony-cockpit-01-ceremony-aliases | [#185](https://github.com/nold-ai/specfact-cli/issues/185) | — (optional: #220, #170, #171, #169, #183, #184) |

---

## GitHub "Blocked by" relationships

Set these in GitHub so issue dependencies are explicit. Optional dependencies are graceful no-ops (modules degrade when not installed) and do **not** need to be set as hard blockers.

| Issue | Change | Hard blocked by |
|-------|--------|-----------------|
| [#208](https://github.com/nold-ai/specfact-cli/issues/208) | arch-06 manifest security | arch-05 ✅ (already implemented) |
| [#213](https://github.com/nold-ai/specfact-cli/issues/213) | arch-07 schema extensions | arch-04 ✅ (already implemented) |
| [#214](https://github.com/nold-ai/specfact-cli/issues/214) | marketplace-01 registry | #208 |
| [#215](https://github.com/nold-ai/specfact-cli/issues/215) | marketplace-02 advanced features | #214 |
| [#173](https://github.com/nold-ai/specfact-cli/issues/173) | backlog-core-02 interactive create | #116 |
| [#220](https://github.com/nold-ai/specfact-cli/issues/220) | backlog-scrum-01 standup | #116 |
| [#170](https://github.com/nold-ai/specfact-cli/issues/170) | backlog-scrum-02 sprint planning | #116 |
| [#171](https://github.com/nold-ai/specfact-cli/issues/171) | backlog-scrum-03 story complexity | #116 |
| [#183](https://github.com/nold-ai/specfact-cli/issues/183) | backlog-kanban-01 flow metrics | #116 |
| [#184](https://github.com/nold-ai/specfact-cli/issues/184) | backlog-safe-01 PI planning | #116 |
| [#182](https://github.com/nold-ai/specfact-cli/issues/182) | backlog-safe-02 risk rollups | #184 |

**How to set in GitHub**: Open the issue → right sidebar **Relationships** → **Mark as blocked by** → search and select the blocking issue(s).

---

## Parent issues (Epics) per module group

One parent issue per module group for grouping. Set **Type** to Epic on the project board. Link child/change issues via **Relationships** (sub-issues or "tracks") or by setting the project **Parent** field to the epic.

| Module group | Parent issue | GitHub # |
|---|---|---|
| `specfact backlog` (all backlog-* modules) | [Epic] specfact backlog | [#186](https://github.com/nold-ai/specfact-cli/issues/186) |
| `specfact policy` | [Epic] specfact policy | [#187](https://github.com/nold-ai/specfact-cli/issues/187) |
| Patch mode | [Epic] Patch mode (preview/apply) | [#188](https://github.com/nold-ai/specfact-cli/issues/188) |
| `specfact ceremony` | [Epic] specfact ceremony | [#189](https://github.com/nold-ai/specfact-cli/issues/189) |
| Thorough validation | [Epic] Thorough codebase validation | [#190](https://github.com/nold-ai/specfact-cli/issues/190) |
| Sidecar validation | [Epic] Sidecar validation | [#191](https://github.com/nold-ai/specfact-cli/issues/191) |
| Bundle mapping | [Epic] Bundle/spec mapping | [#192](https://github.com/nold-ai/specfact-cli/issues/192) |
| Architecture + Marketplace | [Epic] Architecture (CLI structure, modularity, performance) | [#194](https://github.com/nold-ai/specfact-cli/issues/194) |

---

## Implementation waves

Dependencies flow left-to-right; a wave may start once all its hard blockers are resolved.

- **Wave 0** ✅ **Complete** — arch-01 through arch-05 (modular CLI foundation, bridge registry)

- **Wave 1 — Platform extensions + cross-cutting foundations** (all unblocked now):
  - arch-06, arch-07
  - policy-engine-01, patch-mode-01
  - backlog-core-01
  - validation-01, sidecar-01 ✅, bundle-mapper-01

- **Wave 2 — Marketplace + backlog module layer** (needs Wave 1):
  - marketplace-01 (needs arch-06)
  - backlog-core-02 (needs backlog-core-01)
  - backlog-core-03 ✅
  - backlog-scrum-02, backlog-scrum-03, backlog-scrum-04 (need backlog-core-01)
  - backlog-kanban-01, backlog-safe-01 (need backlog-core-01)

- **Wave 3 — Higher-order backlog + marketplace** (needs Wave 2):
  - marketplace-02 (needs marketplace-01)
  - backlog-scrum-01 ✅ (needs backlog-core-01; benefits from policy-engine-01 + patch-mode-01)
  - backlog-safe-02 (needs backlog-safe-01; integrates with scrum/kanban via bridge registry)

- **Wave 4 — Ceremony layer** (needs Wave 3):
  - ceremony-cockpit-01 (probes installed backlog-* modules at runtime; no hard deps but best after Wave 3)
