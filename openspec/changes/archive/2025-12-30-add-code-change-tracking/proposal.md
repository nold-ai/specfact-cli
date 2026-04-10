# Change: Add Code Change Tracking and Progress Comments

## Why

The current DevOps sync implementation only updates issue bodies when proposal content changes and adds comments for status changes or significant content changes. However, teams need to track implementation progress based on actual code changes (git commits, file modifications) and add progress comments to existing issues without replacing the entire issue body.

This enables:

- Track implementation milestones as code is written
- Notify stakeholders when implementation work progresses
- Provide incremental updates without replacing issue content
- Maintain audit trail of implementation progress separate from proposal content updates

This change extends the existing DevOps sync capability to detect code changes related to change proposals and add progress comments to existing issues, complementing (not replacing) the existing issue body update functionality.

## What Changes

- **EXTEND**: `src/specfact_cli/sync/bridge_sync.py`
  - Add code change detection logic (git commits, file modifications)
  - Add progress comment generation based on code changes
  - Support `--track-code-changes` flag to enable code change tracking
  - Add `--add-progress-comment` flag to add comments without updating issue body

- **EXTEND**: `src/specfact_cli/adapters/github.py`
  - Add `_add_progress_comment()` method for adding implementation progress comments
  - Extend `export_artifact()` to handle `artifact_key="code_change_progress"`
  - Support progress comment formatting with implementation details

- **EXTEND**: `src/specfact_cli/commands/sync.py`
  - Add `--track-code-changes` flag to enable code change detection
  - Add `--add-progress-comment` flag to add comments to existing issues
  - Support code change detection via git history or file monitoring

- **NEW**: Code change detection utilities
  - Detect git commits related to change proposals (via commit messages, file paths)
  - Track file modifications related to implementation
  - Generate progress summaries from code changes

- **EXTEND**: Source tracking metadata
  - Track last code change detection timestamp
  - Support multiple progress comments per issue

## Impact

- **Affected specs**: `devops-sync` (MODIFIED)
- **Affected code**:
  - `src/specfact_cli/sync/bridge_sync.py` (EXTEND)
  - `src/specfact_cli/adapters/github.py` (EXTEND)
  - `src/specfact_cli/commands/sync.py` (EXTEND)
  - Tests for all new/extended components

- **Breaking changes**: None (additive only)
- **Dependencies**:
  - Requires existing DevOps sync capability (`add-devops-backlog-tracking`)
  - Uses git for code change detection (optional, can use file monitoring)
  - Extends existing bridge adapter architecture

## Success Criteria

- ✅ Code changes detected for change proposals (git commits, file modifications)
- ✅ Progress comments added to existing GitHub issues when code changes detected
- ✅ Comments include implementation progress details (files changed, commits, milestones)
- ✅ Issue body is NOT replaced (comments only)
- ✅ CLI command `specfact sync bridge --adapter github --mode export-only --track-code-changes` works
- ✅ CLI command `specfact sync bridge --adapter github --mode export-only --add-progress-comment` works
- ✅ Architecture supports future tools (ADO, Linear, Jira)
- ✅ Integration tests pass
- ✅ Test coverage ≥80%

---

## Source Tracking

### Repository: nold-ai/specfact-cli

- **GitHub Issue**: #107
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/107>
- **Last Synced Status**: applied
- **Sanitized**: true
<!-- content_hash: 2d3738a620200b1a -->