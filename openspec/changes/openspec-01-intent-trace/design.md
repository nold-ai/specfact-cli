# Design: OpenSpec and Spec Kit Import-First Requirement Evidence

## Context

`requirements-01-data-model` and `requirements-02-module-commands` shipped a
normalized requirement evidence schema (`src/specfact_cli/models/requirements.py`)
and a `specfact requirements` command group (module `specfact-requirements`).
The import path is manual: `requirements import --from-file <records.yaml>`.

The repository already contains deterministic parsers for both upstream
formats: `src/specfact_cli/adapters/openspec_parser.py` (OpenSpec change
folders) and `src/specfact_cli/importers/speckit_scanner.py` /
`speckit_converter.py` (Spec Kit feature folders). This change connects those
parsers to the requirements evidence schema and adds deterministic gates.

The principle is: **"OpenSpec and Spec Kit own authoring. SpecFact owns
verification evidence."** No upstream tool adopts a SpecFact schema; SpecFact
reads what they already produce.

## Goals / Non-Goals

**Goals:**

- Import native OpenSpec change folders and Spec Kit feature folders into
  `RequirementInput` records with full source attribution.
- Map spec scenarios (GIVEN/WHEN/THEN) onto `BusinessRule` records so evidence
  is testable, not prose.
- Record a content hash in `RequirementSourceReference.revision` at import
  time so staleness is mechanically detectable.
- Extend requirement context validation with deterministic pass/fail gate
  categories usable in CI via exit codes and JSON evidence.
- Keep the whole path read-only toward upstream artifacts.
- Fail closed when an upstream source declares or signals an untested schema or
  template profile; do not silently emit zero or partial requirement records.

**Non-Goals:**

- Defining any authoring schema, YAML block, or metadata convention that
  upstream authors must write (retired `## Intent Trace` scope).
- Removing or deprecating SpecFact plan-authoring commands (separate change if
  ever needed; this change only repositions documentation).
- Backlog import or drift (`requirements-03-backlog-sync`, deprioritized).
- LLM-assisted mapping or enrichment in the gate path.

## Decisions

### D1: Reuse `RequirementInput` instead of a new intent model

**Decision**: No new top-level model. OpenSpec requirements and Spec Kit specs
normalize into existing `RequirementInput`; scenarios normalize into
`BusinessRule` (given/when/then); sources use existing
`RequirementSourceType.OPENSPEC_CHANGE` and `SPECKIT_SPEC`.
**Rationale**: The requirements-01 schema was designed for exactly this
(source types already exist). A parallel intent model would duplicate the
sidecar, validation, and coverage machinery (DRY violation).
**Alternative rejected**: Separate `IntentRecord` model and sidecar — two
overlapping evidence stores with divergent gates.

### D2: Content hash in `revision` field vs new schema field

**Decision**: Importers populate `RequirementSourceReference.revision` with
`sha256:<hex>` of the parsed artifact content. No schema version bump.
**Rationale**: `revision` is documented as "revision, commit, or version"; a
content hash is a revision. Avoids a schema migration for existing sidecars.
**Trade-off**: Hash convention must be documented and validated by prefix
(`sha256:`); non-prefixed revisions are treated as opaque and exempt from the
staleness gate.

### D3: Deterministic requirement identity

**Decision**: Requirement IDs are derived, stable, and collision-checked:
`openspec:<change-id>:<capability>:<requirement-slug>` and
`speckit:<feature-dir>:<requirement-slug>`. Re-import with an unchanged
artifact is idempotent; re-import with changed content updates the record in
place (merge by `requirement_id`, existing behavior of
`merge_requirement_inputs`).
**Rationale**: Idempotent re-import is what makes "no manual stuff" safe to
run repeatedly (in CI or a pre-commit hook).
**Alternative rejected**: UUIDs per import run — breaks merge and produces
duplicate evidence.

### D4: Gate categories as validation findings, not a new command

