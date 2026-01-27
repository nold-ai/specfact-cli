# Technical Design: AISP Formal Clarification Integration

> **AI LLM Instructions**: This document has a formalized AISP version available at [design.aisp.md](./design.aisp.md). For implementation tasks, use the AISP version which provides mathematically precise architectural decisions, trade-offs, and design constraints with `Ambig < 0.02`. The AISP version encodes all design rules, storage patterns, and integration points in formal notation that eliminates interpretation variance.

## Context

This design implements AISP (AI Symbolic Programming) v5.1 formal clarification integration for SpecFact CLI. AISP provides a proof-carrying protocol that reduces AI interpretation variance from 40–65% to <2% by encoding decision trees and logical boundaries in a form that LLMs can verify deterministically.

The integration establishes SpecFact as the **validation and clarification layer** by storing AISP formal specifications internally in project bundles as a tool-agnostic, AI-optimized representation. This approach maintains SpecFact's independence from SDD tool formats while enabling AI LLMs to consume mathematically precise specifications instead of ambiguous markdown.

## Goals

1. **Internal AISP Storage**: Store AISP proof artifacts in project bundles (`.specfact/projects/<bundle>/aisp/`) without modifying source spec files
2. **Tool-Agnostic Representation**: AISP blocks work with any SDD tool format (OpenSpec, Spec-Kit, etc.) without format dependencies
3. **AI LLM Consumption**: Enable AI LLMs to consume AISP specifications via slash command prompts instead of ambiguous markdown
4. **Automatic Generation**: Generate AISP blocks from natural language requirements via bridge adapters
5. **Developer-Friendly**: Keep AISP as internal representation, avoiding exposure of formal notation to developers
6. **Mathematical Precision**: Achieve `Ambig < 0.02` in AISP formalizations, reducing interpretation variance

## Non-Goals

- Embedding AISP directly in spec markdown files (AISP remains internal)
- Modifying source spec files (OpenSpec, Spec-Kit) with AISP notation
- Requiring developers to write AISP manually (generated automatically)
- Replacing markdown specs with AISP (AISP is supplementary, not replacement)
- AISP syntax validation in spec files (validation only in project bundles)
- Bidirectional AISP sync (AISP is generated from specs, not synced back)

## Decisions

### Decision 1: Internal Storage in Project Bundles

**What**: AISP proof artifacts are stored internally in `.specfact/projects/<bundle>/aisp/` directory, not in source spec files.

**Why**:

- Maintains tool-agnostic independence from SDD tool formats
- Avoids exposing developers to formal notation ("hieroglyphs")
- Enables SpecFact to act as validation/clarification layer
- Preserves source spec file integrity (no modifications)
- Allows AISP to evolve independently from spec file formats

**Alternatives Considered**:

- Embedding AISP in spec markdown files (rejected - breaks tool-agnosticism, exposes developers to formal notation)
- Storing AISP in `specs/<capability>/aisp/` subdirectories (rejected - couples AISP to spec file structure)
- Storing AISP in separate repository (rejected - adds complexity, breaks project bundle cohesion)

**Implementation**:

- AISP blocks stored as `proof-<requirement-id>.aisp.md` files in `.specfact/projects/<bundle>/aisp/`
- Proof ID to requirement ID mapping in project bundle metadata
- AISP loading from project bundle for slash commands and validation
- Source spec files remain unchanged (no AISP notation visible)

### Decision 2: Bridge Adapter Pattern for Generation

**What**: AISP blocks are generated from requirements via bridge adapters (OpenSpec, Spec-Kit) during import/sync operations.

**Why**:

- Follows existing bridge adapter pattern (consistent with project architecture)
- Enables automatic AISP generation from any SDD tool format
- Maintains separation of concerns (adapters handle tool-specific logic)
- Supports cross-repository AISP generation via `external_base_path`
- Allows future adapters to generate AISP without code changes

**Alternatives Considered**:

- Manual AISP authoring (rejected - too complex, defeats purpose of automatic clarification)
- Separate AISP generation service (rejected - adds unnecessary complexity)
- AISP generation in CLI commands only (rejected - misses import/sync opportunities)

**Implementation**:

- OpenSpec adapter: Generate AISP during `import_artifact()` and `sync_artifact()` calls
- Spec-Kit adapter: Generate AISP during spec import/sync operations
- Generated AISP stored in project bundle immediately after generation
- Proof IDs mapped to requirement IDs for binding validation

### Decision 3: Slash Commands for AI LLM Consumption

**What**: Slash command prompts (`/specfact.compile-aisp`, `/specfact.update-aisp`) instruct AI LLMs to consume AISP from project bundles instead of markdown specs.

