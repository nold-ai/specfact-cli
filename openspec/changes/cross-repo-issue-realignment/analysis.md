# Cross-Repo Classification Matrix

## Sources Used

- [core-lean-package](/home/dom/git/nold-ai/specfact-cli/openspec/specs/core-lean-package/spec.md)
- [bundle-extraction](/home/dom/git/nold-ai/specfact-cli/openspec/specs/bundle-extraction/spec.md)
- [backlog-module-ownership](/home/dom/git/nold-ai/specfact-cli/openspec/specs/backlog-module-ownership/spec.md)
- [project-codebase-ownership](/home/dom/git/nold-ai/specfact-cli/openspec/specs/project-codebase-ownership/spec.md)
- [code-review-module](/home/dom/git/nold-ai/specfact-cli/openspec/specs/code-review-module/spec.md)
- [module-categories](/home/dom/git/nold-ai/specfact-cli/docs/reference/module-categories.md)
- active proposals under [openspec/changes](/home/dom/git/nold-ai/specfact-cli/openspec/changes/)
- planning inventory in [CHANGE_ORDER.md](/home/dom/git/nold-ai/specfact-cli/openspec/CHANGE_ORDER.md)

## Classification Rules

- `core`: the authoritative owned surface remains in `specfact-cli` core, usually registry, marketplace, shared models, profile/init behavior, AI integration glue, or release/governance orchestration.
- `modules`: the change's primary implementation is a user-facing workflow or bundle command surface that maps cleanly to a canonical bundle in `specfact-cli-modules`.
- `split/rescope`: the proposal currently mixes core-owned contracts or schemas with bundle-owned runtime behavior, or its command topology no longer maps cleanly to a single canonical bundle.

## Evidence Snapshots

- `backlog-scrum-02`, `backlog-scrum-03`, `backlog-scrum-04`, `backlog-kanban-01`, `backlog-safe-01`, and `backlog-safe-02` still describe implementation under `modules/backlog-*` in this repo, while [backlog-module-ownership](/home/dom/git/nold-ai/specfact-cli/openspec/specs/backlog-module-ownership/spec.md) makes `nold-ai/specfact-backlog` the sole owner of backlog and policy command surfaces.
- `profile-01` still describes `modules/profile/`, but [core-lean-package](/home/dom/git/nold-ai/specfact-cli/openspec/specs/core-lean-package/spec.md) limits the core wheel to `init`, `module_registry`, and `upgrade`; the profile behavior must therefore be expressed as core init/config behavior, not as a separate extracted module.
- `sync-01` still describes `modules/sync-kernel/` and `specfact sync ...`, but [module-categories](/home/dom/git/nold-ai/specfact-cli/docs/reference/module-categories.md) assigns sync ownership to the `project` category and `specfact-project` bundle.
- `validation-02` still extends `modules/validate/`, but [module-categories](/home/dom/git/nold-ai/specfact-cli/docs/reference/module-categories.md) assigns validation to the `code` category and `specfact-codebase` bundle; the evidence and governance contracts it references are not purely bundle-local.
- `requirements-02`, `architecture-01`, and `traceability-01` still define old flat command families (`specfact requirements ...`, `specfact architecture ...`, `specfact trace ...`) that do not exist in the canonical grouped command model.

## Matrix

### Stay In `specfact-cli`

