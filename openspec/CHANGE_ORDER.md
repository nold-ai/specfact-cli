# OpenSpec Change Order

This document is the **single source of truth for active work** in this repository.
It lists what is in flight, what is paused, and the order in which active changes
should be implemented.

## Status snapshot

| Bucket | Count | Location |
|---|---|---|
| **Active** | 24 | [`openspec/changes/`](changes/) |
| **Parked** | 21 | [`openspec/parking-lot/`](parking-lot/) |
| **Archived** | 104 | [`openspec/changes/archive/`](changes/archive/) |

`openspec list` reflects the active set only. Parking-lot proposals are paused
pending external signal (paying enterprise customer, third-party publisher,
evidence corpus, etc.) — see [`parking-lot/README.md`](parking-lot/README.md)
for the un-park trigger of each parked change.

## Naming convention

- **Folder**: `<module>-<NN>-<suffix>` (e.g. `requirements-01-data-model`).
- **Order**: lower numbers within a module are implemented first. Cross-module
  dependencies are listed in the **Blocked by** column of each track table.

## Active tracks

The 24 active changes group into five independent tracks. Tracks can run in
parallel; within a track, follow the order column.

### Track A — Full-chain traceability (core thesis)

The end-to-end "Req → Arch → Spec → Code → Tests" chain. This is the headline
SpecFact value proposition; all other tracks support or extend it.

