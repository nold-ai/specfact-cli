# Change Validation Report: add-template-driven-backlog-refinement

**Validation Date**: 2026-01-20 22:26:26 +0100  
**Change Proposal**: [proposal.md](./proposal.md)  
**Validation Method**: Production-readiness analysis for Day 1 DevOps team deployment  
**Validation Focus**: Completeness, production-grade features, integration points

## Executive Summary

- **Breaking Changes**: 0 detected (backward compatible design)
- **Critical Gaps**: 8 major production requirements missing
- **Dependent Files**: Multiple integration points need updates
- **Impact Level**: **HIGH** - Feature is incomplete for production deployment
- **Validation Result**: **FAIL** - Requires significant enhancements before release
- **User Decision**: **Extend Scope** - Add production-grade features

## Production Readiness Assessment

### ✅ Strengths

1. **Core Architecture**: CLI-first design with IDE AI copilot orchestration is correct
2. **Data Model**: `BacklogItem` provides unified representation with lossless preservation
3. **Template System**: Extensible design with persona/framework/provider support
4. **Testing**: Comprehensive test coverage (44 tests) with unit, integration, E2E
5. **Documentation**: Guide created with Jekyll frontmatter

### ❌ Critical Gaps for Production

#### 1. **Definition of Ready (DoR) Support** - MISSING

**Requirement**: Teams need "Definition of Ready" rules that are checked before an issue is ready to be added to a sprint or before work should start. DoR needs to be adjustable per repo (team-wide/project-wide setting).

**Current State**:

- DoR exists in `agile-scrum-workflows.md` documentation
- DoR validation exists in plan/import commands
- **NOT integrated into backlog refinement workflow**

**Impact**: **CRITICAL** - Teams cannot enforce DoR before sprint planning

**Required Changes**:

- Add DoR configuration model (`DefinitionOfReady` with rules, repo-level config)
- Add DoR validation step in `backlog refine` workflow
- Add `--check-dor` flag to `backlog refine` command
- Add DoR status display in refinement output
- Support repo-level DoR config files (`.specfact/dor.yaml` or similar)

#### 2. **Writeback Flag and Preview Mode** - INCOMPLETE

**Requirement**: Writeback to backlog should only happen after adding specific flag to avoid unexpected overwrite. Local preview should show how it will look like for review before updating backlog.

**Current State**:

- TODO comment: `# TODO: Update remote backlog with refined items`
- No `--write` or `--preview` flags
- No preview display of what will be written

**Impact**: **CRITICAL** - Cannot safely update backlogs without risk of accidental overwrite

**Required Changes**:

- Add `--preview` flag (default: preview mode, no writeback)
- Add `--write` flag (explicit opt-in for writeback)
- Implement preview display showing:
  - Original vs refined body diff
  - Fields that will be preserved (priority, assignee, due date, story points)
  - Fields that will be updated (title, body only)
- Implement writeback logic using adapter methods (when available)

#### 3. **Field Preservation** - NOT DOCUMENTED

**Requirement**: Additional fields except title/body should be preserved (not modified) when updating backlog. Support for priority, assignee, due date, story points will be added later.

**Current State**:

- `BacklogItem` has `provider_fields` for lossless preservation
- **No explicit preservation logic in writeback**
- **No documentation of field preservation policy**

**Impact**: **HIGH** - Risk of losing metadata (priority, assignee, story points) during updates

**Required Changes**:

- Document field preservation policy in proposal and design
- Implement writeback to only update `title` and `body_markdown`
- Preserve all other fields (`assignees`, `tags`, `state`, `priority`, `due_date`, `story_points`, etc.)
- Add validation to ensure provider_fields are preserved
- Add tests for field preservation

#### 4. **OpenSpec/Spec-Kit Integration** - ARCHITECTURAL DECISION NEEDED

**Requirement**: Integration into OpenSpec or spec-kit template derivation should add (or modify) respective comments with the change that is being cross-synced, but NOT the body itself. This is required to fully comply with backlog issue/story refinement and optional complementation by SDD formats (OpenSpec/spec-kit) without conflicting with core issue requirements in agile DevOps teams.

