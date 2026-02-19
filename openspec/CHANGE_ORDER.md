# OpenSpec change order by module and implementation dependency

Changes are grouped by **module** and prefixed with **`<module>-NN-`** so implementation order is explicit. Implement **01** before **02** within a module; cross-module dependencies are listed under "Blocked by" below.

## Naming convention

- **Folder**: `<module>-<NN>-<suffix>` (e.g. `backlog-core-01-dependency-analysis-commands`).
- **Module** may be compound: `backlog-core`, `backlog-scrum`, `backlog-kanban`, `backlog-safe`, `policy-engine`, `patch-mode`, `bundle-mapper`, `ceremony-cockpit`.
- **Order**: 01, 02, … within a module group; lower numbers are implemented first where dependencies require it.

---

## Implementation status

### Implemented (archived and pending archive)

| Change | Status / Date |
|--------|---------------|
| arch-01-cli-modular-command-registry | archived 2026-02-04 |
| arch-02-module-package-separation | archived 2026-02-06 |
| arch-03-module-lifecycle-management | archived 2026-02-06 |
| arch-04-core-contracts-interfaces | archived 2026-02-08 |
| arch-05-bridge-registry | archived 2026-02-10 |
| backlog-scrum-01-standup-exceptions-first | archived 2026-02-11 |
| backlog-core-03-refine-writeback-field-splitting | archived 2026-02-12 |
| sidecar-01-flask-support | archived 2026-02-12 |
| ci-01-pr-orchestrator-log-artifacts | implemented 2026-02-16 (archived) |
| arch-06-enhanced-manifest-security | implemented 2026-02-16 (archived) |
| arch-07-schema-extension-system | implemented 2026-02-16 (archived) |
| policy-engine-01-unified-framework | implemented 2026-02-17 (archived) |
| patch-mode-01-preview-apply | implemented 2026-02-18 (archived) |
| validation-01-deep-validation | implemented 2026-02-18 (archived) |
| bundle-mapper-01-mapping-strategy | implemented 2026-02-18 (archived) |
| backlog-core-01-dependency-analysis-commands | implemented 2026-02-18 (archived) |
| ceremony-cockpit-01-ceremony-aliases | implemented 2026-02-18 (archived) |
| workflow-01-git-worktree-management | implemented 2026-02-18 (archived) |
| verification-01-wave1-delta-closure | implemented 2026-02-18 (archived) |

### Pending

Entries in the tables below are pending unless explicitly marked as implemented (pending archive).

## Plan-derived addendum (2026-02-15 architecture integration plan)

The source plan inventory listed 17 new changes. Two additional cross-cutting changes were intentionally added during proposal creation to close integration governance and proof gaps discovered in dependency review:

- `integration-01-cross-change-contracts`: owns cross-change interface ownership, compatibility constraints, and wave gate criteria.
- `dogfooding-01-full-chain-e2e-proof`: defines reproducible end-to-end evidence for running the full chain on real SpecFact backlog slices.

These are derived extensions of the same 2026-02-15 plan and are required to operationalize the plan's end-to-end positioning rather than optional scope expansion.

---

## Module groups and change folders

### Architecture (platform foundation)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| — | — | arch-06, arch-07 implemented 2026-02-16 (see Implemented above) | — | — |

