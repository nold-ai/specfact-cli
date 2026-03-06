# OpenSpec change order by module and implementation dependency

Changes are grouped by **module** and prefixed with **`<module>-NN-`** so implementation order is explicit. Implement **01** before **02** within a module; cross-module dependencies are listed under "Blocked by" below.

## Naming convention

- **Folder**: `<module>-<NN>-<suffix>` (e.g. `backlog-core-01-dependency-analysis-commands`).
- **Module** may be compound: `backlog-core`, `backlog-scrum`, `backlog-kanban`, `backlog-safe`, `policy-engine`, `patch-mode`, `bundle-mapper`, `ceremony-cockpit`.
- **Order**: 01, 02, … within a module group; lower numbers are implemented first where dependencies require it.

---

## Implementation status

### Implemented (archived or archive-pending)

Only changes that are **archived**, shown as **✓ Complete** by `openspec list`, or fully implemented and awaiting archive are listed. Use ✅ in tables below only for these.

| Change | Status / Date |
|--------|---------------|
| ✅ arch-01-cli-modular-command-registry | archived 2026-02-04 |
| ✅ arch-02-module-package-separation | archived 2026-02-06 |
| ✅ arch-03-module-lifecycle-management | archived 2026-02-06 |
| ✅ arch-04-core-contracts-interfaces | archived 2026-02-08 |
| ✅ arch-05-bridge-registry | archived 2026-02-10 |
| ✅ backlog-scrum-01-standup-exceptions-first | archived 2026-02-11 |
| ✅ backlog-core-03-refine-writeback-field-splitting | archived 2026-02-12 |
| ✅ sidecar-01-flask-support | archived 2026-02-12 |
| ✅ ci-01-pr-orchestrator-log-artifacts | implemented 2026-02-16 (archived) |
| ✅ arch-06-enhanced-manifest-security | implemented 2026-02-16 (archived) |
| ✅ arch-07-schema-extension-system | implemented 2026-02-16 (archived) |
| ✅ arch-08-documentation-discrepancies-remediation | archived 2026-02-22 |
| ✅ policy-engine-01-unified-framework | implemented 2026-02-17 (archived) |
| ✅ patch-mode-01-preview-apply | implemented 2026-02-18 (archived) |
| ✅ validation-01-deep-validation | implemented 2026-02-18 (archived) |
| ✅ bundle-mapper-01-mapping-strategy | implemented 2026-02-22 (archived) |
| ✅ backlog-core-01-dependency-analysis-commands | implemented 2026-02-18 (archived) |
| ✅ backlog-core-02-interactive-issue-creation | implemented 2026-02-22 (archived) |
| ✅ backlog-core-04-installed-runtime-discovery-and-add-prompt | implemented 2026-02-23 (archived) |
| ✅ ceremony-cockpit-01-ceremony-aliases | implemented 2026-02-18 (archived) |
| ✅ workflow-01-git-worktree-management | implemented 2026-02-18 (archived) |
| ✅ verification-01-wave1-delta-closure | implemented 2026-02-18 (archived) |
| ✅ marketplace-01-central-module-registry | implemented 2026-02-22 (archived) |
| ✅ marketplace-02-advanced-marketplace-features | implemented 2026-03-03 (archived) |
| ✅ module-migration-01-categorize-and-group | implemented 2026-03-03 (archived) |
| ✅ module-migration-02-bundle-extraction | implemented 2026-03-03 (archived) |
| ✅ module-migration-05-modules-repo-quality | implemented 2026-03-04 (archive pending in specfact-cli) |
| ✅ backlog-auth-01-backlog-auth-commands | implemented 2026-03-03 (archived) |
| ✅ backlog-core-05-user-modules-bootstrap | implemented 2026-03-03 (archived) |
| ✅ backlog-core-06-refine-custom-field-writeback | implemented 2026-03-03 (archived) |

### Pending