**Decision**: Gates extend the existing `requirements validate` report with
finding categories `scenario-unverified`, `stale-import`, `source-missing`,
and `ambiguous-mapping`. Profiles decide severity (error fails the run,
warning does not). No new top-level command.
**Rationale**: `requirements validate` already returns a `ValidationReport`
with profile support and a non-zero exit on failure; CI integration exists.
**Alternative rejected**: New `specfact validate intent` command — surface
sprawl for the same evidence.

Gate severity MUST align with `profile-01-config-layering` (shipped): when the
`--profile` flag is omitted, the effective profile resolves from the layered
config (`resolve_profile_config`: profile defaults -> org baseline -> repo
overlay -> developer local) instead of a hardcoded `startup` default, and the
profile's `requirements_schema.required_fields` participates in completeness
findings. The explicit flag always wins.

The requirements evidence adapter evaluates only the following explicit
aliases: `id` → `requirement_id`, `title` → `title`, `acceptance` →
`business_rules`, and `trace_links` → `evidence_links`. A configured field
outside that set is returned as a machine-readable
`unsupported-profile-field` advisory, not as missing record metadata. Native
OpenSpec and Spec Kit artifacts do not consistently supply owner, risk, or
exception metadata; adding those fields here would violate the import-first,
read-only boundary. A future enrichment change may define a source and schema
for that metadata.

### D5: Import runtime lives in the `specfact-requirements` module

**Decision**: Core owns parsers, normalization, hashing, and gate evaluation
as importable helpers. The `specfact-requirements` module adds
`requirements import --from-openspec [PATH]` and `--from-speckit [PATH]`
flags with auto-detection (`openspec/changes/` and Spec Kit `specs/` layouts)
when the path is omitted.
**Rationale**: Matches the requirements-02 split (core contracts, module
runtime) and keeps the module thin.

### D6: Structural compatibility profiles, not inferred tool versions

**Decision**: Core preflight accepts only two explicitly tested profiles:

- OpenSpec's default `spec-driven` schema (or no schema declaration) with
  native `### Requirement:` and `#### Scenario:` Markdown structure.
- Spec Kit's default Markdown template with `# Feature Specification:` and
  functional-requirement (`FR-`) entries, provided no project template
  override, preset, or extension template root is active.

An OpenSpec custom schema, a Spec Kit customization root, malformed profile
marker, or an unrecognized required Markdown structure returns an error
diagnostic with code `unsupported-source-schema` and **zero records** for that
source. The adapter does not attempt fallback parsing or partial emission.

**Rationale**: Neither source artifact format provides a dependable universal
tool-version field. Inferring a CLI version from Markdown would be false
precision. Structural profiles make the supported contract deterministic and
allow upstream changes to fail visibly until a pinned fixture and an explicit
profile update are added.

**Alternative rejected**: Fetching a current upstream schema during import.
That makes CI non-reproducible, introduces network authority into a read-only
normalizer, and could change results mid-run.

## Risks / Trade-offs

- **[Risk] Upstream format drift** — OpenSpec/Spec Kit layouts evolve.
  Mitigation: profile preflight is fail-closed; unsupported sources emit
  `unsupported-source-schema` and no records until a core fixture-backed
  profile is deliberately added.
- **[Risk] Hash churn on whitespace-only edits** — staleness gate fires on any
  byte change. Accepted: deterministic beats clever; re-import is one command
  and idempotent.
- **[Trade-off] Scenario-to-test linking starts manual** — `evidence_links`
  to tests still come from records or later tooling; the gate reports
  unverified scenarios rather than inventing links. Follow-up changes
  (`traceability-01`, `validation-02`) can populate links mechanically.

## Migration Plan

1. No data migration: existing sidecars validate unchanged.
2. Docs reposition import-first as the flagship path; `--from-file` stays.
3. `requirements-03-backlog-sync` ordering note updated in `CHANGE_ORDER.md`.
4. Adding support for a newer upstream format requires a pinned representative
   fixture, explicit profile change, and a passing compatibility test before
   release; it is not discovered dynamically during import.

## Open Questions

- None currently blocking implementation.
