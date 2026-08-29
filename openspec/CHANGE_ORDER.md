# OpenSpec Change Order

This document is the **single source of truth for active work** in this
repository. It lists what is in flight, what is paused, and the order in which
active changes should be implemented.

## Status snapshot

| Bucket | Count | Location |
|---|---:|---|
| **Active** | 26 | [`openspec/changes/`](changes/) |
| **Parked** | 22 | [`openspec/parking-lot/`](parking-lot/) |
| **Archived** | 117 | [`openspec/changes/archive/`](changes/archive/) |

`openspec list` reflects the active set only. Parking-lot proposals are paused
pending external signal, such as paying customer pull, third-party publisher
adoption, or a real evidence corpus. See
[`parking-lot/README.md`](parking-lot/README.md) for un-park triggers.

## Product thesis

SpecFact is the local validation and AI-bloat defense CLI for AI-assisted and
brownfield delivery. The active roadmap should make that thesis stronger:

- produce deterministic evidence before merge;
- detect AI-bloat, drift, weak contracts, and orphaned artifacts;
- hand remediation packets to AI IDEs without becoming the IDE;
- consume Spec Kit, OpenSpec, backlog, ADR, contract, code, and test artifacts
  as upstream inputs;
- avoid competing with upstream planning stacks that already own spec-driven or
  intent-driven authoring.

## Naming convention

- **Folder**: `<module>-<NN>-<suffix>` such as `requirements-01-data-model`.
- **Order**: lower numbers within a module come first. Cross-module dependencies
  are listed in the **Blocked by** column.

## Active tracks

The 27 active changes group into four product tracks plus one reliability lane.
Tracks can run in parallel; within a track, follow the order column.

### Track A - Validation Evidence Spine

This is the core product path. It turns existing repo and planning artifacts
into auditable validation evidence and cleanup feedback.

