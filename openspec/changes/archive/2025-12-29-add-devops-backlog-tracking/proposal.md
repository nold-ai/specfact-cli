# Change: Add DevOps Backlog Tracking Integration

## Why

OpenSpec change proposals need to be tracked in DevOps backlogs (GitHub Issues, ADO Work Items, Linear Issues, Jira Issues) to align project planning with specifications. This enables teams to:

- Create backlog items from OpenSpec change proposals automatically
- Track implementation status in DevOps tools
- Update issue status when changes are applied or deprecated
- Maintain project plan in sync with specs

This change implements **export-only sync** (OpenSpec → DevOps) starting with GitHub Issues, using the existing bridge adapter architecture (`bridge_sync.py`). The architecture is designed to support other tools (ADO, Linear, Jira) via the same bridge adapter pattern. Bidirectional sync can be added later as it's more complex.

**Key Requirements**:

- **Breaking Changes Communication**: Data model changes and similar breaking changes need early communication before PRs
- **OSS Collaboration**: Public issues needed for contributors/watchers/users to track progress
- **Conditional Sanitization**: Only sanitize when code and planning are in different repos (same-repo users can choose)
- **User Choice**: Ask user if issues should be sanitized (removes competitive analysis, internal strategy)
- **AI-Assisted Sanitization**: Slash command support for interactive, AI-assisted content rewriting

**Dependency**: This change requires the OpenSpec bridge adapter (`implement-openspec-bridge-adapter`) to be implemented first, as it needs to read OpenSpec change proposals.

**Relationship to Existing DevOps Capabilities**: This is a **third capability** for DevOps adapters, complementing (not replacing) existing planned capabilities:

1. **Import** (future): Issues → Specs (DevOps → SpecFact)
2. **Annotation** (future): SpecFact findings → Issue comments (SpecFact → DevOps)
3. **Export** (this proposal): Change proposals → Issues (OpenSpec → DevOps)

All three capabilities can coexist in the same adapter using different sync modes.

## What Changes

- **Issue content updates**: Automatically update existing issue bodies when proposal content changes (via `--update-existing` flag). Content hash is persisted to detect changes.
- **Multi-repository source tracking**: Support multiple source tracking entries (one per repository) to track issues in both internal and public repositories simultaneously. Each entry includes `source_repo` identifier to disambiguate repositories.
- **NEW**: `src/specfact_cli/adapters/github.py` (GitHub bridge adapter)
  - Implements `BridgeAdapter` interface (standard bridge adapter pattern)
  - `export_artifact()` method handles change proposal → issue creation
  - `export_artifact()` method handles change status → issue status updates
  - `export_artifact()` method handles change proposal content → issue body updates (when `--update-existing` enabled)
  - Link issues to OpenSpec change proposals via `source_tracking`

- **EXTEND**: `src/specfact_cli/models/bridge.py`
  - Add `GITHUB` to `AdapterType` enum (if not already present)
  - Add `preset_github()` classmethod to `BridgeConfig`
  - Add DevOps-specific artifact mappings (change_proposal, change_status)

- **EXTEND**: `src/specfact_cli/sync/bridge_sync.py`
  - Extend existing `BridgeSync` to support `export-only` mode
  - Route to `GitHubAdapter.export_artifact()` for change proposals
  - Support status synchronization via adapter
  - Add change filtering support:
    - Filter proposals by `--change-ids` parameter (comma-separated list)
    - Default: export all active proposals if not specified
  - Add temporary file workflow support:
    - `export_to_tmp`: Export proposal content to temporary file (for LLM review)
    - `import_from_tmp`: Import sanitized content from temporary file (after LLM review)
    - Handle file I/O for `/tmp/specfact-proposal-<change-id>.md` files

- **EXTEND**: `src/specfact_cli/commands/sync.py`
  - Extend `sync bridge` command with `--mode export-only`
  - Support `--adapter github` (and future: ado, linear, jira)
  - Export-only mode: OpenSpec change proposals → DevOps issues
  - Add sanitization support:
    - `--sanitize/--no-sanitize`: User choice for sanitization (default: auto-detect based on repo setup)
    - `--target-repo`: Target repository for issue creation (default: same as code repo)
    - `--interactive`: Interactive mode for AI-assisted sanitization (requires slash command)
  - Add change selection support:
    - `--change-ids IDS`: Comma-separated list of change proposal IDs to export (default: all active proposals)
  - Add temporary file workflow support (for LLM sanitization review):
    - `--export-to-tmp`: Export proposal content to temporary file for LLM review
    - `--import-from-tmp`: Import sanitized content from temporary file after LLM review
    - `--tmp-file PATH`: Specify temporary file path (default: `/tmp/specfact-proposal-<change-id>.md`)
  - Add issue content update support:
    - `--update-existing/--no-update-existing`: Update existing issue bodies when proposal content changes (default: False for safety)
    - Content hash tracking to detect when proposal content has changed
    - Update issue body via GitHub API PATCH when content hash differs