### Marketplace (module distribution)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| marketplace | 01 | marketplace-01-central-module-registry | [#214](https://github.com/nold-ai/specfact-cli/issues/214) | #208 |
| marketplace | 02 | marketplace-02-advanced-marketplace-features | [#215](https://github.com/nold-ai/specfact-cli/issues/215) | #214 |

### Cross-cutting foundations (no hard dependencies — implement early)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| policy-engine | 01 | policy-engine-01-unified-framework (implemented 2026-02-17; archived) | [#176](https://github.com/nold-ai/specfact-cli/issues/176) | — |
| patch-mode | 01 | patch-mode-01-preview-apply (implemented 2026-02-18; archived) | [#177](https://github.com/nold-ai/specfact-cli/issues/177) | — |
| validation | 01 | validation-01-deep-validation (implemented 2026-02-18; archived) | [#163](https://github.com/nold-ai/specfact-cli/issues/163) | — |
| bundle-mapper | 01 | bundle-mapper-01-mapping-strategy (implemented 2026-02-18; archived) | [#121](https://github.com/nold-ai/specfact-cli/issues/121) | — |
| verification | 01 | verification-01-wave1-delta-closure (implemented 2026-02-18; archived) | [#276](https://github.com/nold-ai/specfact-cli/issues/276) | #177 ✅, #163 ✅, #116 ✅, #121 ✅ |

### CI/CD (workflow and artifacts)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|----------------|----------|------------|
| — | — | ci-01 implemented 2026-02-16 (see Implemented above) | — | — |

### Developer workflow (parallel branch operations)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| workflow | 01 | workflow-01-git-worktree-management ✅ (implemented 2026-02-18; archived) | [#267](https://github.com/nold-ai/specfact-cli/issues/267) | — |

### backlog-core (required by all backlog-* modules)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| backlog-core | 01 | backlog-core-01-dependency-analysis-commands ✅ (implemented 2026-02-18; archived) | [#116](https://github.com/nold-ai/specfact-cli/issues/116) | — |
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
| ceremony-cockpit | 01 | ceremony-cockpit-01-ceremony-aliases ✅ (implemented 2026-02-18; archived) | [#185](https://github.com/nold-ai/specfact-cli/issues/185) | — (optional: #220, #170, #171, #169, #183, #184) |

### Profile and configuration layering (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| profile | 01 | profile-01-config-layering | [#237](https://github.com/nold-ai/specfact-cli/issues/237) | #193 (existing init/module-state baseline) |
| profile | 02 | profile-02-central-config-sources | [#249](https://github.com/nold-ai/specfact-cli/issues/249) | profile-01 |
| profile | 03 | profile-03-domain-overlays | [#250](https://github.com/nold-ai/specfact-cli/issues/250) | profile-01, profile-02, #213 |

### Requirements layer (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| requirements | 01 | requirements-01-data-model | [#238](https://github.com/nold-ai/specfact-cli/issues/238) | #213 |
| requirements | 02 | requirements-02-module-commands | [#239](https://github.com/nold-ai/specfact-cli/issues/239) | requirements-01, #213 |
| requirements | 03 | requirements-03-backlog-sync | [#244](https://github.com/nold-ai/specfact-cli/issues/244) | requirements-02, sync-01 |

### Architecture and traceability chain (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| architecture | 01 | architecture-01-solution-layer | [#240](https://github.com/nold-ai/specfact-cli/issues/240) | requirements-01, requirements-02 |
| validation | 02 | validation-02-full-chain-engine | [#241](https://github.com/nold-ai/specfact-cli/issues/241) | requirements-02, architecture-01, #176 |
| traceability | 01 | traceability-01-index-and-orphans | [#242](https://github.com/nold-ai/specfact-cli/issues/242) | requirements-02, architecture-01 |

### Sync and ceremony integration (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| sync | 01 | sync-01-unified-kernel | [#243](https://github.com/nold-ai/specfact-cli/issues/243) | #177 |
| ceremony | 02 | ceremony-02-requirements-aware-output | [#245](https://github.com/nold-ai/specfact-cli/issues/245) | requirements-02, #185 |

### Governance extensions (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| policy | 02 | policy-02-packs-and-modes | [#246](https://github.com/nold-ai/specfact-cli/issues/246) | profile-01, #176 |
| governance | 01 | governance-01-evidence-output | [#247](https://github.com/nold-ai/specfact-cli/issues/247) | validation-02, policy-02 |
| governance | 02 | governance-02-exception-management | [#248](https://github.com/nold-ai/specfact-cli/issues/248) | policy-02 |

### AI integration (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| ai-integration | 01 | ai-integration-01-agent-skill | [#251](https://github.com/nold-ai/specfact-cli/issues/251) | validation-02 |
| ai-integration | 02 | ai-integration-02-mcp-server | [#252](https://github.com/nold-ai/specfact-cli/issues/252) | validation-02 |
| ai-integration | 03 | ai-integration-03-instruction-files | [#253](https://github.com/nold-ai/specfact-cli/issues/253) | ai-integration-01 |

### Integration governance and proof (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| integration | 01 | integration-01-cross-change-contracts | [#254](https://github.com/nold-ai/specfact-cli/issues/254) | profile-01, requirements-02, architecture-01, validation-02, policy-02 |
| dogfooding | 01 | dogfooding-01-full-chain-e2e-proof | [#255](https://github.com/nold-ai/specfact-cli/issues/255) | requirements-02, architecture-01, validation-02, traceability-01, governance-01 |

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
| [#237](https://github.com/nold-ai/specfact-cli/issues/237) | profile-01 config layering | #193 |
| [#249](https://github.com/nold-ai/specfact-cli/issues/249) | profile-02 central config sources | #237 |
| [#250](https://github.com/nold-ai/specfact-cli/issues/250) | profile-03 domain overlays | #237, #249, #213 |
| [#238](https://github.com/nold-ai/specfact-cli/issues/238) | requirements-01 data model | #213 |
| [#239](https://github.com/nold-ai/specfact-cli/issues/239) | requirements-02 module commands | #238, #213 |
| [#244](https://github.com/nold-ai/specfact-cli/issues/244) | requirements-03 backlog sync | #239, #243 |
| [#240](https://github.com/nold-ai/specfact-cli/issues/240) | architecture-01 solution layer | #238, #239 |
| [#241](https://github.com/nold-ai/specfact-cli/issues/241) | validation-02 full-chain engine | #239, #240, #176 |
| [#242](https://github.com/nold-ai/specfact-cli/issues/242) | traceability-01 index and orphans | #239, #240 |
| [#243](https://github.com/nold-ai/specfact-cli/issues/243) | sync-01 unified kernel | #177 |
| [#245](https://github.com/nold-ai/specfact-cli/issues/245) | ceremony-02 requirements-aware output | #239, #185 |
| [#246](https://github.com/nold-ai/specfact-cli/issues/246) | policy-02 packs and modes | #237, #176 |
| [#247](https://github.com/nold-ai/specfact-cli/issues/247) | governance-01 evidence output | #241, #246 |
| [#248](https://github.com/nold-ai/specfact-cli/issues/248) | governance-02 exception management | #246 |
| [#251](https://github.com/nold-ai/specfact-cli/issues/251) | ai-integration-01 agent skill | #241 |
| [#252](https://github.com/nold-ai/specfact-cli/issues/252) | ai-integration-02 mcp server | #241 |
| [#253](https://github.com/nold-ai/specfact-cli/issues/253) | ai-integration-03 instruction files | #251 |
| [#254](https://github.com/nold-ai/specfact-cli/issues/254) | integration-01 cross-change contracts | #237, #239, #240, #241, #246 |
| [#255](https://github.com/nold-ai/specfact-cli/issues/255) | dogfooding-01 full-chain e2e proof | #239, #240, #241, #242, #247 |

**How to set in GitHub**: Open the issue → right sidebar **Relationships** → **Mark as blocked by** → search and select the blocking issue(s).

---

## Ownership Authority (Cross-Change)

The following ownership boundaries are mandatory before implementation for overlapping files/interfaces.

| Owned surface | Authoritative change | Dependent changes |
|---|---|---|
| Policy mode execution semantics and per-rule mode handling | `policy-02-packs-and-modes` | `governance-01-evidence-output`, `governance-02-exception-management` |
| Evidence JSON envelope and CI verdict schema | `governance-01-evidence-output` | `validation-02-full-chain-engine`, `governance-02-exception-management`, `dogfooding-01-full-chain-e2e-proof` |
| Exception scope suppression logic and expiry behavior | `governance-02-exception-management` | `policy-02-packs-and-modes`, `governance-01-evidence-output` |
| Base requirements schema model (`src/specfact_cli/models/requirements.py`) | `requirements-01-data-model` | `profile-03-domain-overlays`, `requirements-02-module-commands` |
| Architecture namespace extension on `ProjectBundle` (`src/specfact_cli/models/project.py`) | `architecture-01-solution-layer` | `validation-02-full-chain-engine`, `traceability-01-index-and-orphans` |
| Requirements namespace extension on `ProjectBundle` (`src/specfact_cli/models/project.py`) | `requirements-01-data-model` | `requirements-02-module-commands`, `requirements-03-backlog-sync`, `architecture-01-solution-layer` |
| Backlog requirements extraction/update adapter contract (`modules/backlog/src/adapters/`) | `requirements-02-module-commands` | `requirements-03-backlog-sync` |

Pre-implementation rule:
- No dependent change may redefine an owned surface. Any required semantic change must be proposed as a delta to the authoritative change first.

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

- **Wave 1** ✅ **Complete** — Platform extensions + cross-cutting foundations (arch-06 ✅, arch-07 ✅, ci-01 ✅):
  - arch-06 ✅, arch-07 ✅, ci-01 ✅
  - policy-engine-01 ✅, patch-mode-01 ✅
  - backlog-core-01 ✅
  - validation-01 ✅, sidecar-01 ✅, bundle-mapper-01 ✅

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
  - ceremony-cockpit-01 ✅ (probes installed backlog-* modules at runtime; no hard deps but best after Wave 3)

- **Wave 5 — Foundations for business-first chain** (architecture integration):
  - profile-01
  - requirements-01
  - requirements-02 (after requirements-01 + arch-07)

- **Wave 6 — End-to-end chain and sync kernel**:
  - architecture-01 (after requirements-01 + requirements-02)
  - validation-02 (after architecture-01 + requirements-02 + policy-engine-01)
  - traceability-01 (after architecture-01 + requirements-02)
  - sync-01 (after patch-mode-01)
  - requirements-03 (after requirements-02 + sync-01)

- **Wave 7 — Governance and ceremony business context**:
  - policy-02 (after profile-01 + policy-engine-01)
  - governance-01 (after validation-02 + policy-02)
  - governance-02 (after policy-02)
  - ceremony-02 (after requirements-02 + ceremony-cockpit-01)

- **Wave 8 — Enterprise profile maturity and AI interfaces**:
  - profile-02 (after profile-01)
  - profile-03 (after profile-01 + profile-02 + arch-07)
  - ai-integration-01 (after validation-02)
  - ai-integration-02 (after validation-02)
  - ai-integration-03 (after ai-integration-01)

- **Wave 9 — Integration contract and product proof**:
  - integration-01 (after profile-01 + requirements-02 + architecture-01 + validation-02 + policy-02)
  - dogfooding-01 (after requirements-02 + architecture-01 + validation-02 + traceability-01 + governance-01)

---

## Mandatory Wave Exit Gates

A wave cannot be considered complete until all gate criteria listed for that wave are met and auditable.

- Wave 0 gate: Core modular CLI and bridge registry flows remain stable and archived changes are validated.
- Wave 1 gate: arch-06/07, policy-engine-01, patch-mode-01, backlog-core-01, validation-01 produce passing contract and strict OpenSpec validation. ✅ Completed 2026-02-18.
- Wave 2 gate: At least one backlog planning workflow completes with no blocking dependency regressions across backlog-core + marketplace-01.
- Wave 3 gate: Higher-order backlog workflows and marketplace-02 interoperate without command-group regressions.
- Wave 4 gate: `ceremony-cockpit-01` aliases resolve and execute against installed modules without fallback failures.
- Wave 5 gate: `profile-01`, `requirements-01`, `requirements-02` demonstrate profile-aware requirement lifecycle with strict validation and TDD evidence.
- Wave 6 gate: One chain run proves requirements -> architecture -> validation/traceability/sync compatibility with no unresolved ownership conflicts.
- Wave 7 gate: policy/governance/ceremony integration emits consistent evidence and exception semantics aligned to ownership authority.
- Wave 8 gate: profile maturity + AI interfaces (`ai-integration-01/02/03`) operate on top of validation-02 outputs with no schema divergence.
- Wave 9 gate: integration umbrella contract is adopted by all dependent changes and dogfooding E2E proof artifacts confirm end-to-end positioning claims.
