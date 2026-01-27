## ADDED Requirements

### Requirement: Code Change Detection and Progress Comments

The system SHALL detect code changes related to change proposals and add progress comments to existing GitHub issues without replacing the issue body.

#### Scenario: Detect Code Changes and Add Progress Comment

- **GIVEN** an OpenSpec change proposal with existing GitHub issue (tracked in `source_tracking` for repository `nold-ai/specfact-cli`)
- **AND** code changes are detected (git commits, file modifications) related to the proposal
- **AND** `--track-code-changes` flag is enabled
- **WHEN** DevOps sync is executed with `target_repo="nold-ai/specfact-cli"`
- **THEN** system detects code changes related to the proposal (via git commits or file monitoring)
- **AND** system finds entry in `source_tracking` list where `source_repo="nold-ai/specfact-cli"`
- **AND** progress comment is added to existing GitHub issue
- **AND** comment includes implementation progress details (files changed, commits, milestones)
- **AND** issue body is NOT replaced (comment only)
- **AND** progress comment is tracked in that entry's `source_metadata.progress_comments`
- **AND** last code change detection timestamp is stored in that entry's `source_metadata.last_code_change_detected`

#### Scenario: Skip Comment When No Code Changes Detected

- **GIVEN** an OpenSpec change proposal with existing GitHub issue
- **AND** no code changes detected since last detection timestamp
- **AND** `--track-code-changes` flag is enabled
- **WHEN** DevOps sync is executed
- **THEN** no progress comment is added
- **AND** existing issue remains unchanged
- **AND** sync result indicates "no code changes detected"

#### Scenario: Add Progress Comment Without Code Change Detection

- **GIVEN** an OpenSpec change proposal with existing GitHub issue
- **AND** `--add-progress-comment` flag is enabled (without `--track-code-changes`)
- **WHEN** DevOps sync is executed
- **THEN** progress comment is added to existing GitHub issue
- **AND** comment includes manual progress information
- **AND** issue body is NOT replaced (comment only)
- **AND** progress comment is tracked in `source_metadata.progress_comments`

#### Scenario: Prevent Duplicate Progress Comments

- **GIVEN** an OpenSpec change proposal with existing GitHub issue
- **AND** code changes are detected
- **AND** progress comment with same content already exists (checked via `source_metadata.progress_comments`)
- **WHEN** DevOps sync is executed
- **THEN** duplicate progress comment is NOT added
- **AND** sync result indicates "comment already exists"

#### Scenario: Track Multiple Progress Comments Per Issue

- **GIVEN** an OpenSpec change proposal with existing GitHub issue
- **AND** multiple code changes detected over time
- **AND** `--track-code-changes` flag is enabled
- **WHEN** DevOps sync is executed multiple times (once per code change)
- **THEN** each code change detection adds a new progress comment
- **AND** all progress comments are tracked in `source_metadata.progress_comments` (list)
- **AND** each comment includes timestamp and change details
- **AND** issue body is NOT replaced (comments only)

#### Scenario: Handle Code Change Detection Errors Gracefully

- **GIVEN** an OpenSpec change proposal with existing GitHub issue
- **AND** `--track-code-changes` flag is enabled
- **AND** code change detection fails (git not available, repository not found)
- **WHEN** DevOps sync is executed
- **THEN** error is logged
- **AND** sync continues with other proposals
- **AND** error is reported in sync result
- **AND** no progress comment is added

#### Scenario: Support Cross-Repository Code Change Detection

- **GIVEN** an OpenSpec change proposal with issues in multiple repositories
- **AND** `source_tracking` contains entries for both `nold-ai/specfact-cli-internal` and `nold-ai/specfact-cli`
- **AND** code changes are detected in the code repository
- **AND** `--track-code-changes` flag is enabled
- **WHEN** DevOps sync is executed with `target_repo="nold-ai/specfact-cli"`
- **THEN** system detects code changes in the code repository
- **AND** progress comment is added only to the issue for `nold-ai/specfact-cli` (matches `target_repo`)
- **AND** progress comment is tracked in that entry's `source_metadata.progress_comments`
- **AND** system does NOT add comment to the issue for `nold-ai/specfact-cli-internal` (different repo)

## MODIFIED Requirements

### Requirement: Issue Content Update Support

The system SHALL support updating existing issue bodies when proposal content changes, leveraging tool-native change tracking, AND adding progress comments when code changes are detected (separate from body updates).

#### Scenario: Update Issue Body When Content Changed (Single Repository)

