# Design: OpenSpec Intent Trace — Bridge Adapter Integration

## Context

SpecFact's OpenSpec bridge adapter (`specfact sync bridge --adapter openspec`) reads proposal and task files from an OpenSpec change directory and imports them into SpecFact's project bundle. Currently it reads: title, description, tasks list, and spec references. It does not read any business intent context. This change adds an optional `## Intent Trace` YAML block to the OpenSpec proposal format and teaches the bridge adapter to import it into the `.specfact/requirements/` storage hierarchy used by requirements-01-data-model.

The principle is: **"OpenSpec owns the intent. SpecFact owns the evidence."** OpenSpec authors write intent in a human-readable YAML block; SpecFact validates conformance and generates evidence. This separation keeps the intent format tool-agnostic.

## Goals / Non-Goals

**Goals:**
- Define the `## Intent Trace` section YAML schema and JSON Schema validator
- Extend the OpenSpec bridge adapter to parse and import intent artifacts when the section is present
- Keep the `## Intent Trace` section strictly optional — existing proposals without it are unaffected
- Validate the section against the JSON Schema during `openspec validate --strict`
- Produce `.specfact/requirements/{id}.req.yaml` artifacts from imported intent data

**Non-Goals:**
- Forcing all existing OpenSpec proposals to add an `## Intent Trace` section
- Building a new proposal authoring tool — the section is hand-authored YAML in Markdown
- Replacing requirements-01/02 commands — the bridge adapter imports intent; the requirements module validates and traces it

## Decisions

### D1: YAML fenced block vs structured Markdown headings for Intent Trace

**Decision**: YAML fenced block under `## Intent Trace` heading
```yaml
intent_trace:
  business_outcomes:
    - id: "BO-001"
      description: "..."
      persona: "..."
  business_rules:
    - id: "BR-001"
      outcome_ref: "BO-001"
      given: "..."
      when: "..."
      then: "..."
```
**Rationale**: YAML is machine-parseable with a single `yaml.safe_load()` call and maps directly to Pydantic models. Structured Markdown headings require custom parsing logic that is brittle and hard to validate with JSON Schema. YAML fenced blocks are already used in GitHub Actions, Docker Compose, and Kubernetes manifests — authors are familiar with the pattern.
**Alternative rejected**: Structured `### Business Outcomes / ### Business Rules` Markdown sub-sections — readable but not JSON Schema validatable.

### D2: JSON Schema stored in SpecFact vs in OpenSpec format repo

**Decision**: JSON Schema at `openspec/schemas/intent-trace.schema.json` within SpecFact's own repo
**Rationale**: SpecFact is the authority for validation. The schema living in SpecFact's repo means the bridge adapter always validates against the version it was built with. When OpenSpec is an external tool (not this repo), the schema reference is still resolvable locally.
**Alternative rejected**: Hosting schema at `openspec.dev/schemas/intent-trace` — external HTTP dependency violates offline-first constraint.

### D3: `--import-intent` flag vs automatic intent import

**Decision**: `specfact sync bridge --adapter openspec --import-intent` — opt-in flag
**Rationale**: Not every team using the OpenSpec bridge wants `.specfact/requirements/` files created from every proposal import. The opt-in flag gives teams control. When `## Intent Trace` is present but `--import-intent` is not passed, the bridge still validates the section on `openspec validate --strict` but does not write requirements artifacts.
**Alternative rejected**: Automatic import when section is present — surprising side effect; could overwrite existing requirement files.

### D4: `requirement_refs` in tasks.md — free-form vs validated IDs

**Decision**: Free-form string list (`["BR-001", "AC-002"]`) with advisory validation
**Rationale**: Task-level requirement refs are metadata for traceability, not for enforcement. Advisory-mode validation warns if a ref ID does not match any known `BusinessRule` or `ArchitecturalConstraint` in `.specfact/requirements/` but does not block import. Hard enforcement would break workflows where requirements are not yet captured.

### D5: `evidence` field in archived changes

**Decision**: Optional string field in change archive metadata: `evidence: ".specfact/evidence/{timestamp}_{run_id}_evidence.json"`
**Rationale**: Minimal — just a file path reference. The evidence file itself is owned by governance-01-evidence-output. The archive metadata is a pointer, not a copy. This keeps the archive lightweight while enabling audit trail navigation.

## Risks / Trade-offs

- **[Risk] YAML indentation errors in proposals** — Authors writing `## Intent Trace` blocks manually may introduce YAML syntax errors. Mitigation: `openspec validate --strict` catches YAML parse errors before import; error message shows the line number and suggests a fix.
- **[Risk] ID collision between imported BusinessOutcome IDs and existing requirements** — If a team runs `--import-intent` twice with the same proposal, duplicate `.req.yaml` files may result. Mitigation: bridge adapter checks for existing file with same ID before writing; uses `--overwrite` flag to allow update.
- **[Trade-off] Schema evolution** — As requirements-01-data-model evolves (new fields), the `intent-trace.schema.json` must stay in sync. Mitigation: schema versioning (`schema_version: "1.0"` in the YAML block); bridge adapter rejects unknown schema versions with a clear error.

## Migration Plan

1. Land requirements-01-data-model (#238) — `BusinessOutcome` and `BusinessRule` Pydantic models must exist.
2. Define `intent-trace.schema.json` using the Pydantic model fields from requirements-01 as source of truth.
3. Extend bridge adapter parser to detect `## Intent Trace` section and extract the YAML block.
4. Implement `--import-intent` flag and requirements artifact writer.
5. Extend `openspec validate --strict` to call JSON Schema validator on intent trace section.
6. Update existing SpecFact dogfood proposals (this repo's `openspec/changes/`) with `## Intent Trace` sections as the team adopts the format.

## Open Questions

- None currently blocking implementation.