| Change | GitHub | Classification | Why it stays | Required rewrite before implementation |
|---|---|---:|---|---|
| `marketplace-03-publisher-identity` | `#327` | `core` | Registry publisher identity, signing, and trust remain core marketplace responsibilities. | Keep proposal focused on core registry and publisher trust surfaces. |
| `marketplace-04-revocation` | `#328` | `core` | Revocation is part of core marketplace trust and registry lifecycle. | No repo move; keep scoped to core registry behavior. |
| `marketplace-05-registry-federation` | `#329` | `core` | Federation is a marketplace/registry concern, not a bundle-owned workflow command. | No repo move; keep core registry scope explicit. |
| `profile-01-config-layering` | `#237` | `core` | Profile selection belongs to `specfact init` and core config resolution, not to a bundle. | Replace `modules/profile/` and `specfact profile ...` assumptions with core init/config behavior. |
| `profile-02-central-config-sources` | `#249` | `core` | Central baseline resolution is core config ownership. | Reframe around core config loading and profile overlays; remove implied profile bundle ownership. |
| `profile-03-domain-overlays` | `#250` | `core` | Domain overlays extend profile/config layering and shared requirement fields. | Rewrite command references so overlay behavior is expressed through core/profile-aware workflows. |
| `requirements-01-data-model` | `#238` | `core` | Shared requirements models and schema extensions are cross-bundle contracts. | Keep focused on models, schema, and extension ownership; avoid bundle command scope. |
| `integration-01-cross-change-contracts` | `#254` | `core` | Cross-change ownership and interface contracts are core governance. | Keep as authoritative contract change; add explicit references to downstream bundle owners where needed. |
| `ai-integration-01-agent-skill` | `#251` | `core` | Agent skill packaging and integration guidance are core AI surface work. | Update stale command examples to canonical grouped commands and cross-repo owners. |
| `ai-integration-02-mcp-server` | `#252` | `core` | MCP server integration is core runtime/integration infrastructure. | Clarify which bundle commands are proxied versus which schemas remain core-owned. |
| `ai-integration-03-instruction-files` | `#253` | `core` | Instruction files and repo-local agent guidance stay in the core repo. | Rewrite command examples and ownership assumptions for grouped bundle commands. |
| `ai-integration-04-intent-skills` | `#349` | `core` | Skill assets still belong with AI integration guidance in core. | Replace references to unsettled `requirements` and `architecture` command families with whichever paired follow-ups are approved. |
| `cli-val-01-behavior-contract-standard` | `#279` | `core` | CLI behavioral contract standards are release-gate and product-governance work. | Rewrite acceptance scope to cover grouped bundle commands rather than pre-split flat commands. |
| `cli-val-02-output-snapshot-stability` | `#280` | `core` | Snapshot policy is a release-quality gate across the product. | Update target commands/help output expectations to grouped command topology. |
| `cli-val-03-misuse-safety-proof` | `#281` | `core` | Misuse-safety proof is product-governance evidence, not bundle-local feature code. | Reframe command coverage to installed-bundle behavior and lean-core defaults. |
| `cli-val-04-acceptance-test-runner` | `#282` | `core` | Acceptance harness and runner policy stay in core CI/release orchestration. | Target canonical bundle install plus grouped command flows. |
| `cli-val-05-ci-integration` | `#283` | `core` | CI integration for acceptance evidence remains core release infrastructure. | Align with cross-repo test ownership and installed-bundle execution model. |
| `cli-val-06-copilot-test-generation` | `#284` | `core` | Test-generation workflow and governance belong to core AI/release tooling. | Update command targets and fixture assumptions to post-split architecture. |
| `dogfooding-01-full-chain-e2e-proof` | `#255` | `core` | End-to-end proof is a cross-repo evidence and release-governance activity. | Clarify that the proof orchestrates bundle-installed workflows rather than implementing them in core. |

### Move To `specfact-cli-modules`

| Change | GitHub | Classification | Target bundle | Why it moves | Required rewrite in replacement proposal |
|---|---|---:|---|---|---|
| `backlog-scrum-02-sprint-planning` | `#170` | `modules` | `specfact-backlog` | Proposal still implements `modules/backlog-scrum/...`; canonical backlog command ownership is bundle-side. | Rewrite paths and package names to modules-repo bundle layout; keep `backlog` grouped surface. |
| `backlog-scrum-03-story-complexity` | `#171` | `modules` | `specfact-backlog` | Complexity and story splitting are backlog refinement behavior in the backlog bundle. | Rewrite to modules-repo bundle layout and extension hooks. |
| `backlog-scrum-04-definition-of-done` | `#169` | `modules` | `specfact-backlog` | DoD validation is backlog/policy workflow behavior, not core. | Rewrite to modules-repo backlog bundle ownership. |
| `backlog-kanban-01-flow-metrics` | `#183` | `modules` | `specfact-backlog` | Kanban flow metrics proposal still targets `modules/backlog-kanban/...`; canonical owner is backlog bundle. | Rewrite to modules-repo bundle paths and grouped backlog command surface. |
| `backlog-safe-01-pi-planning` | `#184` | `modules` | `specfact-backlog` | PI planning and WSJF are SAFe backlog behavior owned by the backlog bundle. | Rewrite to modules-repo backlog bundle ownership. |
| `backlog-safe-02-risk-rollups` | `#182` | `modules` | `specfact-backlog` | Risk rollups are described as a shared capability inside `backlog-safe`; still bundle-owned backlog behavior. | Rewrite to modules-repo backlog bundle paths and hooks. |
| `ceremony-02-requirements-aware-output` | `#245` | `modules` | `specfact-backlog` | Extends backlog ceremony commands, which are bundle-owned backlog surfaces. | Rewrite to backlog bundle ownership and grouped backlog ceremony flows. |
| `policy-02-packs-and-modes` | `#246` | `modules` | `specfact-backlog` | Policy command surface is owned by the backlog bundle per [backlog-module-ownership](/home/dom/git/nold-ai/specfact-cli/openspec/specs/backlog-module-ownership/spec.md). | Rewrite package paths and command examples to canonical backlog/policy bundle ownership. |
| `sync-01-unified-kernel` | `#243` | `modules` | `specfact-project` | Sync is owned by the `project` category and `specfact-project` bundle. | Rewrite from old `specfact sync ...` and `modules/sync-kernel/` to canonical project-bundle command ownership. |

