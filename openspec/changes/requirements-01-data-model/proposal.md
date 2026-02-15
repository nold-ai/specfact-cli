# Change: Requirements Data Model & Storage

## Why




Business requirements have no formal representation in SpecFact. They exist only as unstructured text in backlog items (acceptance criteria, descriptions). This means the most impactful validation gap — "are we building the right thing?" — cannot be programmatically checked. A Pydantic domain model for business requirements with versioned YAML storage under `.specfact/requirements/` gives requirements first-class status in the traceability chain, enabling all downstream validation (Req → Arch → Spec → Code → Tests).

## What Changes




- **NEW**: Pydantic domain models in `src/specfact_cli/models/requirements.py`:
  - `BusinessOutcome` — success metrics and quantified business value
  - `BusinessRule` — rule ID, name, Given/When/Then scenario, MoSCoW priority
  - `ArchitecturalConstraint` — constraint type (performance/security/integration/compliance/ux), requirement, validation criteria
  - `BusinessRequirement` — the top-level model: requirement ID, schema version, user story link, business outcome, business rules, architectural constraints, UX requirements
  - `RequirementTrace` — traceability links: requirement ID → architecture refs, spec refs, code refs, test refs
- **NEW**: Storage convention: `.specfact/requirements/{requirement_id}.req.yaml` with human-readable YAML serialization
- **NEW**: Schema versioning: all requirement models carry `schema_version` field for forward-compatible migration
- **NEW**: Profile-aware field validation: required fields determined by active profile tier (solo = minimal 3 fields, enterprise = all fields + regulatory references)
- **EXTEND**: `ProjectBundle` extended with optional `requirements` field via arch-07 schema extension system (namespace: `requirements.business_requirements`)

## Capabilities
### New Capabilities

- `requirements-data-model`: Pydantic domain models for business requirements (BusinessOutcome, BusinessRule, ArchitecturalConstraint, BusinessRequirement, RequirementTrace) with versioned YAML storage and profile-aware field validation.

### Modified Capabilities

- `data-models`: ProjectBundle extended with requirements field via arch-07 schema extensions


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #238
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/238>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 1dad52a86e44c9f9 -->