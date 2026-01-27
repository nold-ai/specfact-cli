# Change: Add AISP Formal Clarification to Spec-Kit and OpenSpec Workflows

## Why

Current spec-driven development tools (Spec-Kit, OpenSpec, SpecFact) solve *structural* ambiguity through formatting discipline, but they don't eliminate **semantic ambiguity** when LLMs interpret specifications. AISP (AI Symbolic Programming) v5.1 provides a proof-carrying protocol that reduces AI interpretation variance from 40–65% to <2% by encoding decision trees and logical boundaries in a form that LLMs can verify deterministically.

This change establishes SpecFact as the **validation and clarification layer** by storing AISP formal specifications internally in project bundles (`.specfact/projects/<bundle>/aisp/`) as a tool-agnostic, AI-optimized representation. This approach:

- Keeps AISP as an internal representation, avoiding exposure of formal notation to developers
- Maintains SpecFact's independence from SDD tool formats (OpenSpec, Spec-Kit, etc.)
- Enables AI LLM to consume AISP specifications instead of ambiguous markdown specs
- Provides automatic translation/compilation from natural language specs to AISP via slash command prompts
- Establishes SpecFact as the clarification layer that enforces mathematical clarity under the hood

The integration follows the bridge adapter pattern (per project.md) and maintains complete backward compatibility by keeping AISP as an internal representation that doesn't affect existing spec files or workflows.

## What Changes

- **NEW**: Add AISP internal storage in project bundles
  - AISP proof artifacts stored in `.specfact/projects/<bundle>/aisp/` directory (internal to SpecFact)
  - Proof artifacts stored as separate files (e.g., `proof-<requirement-id>.aisp.md`) mapped to requirements
  - Each proof block includes unique proof id, input schema, decision tree, outcomes, and invariants
  - Reference AISP v5.1 specification from <https://github.com/bar181/aisp-open-core/blob/main/AI_GUIDE.md>
  - **No changes to existing spec files** - AISP remains internal representation

- **NEW**: Add AISP parser and data models to SpecFact CLI
  - New parser: `src/specfact_cli/parsers/aisp.py` for parsing AISP blocks from internal storage
  - New models: `src/specfact_cli/models/aisp.py` with `AispProofBlock`, `AispBinding`, `AispParseResult`
  - Validator: `src/specfact_cli/validators/aisp_schema.py` for syntax and binding validation
  - Storage strategy: AISP blocks stored in project bundle, mapped to requirements by ID

- **NEW**: Add automatic AISP generation from specs via adapters
  - OpenSpec adapter: Generate AISP blocks from OpenSpec requirements during import/sync
  - Spec-Kit adapter: Generate AISP blocks from Spec-Kit requirements during import/sync
  - Both adapters generate AISP internally without modifying source spec files
  - Generated AISP stored in `.specfact/projects/<bundle>/aisp/` for tool-agnostic access

- **NEW**: Add SpecFact CLI commands for AISP validation and clarification
  - `specfact validate --aisp`: Validates AISP blocks in project bundle, validates proof ids, syntax, and requirement bindings, reports coverage gaps
  - `specfact clarify requirement <requirement-id>`: Generates/updates AISP block from requirement, clarifies vague/ambiguous elements, stores in project bundle
  - `specfact validate --aisp --against-code`: Compares extracted contracts to AISP decision trees, flags deviations

- **NEW**: Add specfact slash command prompts for AI LLM consumption
  - `/specfact.compile-aisp`: Instructs AI LLM to first update internal AISP spec from available spec, clarify vague/ambiguous elements, then execute AISP spec instead of markdown spec
  - `/specfact.update-aisp`: Detects spec changes and updates corresponding AISP blocks in project bundle
  - Both commands use AISP v5.1 specification as reference for formal semantics
  - Commands enable AI LLM to consume mathematically precise AISP instead of ambiguous markdown

- **EXTEND**: Add AISP proof artifact examples and templates
  - Example AISP blocks for common patterns (auth, payment, state machines) in `resources/templates/aisp/`
  - Documentation for AISP generation and validation workflows
  - Integration examples showing AISP as internal representation layer

## Impact

- **Affected specs**: `bridge-adapter` (adapter hooks for AISP parsing), `cli-output` (new CLI commands), `data-models` (AISP data models)
- **Affected code**:
  - `src/specfact_cli/parsers/aisp.py` (new AISP parser)
  - `src/specfact_cli/models/aisp.py` (new AISP data models)
  - `src/specfact_cli/validators/aisp_schema.py` (new AISP validator)
  - `src/specfact_cli/adapters/openspec.py` (add AISP generation from OpenSpec requirements)
  - `src/specfact_cli/adapters/speckit.py` (add AISP generation from Spec-Kit requirements)
  - `src/specfact_cli/commands/validate.py` (add `--aisp` and `--aisp --against-code` flags)
  - `src/specfact_cli/commands/clarify.py` (new command for clarification workflow)
  - `src/specfact_cli/utils/bundle_loader.py` (add AISP storage in project bundle)
  - `resources/templates/slash-commands/` (slash command prompts for AI LLM)
  - `resources/templates/aisp/` (AISP block templates and examples)
  - `docs/guides/aisp-integration.md` (new documentation)
- **Integration points**:
  - OpenSpec adapter (AISP generation from requirements)
  - Spec-Kit adapter (AISP generation from requirements)
  - SpecFact validation (AISP-aware contract matching)
  - SpecFact CLI commands (validation and clarification workflows)
  - AI reasoning integration (slash commands for AISP compilation and consumption)
  - Project bundle storage (`.specfact/projects/<bundle>/aisp/` directory)


---

## Source Tracking

- **GitHub Issue**: #106
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/106>
- **Last Synced Status**: proposed
<!-- content_hash: c1a67e2c4e8710c3 -->