Entries in the tables below are pending unless explicitly marked as implemented (archived).

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
| — | — | ✅ arch-06, arch-07, arch-08 (see Implemented above) | — | — |
| arch | 08 | ✅ arch-08-documentation-discrepancies-remediation (archived 2026-02-22) | [#291](https://github.com/nold-ai/specfact-cli/issues/291) | — |

### Documentation and docs governance

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| docs | 01 | docs-01-core-modules-docs-alignment | [#348](https://github.com/nold-ai/specfact-cli/issues/348) | module-migration-01 ✅; module-migration-02 ✅; module-migration-03 ✅; module-migration-05 ✅; module-migration-06/07 outputs inform residual cleanup wording |

### Marketplace (module distribution)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| marketplace | 01 | ✅ marketplace-01-central-module-registry (implemented 2026-02-22; archived) | [#214](https://github.com/nold-ai/specfact-cli/issues/214) | #208 |
| marketplace | 02 | ✅ marketplace-02-advanced-marketplace-features (implemented 2026-03-03; archived) | [#215](https://github.com/nold-ai/specfact-cli/issues/215) | ✅ #214 |
| marketplace | 03 | marketplace-03-publisher-identity | [#327](https://github.com/nold-ai/specfact-cli/issues/327) | #215 (marketplace-02) |
| marketplace | 04 | marketplace-04-revocation | [#328](https://github.com/nold-ai/specfact-cli/issues/328) | #327 (marketplace-03) |
| marketplace | 05 | marketplace-05-registry-federation | [#329](https://github.com/nold-ai/specfact-cli/issues/329) | #327 (marketplace-03) |

### Module migration (UX grouping and extraction)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| module-migration | 01 | module-migration-01-categorize-and-group | [#315](https://github.com/nold-ai/specfact-cli/issues/315) | #215 ✅ (marketplace-02) |
| module-migration | 02 | module-migration-02-bundle-extraction | [#316](https://github.com/nold-ai/specfact-cli/issues/316) | module-migration-01 ✅ |
| module-migration | 03 | module-migration-03-core-slimming | [#317](https://github.com/nold-ai/specfact-cli/issues/317) | module-migration-02; migration-05 sections 18-22 (tests, decoupling, docs, pipeline/config) must precede deletion |
| module-migration | 04 | module-migration-04-remove-flat-shims | [#330](https://github.com/nold-ai/specfact-cli/issues/330) | module-migration-01; shim-removal scope only (no broad legacy test migration) |
| module-migration | 06 | module-migration-06-core-decoupling-cleanup (in progress) | [#338](https://github.com/nold-ai/specfact-cli/issues/338) | module-migration-03 ✅; migration-05 ✅ bundle-parity baseline |
| module-migration | 07 | module-migration-07-test-migration-cleanup | [#339](https://github.com/nold-ai/specfact-cli/issues/339) | migration-03 phase 20 handoff; migration-04 and migration-05 residual specfact-cli test debt |
| module-migration | 08 | module-migration-08-release-suite-stabilization | TBD | module-migration-03/04/06/07 merged; residual release-suite regressions after migration merge |
| module-migration | 09 | backlog-module-ownership-cleanup | TBD | module-migration-06; backlog-core-07; cli-val-07 findings |
| init-ide | 01 | init-ide-prompt-source-selection | TBD | backlog-module-ownership-cleanup |
| backlog-auth | 01 | backlog-auth-01-backlog-auth-commands | TBD | module-migration-03 (central auth interface in core; auth removed from core) |

### Cross-cutting foundations (no hard dependencies — implement early)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| policy-engine | 01 | ✅ policy-engine-01-unified-framework (implemented 2026-02-17; archived) | [#176](https://github.com/nold-ai/specfact-cli/issues/176) | — |
| patch-mode | 01 | ✅ patch-mode-01-preview-apply (implemented 2026-02-18; archived) | [#177](https://github.com/nold-ai/specfact-cli/issues/177) | — |
| validation | 01 | ✅ validation-01-deep-validation (implemented 2026-02-18; archived) | [#163](https://github.com/nold-ai/specfact-cli/issues/163) | — |
| bundle-mapper | 01 | ✅ bundle-mapper-01-mapping-strategy (implemented 2026-02-22; archived) | [#121](https://github.com/nold-ai/specfact-cli/issues/121) | — |
| verification | 01 | ✅ verification-01-wave1-delta-closure (implemented 2026-02-18; archived) | [#276](https://github.com/nold-ai/specfact-cli/issues/276) | ✅ #177, ✅ #163, ✅ #116, ✅ #121 |

### CI/CD (workflow and artifacts)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|----------------|----------|------------|
| — | — | ✅ ci-01 implemented 2026-02-16 (see Implemented above) | — | — |

### Packaging and distribution

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| packaging | 01 | packaging-01-wheel-package-inclusion | TBD | module-migration-06 ✅; release artifact regression discovered post-0.40.0 publish |

### Developer workflow (parallel branch operations)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| workflow | 01 | ✅ workflow-01-git-worktree-management (implemented 2026-02-18; archived) | [#267](https://github.com/nold-ai/specfact-cli/issues/267) | — |

### backlog-core (required by all backlog-* modules)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| backlog-core | 01 | ✅ backlog-core-01-dependency-analysis-commands (implemented 2026-02-18; archived) | [#116](https://github.com/nold-ai/specfact-cli/issues/116) | — |
| backlog-core | 02 | ✅ backlog-core-02-interactive-issue-creation (implemented 2026-02-22; archived) | [#173](https://github.com/nold-ai/specfact-cli/issues/173) | #116 (optional: #176, #177) |
| backlog-core | 04 | ✅ backlog-core-04-installed-runtime-discovery-and-add-prompt (implemented 2026-02-23; archived) | [#295](https://github.com/nold-ai/specfact-cli/issues/295) | #173 |
| backlog-core | 05 | ✅ backlog-core-05-user-modules-bootstrap (implemented 2026-03-03; archived) | [#298](https://github.com/nold-ai/specfact-cli/issues/298) | #173 |
| backlog-core | 06 | ✅ backlog-core-06-refine-custom-field-writeback (implemented 2026-03-03; archived) | [#310](https://github.com/nold-ai/specfact-cli/issues/310) | #173 |
| backlog-core | 07 | backlog-core-07-ado-required-custom-fields-and-picklists | [#337](https://github.com/nold-ai/specfact-cli/issues/337) | ✅ #310 |

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
| ceremony-cockpit | 01 | ✅ ceremony-cockpit-01-ceremony-aliases (implemented 2026-02-18; archived) | [#185](https://github.com/nold-ai/specfact-cli/issues/185) | — (optional: #220, #170, #171, #169, #183, #184) |

### Profile and configuration layering (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| profile | 01 | profile-01-config-layering | [#237](https://github.com/nold-ai/specfact-cli/issues/237) | #193 (existing init/module-state baseline) |
| profile | 02 | profile-02-central-config-sources | [#249](https://github.com/nold-ai/specfact-cli/issues/249) | #237 (profile-01) |
| profile | 03 | profile-03-domain-overlays | [#250](https://github.com/nold-ai/specfact-cli/issues/250) | #237 (profile-01), #249 (profile-02), #213 |

### Requirements layer (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| requirements | 01 | requirements-01-data-model | [#238](https://github.com/nold-ai/specfact-cli/issues/238) | #213 |
| requirements | 02 | requirements-02-module-commands | [#239](https://github.com/nold-ai/specfact-cli/issues/239) | #238 (requirements-01), #213 |
| requirements | 03 | requirements-03-backlog-sync | [#244](https://github.com/nold-ai/specfact-cli/issues/244) | #239 (requirements-02), #243 (sync-01) |

### Architecture and traceability chain (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| architecture | 01 | architecture-01-solution-layer | [#240](https://github.com/nold-ai/specfact-cli/issues/240) | #238 (requirements-01), #239 (requirements-02) |
| validation | 02 | validation-02-full-chain-engine | [#241](https://github.com/nold-ai/specfact-cli/issues/241) | #239 (requirements-02), #240 (architecture-01), #176 |
| traceability | 01 | traceability-01-index-and-orphans | [#242](https://github.com/nold-ai/specfact-cli/issues/242) | #239 (requirements-02), #240 (architecture-01) |

### Sync and ceremony integration (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| sync | 01 | sync-01-unified-kernel | [#243](https://github.com/nold-ai/specfact-cli/issues/243) | #177 |
| ceremony | 02 | ceremony-02-requirements-aware-output | [#245](https://github.com/nold-ai/specfact-cli/issues/245) | #239 (requirements-02), #185 |

### Governance extensions (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| policy | 02 | policy-02-packs-and-modes | [#246](https://github.com/nold-ai/specfact-cli/issues/246) | #237 (profile-01), #176 |
| governance | 01 | governance-01-evidence-output | [#247](https://github.com/nold-ai/specfact-cli/issues/247) | #241 (validation-02), #246 (policy-02) |
| governance | 02 | governance-02-exception-management | [#248](https://github.com/nold-ai/specfact-cli/issues/248) | #246 (policy-02) |

### AI integration (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| ai-integration | 01 | ai-integration-01-agent-skill | [#251](https://github.com/nold-ai/specfact-cli/issues/251) | #241 (validation-02) |
| ai-integration | 02 | ai-integration-02-mcp-server | [#252](https://github.com/nold-ai/specfact-cli/issues/252) | #241 (validation-02) |
| ai-integration | 03 | ai-integration-03-instruction-files | [#253](https://github.com/nold-ai/specfact-cli/issues/253) | #251 (ai-integration-01) |
| ai-integration | 04 | ai-integration-04-intent-skills | [#349](https://github.com/nold-ai/specfact-cli/issues/349) | #251 (ai-integration-01); #239 (requirements-02) |

### OpenSpec bridge integration (intent engineering plan, 2026-03-05)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| openspec | 01 | openspec-01-intent-trace | [#350](https://github.com/nold-ai/specfact-cli/issues/350) | #238 (requirements-01); #239 (requirements-02) |

### CLI end-user validation (validation gap plan, 2026-02-19)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| cli-val | 01 | cli-val-01-behavior-contract-standard | [#279](https://github.com/nold-ai/specfact-cli/issues/279) | — |
| cli-val | 02 | cli-val-02-output-snapshot-stability | [#280](https://github.com/nold-ai/specfact-cli/issues/280) | — |
| cli-val | 03 | cli-val-03-misuse-safety-proof | [#281](https://github.com/nold-ai/specfact-cli/issues/281) | #279 |
| cli-val | 04 | cli-val-04-acceptance-test-runner | [#282](https://github.com/nold-ai/specfact-cli/issues/282) | #279, #281 |
| cli-val | 05 | cli-val-05-ci-integration | [#283](https://github.com/nold-ai/specfact-cli/issues/283) | #280, #282 |
| cli-val | 06 | cli-val-06-copilot-test-generation | [#284](https://github.com/nold-ai/specfact-cli/issues/284) | #279 (soft: #283) |
| cli-val | 07 | cli-val-07-command-package-runtime-validation | TBD | marketplace-02 ✅; backlog-core-05 ✅; module-migration-08 ✅ |

### Integration governance and proof (architecture integration plan, 2026-02-15)

| Module | Order | Change folder | GitHub # | Blocked by |
|--------|-------|---------------|----------|------------|
| integration | 01 | integration-01-cross-change-contracts | [#254](https://github.com/nold-ai/specfact-cli/issues/254) | #237 (profile-01), #239 (requirements-02), #240 (architecture-01), #241 (validation-02), #246 (policy-02) |
| dogfooding | 01 | dogfooding-01-full-chain-e2e-proof | [#255](https://github.com/nold-ai/specfact-cli/issues/255) | #239 (requirements-02), #240 (architecture-01), #241 (validation-02), #242 (traceability-01), #247 (governance-01) |

---

## GitHub "Blocked by" relationships

Set these in GitHub so issue dependencies are explicit. Optional dependencies are graceful no-ops (modules degrade when not installed) and do **not** need to be set as hard blockers.

| Issue | Change | Hard blocked by |
|-------|--------|-----------------|
| [#208](https://github.com/nold-ai/specfact-cli/issues/208) | arch-06 manifest security | ✅ arch-05 (already implemented) |
| [#213](https://github.com/nold-ai/specfact-cli/issues/213) | arch-07 schema extensions | ✅ arch-04 (already implemented) |
| [#214](https://github.com/nold-ai/specfact-cli/issues/214) | marketplace-01 registry | #208 |
| [#215](https://github.com/nold-ai/specfact-cli/issues/215) | marketplace-02 advanced features | #214 |
| [#327](https://github.com/nold-ai/specfact-cli/issues/327) | marketplace-03 publisher identity | #215 |
| [#328](https://github.com/nold-ai/specfact-cli/issues/328) | marketplace-04 revocation | marketplace-03 (#327) |
| [#329](https://github.com/nold-ai/specfact-cli/issues/329) | marketplace-05 registry federation | marketplace-03 (#327) |
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
| [#349](https://github.com/nold-ai/specfact-cli/issues/349) | ai-integration-04 intent skills | #251, #239 |
| [#350](https://github.com/nold-ai/specfact-cli/issues/350) | openspec-01 intent trace | #238, #239 |
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
| Architecture Layer Integration (Requirements to AI) | [Epic] Architecture Layer Integration | [#256](https://github.com/nold-ai/specfact-cli/issues/256) |
| AI IDE Integration | [Epic] AI IDE Integration | [#257](https://github.com/nold-ai/specfact-cli/issues/257) |
| Integration Governance and Dogfooding | [Epic] Integration Governance and Dogfooding | [#258](https://github.com/nold-ai/specfact-cli/issues/258) |
| CLI end-user validation | [Epic] CLI End-User Validation | [#285](https://github.com/nold-ai/specfact-cli/issues/285) |

---

## Implementation waves

Dependencies flow left-to-right; a wave may start once all its hard blockers are resolved.

- **Wave 0** ✅ **Complete** — ✅ arch-01 through ✅ arch-05 (modular CLI foundation, bridge registry)

- **Wave 1** ✅ **Complete** — Platform extensions + cross-cutting foundations (✅ arch-06, ✅ arch-07, ✅ arch-08, ✅ ci-01):
  - ✅ arch-06, ✅ arch-07, ✅ arch-08, ✅ ci-01
  - ✅ policy-engine-01, ✅ patch-mode-01
  - ✅ backlog-core-01
  - ✅ validation-01, ✅ sidecar-01, ✅ bundle-mapper-01

- **Wave 1.5 — CLI end-user validation** (cross-cutting, parallel to Wave 2+):
  - cli-val-01 (#279), cli-val-02 (#280) (no blockers — start immediately after Wave 1)
  - cli-val-03 (#281), cli-val-06 (#284) (after cli-val-01 #279)
  - cli-val-04 (#282) (after cli-val-01 #279 + cli-val-03 #281)
  - cli-val-05 (#283) (after cli-val-02 #280 + cli-val-04 #282 — capstone)

- **Wave 2 — Marketplace + backlog module layer** (needs Wave 1):
  - ✅ marketplace-01 (#214) (needs arch-06 #208)
  - ✅ backlog-core-02 (#173) (needs backlog-core-01 #116)
  - ✅ backlog-core-03
  - ✅ backlog-core-04, ✅ backlog-core-05, ✅ backlog-core-06
  - backlog-core-07 (#337) (needs backlog-core-06 #310)
  - backlog-scrum-02 (#170), backlog-scrum-03 (#171), backlog-scrum-04 (#169) (need backlog-core-01 #116)
  - backlog-kanban-01 (#183), backlog-safe-01 (#184) (need backlog-core-01 #116)

- **Wave 3 — Higher-order backlog + marketplace + module migration** (needs Wave 2):
  - ✅ marketplace-02 (#215) (needs marketplace-01 #214)
  - ✅ backlog-scrum-01 (needs backlog-core-01 #116; benefits from policy-engine-01 #176 + patch-mode-01 #177)
  - backlog-safe-02 (#182) (needs backlog-safe-01 #184; integrates with scrum/kanban via bridge registry)
  - ✅ module-migration-01-categorize-and-group (#315) (marketplace-02 #215 dependency resolved; adds category metadata + group commands)
  - module-migration-04-remove-flat-shims (#330) (0.40.x; needs module-migration-01 #315; removes flat shims, category-only CLI; see overlap note with migration-03 in tasks.md 17.9.1)
  - ✅ module-migration-02-bundle-extraction (#316) (needs module-migration-01 #315; moves module source to bundle packages, publishes to marketplace registry)
  - marketplace-03-publisher-identity (#327) (needs marketplace-02 #215; can run parallel with module-migration-01/02/03)
  - marketplace-04-revocation (#328) (needs marketplace-03 #327; must land before external publisher onboarding)
  - marketplace-05-registry-federation (#329) (needs marketplace-03 #327)

- **Wave 4 — Ceremony layer + module slimming + modules repo quality** (needs Wave 3):
  - ceremony-cockpit-01 ✅ (probes installed backlog-* modules at runtime; no hard deps but best after Wave 3)
  - **module-migration-05-modules-repo-quality** (needs module-migration-02; sections 18-22 must land **before or simultaneously with** module-migration-03): quality tooling, tests, dependency decoupling, docs, pipeline/config for specfact-cli-modules
  - module-migration-03-core-slimming (needs module-migration-02 AND migration-05 sections 18-22; removes bundled modules from core; see tasks.md 17.9 for proposal consistency requirements before implementation starts)
  - **module-migration-06-core-decoupling-cleanup** (needs module-migration-03 + migration-05 baseline; removes residual non-core components/couplings from specfact-cli core, e.g. models/utilities tied only to extracted modules)
  - docs-01-core-modules-docs-alignment (after the module-migration baseline above; full live-docs alignment for lean core + marketplace bundles)

- **Wave 5 — Foundations for business-first chain** (architecture integration):
  - profile-01 (#237)
  - requirements-01 (#238)
  - requirements-02 (#239) (after requirements-01 #238 + arch-07 #213)

- **Wave 6 — End-to-end chain and sync kernel**:
  - architecture-01 (#240) (after requirements-01 #238 + requirements-02 #239)
  - validation-02 (#241) (after architecture-01 #240 + requirements-02 #239 + policy-engine-01 #176)
  - traceability-01 (#242) (after architecture-01 #240 + requirements-02 #239)
  - sync-01 (#243) (after patch-mode-01 #177)
  - requirements-03 (#244) (after requirements-02 #239 + sync-01 #243)

- **Wave 7 — Governance and ceremony business context**:
  - policy-02 (#246) (after profile-01 #237 + policy-engine-01 #176)
  - governance-01 (#247) (after validation-02 #241 + policy-02 #246)
  - governance-02 (#248) (after policy-02 #246)
  - ceremony-02 (#245) (after requirements-02 #239 + ceremony-cockpit-01 #185)

- **Wave 8 — Enterprise profile maturity and AI interfaces**:
  - profile-02 (#249) (after profile-01 #237)
  - profile-03 (#250) (after profile-01 #237 + profile-02 #249 + arch-07 #213)
  - ai-integration-01 (#251) (after validation-02 #241)
  - ai-integration-02 (#252) (after validation-02 #241)
  - ai-integration-03 (#253) (after ai-integration-01 #251)

- **Wave 8 additions — Intent engineering layer (intent engineering plan, 2026-03-05)**:
  - ai-integration-04 (#349) (after ai-integration-01 #251 + requirements-02 #239)
  - openspec-01 (#350) (after requirements-01 #238 + requirements-02 #239; aligns with Wave 5/6)

- **Wave 9 — Integration contract and product proof**:
  - integration-01 (#254) (after profile-01 #237 + requirements-02 #239 + architecture-01 #240 + validation-02 #241 + policy-02 #246)
  - dogfooding-01 (#255) (after requirements-02 #239 + architecture-01 #240 + validation-02 #241 + traceability-01 #242 + governance-01 #247)

---

## Mandatory Wave Exit Gates

A wave cannot be considered complete until all gate criteria listed for that wave are met and auditable.

- Wave 0 gate: Core modular CLI and bridge registry flows remain stable and archived changes are validated.
- Wave 1 gate: arch-06/07, policy-engine-01, patch-mode-01, backlog-core-01, validation-01 produce passing contract and strict OpenSpec validation. ✅ Completed 2026-02-18.
- Wave 1.5 gate: CLI behavior contract schema validated, snapshot tests pass for all command groups, black-box acceptance tests prove installed binary works, anti-pattern safety assertions pass for all Wave 1 commands, CI gates enforce all of the above.
- Wave 2 gate: At least one backlog planning workflow completes with no blocking dependency regressions across backlog-core + marketplace-01.
- Wave 3 gate: Higher-order backlog workflows and marketplace-02 interoperate without command-group regressions.
- Wave 4 gate: `ceremony-cockpit-01` aliases resolve and execute against installed modules without fallback failures.
- Wave 5 gate: `profile-01`, `requirements-01`, `requirements-02` demonstrate profile-aware requirement lifecycle with strict validation and TDD evidence.
- Wave 6 gate: One chain run proves requirements -> architecture -> validation/traceability/sync compatibility with no unresolved ownership conflicts.
- Wave 7 gate: policy/governance/ceremony integration emits consistent evidence and exception semantics aligned to ownership authority.
- Wave 8 gate: profile maturity + AI interfaces (`ai-integration-01/02/03`) operate on top of validation-02 outputs with no schema divergence.
- Wave 9 gate: integration umbrella contract is adopted by all dependent changes and dogfooding E2E proof artifacts confirm end-to-end positioning claims.