### Split / Rescope Before Reassignment

| Change | GitHub | Classification | Why it cannot move or stay as-is | Required follow-up split |
|---|---|---:|---|---|
| `requirements-02-module-commands` | `#239` | `split/rescope` | Defines a non-canonical `specfact requirements ...` command family and couples shared requirements semantics with user-facing command implementation. | Keep core-owned schema/contract deltas with `requirements-01`; create a bundle-owned replacement for the actual command surface after target bundle ownership is decided. |
| `requirements-03-backlog-sync` | `#244` | `split/rescope` | Mixes requirements lifecycle, backlog synchronization, and spec-kit bridge behavior under a non-canonical command family. | Split into core adapter/contracts plus one or more bundle-owned follow-ups for project/backlog runtime workflows. |
| `architecture-01-solution-layer` | `#240` | `split/rescope` | Defines `specfact architecture ...` as a flat command family that does not exist in the canonical grouped topology. | Keep core-owned architecture schema/extension contracts only if needed; create a bundle-owned replacement once the canonical command home is chosen. |
| `traceability-01-index-and-orphans` | `#242` | `split/rescope` | Defines `specfact trace ...`, another non-canonical flat command family, while also introducing shared index contracts. | Split core index/schema contracts from bundle-owned query/reporting command implementation. |
| `validation-02-full-chain-engine` | `#241` | `split/rescope` | Bundle-owned validation runtime (`code`/`specfact-codebase`) is mixed with cross-change evidence contracts and governance dependencies. | Keep only shared report/evidence contracts in core where necessary; move the runtime engine to a modules-repo codebase change. |
| `governance-01-evidence-output` | `#247` | `split/rescope` | Owns the evidence envelope contract, but proposal also extends bundle-owned validation runtime flags and output behavior. | Keep evidence schema and CI contract in core; create bundle follow-up(s) for validation/govern emitters. |
| `governance-02-exception-management` | `#248` | `split/rescope` | Mixes core exception semantics with user-facing exception commands and bundle-owned policy enforcement behavior. | Keep exception schema/suppression semantics in core; move command and runtime enforcement flows into bundle-owned follow-up changes. |
| `openspec-01-intent-trace` | `#350` | `split/rescope` | OpenSpec proposal metadata is core-owned, but the proposal also extends bundle-owned sync/import behavior. | Keep proposal schema and import contract metadata in core; create a project-bundle follow-up for runtime import behavior. |

## Summary Counts

- `core`: 18 active changes
- `modules`: 9 active changes
- `split/rescope`: 8 active changes

## Immediate Consequences

- The nine `modules` issues are the first candidates for transfer or close-and-recreate in `specfact-cli-modules`.
- The eight `split/rescope` issues must not be moved unchanged; each one needs a paired ownership decision before any transfer.
- Several `core` issues still require proposal rewrites because they mention obsolete module paths or flat command families, even though the issues themselves stay in `specfact-cli`.

## Reassignment Strategy

### Preferred path

- Use native GitHub transfer for the nine `modules` issues because `gh issue transfer` is available for `specfact-cli` -> `specfact-cli-modules`.
- Create the target Epic and Feature parents in `specfact-cli-modules` before transferring child stories.
- After transfer, normalize labels to the target repo taxonomy and attach the transferred story under its new Feature.

### Fallback path

- Use `close-and-recreate` only when transfer fails technically, cannot preserve the needed planning state, or the issue is `split/rescope` and must be replaced with a narrower modules-owned follow-up.
- When fallback is used:
  - close the `specfact-cli` issue with a comment linking the replacement issue
  - create the modules-repo replacement with updated scope and a backlink to the original issue
  - update both `CHANGE_ORDER.md` files with old/new issue references

### Active proposals that must be rewritten for stale monolithic ownership

- `profile-01-config-layering`
- `requirements-02-module-commands`
- `architecture-01-solution-layer`
- `traceability-01-index-and-orphans`
- `sync-01-unified-kernel`
- `validation-02-full-chain-engine`
- `backlog-scrum-02-sprint-planning`
- `backlog-scrum-03-story-complexity`
- `backlog-scrum-04-definition-of-done`
- `backlog-kanban-01-flow-metrics`
- `backlog-safe-01-pi-planning`
- `backlog-safe-02-risk-rollups`

### `split/rescope` changes that require paired ownership follow-up