| Order | Change | Issue | Blocked by |
|---|---|---|---|
| 1 | `requirements-01-data-model` | [#238](https://github.com/nold-ai/specfact-cli/issues/238) | arch-07 ✅ |
| 2 | `requirements-02-module-commands` | [#239](https://github.com/nold-ai/specfact-cli/issues/239) | requirements-01 |
| 3 | `architecture-01-solution-layer` | [#240](https://github.com/nold-ai/specfact-cli/issues/240) | requirements-01, requirements-02 |
| 4 | `requirements-03-backlog-sync` | [#244](https://github.com/nold-ai/specfact-cli/issues/244) | requirements-02; modules `sync-01` |
| 5 | `traceability-01-index-and-orphans` | [#242](https://github.com/nold-ai/specfact-cli/issues/242) | requirements-02, architecture-01 |
| 6 | `validation-02-full-chain-engine` | [#241](https://github.com/nold-ai/specfact-cli/issues/241) | requirements-02, architecture-01, policy-engine-01 ✅ |
| 7 | `governance-01-evidence-output` | [#247](https://github.com/nold-ai/specfact-cli/issues/247) | validation-02; modules `policy-02` |
| 8 | `dogfooding-01-full-chain-e2e-proof` | [#255](https://github.com/nold-ai/specfact-cli/issues/255) | requirements-02, architecture-01, validation-02, traceability-01, governance-01 |

**Critical path**: requirements-01 → requirements-02 → architecture-01 →
traceability-01 + validation-02 → governance-01.

### Track B — AI IDE distribution

Skills-first integration so AI IDEs invoke SpecFact validation in-loop.

| Order | Change | Issue | Blocked by |
|---|---|---|---|
| 1 | `ai-integration-01-agent-skill` | [#251](https://github.com/nold-ai/specfact-cli/issues/251) | validation-02 |
| 2 | `ai-integration-03-instruction-files` | [#253](https://github.com/nold-ai/specfact-cli/issues/253) | ai-integration-01 |
| 3 | `ai-integration-02-mcp-server` *(scope: trim to 2-3 tools before implementation — see Modify queue)* | [#252](https://github.com/nold-ai/specfact-cli/issues/252) | ai-integration-01 |
| 4 | `ai-integration-04-intent-skills` *(scope: collapse to single intent-capture skill — see Modify queue)* | [#349](https://github.com/nold-ai/specfact-cli/issues/349) | ai-integration-01, requirements-02 |
| — | `openspec-01-intent-trace` *(scope: convert to optional adapter convention — see Modify queue)* | [#350](https://github.com/nold-ai/specfact-cli/issues/350) | requirements-01, requirements-02 |

### Track C — Profile and configuration

Adoption gradient from solo developer to enterprise.

| Order | Change | Issue | Blocked by |
|---|---|---|---|
| 1 | `profile-01-config-layering` | [#237](https://github.com/nold-ai/specfact-cli/issues/237) | — |
| — | `profile-04-safe-project-artifact-writes` *(in flight: 16/22 done)* | [#490](https://github.com/nold-ai/specfact-cli/issues/490) | — |

`profile-02` and `profile-03` are parked pending profile-01 shipping with
demonstrated drift complaints — see parking-lot README.

### Track D — CLI reliability

User-facing CLI behavior assertions and acceptance-test surface.

| Order | Change | Issue | Blocked by |
|---|---|---|---|
| 1 | `cli-val-03-misuse-safety-proof` | [#281](https://github.com/nold-ai/specfact-cli/issues/281) | — |
| 2 | `cli-val-04-acceptance-test-runner` | [#282](https://github.com/nold-ai/specfact-cli/issues/282) | cli-val-03 |

The remaining cli-val items (01, 02, 05, 06) are parked — see parking-lot
README. Snapshot/CI work folds into 03 and 04 if and when needed.

### Track E — Other active work

| Change | Status | Notes |
|---|---|---|
| `dep-security-cleanup` | 62/69 done | Apache-2.0 license-cleanliness pass |
| `marketplace-07-module-install-state-consistency` | ✓ archive pending | Resolves install-state disagreement across scopes |
| `upgrade-01-install-method-aware` | ✓ archive pending | Bug-fix for uvx/uv users |
| `governance-02-exception-management` | active | Time-bound policy exceptions |
| `architecture-02-well-architected-review` | **gated on architecture-01 shipping + 1 cycle of usage** | Boundary/ADR review pillar |
| `telemetry-01-opentelemetry-default-on` | **modify queue** | Flip to opt-in; revisit default-on later |
| `integration-01-cross-change-contracts` | **convert to living `INTEGRATION.md`** | Stops being a tasked change |

## Modify queue (do this before implementing)

Five active changes need scope adjustments before any implementation work
begins. One PR per change, focused.

| Change | Required adjustment |
|---|---|
| `openspec-01-intent-trace` | Rewrite proposal to describe an *optional adapter convention* SpecFact reads if present, not a mandatory upstream OpenSpec schema change. |
| `ai-integration-04-intent-skills` | Collapse to a single intent-capture skill; drop "SQUER" branding and the 7-question interview machinery. |
| `ai-integration-02-mcp-server` | Trim to 2–3 tools; explicitly gate on ai-integration-01 shipping and showing user pull. |
| `telemetry-01-opentelemetry-default-on` | Default to opt-in, not opt-out. Document criteria under which it would flip to default-on later. |
| `integration-01-cross-change-contracts` | Replace tasked change with a living `INTEGRATION.md` that other changes reference; archive the change once doc exists. |
| `architecture-02-well-architected-review` | Add explicit "BLOCKED ON: architecture-01 shipped + 1 usage cycle" at top of proposal. |

## Implementation waves

Waves are dependency-ordered. A wave can start once all its hard blockers are
green; tracks within a wave can run in parallel.

### Wave 1 — Adjust active scope (immediate)

Run the **Modify queue** above. No implementation, just proposal rewrites and
the integration-01 → INTEGRATION.md conversion.

### Wave 2 — Foundations (parallel)

- Track A items 1–3: `requirements-01` → `requirements-02` → `architecture-01`
- Track C item 1: `profile-01-config-layering`
- Track D item 1: `cli-val-03-misuse-safety-proof`
- Track E in-flight items: finish `dep-security-cleanup`, `profile-04`,
  archive `marketplace-07` and `upgrade-01`

### Wave 3 — Chain assembly

- Track A items 4–6: `requirements-03`, `traceability-01`, `validation-02`
- Track D item 2: `cli-val-04-acceptance-test-runner`

### Wave 4 — Evidence and AI surface

- Track A item 7: `governance-01-evidence-output`
- Track B items 1–2: `ai-integration-01-agent-skill`, `ai-integration-03-instruction-files`

### Wave 5 — Proof, intent, extensions

- Track A item 8: `dogfooding-01-full-chain-e2e-proof`
- Track B items 3–4: `ai-integration-02-mcp-server` (trimmed), `ai-integration-04-intent-skills` (trimmed)
- `openspec-01-intent-trace` (trimmed)
- `governance-02-exception-management`
- `architecture-02-well-architected-review` (only after architecture-01 has been used for one full development cycle)

## Wave exit gates

A wave is complete only when all listed criteria are auditable:

- **Wave 1**: Each item in the Modify queue has either (a) a rewritten proposal
  validated by `openspec validate`, or (b) for integration-01, an
  `INTEGRATION.md` doc replacing the tasked change.
- **Wave 2**: Three foundations (`requirements-01/02`, `architecture-01`) pass
  contract tests + strict OpenSpec validation. `profile-01` and `cli-val-03`
  archived.
- **Wave 3**: One chain run proves `requirements → architecture →
  validation/traceability` flows end-to-end with no ownership conflicts.
- **Wave 4**: `governance-01` evidence JSON consumed by at least one CI run.
  `ai-integration-01` skill installed in one IDE end-to-end.
- **Wave 5**: `dogfooding-01` artifacts demonstrate the full chain on real
  SpecFact backlog data. `openspec-01` and `ai-integration-04` adopted by at
  least one upstream OpenSpec project / IDE.

## Ownership authority (cross-change)

These ownership boundaries are mandatory before implementation when changes
overlap on shared files or interfaces. **No dependent change may redefine an
owned surface** — propose a delta to the authoritative change first.

| Owned surface | Authoritative change | Dependent changes |
|---|---|---|
| Requirements schema (`src/specfact_cli/models/requirements.py`) | `requirements-01-data-model` | `requirements-02`, `requirements-03`, `architecture-01` |
| `ProjectBundle` requirements namespace | `requirements-01-data-model` | `requirements-02`, `requirements-03`, `architecture-01` |
| `ProjectBundle` architecture namespace | `architecture-01-solution-layer` | `validation-02`, `traceability-01` |
| Backlog requirements extraction adapter contract | `requirements-02-module-commands` | `requirements-03-backlog-sync` |
| Evidence JSON envelope and CI verdict schema | `governance-01-evidence-output` | `validation-02`, `governance-02`, `dogfooding-01` |
| Exception scope suppression and expiry | `governance-02-exception-management` | `governance-01`; modules `policy-02` |

## Parent issues (Epics)

| Module group | Epic |
|---|---|
| Architecture Layer Integration (Requirements → AI) | [#256](https://github.com/nold-ai/specfact-cli/issues/256) |
| AI IDE Integration | [#257](https://github.com/nold-ai/specfact-cli/issues/257) |
| Integration Governance and Dogfooding | [#258](https://github.com/nold-ai/specfact-cli/issues/258) |
| CLI End-User Validation | [#285](https://github.com/nold-ai/specfact-cli/issues/285) |

Set the GitHub **Type** to Epic on the project board and link child issues
via **Relationships → tracks** or by setting the project **Parent** field.

## Cross-repo coordination

Module-side companions live in
[`nold-ai/specfact-cli-modules`](https://github.com/nold-ai/specfact-cli-modules).
The runtime pairs for `requirements-02`, `requirements-03`, `architecture-01`,
`validation-02`, `traceability-01`, `governance-01`, `governance-02`, and
`openspec-01` are in that repo's `CHANGE_ORDER.md`. Treat both files as a
single cross-repo plan.

## Archive

All implemented changes are under
[`openspec/changes/archive/`](changes/archive/) with date-prefixed folder
names. Run `git log openspec/changes/archive/` for chronological history.
After a change merges to `dev`, run `openspec archive <change-id>` from the
repo root — do not move folders manually.

## See also

- [`parking-lot/README.md`](parking-lot/README.md) — paused proposals + un-park triggers
- [`config.yaml`](config.yaml) — repo-wide OpenSpec rules and context
- [`specfact-cli-modules/openspec/CHANGE_ORDER.md`](https://github.com/nold-ai/specfact-cli-modules/blob/main/openspec/CHANGE_ORDER.md) — module-side companion plan