**Current State**:

- `sync_bridge` command updates issue body directly (`_update_issue_body`)
- `sync_bridge` can add comments (`change_proposal_comment` artifact)
- **No integration with backlog refine workflow**
- **No decision on comment-only vs body update**

**Impact**: **CRITICAL** - Architectural misalignment with agile DevOps practices

**Required Changes**:

- **Confirm architectural decision**: Refine issues using selected template, but OpenSpec/spec-kit integration should add/modify comments, NOT replace body
- Update `sync_bridge` integration to use comment-only updates for refined backlog items
- Add `--openspec-comment` flag to add OpenSpec change proposal as comment
- Preserve original body, add structured comment with OpenSpec link/reference
- Update design.md and proposal.md with this decision

#### 5. **Slash Prompt Commands** - MISSING

**Requirement**: Add specific slash prompt commands that will be executed as entry point to start the refinement in AI IDE copilot session. Templates are in `resources/prompts/` and need to be structured similar to existing prompts and integrated into `ide_setup.py`.

**Current State**:

- `ide_setup.py` has `SPECFACT_COMMANDS` list
- `resources/prompts/` has existing prompt templates
- **No `specfact.backlog-refine.md` prompt template**
- **Not added to `SPECFACT_COMMANDS` list**

**Impact**: **HIGH** - Teams cannot use IDE AI copilot slash commands for refinement

**Required Changes**:

- Create `resources/prompts/specfact.backlog-refine.md` with YAML frontmatter
- Add `specfact.backlog-refine` to `SPECFACT_COMMANDS` in `ide_setup.py`
- Template should include:
  - Description: "Refine backlog items using template-driven AI assistance"
  - Placeholder for adapter, filters, template selection
  - Instructions for IDE AI copilot to execute `specfact backlog refine` command
- Update `ide_setup.py` to copy template to IDE-specific locations

#### 6. **Adapter Search Methods** - NOT IMPLEMENTED

**Requirement**: Full support for existing backlogs (ADO, GitHub) with extensibility for new adapters (Jira, Linear, SAFe, etc.).

**Current State**:

- `_fetch_backlog_items` has placeholders:
  - `# Note: Actual fetching will be implemented when adapter.search_issues() is available`
  - `# Note: Actual fetching will be implemented when adapter.list_work_items() is available`
- GitHub adapter has `search_issues()` method (needs verification)
- ADO adapter needs `list_work_items()` method

**Impact**: **CRITICAL** - Cannot fetch backlog items, feature is non-functional

**Required Changes**:

- Verify GitHub adapter `search_issues()` method exists and works
- Implement ADO adapter `list_work_items()` method
- Update `_fetch_backlog_items` to use adapter methods
- Add error handling for adapter failures
- Add tests for adapter search/list methods

#### 7. **Filter Implementation** - INCOMPLETE

**Requirement**: Filter support for common criteria used in agile DevOps teams (scrum, kanban, SAFe, etc.).

**Current State**:

- Filter options designed but not fully implemented
- `--search` option exists (generic, provider-specific syntax)
- Filter options (`--labels`, `--state`, `--assignee`, `--iteration`, `--sprint`, `--release`, `--persona`, `--framework`) are in design but not in command signature
- `_fetch_backlog_items` doesn't support filters

**Impact**: **HIGH** - Cannot filter backlog items effectively

**Required Changes**:

- Add all filter options to `backlog refine` command signature
- Implement post-fetch filtering for common fields (tags, state, assignees)
- Implement provider API filtering when available (GitHub search, ADO query)
- Combine multiple filters with AND logic
- Add filter validation and error messages

#### 8. **CLI Integration** - NEEDS VERIFICATION

**Requirement**: Ensure enhancement adjusts/integrates with existing specfact sync/backlog CLI commands and CLI help seamlessly.

**Current State**:

- `backlog refine` command exists in `backlog_commands.py`
- `sync_bridge` command exists in `sync.py`
- **No explicit integration between `backlog refine` and `sync_bridge`**
- **No verification of CLI help integration**