| Order | Change | Issue | Positioning | Blocked by |
|---:|---|---|---|---|
| 1 | `profile-01-config-layering` | [#237](https://github.com/nold-ai/specfact-cli/issues/237) | Rollout modes for validation severity and evidence strictness | - |
| 2 | `governance-01-evidence-output` | [#247](https://github.com/nold-ai/specfact-cli/issues/247) | Evidence JSON, CI verdicts, remediation packet attachment points | modules `policy-02` |
| 3 | `governance-02-exception-management` | [#248](https://github.com/nold-ai/specfact-cli/issues/248) | Time-bound validation exceptions and waiver evidence | governance-01; modules `policy-02` |
| 4 | `traceability-01-index-and-orphans` | [#242](https://github.com/nold-ai/specfact-cli/issues/242) | Generic artifact index and orphan/drift classification across normalized inputs | requirements input contracts; other adapters optional when present |
| 5 | `validation-02-full-chain-engine` | [#241](https://github.com/nold-ai/specfact-cli/issues/241) | Validation evidence graph over existing inputs, not a product lifecycle engine | governance-01, traceability-01 |
| 6 | `dogfooding-01-full-chain-e2e-proof` | [#255](https://github.com/nold-ai/specfact-cli/issues/255) | AI-bloat defense and validation proof on real PRs | governance-01, validation-02, traceability-01 |

**Critical path**: profile-01, governance-01, and traceability-01 converge at
validation-02 -> dogfooding proof. Traceability requires requirements inputs;
governance and traceability do not block each other.

### Track B - AI IDE Validation Distribution

AI integrations should teach agents how to run SpecFact validation, interpret
evidence, apply remediation packets, and rerun proof. They should not become an
upstream intent-engineering product.

| Order | Change | Issue | Positioning | Blocked by |
|---:|---|---|---|---|
| 1 | `ai-integration-01-agent-skill` | [#251](https://github.com/nold-ai/specfact-cli/issues/251) | Discover, verify, install, update, uninstall, and canonically export module-owned skills under `.agents/skills`; no workflow-content ownership | signed modules checkpoint/conformance release [#434](https://github.com/nold-ai/specfact-cli-modules/issues/434) |
| 2 | `ai-integration-03-instruction-files` | [#253](https://github.com/nold-ai/specfact-cli/issues/253) | Generate compact AGENTS/OpenSpec/Spec Kit and harness gate references; no validation logic or adapter packaging | ai-integration-01 |
| 3 | `ai-integration-02-mcp-server` | [#252](https://github.com/nold-ai/specfact-cli/issues/252) | Later thin adapter with 2-3 validation tools only | CLI pull from ai-integration-01 |

### Track C - Upstream Context Adapters

These changes are useful only when they improve validation evidence. They import
and normalize upstream context from Spec Kit, OpenSpec, backlog systems, ADRs,
and architecture docs. They do not own authoring, ceremonies, or bidirectional
planning workflows.

| Order | Change | Issue | Positioning | Blocked by |
|---:|---|---|---|---|
| 1 | `requirements-01-data-model` | [#238](https://github.com/nold-ai/specfact-cli/issues/238) | Normalized requirements-input records for evidence | arch-07 |
| 2 | `requirements-02-module-commands` | [#239](https://github.com/nold-ai/specfact-cli/issues/239) | Import and normalize existing requirement context | requirements-01 |
| 3 | `openspec-01-intent-trace` | [#350](https://github.com/nold-ai/specfact-cli/issues/350) | Import-first OpenSpec and Spec Kit requirement evidence with pass/fail gates (rescoped 2026-07-13) | requirements-01/02 |
| 4 | `requirements-04-upstream-source-readiness` | [#648](https://github.com/nold-ai/specfact-cli/issues/648) | Reject incomplete or policy-invalid native OpenSpec and Spec Kit sources before requirement normalization | openspec-01; paired modules #346 |
| 5 | `requirements-06-evidence-enforcement` | [#657](https://github.com/nold-ai/specfact-cli/issues/657) | Enforce released Requirements evidence reports in staged pre-commit and pull-request delivery gates | released modules #361 fixture |
| 6 | `requirements-07-runtime-proof-delivery` | [#662](https://github.com/nold-ai/specfact-cli/issues/662) | Execute exact scenario selectors and report current-run JUnit evidence independently from historical chronology | corrected modules R07 signed release |
| Parked | `requirements-08-bounded-red-green-proof` | [#675](https://github.com/nold-ai/specfact-cli/issues/675) | Superseded by seal-bound risk/test intent plus implementation checkpoints; no B/R/H/D replay implementation planned | closed Not Planned; preserved under `openspec/parking-lot/` without archiving or canonical spec merge |
| 8 | `architecture-01-solution-layer` | [#240](https://github.com/nold-ai/specfact-cli/issues/240) | Architecture-boundary records and drift validation | requirements input contracts |
| Parked | `requirements-03-backlog-sync` | [#244](https://github.com/nold-ai/specfact-cli/issues/244) | Read-first drift evidence; no write-back critical path. Deprioritized 2026-07-13 behind openspec-01 | requirements-02; modules `sync-01` |
| Gated | `architecture-02-well-architected-review` | [#524](https://github.com/nold-ai/specfact-cli/issues/524) | Architecture-boundary review findings | architecture-01 shipped plus one usage cycle |
| Gated | `telemetry-01-opentelemetry-default-on` | [#518](https://github.com/nold-ai/specfact-cli/issues/518) | Opt-in validation outcome telemetry only | governance-01 evidence fields |

### Track D - CLI Validation Trust

These changes make the CLI itself trustworthy enough to be the validation tool.

| Order | Change | Issue | Positioning | Blocked by |
|---:|---|---|---|---|
| 1 | `cli-val-03-misuse-safety-proof` | [#281](https://github.com/nold-ai/specfact-cli/issues/281) | Misuse safety proof for user-facing commands | - |
| 2 | `cli-val-04-acceptance-test-runner` | [#282](https://github.com/nold-ai/specfact-cli/issues/282) | Acceptance-test runner for CLI behavior proof | cli-val-03 |
| 3 | `cli-val-05-ci-integration` | [#643](https://github.com/nold-ai/specfact-cli/issues/643) | Fail-closed documentation accountability and CI validation enforcement | cli-val-02, cli-val-03, cli-val-04 |

### Track E - Deterministic Pre-Implementation Assurance

Core owns durable assurance interfaces and dogfood/readiness evidence. The
modules repository owns executable validators, CLI/workflow behavior, stable
publication, checkpoints/conformance, and external adapters. Checkpoints reuse
the approved seal during implementation; final range conformance remains a
separate authority class.

| Order | Change | Issue | Positioning | Blocked by |
|---:|---|---|---|---|
| 1 | `preflight-01-design-contract-core` | [#682](https://github.com/nold-ai/specfact-cli/issues/682) | Design-contract, validation-result, canonical digest, approval-seal, and side-effect-free verifier interfaces | architecture/governance/traceability/OpenSpec import are upstream inputs, not reowned blockers |
| 2 | `preflight-03-dogfood-hardening-and-release` (core) | [#683](https://github.com/nold-ai/specfact-cli/issues/683) | Identity-bound C14 dogfood evidence and bounded readiness decision | core C14 [#680](https://github.com/nold-ai/specfact-cli/issues/680) |
| 3 | `preflight-05-implementation-conformance` (core) | [#684](https://github.com/nold-ai/specfact-cli/issues/684) | Worktree/index/range snapshots, sealed-obligation mapping, local checkpoint/final conformance results, findings, authority, and pure verifier | signed modules hardening/publication [#432](https://github.com/nold-ai/specfact-cli-modules/issues/432) |

The cross-repository dependency sequence is:

`core #682 -> modules #431 -> core C14 #680/#683 -> modules #432 -> core #684 -> modules #434 -> core #251 -> core #253 -> modules #433`.
Modules #432 also unblocks modules C15 #417, which remains upstream of core C15
issue #679. Native GitHub relationships, not this prose alone, are authoritative
for readiness.

## Modify queue before implementation

No behavior implementation should start from stale upstream-planning language.
Update each proposal first, then run strict OpenSpec validation.

| Change | Required adjustment |
|---|---|
| `validation-02-full-chain-engine` | Rewrite as a validation evidence graph engine over existing inputs. Do not own requirements-to-code lifecycle authoring. |
| `traceability-01-index-and-orphans` | Keep artifact drift, orphan, and linkage evidence. Remove ceremony/dashboard positioning. |
| `requirements-01-data-model` | Reduce to optional normalized requirements-input records for validation evidence. |
| `requirements-02-module-commands` | Drop requirement authoring as a flagship path. Keep import, normalization, validation, and coverage inspection. |
| `requirements-03-backlog-sync` | Make drift detection/read-first import the product value. Keep write-back preview out of the critical path. |
| `requirements-04-upstream-source-readiness` | Keep source readiness core-owned and atomic; do not create an upstream authoring schema or require the OpenSpec CLI outside explicit or strict/enterprise policy. |
| `architecture-01-solution-layer` | Reduce to architecture-boundary validation and drift evidence. Do not generate architecture. |
| `openspec-01-intent-trace` | Done 2026-07-13: rescoped to import-first adapter consuming native OpenSpec and Spec Kit artifacts with deterministic pass/fail gates. |
| `dogfooding-01-full-chain-e2e-proof` | Rewrite proof around real PR review, JSON evidence, AI-bloat findings, remediation packets, rerun proof. |
| `ai-integration-01-agent-skill` | Decision complete 2026-08-25: keep shared module-owned skill discovery, integrity, installation, update/uninstall, and canonical `.agents/skills` export only. |
| `ai-integration-03-instruction-files` | Decision complete 2026-08-25: generate compact AGENTS/OpenSpec/Spec Kit and harness gate references only; no validation logic or external adapter packaging. |
| `ai-integration-02-mcp-server` | Gate later, after CLI validation has pull; expose only 2-3 validation tools. |
| `telemetry-01-opentelemetry-default-on` | Keep opt-in only and measure validation outcomes, not product-management workflow analytics. |
| `architecture-02-well-architected-review` | Add explicit blocked status until architecture-01 ships and completes one usage cycle. |

## Implementation waves

### Preflight assurance sequence - mandatory dependency gate

1. Implement core `preflight-01-design-contract-core` [#682](https://github.com/nold-ai/specfact-cli/issues/682).
2. Implement the unpublished modules runtime `preflight-02-assurance-runtime` [#431](https://github.com/nold-ai/specfact-cli-modules/issues/431).
3. Complete core C14 adoption [#680](https://github.com/nold-ai/specfact-cli/issues/680).
4. Run the exact preflight loop through core dogfood/readiness [#683](https://github.com/nold-ai/specfact-cli/issues/683).
5. Harden, sign, and publish the stable modules release [#432](https://github.com/nold-ai/specfact-cli-modules/issues/432) from accepted dogfood evidence only.
6. Implement core seal-bound checkpoint/conformance contracts [#684](https://github.com/nold-ai/specfact-cli/issues/684).
7. Implement, dogfood, sign, and publish modules checkpoint/conformance runtime [#434](https://github.com/nold-ai/specfact-cli-modules/issues/434).
8. Use that release for #251 -> #253 -> external adapters #433. Modules C15 #417 -> core C15 #679 may proceed from the stable #432 handoff independently.

Every implementation item starts in its own issue-linked worktree and dedicated
session. Proposal-stage preflight review may refine another pending change only
with its owner’s explicit approval; any refinement invalidates prior readiness
and requires a complete rerun.

### Wave 1 - Scope cleanup and archives

- Archive completed active OpenSpec folders whose GitHub issues are closed.
- Move `ai-integration-04-intent-skills` to the parking lot because upstream
  intent engineering is no longer active scope.
- Convert `integration-01-cross-change-contracts` into
  [`INTEGRATION.md`](INTEGRATION.md) and archive the change.
- Apply the modify queue above to active proposals and internal wiki mirrors.
- Recheck GitHub Project fields with a token that has `read:project` before
  implementation work begins.

### Wave 2 - Validation foundations

- `profile-01-config-layering`
- `governance-01-evidence-output`
- `governance-02-exception-management`
- `cli-val-03-misuse-safety-proof`
- `requirements-06` as the core delivery gate for released Requirements
  evidence; it consumes the immutable modules #361 fixture without duplicating
  module command semantics.

### Wave 3 - Evidence graph and drift detection

- `validation-02-full-chain-engine`
- `traceability-01-index-and-orphans`
- `cli-val-04-acceptance-test-runner`

### Wave 4 - AI IDE validation loop

- `ai-integration-01-agent-skill` after the signed preflight workflow exists.
- `ai-integration-03-instruction-files` after canonical installation/export is released.
- Dogfooding slice: run review on a real repo, emit JSON evidence, identify
  AI-bloat findings, hand remediation packets to an AI IDE, rerun review, and
  show improved evidence.

### Wave 5 - Optional adapters and later extensions

- `requirements-01/02` only as validation input adapters (shipped);
  `requirements-03` parked 2026-07-13.
- `architecture-01` only as architecture-boundary validation input.
- `openspec-01` as import-first OpenSpec and Spec Kit requirement evidence
  adapter with deterministic gates; pulled forward to Track C order 3 on
  2026-07-13 (rescoped, no longer positioned as optional-only).
- `requirements-04` as the core-owned source-readiness follow-up to
  `openspec-01`; it blocks the paired modules command/persistence patch.
- `architecture-02`, `telemetry-01`, and `ai-integration-02` only after pull
  from the validation loop exists.
- core/modules `preflight-05` after the signed #432 handoff and before generic
  installation/instructions; modules `preflight-04-harness-adapters` only after
  #253 and the signed #434 checkpoint/conformance handoff.

## Wave exit gates

A wave is complete only when all listed criteria are auditable:

- **Wave 1**: Active changes match the validation positioning and completed
  work is archived.
- **Wave 2**: Evidence envelope, exception model, profile severity, and CLI
  misuse proof validate strictly.
- **Wave 3**: One evidence graph run proves drift/orphan detection over existing
  artifacts without ownership conflicts.
- **Wave 4**: One AI-bloat defense loop produces JSON evidence, remediation
  packets, rerun proof, and improved evidence on a real repository slice.
- **Wave 5**: External planning artifacts are consumed as inputs. They are not
  positioned as workflows SpecFact replaces.
- **Preflight sequence**: Exact C14 dogfood evidence produces a bounded go/no-go
  decision; stable publication and downstream installation stay blocked on no-go.

## Ownership authority

The cross-change ownership contract lives in
[`INTEGRATION.md`](INTEGRATION.md). No dependent change may redefine an owned
surface. Propose a delta to the authoritative change first.

## Parent issues and epic framing

Rename or reframe parent issues where possible:

| Current issue | Desired framing |
|---|---|
| [#256](https://github.com/nold-ai/specfact-cli/issues/256) | Validation evidence and context adapters |
| [#257](https://github.com/nold-ai/specfact-cli/issues/257) | AI IDE validation integration |
| [#258](https://github.com/nold-ai/specfact-cli/issues/258) | Evidence dogfooding and governance |
| [#285](https://github.com/nold-ai/specfact-cli/issues/285) | CLI validation trust |
| [#681](https://github.com/nold-ai/specfact-cli/issues/681) | Deterministic pre-implementation change assurance Feature under #285 |

Set GitHub **Type** to Epic on the project board and link child issues via
**Relationships -> tracks** or by setting the project **Parent** field. Project
board metadata was not available with the current token, so final issue
governance must recheck those fields before implementation.

## Cross-repo coordination

Module-side companions live in
[`nold-ai/specfact-cli-modules`](https://github.com/nold-ai/specfact-cli-modules).
The modules roadmap should now treat `specfact code` and AI-bloat defense as
the flagship product path, while backlog, ceremony, enterprise, FinOps, and
knowledge extensions remain parked unless validation evidence requires them.

## Archive

All implemented changes are under
[`openspec/changes/archive/`](changes/archive/) with date-prefixed folder names.
After a change merges to `dev`, run `openspec archive <change-id>` from the
repo root. Do not move folders manually.

## See also

- [`parking-lot/README.md`](parking-lot/README.md) - paused proposals and
  un-park triggers
- [`INTEGRATION.md`](INTEGRATION.md) - cross-change ownership contract
- [`config.yaml`](config.yaml) - repo-wide OpenSpec rules and context
- [`specfact-cli-modules/openspec/CHANGE_ORDER.md`](https://github.com/nold-ai/specfact-cli-modules/blob/main/openspec/CHANGE_ORDER.md) - module-side companion plan