**Why**:

- Enables AI LLMs to use mathematically precise AISP instead of ambiguous markdown
- Provides interactive clarification workflow for vague/ambiguous elements
- Maintains developer workflow (developers work with markdown, AI LLMs consume AISP)
- Establishes SpecFact as the clarification layer that enforces mathematical clarity
- References AISP v5.1 specification for formal semantics

**Alternatives Considered**:

- Requiring developers to manually invoke AISP compilation (rejected - too complex, defeats automation)
- Embedding AISP compilation in all AI interactions (rejected - may not always be needed)
- Separate AISP compilation CLI command only (rejected - misses AI LLM integration opportunity)

**Implementation**:

- `/specfact.compile-aisp`: Instructs AI LLM to update AISP from spec, clarify ambiguities, then execute AISP
- `/specfact.update-aisp`: Detects spec changes and updates corresponding AISP blocks
- Slash command prompts stored in `resources/templates/slash-commands/`
- Prompts reference AISP v5.1 specification for AI LLM context

### Decision 4: Tool-Agnostic Data Models

**What**: AISP data models (`AispProofBlock`, `AispBinding`, `AispParseResult`) are tool-agnostic and work with any SDD tool format.

**Why**:

- Maintains SpecFact's independence from SDD tool formats
- Enables AISP to work with future SDD tools without code changes
- Separates AISP concerns from tool-specific metadata
- Allows AISP blocks to be shared across different tool formats
- Supports cross-tool AISP validation and comparison

**Alternatives Considered**:

- Tool-specific AISP models (rejected - breaks tool-agnosticism, adds complexity)
- Embedding AISP in tool-specific models (rejected - couples AISP to tool formats)
- Separate AISP models per tool (rejected - unnecessary duplication)

**Implementation**:

- `AispProofBlock`: Tool-agnostic proof block structure (id, input_schema, decisions, outcomes, invariants)
- `AispBinding`: Tool-agnostic requirement-proof binding (requirement_id, proof_id, scenario_ids)
- `AispParseResult`: Tool-agnostic parse result (proofs, bindings, errors, warnings)
- AISP models stored separately from tool-specific models (Feature, Story, etc.)

### Decision 5: Internal Representation Only

**What**: AISP blocks are never exposed in source spec files or exported artifacts - they remain internal to SpecFact.

**Why**:

- Keeps developers working with natural language specs (no formal notation exposure)
- Maintains spec file compatibility with SDD tools (OpenSpec, Spec-Kit)
- Preserves spec file readability and maintainability
- Allows AISP to evolve independently from spec file formats
- Establishes SpecFact as the clarification layer (AISP is SpecFact's internal optimization)

**Alternatives Considered**:

- Exporting AISP in spec files (rejected - breaks tool compatibility, exposes developers to formal notation)
- Embedding AISP in exported artifacts (rejected - couples exports to AISP format)
- Making AISP optional in spec files (rejected - breaks tool-agnosticism)

**Implementation**:

- AISP blocks stored only in `.specfact/projects/<bundle>/aisp/`
- Source spec files never modified with AISP notation
- Exported artifacts (spec.md, plan.md) never include AISP blocks
- AISP accessible only through SpecFact CLI commands and slash commands

### Decision 6: AISP v5.1 Specification Reference

**What**: All AISP blocks reference AISP v5.1 specification from <https://github.com/bar181/aisp-open-core/blob/main/AI_GUIDE.md> for formal semantics.

**Why**:

- Ensures AISP blocks follow standard formal notation
- Enables AI LLMs to understand AISP semantics via specification reference
- Provides validation rules for AISP syntax checking
- Maintains consistency across all AISP blocks
- Supports future AISP specification updates

**Alternatives Considered**:

- Custom AISP syntax (rejected - breaks standardization, adds maintenance burden)
- Multiple AISP versions (rejected - adds complexity, breaks consistency)
- No specification reference (rejected - AI LLMs need formal semantics)

**Implementation**:

- AISP blocks include AISP v5.1 header: `𝔸5.1.complete@<date>`
- Slash command prompts reference AISP specification URL
- Validator checks AISP syntax against v5.1 specification
- Documentation references AISP specification for syntax rules

## Architecture

### Storage Architecture

```bash
.specfact/
└── projects/
    └── <bundle>/
        ├── contracts/          # Existing contract storage
        ├── reports/            # Existing report storage
        └── aisp/               # NEW: AISP proof artifact storage
            ├── proof-<req-id-1>.aisp.md
            ├── proof-<req-id-2>.aisp.md
            └── ...
```

### Generation Flow

1. **Import/Sync**: Bridge adapter (OpenSpec/Spec-Kit) imports requirements
2. **AISP Generation**: Adapter generates AISP blocks from requirement text and scenarios
3. **Storage**: Generated AISP blocks stored in `.specfact/projects/<bundle>/aisp/`
4. **Mapping**: Proof IDs mapped to requirement IDs in project bundle metadata
5. **Validation**: AISP blocks validated for syntax and binding consistency

### Consumption Flow

1. **Slash Command**: AI LLM invokes `/specfact.compile-aisp` or `/specfact.update-aisp`
2. **AISP Loading**: SpecFact loads AISP blocks from project bundle
3. **Clarification**: Vague/ambiguous elements flagged for clarification
4. **AI LLM Consumption**: AI LLM consumes AISP instead of markdown spec
5. **Implementation**: AI LLM follows AISP decision trees and invariants

### Integration Points

- **Bridge Adapters**: Generate AISP during import/sync operations
- **CLI Commands**: Validate and clarify AISP blocks (`validate --aisp`, `clarify`)
- **Slash Commands**: AI LLM consumption of AISP (`/specfact.compile-aisp`, `/specfact.update-aisp`)
- **Project Bundle**: AISP storage and mapping infrastructure
- **Validators**: AISP syntax and binding validation

## Trade-offs

### Trade-off 1: Internal Storage vs. Embedded Storage

**Chosen**: Internal storage in project bundles

**Benefits**:

- Tool-agnostic independence
- Developer-friendly (no formal notation exposure)
- Spec file integrity preserved

**Costs**:

- AISP blocks not visible in source spec files
- Requires SpecFact CLI to access AISP
- Additional storage layer

**Mitigation**: Slash commands provide easy AI LLM access, CLI commands provide developer access

### Trade-off 2: Automatic Generation vs. Manual Authoring

**Chosen**: Automatic generation via bridge adapters

**Benefits**:

- No manual AISP authoring required
- Consistent AISP generation across tools
- Automatic updates when specs change

**Costs**:

- Generation may miss some decision points
- Requires clarification workflow for ambiguous elements
- Generation logic complexity

**Mitigation**: Clarification command (`specfact clarify`) handles ambiguous elements, validation detects gaps

### Trade-off 3: Tool-Agnostic Models vs. Tool-Specific Models

**Chosen**: Tool-agnostic AISP models

**Benefits**:

- Works with any SDD tool format
- Future-proof for new tools
- Consistent AISP structure

**Costs**:

- Additional mapping layer between tool-specific and tool-agnostic
- May lose some tool-specific context
- Requires adapter logic for each tool

**Mitigation**: Bridge adapters handle tool-specific to tool-agnostic mapping, AISP focuses on decision trees (tool-agnostic)

## Risks and Mitigations

### Risk 1: AISP Generation Quality

**Risk**: Generated AISP blocks may miss decision points or encode incorrect logic.

**Mitigation**:

- Validation detects coverage gaps (requirements without proofs, orphaned proofs)
- Clarification command allows manual refinement
- Contract-to-AISP comparison flags deviations

### Risk 2: AISP Maintenance Overhead

**Risk**: AISP blocks may become stale when specs change.

**Mitigation**:

- `/specfact.update-aisp` slash command detects spec changes and updates AISP
- Validation reports stale AISP blocks
- Automatic regeneration during import/sync

### Risk 3: Developer Confusion

**Risk**: Developers may not understand AISP's role or how to use it.

**Mitigation**:

- AISP remains internal (developers work with markdown)
- Documentation explains AISP's role as clarification layer
- Slash commands handle AISP consumption automatically

## Success Criteria

- ✅ AISP blocks stored internally in project bundles (not in spec files)
- ✅ AISP blocks generated automatically from requirements via adapters
- ✅ AI LLMs consume AISP via slash commands instead of markdown
- ✅ AISP blocks achieve `Ambig < 0.02` (mathematical precision)
- ✅ Developers work with natural language specs (no AISP exposure)
- ✅ Validation detects coverage gaps and binding inconsistencies
- ✅ Clarification workflow handles vague/ambiguous elements

## Related Documentation

- [AISP v5.1 Specification](https://github.com/bar181/aisp-open-core/blob/main/AI_GUIDE.md)
- [proposal.md](./proposal.md) - Change proposal overview
- [tasks.md](./tasks.md) - Implementation tasks
- [specs/bridge-adapter/spec.md](./specs/bridge-adapter/spec.md) - Adapter requirements
- [specs/cli-output/spec.md](./specs/cli-output/spec.md) - CLI command requirements
- [specs/data-models/spec.md](./specs/data-models/spec.md) - Data model requirements
