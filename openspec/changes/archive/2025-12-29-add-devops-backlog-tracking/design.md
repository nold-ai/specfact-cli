# Technical Design: DevOps Backlog Tracking Integration

## Context

This design implements **export-only sync** from OpenSpec change proposals to DevOps backlog tools (GitHub Issues, ADO Work Items, Linear Issues, Jira Issues) using the existing bridge adapter architecture. This enables teams to track OpenSpec changes in their existing project management tools, maintaining alignment between specifications and project planning.

**Architecture Alignment**: This uses the existing `bridge_sync.py` framework and `BridgeAdapter` interface, not a separate DevOps sync framework. All DevOps adapters (GitHub, ADO, Linear, Jira) implement the standard `BridgeAdapter` interface and use `BridgeSync` for orchestration.

**Relationship to Other DevOps Capabilities**: This is one of three planned DevOps adapter capabilities:

1. **Import** (future): Issues → Specs (DevOps → SpecFact) - `mode: import-annotation`
2. **Annotation** (future): SpecFact findings → Issue comments (SpecFact → DevOps) - `mode: import-annotation`
3. **Export** (this proposal): Change proposals → Issues (OpenSpec → DevOps) - `mode: export-only`

## Goals

1. **Export-Only Sync**: Create DevOps issues from OpenSpec change proposals
2. **Status Tracking**: Update issue status when changes are applied or deprecated
3. **GitHub First**: Start with GitHub Issues, architecture supports other tools
4. **Bridge Adapter Pattern**: Use existing bridge adapter architecture for consistency
5. **Foundation for Bidirectional**: Design supports future bidirectional sync

## Non-Goals

- Bidirectional sync (DevOps → OpenSpec) - deferred to future phase
- Issue import (DevOps → SpecFact) - separate capability (`mode: import-annotation`)
- Issue annotation (SpecFact findings → DevOps comments) - separate capability (`mode: import-annotation`)
- Separate DevOps sync framework - uses existing `bridge_sync.py`

## Decisions

### Decision 1: Export-Only Sync First

**What**: Phase 1 implements export-only sync (OpenSpec → DevOps) only.

**Why**:

- Simpler to implement and validate
- Meets immediate need (track OpenSpec changes in backlog)
- Establishes foundation for bidirectional sync
- Lower risk than bidirectional sync
- Aligns with existing bridge adapter architecture

**Alternatives Considered**:

- Start with bidirectional sync (rejected - too complex for initial phase)
- Manual issue creation only (rejected - doesn't meet automation need)
- Separate DevOps sync framework (rejected - violates bridge adapter pattern)

**Implementation**:

- Use existing `bridge_sync.py` with `--mode export-only`
- `GitHubAdapter.export_artifact()` creates/updates issues
- No import from DevOps to OpenSpec (deferred to future)

### Decision 2: GitHub First, Extensible Architecture

**What**: Start with GitHub Issues, but design supports ADO, Linear, Jira.

**Why**:

- GitHub is most common DevOps tool
- Validates approach before adding complexity
- Extensible architecture via bridge adapters
- Other tools can reuse same pattern

**Alternatives Considered**:

- Support all tools simultaneously (rejected - too complex)
- Generic DevOps API (rejected - each tool has unique API)

**Implementation**:

- `GitHubAdapter` implements `BridgeAdapter` interface
- Uses existing `BridgeSync` framework for orchestration
- Registered via `AdapterRegistry` pattern
- Future adapters (ADO, Linear, Jira) follow same pattern

### Decision 3: Status Mapping Strategy

**What**: Map OpenSpec change status to DevOps issue state.

**Why**:

- Keeps issues in sync with change status
- Provides clear project status visibility
- Aligns with DevOps workflow expectations

**Mapping**:

- `proposed` → open issue
- `in-progress` → open issue (with label/comment)
- `applied` → closed issue (with resolution comment)
- `deprecated` → closed issue (with deprecation comment)
- `discarded` → closed issue (with discard comment)

**Alternatives Considered**:

- Keep all issues open (rejected - doesn't reflect status)
- Use labels only (rejected - less visible than state)

### Decision 4: Content Sanitization Strategy

**What**: Support conditional sanitization of proposal content for public issues.

**Why**:

- **Breaking Changes Communication**: Data model changes and similar breaking changes need early communication before PRs
- **OSS Collaboration**: Public issues needed for contributors/watchers/users to track progress
- **Strategic Protection**: Internal competitive analysis and market positioning should not be disclosed
- **User Choice**: Users should control whether to sanitize or not

**Conditional Sanitization Logic**:

1. **Auto-Detect Repo Setup**:
   - If code and planning are in **same repo**: Sanitization optional (user choice)
   - If code and planning are in **different repos**: Sanitization recommended (default: yes)

2. **User Choice**:
   - `--sanitize`: Force sanitization (removes competitive analysis, internal strategy)
   - `--no-sanitize`: Skip sanitization (use proposal content as-is)
   - Default: Auto-detect based on repo setup

3. **Sanitization Rules**:
   - **Remove**: Competitive analysis, market positioning, implementation details, effort estimates, technical architecture
   - **Keep**: High-level feature description, user-facing use cases, acceptance criteria, external links

**AI-Assisted Sanitization**:

- Slash command (`/specfact-cli/sync-backlog`) provides interactive experience
- AI rewrites content when sanitization is requested
- User can review and approve sanitized content before issue creation

**Alternatives Considered**:

- Always sanitize (rejected - users may want full disclosure in same-repo setup)
- Never sanitize (rejected - exposes internal strategy in public repos)
- Manual sanitization only (rejected - too much work, error-prone)

**Implementation**:

- Status mapping in adapter
- Update issue state via API
- Add comments explaining status change

### Decision 4: Multi-Repository Source Tracking Integration

**What**: Store DevOps issue IDs in `ChangeProposal.source_tracking` as a **list of entries** (one per repository).

**Why**:

- **Cross-Repository Workflows**: Support tracking issues in multiple repositories (internal + public)
- **Independent Updates**: Update issues per repository independently based on `source_repo` match
- **Sanitization Tracking**: Track which issues are sanitized vs. unsanitized per repository
- **Future Extensibility**: Supports multiple DevOps tools per change (future enhancement)

**Alternatives Considered**:

- Single `source_tracking` entry (rejected - cannot track multiple repositories)
- Separate tracking table (rejected - adds complexity)
- Store in change proposal metadata (rejected - not standardized)

**Implementation**:

- `source_tracking` is a **list** of entries, each containing:
  - `source_id`: Issue number (e.g., "63")
  - `source_url`: Issue URL (e.g., `<https://github.com/nold-ai/specfact-cli/issues/63>`)
  - `source_type`: Tool type (e.g., "github")
  - `source_repo`: Repository identifier (e.g., "nold-ai/specfact-cli-internal", "nold-ai/specfact-cli")
  - `source_metadata`: Repository-specific metadata:
    - `content_hash`: Content hash for change detection (per repository)
    - `last_synced_status`: Last synced status (per repository)
    - `sanitized`: Boolean flag indicating if content was sanitized (per repository)
    - `repo_owner`, `repo_name`, `issue_number`, `issue_url`, `last_updated`
- **Repository Matching**: System matches entries by `source_repo` to `target_repo` (e.g., "nold-ai/specfact-cli")
- **Independent Updates**: Each repository's issue can be updated independently
- **Markdown Format**: Source Tracking section in `proposal.md` includes repository identifier for each entry:

  ```markdown
  ---

  ## Source Tracking

  ### Repository: nold-ai/specfact-cli

  - **GitHub Issue**: #63
  - **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/63>
  - **Last Synced Status**: proposed
  - **Sanitized**: true
  ```

### Decision 5: Use Existing Bridge Sync Framework

**What**: Use existing `bridge_sync.py` instead of creating separate `devops_sync.py`.

**Why**:

- Maintains architectural consistency
- Reuses proven sync orchestration logic
- Reduces code duplication
- Aligns with bridge adapter pattern

**Alternatives Considered**:

- Create separate `devops_sync.py` (rejected - violates DRY principle, creates inconsistency)
- Extend `bridge_sync.py` (accepted - maintains single source of truth)

**Implementation**:

- Extend `BridgeSync` to support `export-only` mode
- Route to `GitHubAdapter.export_artifact()` via adapter registry
- Reuse existing sync result reporting and error handling

### Decision 6: Interactive Change Selection and Per-Change Sanitization

**What**: Support interactive selection of which changes to export and per-change sanitization preferences.

**Why**:

- Users may want to export only specific proposals (not all)
- Different proposals may have different sanitization needs
- Provides fine-grained control over what gets exposed publicly
- Enables selective backlog management

**Workflow**:

1. **Interactive Selection** (slash command only):
   - List available change proposals with status and existing issues
   - User selects which proposals to export (comma-separated numbers, 'all', 'none')
   - For each selected proposal, prompt for sanitization preference (y/n/auto)

2. **Per-Change Sanitization**:
   - Each proposal can be sanitized independently
   - User choice takes precedence over auto-detection
   - Allows mixed export (some sanitized, some not)

**Alternatives Considered**:

- Always export all proposals (rejected - too broad, may expose unwanted changes)
- Single sanitization flag for all proposals (rejected - too coarse-grained)
- Manual file editing (rejected - error-prone, not user-friendly)

**Implementation**:

- Add `--change-ids` parameter to CLI (comma-separated list)
- Slash command provides interactive prompts
- Store per-change sanitization preferences in workflow state

### Decision 7: CLI → LLM → CLI Workflow for Sanitization

**What**: Use temporary files (`/tmp/`) to enable LLM review of sanitized content before creating issues.

**Why**:

- Ensures proper sanitization before public exposure
- Allows user review and approval of sanitized content
- Maintains CLI as single source of truth for issue creation
- Prevents accidental exposure of internal information

**Workflow**:

1. **For Sanitized Proposals**:
   - CLI exports proposal to `/tmp/specfact-proposal-<change-id>.md`
   - LLM reviews and sanitizes content
   - LLM writes sanitized version to `/tmp/specfact-proposal-<change-id>-sanitized.md`
   - User reviews and approves sanitized content
   - CLI imports sanitized content and creates issue

2. **For Non-Sanitized Proposals**:
   - Skip LLM workflow entirely
   - Direct export to GitHub issues
   - No temporary files needed

**Temporary File Format**:

- Original: `/tmp/specfact-proposal-<change-id>.md` (full proposal content)
- Sanitized: `/tmp/specfact-proposal-<change-id>-sanitized.md` (LLM-reviewed content)
- Cleanup: Remove temporary files after issue creation

**Alternatives Considered**:

- In-memory sanitization only (rejected - no user review, error-prone)
- Direct LLM API calls from CLI (rejected - violates CLI enforcement, adds complexity)
- Two-pass CLI execution (accepted - maintains CLI as source of truth)

**Implementation**:

- Add `--export-to-tmp` and `--import-from-tmp` flags to CLI
- Add `--tmp-file` parameter for custom temporary file paths
- Slash command orchestrates workflow (CLI → LLM → CLI)
- Cleanup temporary files after completion

### Decision 8: Issue Content Update Support

**What**: Support updating existing issue bodies when proposal content changes, leveraging tool-native change tracking.

**Why**:

- **Keep Issues in Sync**: Issue bodies should stay current with proposal content
- **Leverage Tool Features**: Most backlog tools (GitHub, ADO, Linear, Jira) have built-in change tracking/history
- **Selective Updates**: Only update when content actually changes (not on every sync)
- **User Control**: `--update-existing` flag gives users control over update behavior

**Content Change Detection**:

1. **Content Hash Tracking**:
   - Calculate hash of proposal content (Why + What Changes sections)
   - Store hash in `source_tracking.source_metadata.content_hash`
   - Compare hash on each sync to detect content changes

2. **Update Logic**:
   - When `--update-existing` flag is enabled and content hash differs, update issue body
   - Reuse existing body formatting logic from `_create_issue_from_proposal()`
   - Update stored hash after successful update

**Tool-Native Change Tracking**:

- GitHub (and most tools) have built-in change history
- No need to manually track every change in comments
- Optional comment only for significant changes (breaking changes, major scope changes)

**Default Behavior**:

- Default to `--no-update-existing` for safety (don't overwrite manual edits)
- User must explicitly enable with `--update-existing` flag

**Alternatives Considered**:

- Always update existing issues (rejected - may overwrite manual edits, too aggressive)
- Never update existing issues (rejected - issues become stale when proposals change)
- Manual update only (rejected - too much work, error-prone)

**Implementation**:

- Add `_update_issue_body()` method to `GitHubAdapter`
- Add content hash calculation in `BridgeSync`
- Add `--update-existing/--no-update-existing` flag to CLI
- Update `export_change_proposals_to_devops()` to check content hash and update when needed

### Decision 9: On-Demand Status Sync

**What**: Status synchronization is triggered on-demand via CLI command execution.

**Why**:

- Simpler to implement and debug
- User controls when sync occurs
- Avoids complex event-driven infrastructure
- Clear audit trail (command execution logs)

**Alternatives Considered**:

- Event-driven sync (rejected - too complex for Phase 1)
- Scheduled sync (rejected - requires background job infrastructure)
- File watching (rejected - platform-specific complexity)

**Implementation**:

- User runs `specfact sync bridge --adapter github --mode export-only`
- Sync reads OpenSpec change proposals via OpenSpec adapter
- Compares current status with last synced status (stored in each entry's `source_metadata.last_synced_status`, per repository)
- Updates issues for proposals with status changes
- **Future**: Event-driven sync can be added later (watch OpenSpec changes directory)

## Architecture

### Component Overview

```text
BridgeConfig (extended)
├── AdapterType.GITHUB
├── preset_github()
└── DevOps-specific artifact mappings (change_proposal, change_status)

GitHubAdapter (new, implements BridgeAdapter)
├── detect() - Detect GitHub repository
├── import_artifact() - Not used in export-only mode
├── export_artifact() - Create/update issues from change proposals
│   ├── artifact_key="change_proposal" → create_issue_from_change_proposal()
│   └── artifact_key="change_status" → update_issue_status()
└── generate_bridge_config() - Auto-generate GitHub bridge config

BridgeSync (extended)
├── Support --mode export-only
├── Route to GitHubAdapter.export_artifact()
└── Reuse existing sync orchestration

AdapterRegistry (existing)
└── Register GitHubAdapter for "github" type

CLI Command (extended)
└── sync bridge --adapter github --mode export-only
```

### Data Flow

```text
1. User runs: specfact sync bridge --adapter github --mode export-only

2. BridgeSync.export_artifact() (extended for export-only mode)
   ├── Reads OpenSpec change proposals via OpenSpec adapter
   ├── Filters active proposals (proposed, in-progress)
   └── For each proposal:
       ├── Check if issue exists (via source_tracking)
       ├── If not: call GitHubAdapter.export_artifact(artifact_key="change_proposal")
       ├── If exists: check status change, call GitHubAdapter.export_artifact(artifact_key="change_status")
       └── Store issue ID in source_tracking

3. GitHubAdapter.export_artifact(artifact_key="change_proposal")
   ├── Maps proposal fields to GitHub issue
   ├── Creates issue via GitHub API
   └── Returns issue number and URL (stored in source_tracking)

4. GitHubAdapter.export_artifact(artifact_key="change_status")
   ├── Retrieves issue from GitHub API (using source_tracking.source_id)
   ├── Maps change status to issue state (applied → closed, etc.)
   ├── Updates issue via GitHub API
   └── Adds comment explaining status change
```

### Status Synchronization

**Change Proposal Status → GitHub Issue State**:

```text
proposed → open (new issue)
in-progress → open (add "in-progress" label)
applied → closed (add "applied" comment, close issue)
deprecated → closed (add "deprecated" comment, close issue)
discarded → closed (add "discarded" comment, close issue)
```

**Implementation**:

- On-demand sync: User runs CLI command
- Compare current proposal status with last synced status (stored in `source_tracking.source_metadata`)
- Update issue when status changes detected
- Add comments for context
- **Future**: Event-driven sync (watch OpenSpec changes directory)

### Future Extensibility

**ADO Work Items**:

- `ADOAdapter` implements same interface
- Maps to ADO work item types (Feature, User Story)
- Uses ADO REST API

**Linear Issues**:

- `LinearAdapter` implements same interface
- Maps to Linear issue types
- Uses Linear GraphQL API

**Jira Issues**:

- `JiraAdapter` implements same interface
- Maps to Jira issue types (Epic, Story)
- Uses Jira REST API

**All adapters implement `BridgeAdapter` interface**:

- `detect()` - Detect tool installation
- `import_artifact()` - Import issues → specs (future, not used in export-only mode)
- `export_artifact()` - Export change proposals → issues (this proposal)
  - `artifact_key="change_proposal"` → create issue
  - `artifact_key="change_status"` → update issue status
- `generate_bridge_config()` - Auto-generate bridge config

## Risks / Trade-offs

### Risk 1: API Rate Limiting

**Risk**: GitHub API has rate limits that may be exceeded.

**Mitigation**:

- Implement rate limit handling
- Add retry logic with exponential backoff
- Batch operations when possible
- Cache API responses

### Risk 2: Issue Duplication

**Risk**: Multiple syncs may create duplicate issues.

**Mitigation**:

- Check `source_tracking` before creating issue
- Use issue title/content matching as fallback
- Provide deduplication command

### Risk 3: Status Sync Conflicts

**Risk**: Manual issue status changes may conflict with automated sync.

**Mitigation**:

- Export-only sync (OpenSpec → DevOps) takes precedence
- Document manual changes will be overwritten on next sync
- Future bidirectional sync will handle conflicts with merge strategies

### Risk 4: Authentication Complexity

**Risk**: Different DevOps tools require different authentication methods.

**Mitigation**:

- Use environment variables for tokens
- Support OAuth for GitHub (future)
- Document authentication requirements per tool

## Open Questions

- **Multiple DevOps Tools**: Phase 1 supports **one DevOps tool per change proposal**. Future: Multiple tools per change (requires `source_tracking` extension to list).
- **Sync Scope**: Phase 1 syncs **active proposals only** (proposed, in-progress). Future: Option to sync all proposals including archived.
- **Custom Issue Templates**: Deferred - use default mapping in Phase 1. Future: Support custom templates via bridge config.
- **Issue Assignment**: Deferred - manual assignment in Phase 1. Future: Auto-assign based on proposal owner or metadata.

## Implementation Notes

### File Structure

```text
src/specfact_cli/
├── models/
│   └── bridge.py          # EXTEND: AdapterType.GITHUB, preset_github()
├── adapters/
│   ├── base.py            # BridgeAdapter interface (existing)
│   ├── registry.py        # AdapterRegistry (existing or new)
│   └── github.py          # NEW: GitHubAdapter implements BridgeAdapter
├── sync/
│   └── bridge_sync.py     # EXTEND: Support export-only mode
└── commands/
    └── sync.py            # EXTEND: sync bridge --mode export-only
```

### Dependencies

**Required**:

- OpenSpec bridge adapter (`implement-openspec-bridge-adapter`)
- Change tracking data model (`add-change-tracking-datamodel`)
- GitHub API client (PyGithub or requests)

**Optional**:

- Other DevOps tool APIs (for future adapters)

### Testing Strategy

1. **Unit Tests**: Mock GitHub API for adapter tests
   - Test `GitHubAdapter.export_artifact()` with mock API
   - Test status mapping logic
   - Test error handling (API failures, missing issues, rate limits)
2. **Integration Tests**: Use test GitHub repository for real API tests
   - Test end-to-end sync via `bridge_sync.py`
   - Test issue creation and status updates
   - Test idempotency (multiple syncs of same proposal)
3. **Status Sync Tests**: Verify status mapping and updates
   - Test all status transitions (proposed → applied, etc.)
   - Test status update when issue already closed
4. **Edge Cases**:
   - Duplicate issues (check source_tracking before creation)
   - Missing proposals (graceful handling)
   - API failures (retry logic, error reporting)
   - Missing GitHub token (clear error message)
   - Invalid repository (clear error message)

### Success Metrics

- ✅ Issues created from change proposals
- ✅ Issue status updated correctly
- ✅ Issue IDs tracked in change proposals
- ✅ CLI command works
- ✅ Test coverage ≥80%
- ✅ Architecture supports future tools
