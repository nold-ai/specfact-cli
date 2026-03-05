# Change: OpenSpec Intent Trace — Bridge Adapter Integration

## Why

OpenSpec proposals are plain Markdown with no structured business-intent metadata. When SpecFact imports a proposal via `specfact sync bridge --adapter openspec`, it has no machine-readable context about the business outcomes, business rules, or architectural constraints the change is supposed to satisfy — it only sees tasks and specs. This means the traceability chain starts at the spec level, missing the upstream intent layer entirely. Adding a structured `## Intent Trace` section to OpenSpec proposals (with JSON Schema validation) gives SpecFact the data it needs to construct the full outcome → rule → constraint → spec → code chain automatically on import.

## What Changes

- **NEW**: `## Intent Trace` section schema for OpenSpec `proposal.md` files:
  - YAML-fenced block under `## Intent Trace` with `intent_trace` root key
  - Fields: `business_outcomes` (id, description, persona), `business_rules` (id, outcome_ref, given, when, then), `architectural_constraints` (id, outcome_ref, constraint), `requirement_refs` (list of REQ-NNN strings)
  - JSON Schema at `openspec/schemas/intent-trace.schema.json` for validation
- **NEW**: `requirement_refs` optional field on individual tasks in `tasks.md` — links a task to specific `BusinessRule` IDs or `ArchitecturalConstraint` IDs
- **NEW**: `evidence` optional field on archived changes — points to evidence JSON envelope file(s) generated during implementation; creates immutable proposal → intent trace → implementation → evidence → archive chain
- **NEW**: `specfact sync bridge --adapter openspec --import-intent` — reads `## Intent Trace` section from imported proposals and populates `.specfact/requirements/` with `BusinessOutcome` and `BusinessRule` artifacts automatically
- **EXTEND**: `specfact sync bridge --adapter openspec` — when `## Intent Trace` section is present, include intent context in the imported project bundle; backwards-compatible (section is optional)
- **EXTEND**: `openspec validate <change-id> --strict` — validates `## Intent Trace` section against `intent-trace.schema.json` when present

## Capabilities

### New Capabilities

- `openspec-intent-trace-schema`: JSON Schema definition and validation for the `## Intent Trace` section in OpenSpec proposals — enabling machine-readable business-outcome traceability in change proposals.
- `openspec-bridge-intent-import`: Extended SpecFact OpenSpec bridge adapter that reads, validates, and imports `## Intent Trace` sections from proposals into `.specfact/requirements/` artifacts automatically.

### Modified Capabilities

- `openspec-bridge-adapter`: Extended to parse optional `## Intent Trace` section on proposal import; backwards-compatible when section is absent.

## Impact

- New file: `openspec/schemas/intent-trace.schema.json`
- Existing bridge adapter: `src/specfact_cli/adapters/` OpenSpec adapter extended with intent-trace parsing
- CLI change: `specfact sync bridge --adapter openspec` — new optional `--import-intent` flag; no breaking change to existing workflows
- Depends on: `requirements-01-data-model` (#238) — `BusinessOutcome` and `BusinessRule` schemas must exist to populate; `requirements-02-module-commands` (#239) — `specfact requirements capture` used for artifact creation
- Wave: aligns with Wave 5/6 (after requirements-01/02 land)
- Docs: new `docs/guides/openspec-journey.md` section on Intent Trace; update `docs/adapters/` for OpenSpec adapter

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #350
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/350>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
