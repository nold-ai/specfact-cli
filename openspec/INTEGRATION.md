# OpenSpec Integration Contract

This document is the living ownership contract for active SpecFact OpenSpec
changes. It exists to keep parallel roadmap work aligned without creating a
separate product feature for integration governance.

## Positioning

SpecFact is the local validation and AI-bloat defense CLI. Active changes SHALL
strengthen deterministic evidence, code-review remediation, artifact drift
detection, and trusted CLI behavior.

Spec Kit, OpenSpec, backlog systems, ADRs, and architecture documents are
upstream inputs. SpecFact consumes those artifacts to validate implementation
reality; it does not try to replace the upstream planning stack.

## Ownership Rules

- `governance-01-evidence-output` owns the evidence envelope, CI verdict schema,
  severity taxonomy, and remediation packet attachment points.
- `governance-02-exception-management` owns exception scope, expiry,
  suppression behavior, and waiver evidence.
- `validation-02-full-chain-engine` owns the validation evidence graph contract
  and graph-level aggregation rules.
- `traceability-01-index-and-orphans` owns artifact identity, linkage, and
  orphan/drift classification.
- `requirements-01-data-model` owns normalized requirements-input records only.
  It does not own requirement authoring or backlog source-of-truth behavior.
- `requirements-02-module-commands` owns import and normalization contracts for
  upstream planning inputs.
- `requirements-03-backlog-sync` owns read-first drift evidence between backlog
  systems and normalized inputs. Write-back remains outside the critical path.
- `architecture-01-solution-layer` owns architecture-boundary input records and
  validation hooks, not architecture generation.
- `architecture-02-well-architected-review` owns architecture-review finding
  contracts after `architecture-01` has shipped and completed one usage cycle.
- `profile-01-config-layering` owns rollout mode defaults that tune validation
  severity without changing evidence semantics.
- `preflight-01-design-contract-core` owns the durable pre-implementation
  design-contract, role-classified scope, component/risk/verification intent,
  Requirements-plan references, validation-result, canonical digest,
  approval-seal, and side-effect-free verifier interfaces. It owns no CLI,
  validator execution, rendering, persistence, skill, or adapter behavior.
- modules `preflight-02-assurance-runtime` owns the executable pre-implementation
  loop, Python validators, CLI, human/JSON rendering, explicit persistence, and
  canonical module-owned workflow content.
- core `preflight-03-dogfood-hardening-and-release` owns C14 dogfood evidence
  and the bounded readiness decision. Its paired modules change owns only
  evidence-backed hardening, signing, compatibility proof, and stable publication.
- `ai-integration-01-agent-skill` owns discovery, integrity verification,
  installation, update/uninstall, and canonical `.agents/skills` export of
  module-owned skills. It does not own any installed workflow body.
- `ai-integration-03-instruction-files` owns compact generated AGENTS/OpenSpec/
  Spec Kit and harness gate references. It does not own validators, workflow
  content, or external adapter packages.
- modules `preflight-04-harness-adapters` owns later thin Codex, ECC, and
  hatch3r packaging against the signed canonical workflow. Adapters may map
  invocation and assets but must not duplicate validators or readiness logic.
- core `preflight-05-implementation-conformance` owns worktree/index/range
  snapshots, sealed-obligation mapping, checkpoint/conformance results,
  closed finding classes, authority separation, and pure verifier interfaces.
  Its paired modules change owns Git extraction, bounded pytest and code-review
  execution, remediation packets, agent-loop orchestration, rendering,
  persistence, and release.

## Compatibility Rules

Shared payloads MUST be additive by default. A change that needs to remove or
rename evidence fields, graph node kinds, severity values, policy modes, or
artifact IDs MUST first update the owning change and document migration impact.

Dependent changes MAY consume owner-defined payloads, but MUST NOT redefine
their semantics in local proposal text, spec deltas, tests, or implementation
notes.

A preflight approval seal identifies exact reviewed and approved inputs. It is
not proof of design quality, LLM understanding, implementation correctness, or
final conformance. Any bound design input change invalidates the seal and
requires a new snapshot, full validation rerun, and explicit approval. Normal
implementation snapshots remain separate evidence against that unchanged seal.

General AGENTS.md, OpenSpec, Spec Kit, and command-harness instructions MUST
contain only the compact gate and installed workflow reference. The signed
module skill is the canonical workflow source; Python validators are the
canonical determinate checks.

## Wave Gates

A roadmap wave closes only when its evidence is auditable:

- Active OpenSpec changes validate with `openspec validate --strict`.
- Closed GitHub issues are archived instead of left as planned work.
- Validation evidence is available as JSON, not only prose.
- AI-bloat findings and remediation packets can be produced, applied, and
  rechecked on a real repository slice.
- Spec Kit and OpenSpec artifacts are documented as upstream inputs whenever
  they appear in examples or adapters.
- Preflight hardening is authorized only by identity-bound C14 dogfood evidence
  and a core-owned go decision; downstream publication remains blocked on no-go.
- Local checkpoints and final conformance remain distinct from pre-implementation
  approval and from each other; local authority cannot be promoted to protected
  PR-range authority, and unknown or stale evidence never implies success.

## Issue Governance

Before implementation, linked GitHub issues still need the repository governance
checks in `docs/agent-rules/60-github-change-governance.md`: type, parent,
labels, assignee, project assignment and status, blockers, blocked-by
relationships, and `In Progress` concurrency. Read back those native fields
from GitHub immediately before work; body-only dependency text is insufficient.