- **GIVEN** a change proposal with existing GitHub issue (tracked in `source_tracking` for repository `nold-ai/specfact-cli`)
- **AND** proposal content (Why or What Changes sections) has been modified
- **AND** `--update-existing` flag is enabled
- **WHEN** DevOps sync is executed with `target_repo="nold-ai/specfact-cli"`
- **THEN** system finds entry in `source_tracking` list where `source_repo="nold-ai/specfact-cli"`
- **AND** content hash is calculated from current proposal content
- **AND** stored hash is compared with current hash (from that entry's `source_metadata.content_hash`)
- **AND** if hashes differ, issue body is updated via GitHub API PATCH for that repository's issue
- **AND** updated hash is stored in that entry's `source_metadata.content_hash`
- **AND** issue body reflects current proposal content
- **NOTE**: Progress comments (from code change tracking) are separate from body updates and can coexist

#### Scenario: Update Issue Body for Multiple Repositories

- **GIVEN** a change proposal with issues in multiple repositories
- **AND** `source_tracking` contains entries for both `nold-ai/specfact-cli-internal` and `nold-ai/specfact-cli`
- **AND** proposal content has been modified
- **AND** `--update-existing` flag is enabled
- **WHEN** DevOps sync is executed with `target_repo="nold-ai/specfact-cli"`
- **THEN** system updates only the issue for `nold-ai/specfact-cli` (matches `target_repo`)
- **AND** system does NOT update the issue for `nold-ai/specfact-cli-internal` (different repo)
- **AND** each repository's issue can be updated independently
- **AND** each entry's `source_metadata.content_hash` is updated independently

#### Scenario: Skip Update When Content Unchanged

- **GIVEN** a change proposal with existing GitHub issue
- **AND** proposal content has not changed (hash matches stored hash)
- **WHEN** DevOps sync is executed
- **THEN** issue body is not updated
- **AND** no API call is made to update issue
- **AND** sync result indicates "no change"
- **NOTE**: Code change tracking and progress comments operate independently of body updates

#### Scenario: Skip Update When Flag Disabled

- **GIVEN** a change proposal with existing GitHub issue
- **AND** proposal content has changed (hash differs)
- **AND** `--update-existing` flag is NOT enabled (default: False)
- **WHEN** DevOps sync is executed
- **THEN** issue body is not updated
- **AND** sync result indicates "skipped" (update disabled)
- **AND** user must explicitly enable with `--update-existing` flag
- **NOTE**: Progress comments can still be added via `--track-code-changes` or `--add-progress-comment` flags

#### Scenario: Update Issue Body with Sanitized Content (Per Repository)

- **GIVEN** a change proposal with existing GitHub issue in public repository `nold-ai/specfact-cli`
- **AND** `source_tracking` contains entry for `source_repo="nold-ai/specfact-cli"` with `source_metadata.sanitized=true`
- **AND** `--import-from-tmp` flag is used with sanitized content
- **AND** `--update-existing` flag is enabled
- **WHEN** DevOps sync is executed with `target_repo="nold-ai/specfact-cli"`
- **THEN** system finds entry for `source_repo="nold-ai/specfact-cli"`
- **AND** sanitized content is used to update issue body for that repository
- **AND** hash is calculated from sanitized content (not original)
- **AND** sanitized content hash is stored in that entry's `source_metadata.content_hash`
- **AND** `source_metadata.sanitized` flag remains `true`
- **AND** issue body reflects sanitized proposal content
- **NOTE**: Internal repository issue (if exists) is not updated with sanitized content

#### Scenario: Handle Update Errors Gracefully

- **GIVEN** a change proposal with existing GitHub issue
- **AND** content has changed and `--update-existing` is enabled
- **WHEN** GitHub API returns an error during issue update
- **THEN** error is logged
- **AND** sync continues with other proposals
- **AND** error is reported in sync result
- **AND** stored hash is not updated (allows retry on next sync)

#### Scenario: Use Tool-Native Change Tracking

- **GIVEN** a change proposal with existing GitHub issue
- **AND** issue body is updated via sync
- **WHEN** issue update succeeds
- **THEN** GitHub's built-in change history tracks the update
- **AND** no manual comment is added (unless significant change detected)
- **AND** users can view change history via GitHub UI
- **NOTE**: Tool-native history provides full audit trail without manual tracking
- **NOTE**: Progress comments (from code change tracking) are separate from body update history

#### Scenario: Optional Comment for Significant Changes

- **GIVEN** a change proposal with existing GitHub issue
- **AND** proposal content contains "BREAKING" or "major" scope change keywords
- **AND** content has changed and `--update-existing` is enabled
- **WHEN** DevOps sync is executed
- **THEN** issue body is updated
- **AND** optional comment is added indicating significant change
- **AND** comment highlights breaking changes or major scope changes
- **NOTE**: Comment is optional, not required - tool-native history is primary tracking
- **NOTE**: This comment is separate from progress comments (code change tracking)
