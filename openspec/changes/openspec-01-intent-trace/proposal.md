# Change: OpenSpec and Spec Kit Import-First Requirement Evidence

## Why

OpenSpec and Spec Kit own upstream specification and planning authoring. SpecFact
must not compete with them as an authoring surface. The product value is
downstream: import their native artifacts as accountable source-of-truth items,
normalize them into the requirements evidence schema, enrich them with
verification links, and emit deterministic pass/fail gates that CI and reviewers
can trust.

Today the `specfact requirements` command group works but is manual: users
hand-author JSON/YAML records and pass `--from-file`. This change makes upstream
OpenSpec change folders and Spec Kit feature folders first-class import sources,
so requirement evidence exists without manual authoring and every record carries
source attribution back to the accountable upstream artifact.

## Rescope (2026-07-13)

This change was previously scoped as an optional `## Intent Trace` YAML block
that upstream authors would hand-write into proposals. That scope is retired:
it made SpecFact define an authoring schema for other tools, which contradicts
the validation-evidence thesis. The new scope is **import-first**:

- SpecFact parses **native** OpenSpec and Spec Kit artifacts as they exist
  today. Upstream tools change nothing.
- Imported records normalize into the existing requirements evidence schema
  (`requirements-01-data-model`): scenarios become given/when/then business
  rules, sources carry locator plus content-hash revision.
- Validation gates are deterministic and mechanical: unverified scenarios,
  stale imports, missing sources, and ambiguous mappings fail or warn by
  profile. No LLM speculation in the gate path.
- SpecFact bundle records for specs and intent are **derived, read-only
  imports**. SpecFact never writes into `openspec/` or Spec Kit directories.

`requirements-03-backlog-sync` remains proposed but is deprioritized behind
this change (see `openspec/CHANGE_ORDER.md`).

## Ownership Alignment (2026-07-13)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: import contracts for OpenSpec and Spec Kit
  artifacts, normalization and source-attribution semantics, content-hash
  staleness contract, gate categories, and validation behavior.
- Bundle-owned follow-up required: import runtime flags and command wiring in
  the `specfact-requirements` module.
- Target modules-repo follow-up issue: [#168](https://github.com/nold-ai/specfact-cli-modules/issues/168)
- Implementation MUST NOT require OpenSpec or Spec Kit to change their native
  authoring model, and MUST NOT create or mutate upstream artifacts.

## What Changes

- **NEW**: Deterministic import of OpenSpec change folders (`proposal.md`,
  `specs/*/spec.md` requirements and scenarios, `tasks.md`) into normalized
  `RequirementInput` records with `openspec_change` source references.
- **NEW**: Deterministic import of Spec Kit feature folders (`spec.md`,
  `plan.md`, `tasks.md`) into normalized `RequirementInput` records with
  `speckit_spec` source references.
- **NEW**: Source references from these importers MUST populate `revision`
  with a content hash of the parsed artifact, enabling staleness detection.
- **NEW**: Import preflight recognizes only the tested default OpenSpec
  `spec-driven` Markdown profile and the tested default Spec Kit Markdown
  profile. Custom OpenSpec schemas and Spec Kit template override/preset or
  extension roots are rejected with a blocking `unsupported-source-schema`
  diagnostic before any requirement record is emitted; the importer never
  guesses or returns a partial import.
- **NEW**: Requirement context validation gains deterministic gate categories:
  `scenario-unverified` (business rule without test/validation evidence link),
  `stale-import` (source content hash no longer matches artifact on disk),
  `source-missing` (referenced artifact absent), and `ambiguous-mapping`
  (duplicate or conflicting requirement identity across sources). Severity is
  profile-driven; failed gates exit non-zero with JSON evidence.
- **CHANGED**: OpenSpec and Spec Kit are documented as the accountable
  authoring systems of record. SpecFact plan-authoring commands remain
  available but are repositioned as secondary; import-first is the documented
  flagship path. Command deprecation mechanics are out of scope here.
- **CHANGED (shipped-gap fix, folded in 2026-07-13)**: the core
  `validate_requirement_context` helper resolves the effective profile from the layered configuration
  shipped by `profile-01-config-layering` when no explicit profile is passed
  (an explicit flag always wins), and honors the profile's
  `requirements_schema.required_fields` through an explicit evidence-field
  mapping: `id` → `requirement_id`, `title` → `title`, `acceptance` →
  `business_rules`, and `trace_links` → `evidence_links`. Unsupported profile
  fields are emitted as machine-readable `unsupported-profile-field`
  advisories; they never make a native imported record incomplete. This change
  does not add owner, risk, or exception metadata to the import-first schema.
  The requirements CLI still hardcodes the `startup` default; the paired
  module follow-up (#168) will adopt the core helper rather than duplicating
  profile resolution.
- **REMOVED (from this change's previous scope)**: the `## Intent Trace` YAML
  authoring block, `intent-trace.schema.json`, and `--import-intent` bridge
  flag. Never implemented; retired before implementation.

## Capabilities

### New Capabilities

- `openspec-speckit-evidence-adapter`: Deterministic, read-only,
  source-attributed import of native OpenSpec and Spec Kit artifacts into the
  requirements evidence schema.

### Modified Capabilities

- `requirements-module`: Requirement context import gains OpenSpec and Spec
  Kit sources; validation gains deterministic pass/fail gate categories with
  profile-driven severity.

## Impact

- `specfact requirements import` becomes useful without hand-authored files;
  `--from-file` remains for generic records.
- `specfact requirements validate` becomes a CI-usable pass/fail gate over
  imported upstream context.
- No breaking changes: existing bundles, sidecars, and `--from-file` flows are
  unchanged. Depends on `requirements-01-data-model` and
  `requirements-02-module-commands` (both shipped).
- This intentionally pins compatibility to source *format profiles*, not an
  inferred upstream CLI version: native artifacts do not reliably carry one.
  Future upstream profiles require explicit fixtures and a core adapter update.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #350
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/350>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#168
- **Paired Modules Scope**: OpenSpec and Spec Kit evidence import runtime
- **Last Synced Status**: proposed
- **Sanitized**: false
