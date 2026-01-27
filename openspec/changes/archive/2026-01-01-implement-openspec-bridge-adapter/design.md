# Technical Design: OpenSpec Bridge Adapter

## Context

This design implements Phase 1 (read-only sync) of the OpenSpec integration for SpecFact CLI. The bridge adapter enables SpecFact to validate extracted specs against OpenSpec's source-of-truth specifications, creating a complete brownfield modernization workflow.

## Goals

1. **Read-Only Sync**: Validate SpecFact extracted specs against OpenSpec source-of-truth
2. **Cross-Repository Support**: Support OpenSpec in different repository (specfact-cli-internal) from code being analyzed (specfact-cli)
3. **Alignment Reporting**: Generate reports showing SpecFact vs OpenSpec alignment
4. **Foundation for Future Phases**: Establish adapter pattern for Phase 2 (sidecar integration) and Phase 3 (bidirectional sync)

## Non-Goals

- Bidirectional sync (Phase 4, deferred to v1.0+)
- Sidecar integration (Phase 2, separate change)
- Change tracking write operations (Phase 4)

## Decisions

### Decision 1: Read-Only Sync First

**What**: Phase 1 implements read-only sync (OpenSpec → SpecFact validation) only.

**Why**:

- Validates integration approach before adding complexity
- Enables alignment reporting (identifies gaps)
- Foundation for future bidirectional sync
- Lower risk than bidirectional sync

**Alternatives Considered**:

- Start with bidirectional sync (rejected - too complex for initial phase)
- Start with sidecar integration (rejected - requires read-only sync first)

**Implementation**:

- Import methods only (no export)
- Alignment report generation
- No write operations to OpenSpec

### Decision 2: Cross-Repository Support

**What**: Bridge adapter supports `external_base_path` for cross-repository OpenSpec access.

**Why**:

- OpenSpec in `specfact-cli-internal` (private), code in `specfact-cli` (public)
- Maintains separation between public code and private planning
- Aligns with sidecar validation pattern
- General capability for all bridge adapters

**Alternatives Considered**:

- Require OpenSpec in same repo (rejected - doesn't meet privacy requirements)
- Separate adapter for cross-repo (rejected - unnecessary complexity)

**Implementation**:

- `BridgeConfig.external_base_path` field
- Path resolution checks external path first
- Detection logic supports cross-repo

### Decision 3: Parser-Based Approach

**What**: Use dedicated `OpenSpecParser` class for parsing OpenSpec format.

**Why**:

- OpenSpec uses markdown format (needs parsing)
- Separates parsing logic from sync logic
- Reusable for future phases
- Testable independently

**Alternatives Considered**:

- Inline parsing in sync methods (rejected - not reusable)
- Use external OpenSpec library (rejected - OpenSpec is file-based, no library)

**Implementation**:

- `OpenSpecParser` class with methods per artifact type
- Markdown parsing for project.md, specs/, changes/
- Structured return values (dicts)

### Decision 4: Alignment Report Generation

**What**: Generate alignment report comparing SpecFact features vs OpenSpec specs.

**Why**:

- Identifies gaps (OpenSpec specs not extracted by SpecFact)
- Validates extraction accuracy
- Provides actionable feedback
- Foundation for gap discovery

**Alternatives Considered**:

- No reporting (rejected - no validation feedback)
- Simple pass/fail (rejected - not actionable)

**Implementation**:

- Compare feature lists (SpecFact vs OpenSpec)
- Calculate coverage percentage
- Generate markdown report with findings

## Architecture

### Component Overview

```
BridgeConfig (extended)
├── AdapterType.OPENSPEC
├── preset_openspec()
└── external_base_path (cross-repo support)

BridgeProbe (extended)
├── _is_openspec_repo() (detection)
├── _detect_openspec() (capabilities)
└── detect() (routing)

OpenSpecParser (new)
├── parse_project_md()
├── parse_spec_md()
├── parse_change_proposal()
├── parse_change_spec_delta()
└── list_active_changes()

BridgeSync (extended)
├── _import_openspec_artifact() (read-only)
└── generate_alignment_report()

CLI Command (extended)
└── sync_bridge() (supports --adapter openspec)
```

### Data Flow

```
1. User runs: specfact sync bridge --adapter openspec --mode read-only

2. BridgeProbe.detect()
   ├── Checks bridge_config.external_base_path
   ├── Detects OpenSpec installation
   └── Returns ToolCapabilities

3. BridgeSync.import_artifact()
   ├── Routes to _import_openspec_artifact()
   └── Uses OpenSpecParser for parsing

4. OpenSpecParser.parse_*()
   ├── Parses project.md, specs/, changes/
   └── Returns structured dicts

5. BridgeSync.generate_alignment_report()
   ├── Compares SpecFact features vs OpenSpec specs
   ├── Identifies gaps
   └── Generates markdown report

6. Output: Alignment report with findings
```

### Cross-Repository Path Resolution

**Same-Repository** (default):

```
repo_path/
├── openspec/
│   ├── project.md
│   ├── specs/
│   └── changes/
└── src/
```

**Cross-Repository** (OpenSpec example):

```
# specfact-cli (code repo)
repo_path/
└── src/

# specfact-cli-internal (OpenSpec repo)
external_base_path/
└── openspec/
    ├── project.md
    ├── specs/
    └── changes/
```

**Path Resolution Logic**:

```python
if bridge_config.external_base_path:
    base_path = Path(bridge_config.external_base_path).resolve()
else:
    base_path = repo_path

openspec_dir = base_path / "openspec"
```

## Risks / Trade-offs

### Risk 1: OpenSpec Format Changes

**Risk**: OpenSpec is new (Sept 2025), format may evolve.

**Mitigation**:

- Version-pin parser expectations
- Handle missing fields gracefully
- Document format assumptions
- Test with current OpenSpec structure

### Risk 2: Cross-Repository Complexity

**Risk**: Cross-repo path resolution adds complexity.

**Mitigation**:

- Clear path resolution logic
- Comprehensive tests (same-repo and cross-repo)
- Document configuration examples
- Validate paths early

### Risk 3: Parsing Accuracy

**Risk**: Markdown parsing may miss edge cases.

**Mitigation**:

- Comprehensive test cases
- Handle missing files gracefully
- Validate parsed structure
- Report parsing errors clearly

## Open Questions

- Should we cache parsed OpenSpec specs? (deferred - Phase 1 is read-only)
- Should we support partial parsing (only active changes)? (deferred - Phase 1 parses all)
- Should we validate OpenSpec format? (deferred - assume valid OpenSpec)

## Implementation Notes

### File Structure

```
src/specfact_cli/
├── models/
│   └── bridge.py          # EXTEND: AdapterType, preset_openspec()
├── sync/
│   ├── bridge_probe.py    # EXTEND: OpenSpec detection
│   ├── bridge_sync.py     # EXTEND: OpenSpec import
│   └── openspec_parser.py # NEW: OpenSpec parsing
└── commands/
    └── sync.py            # EXTEND: OpenSpec adapter support
```

### Dependencies

**Required**:

- Change tracking data model (`add-change-tracking-datamodel`) - must be implemented first
- Existing bridge adapter architecture
- `SourceTracking` model

**Optional**:

- OpenSpec CLI (for validation, not required for parsing)

### Testing Strategy

1. **Unit Tests**: Each component tested independently
2. **Integration Tests**: End-to-end sync workflow
3. **Cross-Repo Tests**: Verify external path resolution
4. **Edge Cases**: Missing files, invalid format, empty specs

### Success Metrics

- ✅ Detection works (same-repo and cross-repo)
- ✅ Parsing works for all artifact types
- ✅ Alignment report generated correctly
- ✅ CLI command works
- ✅ Test coverage ≥80%
