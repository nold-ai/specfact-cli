# Change Validation Report: openspec-01-intent-trace

**Validation Date**: 2026-03-05
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Dry-run simulation — codebase interface analysis + temporary workspace
**Source Plan**: `specfact-cli-internal/docs/internal/implementation/2026-03-05-CLAUDE-RESEARCH-INTENT-DRIVEN-DEVELOPMENT.md`

## Executive Summary

- Breaking Changes: 0 detected
- Dependent Files: 3 files affected (additive, non-breaking)
- Impact Level: Low-Medium (extends existing adapter with optional new capability)
- Validation Result: **Pass**
- User Decision: N/A
- Implementation Constraint Identified: 1 (beartype type-annotation — implementation note, not a blocker)

## Breaking Changes Detected

None. All interface extensions are additive and optional:
- `parse_change_proposal()` returns `dict[str, Any]` — adding optional `"intent_trace"` key is non-breaking
- `--import-intent` CLI flag has no default effect (opt-in)
- New files (`intent_trace_validator.py`, `intent-trace.schema.json`) have no existing callers

## Implementation Constraint (Non-Breaking)

**Constraint**: `_parse_proposal_content()` at `openspec_parser.py:335` has type annotation `dict[str, str]` (return type). If intent trace data (a nested dict) were added here, `@beartype` would raise a type error.

**Required implementation approach**: Intent trace extraction MUST be done in `parse_change_proposal()` (returns `dict[str, Any]`) by:
1. Calling `_parse_proposal_content(content)` as usual → returns `dict[str, str]`
2. Separately extracting the YAML fenced block under `## Intent Trace` from `content`
3. Parsing with `yaml.safe_load()` and assigning to `result["intent_trace"]`
4. `parse_change_proposal()` return dict is `dict[str, Any]` — no type violation

The task at step 5.2 ("Add `## Intent Trace` section parser") should be executed in `parse_change_proposal()`, not in `_parse_proposal_content()`. This is an implementation detail — recommend adding a note to `tasks.md`.

## Dependencies Affected

### Critical (hard blockers — must land before `--import-intent` write path)

| Dependency | Issue | Status |
|---|---|---|
| `requirements-01-data-model` | [#238](https://github.com/nold-ai/specfact-cli/issues/238) | PENDING (Wave 5) |
| `requirements-02-module-commands` | [#239](https://github.com/nold-ai/specfact-cli/issues/239) | PENDING (Wave 5/6) |

Note: The validation/parsing components (JSON Schema, `validate_intent_trace()`, parser extension) do NOT require requirements-01/02. Only the `--import-intent` write path (creating `.req.yaml` files) requires them. This means parsing and validation can be implemented ahead of Wave 5.

### Recommended Updates (affected, not breaking)

| File | Reason | Update Type |
|---|---|---|
| `src/specfact_cli/adapters/openspec_parser.py` | Extend `parse_change_proposal()` with intent trace extraction | Additive |
| `src/specfact_cli/adapters/openspec.py` | Extend `_import_change_proposal()` to pass intent trace to bundle; add `--import-intent` path | Additive |
| `src/specfact_cli/validators/change_proposal_integration.py` | May need to call `validate_intent_trace()` when strict mode enabled | Additive |

## Impact Assessment

- **Code Impact**: Low — 2 existing files extended (additive only), 2 new files created
- **Test Impact**: Low — new test files only; no existing test modifications required
- **Documentation Impact**: Medium — `docs/adapters/openspec.md` and `docs/guides/openspec-journey.md` need updates
- **Release Impact**: Minor version bump (new features, no breaking changes)

## Format Validation

- **proposal.md Format**: Pass
  - `# Change:` title ✓
  - `## Why`, `## What Changes`, `## Capabilities`, `## Impact` sections ✓
  - NEW/EXTEND markers ✓
  - Capabilities linked to spec folders ✓
  - Source Tracking section ✓
- **tasks.md Format**: Pass
  - Hierarchical `## 1.`…`## 10.` structure ✓
  - Task 1 = git worktree creation ✓
  - Task 10 = PR creation (last) ✓
  - Post-merge cleanup section ✓
  - TDD / SDD order section at top ✓
  - Tests before implementation (Tasks 2-3 tests before Tasks 4-5 implementation) ✓
  - `TDD_EVIDENCE.md` recording tasks ✓
  - Quality gate tasks ✓
  - Documentation task included ✓
  - Version and changelog task ✓
  - GitHub issue creation task ✓
  - Module signing verification task: not included — this change has no module-package.yaml changes; acceptable
- **specs Format**: Pass
  - `####` for scenario headers ✓
  - `## ADDED Requirements` / `## MODIFIED Requirements` delta format ✓
  - G/W/T format with THEN/AND ✓
  - Every requirement has ≥1 scenario ✓
- **Config.yaml Compliance**: Pass

## OpenSpec Validation

- **Status**: Pass
- **Command**: `openspec validate openspec-01-intent-trace --strict`
- **Output**: `Change 'openspec-01-intent-trace' is valid`
- **Issues Found/Fixed**: 0

## Dependency Phasing Note

Unlike ai-integration-04, this change has **two separable implementation phases**:

1. **Phase A (can land with Wave 5/6)**: JSON Schema definition, `validate_intent_trace()`, parser extension to extract the intent trace block, `openspec validate --strict` hook. No dependency on requirements-01/02.
2. **Phase B (requires Wave 5 complete)**: `--import-intent` flag and `.req.yaml` artifact writer. Requires `BusinessOutcome`/`BusinessRule` Pydantic models.

Tasks 2-4 can proceed as soon as the worktree is created. Task 5.3 (`--import-intent` flag) should wait for requirements-01 (#238).

## Ownership Authority

- **Intent trace schema** (`openspec/schemas/intent-trace.schema.json`): owned by this change; aligns with `requirements-01-data-model` field definitions (no conflict — requirements-01 owns the Pydantic model, this change owns the JSON Schema)
- **`parse_change_proposal()` return dict** (`openspec_parser.py`): existing authority is `openspec_parser.py` itself; this change adds the `"intent_trace"` key — no conflict
- **`--import-intent` write path** in `openspec.py`: this change is authoritative; no other pending change touches this code path
