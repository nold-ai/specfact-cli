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

## Compatibility Rules

Shared payloads MUST be additive by default. A change that needs to remove or
rename evidence fields, graph node kinds, severity values, policy modes, or
artifact IDs MUST first update the owning change and document migration impact.

Dependent changes MAY consume owner-defined payloads, but MUST NOT redefine
their semantics in local proposal text, spec deltas, tests, or implementation
notes.

## Wave Gates

A roadmap wave closes only when its evidence is auditable:

- Active OpenSpec changes validate with `openspec validate --strict`.
- Closed GitHub issues are archived instead of left as planned work.
- Validation evidence is available as JSON, not only prose.
- AI-bloat findings and remediation packets can be produced, applied, and
  rechecked on a real repository slice.
- Spec Kit and OpenSpec artifacts are documented as upstream inputs whenever
  they appear in examples or adapters.

## Issue Governance

Before implementation, linked GitHub issues still need the repository governance
checks in `docs/agent-rules/60-github-change-governance.md`: parent, labels,
project assignment, blockers, and blocked-by relationships. The current token
does not expose GitHub Project fields, so board metadata must be rechecked by a
token with `read:project` before a scoped implementation begins.