- `requirements-02-module-commands`
- `requirements-03-backlog-sync`
- `architecture-01-solution-layer`
- `traceability-01-index-and-orphans`
- `validation-02-full-chain-engine`
- `governance-01-evidence-output`
- `governance-02-exception-management`
- `openspec-01-intent-trace`

## Modules-Repo Target Hierarchy

### Target Epics

| Target repo | Epic title | Reason |
|---|---|---|
| `specfact-cli-modules` | `[Epic] specfact backlog` | Canonical parent for all backlog bundle workflow stories moved out of core. |
| `specfact-cli-modules` | `[Epic] specfact project` | Canonical parent for project-bundle sync and project orchestration stories moved out of core. |

### Target Features

| Target epic | Feature title | Source alignment |
|---|---|---|
| `[Epic] specfact backlog` | `[Feature] Scrum Workflows` | Mirrors core feature `#359` and groups sprint planning, complexity, and DoD. |
| `[Epic] specfact backlog` | `[Feature] Kanban Flow Metrics` | Mirrors core feature `#360`. |
| `[Epic] specfact backlog` | `[Feature] SAFe & PI Planning` | Mirrors core feature `#361` and groups PI planning plus risk rollups. |
| `[Epic] specfact backlog` | `[Feature] Policy Engine & Enforcement Modes` | Mirrors core feature `#362` for bundle-owned policy command work. |
| `[Epic] specfact backlog` | `[Feature] Ceremony Command Layer` | Mirrors core feature `#363` for bundle-owned ceremony extensions. |
| `[Epic] specfact project` | `[Feature] Sync Engine` | Mirrors core feature `#369` for project-bundle sync ownership. |

### Story Mapping

| Current issue | Change | Target epic | Target feature | Transfer decision |
|---|---|---|---|---|
| `#169` | `backlog-scrum-04-definition-of-done` | `[Epic] specfact backlog` | `[Feature] Scrum Workflows` | `transfer` |
| `#170` | `backlog-scrum-02-sprint-planning` | `[Epic] specfact backlog` | `[Feature] Scrum Workflows` | `transfer` |
| `#171` | `backlog-scrum-03-story-complexity` | `[Epic] specfact backlog` | `[Feature] Scrum Workflows` | `transfer` |
| `#183` | `backlog-kanban-01-flow-metrics` | `[Epic] specfact backlog` | `[Feature] Kanban Flow Metrics` | `transfer` |
| `#184` | `backlog-safe-01-pi-planning` | `[Epic] specfact backlog` | `[Feature] SAFe & PI Planning` | `transfer` |
| `#182` | `backlog-safe-02-risk-rollups` | `[Epic] specfact backlog` | `[Feature] SAFe & PI Planning` | `transfer` |
| `#246` | `policy-02-packs-and-modes` | `[Epic] specfact backlog` | `[Feature] Policy Engine & Enforcement Modes` | `transfer` |
| `#245` | `ceremony-02-requirements-aware-output` | `[Epic] specfact backlog` | `[Feature] Ceremony Command Layer` | `transfer` |
| `#243` | `sync-01-unified-kernel` | `[Epic] specfact project` | `[Feature] Sync Engine` | `transfer` |

### Order of Operations

1. Create `Epic` and `Feature` labels in `specfact-cli-modules`.
2. Create target epics.
3. Create target features and attach them to the correct epic.
4. Transfer the nine module-owned stories.
5. Normalize story labels in `specfact-cli-modules` and attach each story to its target feature.

## Final Verification Snapshot

- `openspec validate cross-repo-issue-realignment --strict` passed on `2026-04-08`.
- All nine `modules`-classified stories now have exactly one authoritative issue in `nold-ai/specfact-cli-modules`:
  - `#169 -> modules#152`
  - `#170 -> modules#160`
  - `#171 -> modules#153`
  - `#182 -> modules#156`
  - `#183 -> modules#155`
  - `#184 -> modules#154`
  - `#243 -> modules#157`
  - `#245 -> modules#159`
  - `#246 -> modules#158`
- The transferred story numbers no longer appear in the active `specfact-cli` issue inventory.
- Modules-repo hierarchy is aligned:
  - `modules#145` -> `modules#151`, `modules#149`, `modules#146`, `modules#148`, `modules#150`
  - `modules#144` -> `modules#147`, `modules#161`
  - `modules#162` -> `modules#163`
- OpenSpec artifact ownership is aligned with issue ownership:
  - moved runtime changes now live only in `specfact-cli-modules`
  - split changes now exist in both repos as paired core-contract and modules-runtime companions
- Core and modules planning inventories were updated in their respective `openspec/CHANGE_ORDER.md` files.
- Core architecture docs were updated so they no longer imply that old flat `architecture`, `requirements`, or `trace` command families remain canonical implementation targets.