- **NEW**: Integration with OpenSpec change tracking
  - Read OpenSpec change proposals via OpenSpec bridge adapter
  - Map change proposals to DevOps issues
  - Track issue IDs in `ChangeProposal.source_tracking` (list of entries, one per repository)
  - Track content hash in each entry's `source_metadata.content_hash` to detect content changes
  - Support multiple repositories per proposal (internal + public issues)
  - Each source tracking entry includes `source_repo` identifier (e.g., "nold-ai/specfact-cli-internal", "nold-ai/specfact-cli")
  - Support conditional sanitization (only when code and planning are in different repos)
  - Support updating existing issue bodies when proposal content changes (with `--update-existing` flag)
  - Update issues per repository independently based on `source_repo` match

- **NEW**: Content sanitization support
  - `src/specfact_cli/utils/content_sanitizer.py` (new) - Sanitize proposal content for public issues
  - Remove competitive analysis, market positioning, implementation details
  - Keep user-facing value, use cases, acceptance criteria
  - Support AI-assisted sanitization via slash command (`/specfact-cli/sync-backlog`)

- **NEW**: Slash command for interactive sync
  - `resources/prompts/specfact.sync-backlog.md` (new) - AI-assisted backlog sync command
  - Interactive change selection (which proposals to export)
  - Per-change sanitization selection (sanitize each proposal individually)
  - CLI → LLM → CLI workflow for sanitized proposals:
    - Step 1: CLI exports proposal to `/tmp/specfact-proposal-<change-id>.md`
    - Step 2: LLM reviews and sanitizes content, writes to `/tmp/specfact-proposal-<change-id>-sanitized.md`
    - Step 3: User approves sanitized content
    - Step 4: CLI imports sanitized content and creates issue
  - Skip LLM workflow for non-sanitized proposals (direct export)
  - Cleanup temporary files after completion

## Impact

- **Affected specs**: None (new capability)
- **Affected code**:
  - `src/specfact_cli/models/bridge.py` (EXTEND)
  - `src/specfact_cli/adapters/github.py` (NEW)
  - `src/specfact_cli/sync/bridge_sync.py` (EXTEND - export-only mode)
  - `src/specfact_cli/commands/sync.py` (EXTEND - sync bridge command)
  - Tests for all new/extended components

- **Breaking changes**: None (additive only)
- **Dependencies**:
  - Requires OpenSpec bridge adapter (`implement-openspec-bridge-adapter`) to be implemented first
  - Requires change tracking data model (`add-change-tracking-datamodel`) for change proposals
  - Uses existing bridge adapter architecture
  - Uses GitHub API (PyGithub or similar)

## Success Criteria

- ✅ GitHub issues created from OpenSpec change proposals
- ✅ Issue status updated when change is applied (closed)
- ✅ Issue status updated when change is deprecated/discarded (closed)
- ✅ Issue content updated when proposal content changes (with `--update-existing` flag)
- ✅ Content hash tracking to detect proposal content changes (per repository)
- ✅ Issue IDs tracked in `ChangeProposal.source_tracking` (list of entries, one per repository)
- ✅ Multi-repository support: Track issues in multiple repositories simultaneously (internal + public)
- ✅ Per-repository issue updates: Update issues independently based on `source_repo` match
- ✅ CLI command `specfact sync bridge --adapter github --mode export-only` works
- ✅ **Conditional sanitization works** (auto-detect when code and planning are in different repos)
- ✅ **User choice for sanitization** (--sanitize/--no-sanitize flags)
- ✅ **Interactive change selection** (select which proposals to export via slash command)
- ✅ **Per-change sanitization selection** (sanitize each proposal individually)
- ✅ **AI-assisted sanitization via slash command** (`/specfact.sync-backlog`)
  - CLI → LLM → CLI workflow for sanitized proposals
  - Temporary file workflow (`/tmp/specfact-proposal-*.md`)
  - User approval step before creating issues
- ✅ **Skip LLM workflow for non-sanitized proposals** (direct export without review)
- ✅ **Breaking changes communicated early** (public issues created before PRs)
- ✅ Architecture supports future tools (ADO, Linear, Jira)
- ✅ Integration tests pass
- ✅ Test coverage ≥80%

---

## Source Tracking

### Repository: nold-ai/specfact-cli

- **GitHub Issue**: #63
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/63>
- **Last Synced Status**: applied
- **Sanitized**: true
<!-- content_hash: 0798f59ffe9b0fa2 -->