**Impact**: **MEDIUM** - May confuse users if commands don't work together

**Required Changes**:

- Verify `specfact backlog --help` shows `refine` command
- Verify `specfact sync --help` mentions backlog refinement
- Add cross-references in command help text
- Test command chaining: `backlog refine` → `sync bridge`
- Update main CLI help to mention backlog refinement

## Format Validation

### proposal.md Format

- **Title format**: ✅ Correct (`# Change: Template-Driven Backlog Refinement`)
- **Required sections**: ✅ All present (`## Why`, `## What Changes`, `## Impact`)
- **"What Changes" format**: ✅ Correct (uses NEW/EXTEND markers)
- **"Impact" format**: ✅ Correct (lists Affected specs, Affected code, Integration points)

### tasks.md Format

- **Section headers**: ✅ Correct (hierarchical numbered format)
- **Task format**: ✅ Correct (`- [ ] 1.1 [Description]`)
- **Sub-task format**: ✅ Correct (indented, numbered)

**Format Issues Found**: 0  
**Format Issues Fixed**: 0

## Breaking Changes Detected

**Count**: 0

All changes are backward compatible:

- New models are additive
- New commands don't conflict with existing ones
- Optional parameters with defaults
- Existing templates continue to work

## Dependencies Affected

### Critical Updates Required

1. **`src/specfact_cli/commands/backlog_commands.py`**:
   - Add DoR validation step
   - Add `--preview`/`--write` flags
   - Add filter options
   - Implement writeback logic
   - Add field preservation logic

2. **`src/specfact_cli/adapters/github.py`**:
   - Verify `search_issues()` method exists
   - Add comment-only update method for OpenSpec integration

3. **`src/specfact_cli/adapters/ado.py`**:
   - Implement `list_work_items()` method
   - Add comment-only update method for OpenSpec integration

4. **`src/specfact_cli/backlog/converter.py`**:
   - Extract sprint/release from provider data (partially done, needs completion)

5. **`src/specfact_cli/utils/ide_setup.py`**:
   - Add `specfact.backlog-refine` to `SPECFACT_COMMANDS`
   - Ensure template copying works

6. **`resources/prompts/specfact.backlog-refine.md`**:
   - Create new prompt template (doesn't exist)

7. **`docs/guides/backlog-refinement.md`**:
   - Add DoR section
   - Add preview/write flags documentation
   - Add field preservation policy
   - Add OpenSpec integration section

8. **`docs/reference/commands.md`**:
   - Update `backlog refine` command with all new flags
   - Add DoR, preview/write, filters documentation

### Recommended Updates

1. **`src/specfact_cli/commands/sync.py`**:
   - Add integration point for backlog refinement
   - Update `sync_bridge` to support comment-only updates for refined items

2. **`docs/index.md`**:
   - Verify backlog refinement guide is linked
   - Add DoR, preview/write features to feature list

3. **`docs/_layouts/default.html`**:
   - Verify backlog refinement is in sidebar navigation

## Impact Assessment

### Code Impact

- **New Models**: `DefinitionOfReady` (DoR configuration)
- **Modified Commands**: `backlog refine` (major enhancements)
- **Modified Adapters**: GitHub, ADO (search/list methods, comment-only updates)
- **New Utilities**: DoR validator, field preservation logic
- **New Prompts**: `specfact.backlog-refine.md`

### Test Impact

- **New Tests Required**:
  - DoR validation tests (unit, integration)
  - Preview/write flag tests
  - Field preservation tests
  - Filter combination tests
  - Adapter search/list method tests
  - OpenSpec comment integration tests

- **Estimated Additional Tests**: 15-20 tests

### Documentation Impact

- **New Sections**: DoR configuration, preview/write workflow, field preservation policy, OpenSpec integration
- **Updated Guides**: backlog-refinement.md, commands.md
- **New Prompt Template**: specfact.backlog-refine.md

### Release Impact

- **Version**: **Minor** (0.X.Y → 0.X+1.0) - New feature with enhancements
- **Breaking Changes**: None
- **Migration Required**: None (backward compatible)

## User Decision

**Decision**: **Extend Scope** - Add production-grade features before release

**Rationale**:

- Feature is incomplete for Day 1 DevOps team deployment
- 8 critical gaps identified that would prevent production use
- All gaps are addressable within current architecture
- No breaking changes required

**Next Steps**:

1. **Immediate (Before Release)**:
   - [ ] Add DoR support (configuration, validation, repo-level config)
   - [ ] Add preview/write flags with preview display
   - [ ] Implement field preservation policy
   - [ ] Confirm and implement OpenSpec comment-only integration
   - [ ] Create slash prompt command template
   - [ ] Implement adapter search/list methods
   - [ ] Complete filter implementation
   - [ ] Verify CLI integration

2. **Documentation**:
   - [ ] Update proposal.md with new requirements
   - [ ] Update design.md with DoR, preview/write, field preservation
   - [ ] Update tasks.md with new implementation tasks
   - [ ] Update backlog-refinement.md guide
   - [ ] Update commands.md reference

3. **Testing**:
   - [ ] Add DoR validation tests
   - [ ] Add preview/write tests
   - [ ] Add field preservation tests
   - [ ] Add filter combination tests
   - [ ] Add adapter search/list tests
   - [ ] Add OpenSpec integration tests

4. **Validation**:
   - [ ] Re-run OpenSpec validation after updates
   - [ ] Re-validate production readiness
   - [ ] Verify all gaps are addressed

## OpenSpec Validation

- **Status**: **PENDING** - Will run after scope extension
- **Validation Command**: `openspec validate add-template-driven-backlog-refinement --strict`
- **Issues Found**: 0 (format validation passed)
- **Issues Fixed**: 0
- **Re-validated**: No (pending scope extension)

## Validation Artifacts

- **Temporary workspace**: Not used (dry-run analysis)
- **Interface scaffolds**: Not created (no breaking changes)
- **Dependency graph**: Analyzed via codebase search
- **Production requirements**: Documented in this report

## Recommendations

### Priority 1 (Blocking Release)

1. **DoR Support**: Essential for agile DevOps teams
2. **Preview/Write Flags**: Essential for safe backlog updates
3. **Adapter Search Methods**: Essential for feature to work
4. **OpenSpec Integration Decision**: Essential for architectural alignment

### Priority 2 (High Value)

1. **Field Preservation**: Prevents data loss
2. **Filter Implementation**: Improves usability
3. **Slash Prompt Commands**: Improves IDE integration

### Priority 3 (Nice to Have)

1. **CLI Integration Verification**: Improves user experience

## Conflict Analysis with Other Pending Changes

### Overlaps and Conflicts Identified

#### 1. **Adapter Search Methods** - OVERLAP with `add-backlog-dependency-analysis-and-commands`

**Conflict**:

- **This change** requires: `search_issues()` and `list_work_items()` methods
- **Other change** (`add-backlog-dependency-analysis-and-commands`) requires: `fetch_all_issues()` and `fetch_relationships()` methods

**Resolution**:

- **Coordinate method naming**: Use consistent method names across both changes
- **Recommendation**:
  - `fetch_all_issues()` can serve both purposes (bulk fetching for dependency analysis, filtered fetching for refinement)
  - `search_issues(query, filters)` can be a wrapper around `fetch_all_issues()` with filtering
  - `list_work_items(query, filters)` can be a wrapper around `fetch_all_issues()` with filtering
  - **Action**: Update this change to use `fetch_all_issues()` when available, or coordinate with other change to ensure both methods exist

**Impact**: **MEDIUM** - Requires coordination but no breaking changes

#### 2. **BacklogAdapter Interface** - OVERLAP with `add-generic-backlog-abstraction`

**Conflict**:

- **This change** uses: `BacklogAdapterMixin` (existing)
- **Other change** (`add-generic-backlog-abstraction`) creates: New `BacklogAdapter` abstract base interface

**Resolution**:

- **Recommendation**:
  - Wait for `add-generic-backlog-abstraction` to be implemented first (it refactors adapters)
  - Then implement this change's adapter methods on the new `BacklogAdapter` interface
  - **Action**: Update this change to note dependency on `add-generic-backlog-abstraction` completion

**Impact**: **HIGH** - This change should be implemented AFTER `add-generic-backlog-abstraction` to avoid refactoring conflicts

#### 3. **BacklogFilters** - OVERLAP with `add-generic-backlog-abstraction`

**Conflict**:

- **This change** requires: Filter options (`--labels`, `--state`, `--assignee`, etc.)
- **Other change** (`add-generic-backlog-abstraction`) introduces: `BacklogFilters` dataclass

**Resolution**:

- **Recommendation**:
  - Use the `BacklogFilters` dataclass from `add-generic-backlog-abstraction` instead of creating new filter logic
  - **Action**: ✅ Updated this change to use `BacklogFilters` dataclass from `add-generic-backlog-abstraction`
- **Status**: ✅ Resolved - This change will use `BacklogFilters` dataclass for filter implementation

**Impact**: **LOW** - Can reuse existing dataclass, reduces duplication

#### 4. **BacklogItem Model** - POTENTIAL CONFLICT with `add-backlog-dependency-analysis-and-commands`

**Conflict**:

- **This change** uses: `BacklogItem` model in `src/specfact_cli/models/backlog_item.py`
- **Other change** (`add-backlog-dependency-analysis-and-commands`) creates: New `BacklogItem` dataclass in `src/specfact_cli/backlog/graph/models.py`

**Resolution**:

- **Recommendation**:
  - **CRITICAL**: These are DIFFERENT models with DIFFERENT purposes:
    - This change: `BacklogItem` = Unified domain model for refinement (title, body, state, metadata)
    - Other change: `BacklogItem` = Graph node model for dependency analysis (id, key, type, parent_id, dependencies)
  - **Action**:
    - **RESOLVED**: `add-backlog-dependency-analysis-and-commands` will use `GraphBacklogItem` name OR extend this change's `BacklogItem` model
    - **Decision**: This change's `BacklogItem` is the base domain model; graph model extends it or uses different name
    - **Status**: ✅ Updated both change proposals with naming decision

**Impact**: **CRITICAL** - Model name collision must be resolved before implementation

#### 5. **Bundle Mapping** - ALIGNMENT with `add-bundle-mapping-strategy`

**Alignment**:

- **This change** mentions: `--auto-bundle` flag (already exists in proposal)
- **Other change** (`add-bundle-mapping-strategy`) extends: `--auto-bundle` flag for `backlog refine` command

**Resolution**:

- **Recommendation**:
  - Use the `BundleMapper` from `add-bundle-mapping-strategy` when implementing `--auto-bundle` in this change
  - **Action**: ✅ Updated this change to use `BundleMapper` from `add-bundle-mapping-strategy`
- **Status**: ✅ Resolved - This change will use `BundleMapper` for `--auto-bundle` flag

**Impact**: **LOW** - Good alignment, can reuse existing bundle mapping

#### 6. **SourceTracking Extensions** - POTENTIAL OVERLAP

**Conflict**:

- **This change** extends: `SourceTracking` with refinement metadata (`template_id`, `refinement_confidence`, etc.)
- **Other change** (`add-bundle-mapping-strategy`) extends: `SourceTracking` with mapping metadata (`bundle_id`, `mapping_confidence`, etc.)

**Resolution**:

- **Recommendation**:
  - Both extensions are additive and non-conflicting
  - **Action**: Ensure both changes use optional fields, no conflicts expected

**Impact**: **LOW** - Both are additive, no conflicts

### Implementation Order Recommendation

**Recommended Sequence**:

1. **First**: `add-generic-backlog-abstraction` (establishes adapter interface)
2. **Second**: `add-bundle-mapping-strategy` (establishes bundle mapping)
3. **Third**: `add-template-driven-backlog-refinement` (this change - uses adapter interface and bundle mapping)
4. **Fourth**: `add-backlog-dependency-analysis-and-commands` (uses adapter interface, may conflict with BacklogItem model name)

**Rationale**:

- Adapter abstraction must be established first
- Bundle mapping is independent and can be done in parallel
- This change (refinement) depends on adapter interface
- Dependency analysis can be done after refinement, but model name conflict must be resolved

### Coordination Actions Required

1. **Model Name Resolution**:
   - [x] ✅ **RESOLVED**: Updated `add-backlog-dependency-analysis-and-commands` to use `GraphBacklogItem` name OR extend this change's `BacklogItem`
   - [x] ✅ **RESOLVED**: Documented decision in both change proposals

2. **Adapter Method Coordination**:
   - [x] ✅ **RESOLVED**: This change's `search_issues()` and `list_work_items()` are wrapper methods around `fetch_all_issues()`
   - [x] ✅ **RESOLVED**: Updated both change proposals with method coordination

3. **Filter Reuse**:
   - [x] ✅ **RESOLVED**: This change will use `BacklogFilters` dataclass from `add-generic-backlog-abstraction`
   - [x] ✅ **RESOLVED**: Updated this change to document filter reuse

4. **Bundle Mapping Integration**:
   - [x] ✅ **RESOLVED**: This change will use `BundleMapper` from `add-bundle-mapping-strategy`
   - [x] ✅ **RESOLVED**: Updated both change proposals with bundle mapping integration

## Conflict Resolution Summary

### ✅ Resolved Conflicts

1. **BacklogItem Model Naming** - ✅ **RESOLVED**
   - **Decision**: This change's `BacklogItem` is the base domain model
   - **Action**: Updated `add-backlog-dependency-analysis-and-commands` to use `GraphBacklogItem` name or extend this model
   - **Status**: Both change proposals updated with naming decision

2. **Adapter Method Naming** - ✅ **RESOLVED**
   - **Decision**: `search_issues()` and `list_work_items()` are wrapper methods around `fetch_all_issues()`
   - **Action**: Updated both change proposals with method coordination
   - **Status**: Implementation pattern documented in both proposals

3. **BacklogFilters Reuse** - ✅ **RESOLVED**
   - **Decision**: This change will use `BacklogFilters` dataclass from `add-generic-backlog-abstraction`
   - **Action**: Updated this change to document filter reuse
   - **Status**: Filter implementation will use existing dataclass

4. **Bundle Mapping Integration** - ✅ **RESOLVED**
   - **Decision**: This change will use `BundleMapper` from `add-bundle-mapping-strategy`
   - **Action**: Updated both change proposals with bundle mapping integration
   - **Status**: `--auto-bundle` flag will use existing `BundleMapper`

### 📋 Implementation Dependencies

**Recommended Implementation Order**:

1. ✅ **First**: `add-generic-backlog-abstraction` (establishes adapter interface and `BacklogFilters`)
2. ✅ **Second**: `add-bundle-mapping-strategy` (establishes `BundleMapper`)
3. ✅ **Third**: `add-template-driven-backlog-refinement` (this change - uses adapter interface and bundle mapping)
4. ⏳ **Fourth**: `add-backlog-dependency-analysis-and-commands` (uses adapter interface, extends `BacklogItem`)

**Status**: All dependencies documented in change proposals

## Conclusion

The change proposal provides a solid foundation for template-driven backlog refinement, but requires significant enhancements before it's production-ready for Day 1 DevOps team deployment. The 8 critical gaps identified must be addressed to ensure teams can safely and effectively use the feature without breaking their existing backlog workflows.

**Critical Finding**: This change had **model name conflicts** and **implementation dependencies** on other pending changes. **All conflicts have been resolved** through coordination and documentation updates.

**Recommendation**:

1. **Resolve conflicts** with other pending changes (especially `BacklogItem` model name)
2. **Extend scope** to include all production-grade features
3. **Coordinate implementation order** with other backlog-related changes
4. **Re-validate** after conflict resolution and scope extension

---

**Validation Completed**: 2026-01-20 22:26:26 +0100  
**Next Action**:

1. Resolve conflicts with other pending changes
2. Extend change proposal scope and implement production-grade features
3. Coordinate implementation order with other backlog-related changes
