# devops-sync Specification

## Purpose
TBD - created by archiving change add-devops-backlog-tracking. Update Purpose after archive.
## Requirements
### Requirement: GitHub Issue Creation from Change Proposals

The system SHALL create GitHub issues from OpenSpec change proposals automatically.

#### Scenario: Create Issue from New Change Proposal

- **GIVEN** an OpenSpec change proposal with status "proposed"
- **WHEN** DevOps sync is executed with GitHub adapter
- **THEN** a GitHub issue is created with:
  - Title: `proposal.title`
  - Body: `proposal.description` + `proposal.rationale`
  - Labels: Extracted from proposal metadata or default labels
  - State: open
- **AND** issue number and URL stored in `proposal.source_tracking`
- **AND** issue ID stored in `source_tracking.source_id`
- **AND** issue URL stored in `source_tracking.source_url`

#### Scenario: Skip Issue Creation for Existing Proposal

- **GIVEN** an OpenSpec change proposal with existing GitHub issue (tracked in `source_tracking`)
- **WHEN** DevOps sync is executed
- **THEN** no new issue is created
- **AND** existing issue is used for status updates

#### Scenario: Handle Issue Creation Errors

- **GIVEN** GitHub API returns an error during issue creation
- **WHEN** DevOps sync attempts to create issue
- **THEN** error is logged
- **AND** sync continues with other proposals
- **AND** error is reported in sync result

### Requirement: Issue Status Synchronization

The system SHALL update GitHub issue status when OpenSpec change proposal status changes.

#### Scenario: Update Issue When Change Applied

- **GIVEN** an OpenSpec change proposal with status "applied"
- **AND** proposal has linked GitHub issue (tracked in `source_tracking`)
- **WHEN** DevOps sync is executed
- **THEN** GitHub issue is closed
- **AND** comment is added explaining change was applied
- **AND** issue state reflects applied status

#### Scenario: Update Issue When Change Deprecated

- **GIVEN** an OpenSpec change proposal with status "deprecated"
- **AND** proposal has linked GitHub issue
- **WHEN** DevOps sync is executed
- **THEN** GitHub issue is closed
- **AND** comment is added explaining change was deprecated
- **AND** issue state reflects deprecated status

#### Scenario: Update Issue When Change Discarded

- **GIVEN** an OpenSpec change proposal with status "discarded"
- **AND** proposal has linked GitHub issue
- **WHEN** DevOps sync is executed
- **THEN** GitHub issue is closed
- **AND** comment is added explaining change was discarded
- **AND** issue state reflects discarded status

#### Scenario: Keep Issue Open for Active Changes

- **GIVEN** an OpenSpec change proposal with status "proposed" or "in-progress"
- **AND** proposal has linked GitHub issue
- **WHEN** DevOps sync is executed
- **THEN** GitHub issue remains open
- **AND** label or comment added if status is "in-progress"

### Requirement: Status Mapping

The system SHALL map OpenSpec change proposal status to GitHub issue state correctly.

#### Scenario: Map Proposed Status

- **GIVEN** change proposal status is "proposed"
- **WHEN** issue is created or updated
- **THEN** GitHub issue state is "open"
- **AND** no special labels or comments added

#### Scenario: Map In-Progress Status

- **GIVEN** change proposal status is "in-progress"
- **WHEN** issue is created or updated
- **THEN** GitHub issue state is "open"
- **AND** "in-progress" label is added (if supported)
- **AND** comment may be added indicating in-progress status

#### Scenario: Map Applied Status

- **GIVEN** change proposal status is "applied"
- **WHEN** issue is updated
- **THEN** GitHub issue state is "closed"
- **AND** comment is added: "Change applied: {proposal.title}"
- **AND** issue reflects completion

#### Scenario: Map Deprecated Status

- **GIVEN** change proposal status is "deprecated"
- **WHEN** issue is updated
- **THEN** GitHub issue state is "closed"
- **AND** comment is added: "Change deprecated: {proposal.title}. Reason: {proposal.rationale}"
- **AND** issue reflects deprecation

#### Scenario: Map Discarded Status

- **GIVEN** change proposal status is "discarded"
- **WHEN** issue is updated
- **THEN** GitHub issue state is "closed"
- **AND** comment is added: "Change discarded: {proposal.title}"
- **AND** issue reflects discard

### Requirement: Source Tracking Integration

The system SHALL store DevOps issue information in change proposal source tracking.

#### Scenario: Store Issue ID After Creation

- **GIVEN** a GitHub issue is created from change proposal
- **WHEN** issue creation succeeds
- **THEN** `proposal.source_tracking.source_id` contains issue number
- **AND** `proposal.source_tracking.source_url` contains issue URL
- **AND** `proposal.source_tracking.source_type` is "github"
- **AND** `proposal.source_tracking.source_metadata` contains GitHub-specific data:
  - `repo_owner`: GitHub repository owner
  - `repo_name`: GitHub repository name
  - `issue_number`: Issue number
  - `issue_url`: Full issue URL
  - `content_hash`: Content hash (SHA-256, first 16 chars) for change detection
  - `last_updated`: Timestamp of last content update (ISO 8601 format)
- **AND** Source Tracking section is written to `proposal.md` with proper markdown formatting:
  - Heading: `## Source Tracking` (with blank line before)
  - Separator: Single `---` before heading (not duplicate)
  - Issue line: `- **GitHub Issue**: #<number>` (correct capitalization: "GitHub", not "Github")
  - URL line: `- **Issue URL**: <https://...>` (URL enclosed in angle brackets for MD034 compliance)
  - Status line: `- **Last Synced Status**: <status>` (if metadata present)
  - Proper blank lines around all elements (MD022 compliance)

#### Scenario: Retrieve Issue Using Source Tracking (Single Repository)

- **GIVEN** a change proposal with GitHub issue tracked in `source_tracking` for repository `nold-ai/specfact-cli`
- **WHEN** issue needs to be retrieved for that repository
- **THEN** system finds entry in `source_tracking` list where `source_repo="nold-ai/specfact-cli"`
- **AND** issue number is read from that entry's `source_id`
- **AND** issue is retrieved from GitHub API using issue number and repository
- **AND** issue data is returned

#### Scenario: Retrieve Issue from Multiple Repositories

- **GIVEN** a change proposal with issues in multiple repositories
- **AND** `source_tracking` contains entries for both `nold-ai/specfact-cli-internal` and `nold-ai/specfact-cli`
- **WHEN** issue needs to be retrieved for `target_repo="nold-ai/specfact-cli"`
- **THEN** system searches `source_tracking` list for entry with `source_repo="nold-ai/specfact-cli"`
- **AND** if found, uses that entry's `source_id` and `source_url`
- **AND** if not found, treats as new issue for that repository
- **AND** does NOT use entry from different repository (e.g., `specfact-cli-internal`)

#### Scenario: Multi-Repository Source Tracking Support

- **GIVEN** a change proposal needs to be synced to multiple repositories (e.g., internal repo and public repo)
- **WHEN** DevOps sync is executed for different target repositories
- **THEN** `source_tracking` stores **multiple entries** (one per repository)
- **AND** each entry includes:
  - `source_id`: Issue number
  - `source_url`: Issue URL
  - `source_type`: Tool type (e.g., "github")
  - `source_repo`: Repository identifier (e.g., "nold-ai/specfact-cli-internal", "nold-ai/specfact-cli")
  - `source_metadata`: Repository-specific metadata (content_hash, last_synced_status, sanitized flag, etc.)
- **AND** system can track issues in multiple repositories simultaneously
- **AND** system can update issues in specific repositories based on `source_repo` match
- **AND** system can create new issues in repositories where no entry exists for that repo

#### Scenario: Store Multiple Repository Issues

- **GIVEN** a change proposal is synced to internal repository (`specfact-cli-internal`)
- **AND** proposal is later synced to public repository (`specfact-cli`) with sanitization
- **WHEN** both syncs complete successfully
- **THEN** `source_tracking` contains two entries:
  - Entry 1: `source_repo="nold-ai/specfact-cli-internal"`, `source_id="14"`, `source_url="https://github.com/nold-ai/specfact-cli-internal/issues/14"`, `source_metadata.sanitized=false`
  - Entry 2: `source_repo="nold-ai/specfact-cli"`, `source_id="63"`, `source_url="https://github.com/nold-ai/specfact-cli/issues/63"`, `source_metadata.sanitized=true`
- **AND** both entries are stored in `proposal.md` Source Tracking section
- **AND** system can update either issue independently based on `source_repo` match

#### Scenario: Check Issue Existence Per Repository

- **GIVEN** a change proposal has `source_tracking` with multiple entries
- **AND** one entry has `source_repo="nold-ai/specfact-cli-internal"`
- **AND** another entry has `source_repo="nold-ai/specfact-cli"`
- **WHEN** DevOps sync is executed with `target_repo="nold-ai/specfact-cli"`
- **THEN** system checks if entry exists for `source_repo="nold-ai/specfact-cli"`
- **AND** if entry exists, uses existing issue (updates if needed)
- **AND** if entry does not exist, creates new issue for that repository
- **AND** does NOT skip issue creation just because another repo has an entry

### Requirement: CLI Command Support

The system SHALL provide CLI command for DevOps sync.

#### Scenario: Sync Change Proposals to GitHub

- **GIVEN** OpenSpec change proposals exist
- **WHEN** user runs `specfact sync bridge --adapter github --mode export-only --repo-owner OWNER --repo-name REPO`
- **THEN** command uses `BridgeSync` with export-only mode
- **AND** reads change proposals via OpenSpec adapter
- **AND** routes to `GitHubAdapter.export_artifact()` via adapter registry
- **AND** creates GitHub issues for proposals without existing issues
- **AND** updates issue status for proposals with existing issues (when status changed)
- **AND** updates issue body for proposals with existing issues (when content changed and `--update-existing` enabled)
- **AND** reports sync results (created, updated, errors)

#### Scenario: Auto-Detect GitHub Configuration

- **GIVEN** bridge config includes GitHub preset
- **WHEN** user runs `specfact sync bridge --adapter github --mode export-only` (without repo options)
- **THEN** command reads GitHub config from bridge config
- **AND** uses configured repository owner and name
- **AND** uses GitHub token from environment variable or config

#### Scenario: Handle Missing Configuration

- **GIVEN** GitHub adapter requires repository owner and name
- **WHEN** user runs sync command without required config
- **THEN** command reports configuration error
- **AND** provides guidance on required configuration
- **AND** exits with error code

#### Scenario: Handle Missing GitHub Token

- **GIVEN** GitHub adapter requires API token
- **WHEN** user runs sync command without GITHUB_TOKEN environment variable
- **THEN** command reports authentication error
- **AND** provides guidance on setting GITHUB_TOKEN
- **AND** exits with error code

#### Scenario: Handle Invalid Repository

- **GIVEN** GitHub adapter is configured with invalid repository
- **WHEN** user runs sync command
- **THEN** command reports repository not found error
- **AND** provides guidance on correct repository configuration
- **AND** exits with error code

#### Scenario: Update Existing Issue with Content Changes

- **GIVEN** OpenSpec change proposals exist
- **AND** proposals have existing GitHub issues
- **WHEN** user runs `specfact sync bridge --adapter github --mode export-only --update-existing`
- **THEN** command calculates content hash for each proposal
- **AND** compares hash with stored hash in `source_tracking.source_metadata.content_hash`
- **AND** for proposals with content changes, updates issue body via GitHub API
- **AND** stores updated hash in metadata
- **AND** reports sync results (created, updated, skipped)

### Requirement: Extensible Architecture

The system SHALL support future DevOps tools (ADO, Linear, Jira) via adapter pattern.

#### Scenario: Support Multiple Adapters

- **GIVEN** bridge adapter architecture is implemented
- **WHEN** new adapter (e.g., ADO) is added
- **THEN** adapter implements `BridgeAdapter` interface
- **AND** adapter is registered via `AdapterRegistry`
- **AND** `BridgeSync` routes to appropriate adapter via registry
- **AND** no changes to core sync logic required

#### Scenario: Adapter Interface Consistency

- **GIVEN** multiple DevOps adapters (GitHub, ADO, Linear, Jira)
- **WHEN** adapters are implemented
- **THEN** all adapters implement `BridgeAdapter` interface:
  - `detect()` - Detect tool installation
  - `import_artifact()` - Import issues → specs (future, not used in export-only mode)
  - `export_artifact()` - Export change proposals → issues
    - `artifact_key="change_proposal"` → create issue
    - `artifact_key="change_status"` → update issue status
  - `generate_bridge_config()` - Auto-generate bridge config
- **AND** interface is consistent across adapters
- **AND** adapters are registered via `AdapterRegistry` pattern

### Requirement: Export-Only Sync Mode

The system SHALL support export-only sync (OpenSpec → DevOps) mode.

#### Scenario: Export-Only Sync Mode

- **GIVEN** DevOps sync is executed
- **WHEN** user runs `specfact sync bridge --adapter github --mode export-only`
- **THEN** export-only sync is used (OpenSpec → DevOps)
- **AND** no import from DevOps to OpenSpec
- **AND** sync is unidirectional
- **AND** uses existing `BridgeSync` framework

#### Scenario: Export-Only Mode Default

- **GIVEN** DevOps adapter is used
- **WHEN** user runs `specfact sync bridge --adapter github` (without mode)
- **THEN** export-only mode is used as default for DevOps adapters
- **AND** no import operations are attempted

#### Scenario: Future Bidirectional Mode

- **GIVEN** bidirectional sync is implemented in future
- **WHEN** user runs `specfact sync bridge --adapter github --mode bidirectional`
- **THEN** both directions are synced (OpenSpec ↔ DevOps)
- **AND** conflict resolution is applied
- **NOTE**: This is future capability, not in Phase 1

### Requirement: Idempotent Sync Operations

The system SHALL ensure sync operations are idempotent (multiple syncs produce same result).

#### Scenario: Multiple Syncs Produce Same Result

- **GIVEN** an OpenSpec change proposal with status "proposed"
- **AND** DevOps sync has been executed once (issue created)
- **WHEN** DevOps sync is executed again (same proposal, same status)
- **THEN** no duplicate issue is created
- **AND** existing issue is not modified (status unchanged, content unchanged)
- **AND** sync result reports 0 created, 0 updated
- **AND** sync is idempotent (can be run multiple times safely)

### Requirement: Content Sanitization Support

The system SHALL support conditional sanitization of proposal content for public issues.

#### Scenario: Conditional Sanitization (Different Repos)

- **GIVEN** code repository is different from planning repository (e.g., code in `specfact-cli`, planning in `specfact-cli-internal`)
- **WHEN** DevOps sync is executed to create public issues
- **THEN** sanitization is recommended (default: enabled)
- **AND** competitive analysis is removed from issue content
- **AND** market positioning statements are removed
- **AND** implementation details are removed
- **AND** effort estimates are removed
- **AND** user-facing value propositions are kept
- **AND** high-level feature descriptions are kept
- **AND** acceptance criteria (user-facing) are kept

#### Scenario: Conditional Sanitization (Same Repo)

- **GIVEN** code repository is same as planning repository (e.g., both in `specfact-cli`)
- **WHEN** DevOps sync is executed to create issues
- **THEN** sanitization is optional (default: disabled)
- **AND** user can choose to sanitize via `--sanitize` flag
- **AND** user can choose to skip sanitization via `--no-sanitize` flag
- **AND** full proposal content can be used if user chooses

#### Scenario: User Choice for Sanitization

- **GIVEN** DevOps sync is executed
- **WHEN** user provides `--sanitize` flag
- **THEN** sanitization is forced (regardless of repo setup)
- **AND** competitive analysis is removed
- **AND** internal strategy is removed
- **AND** sanitized content is used for issue creation

- **WHEN** user provides `--no-sanitize` flag
- **THEN** sanitization is skipped (regardless of repo setup)
- **AND** full proposal content is used for issue creation

#### Scenario: AI-Assisted Sanitization (Slash Command)

- **GIVEN** user runs `/specfact-cli/sync-backlog [change-id]` slash command
- **WHEN** AI analyzes proposal content
- **THEN** AI detects if sanitization is needed (based on repo setup)
- **AND** if sanitization needed:
  - AI rewrites content (removes internal strategy)
  - User reviews sanitized content
  - User approves or requests changes
- **AND** AI creates/updates backlog issues with sanitized content
- **AND** AI updates `source_tracking` in proposal

#### Scenario: Breaking Changes Communication

- **GIVEN** OpenSpec change proposal contains breaking changes (e.g., data model changes)
- **WHEN** DevOps sync is executed
- **THEN** public issue is created **before** PR is opened
- **AND** breaking changes are clearly marked in issue
- **AND** migration path is documented (if applicable)
- **AND** community is notified early about upcoming changes
- **AND** issue links to internal proposal for detailed planning

#### Scenario: OSS Collaboration Support

- **GIVEN** OpenSpec change proposal is for new tool onboarding (e.g., OpenSpec integration)
- **WHEN** DevOps sync is executed
- **THEN** public issue is created to communicate new capability
- **AND** issue includes high-level feature description (sanitized)
- **AND** issue includes user-facing use cases
- **AND** issue includes acceptance criteria
- **AND** issue does NOT include internal competitive analysis
- **AND** issue does NOT include implementation details
- **AND** contributors/watchers/users can track progress

#### Scenario: Idempotent Issue Creation

- **GIVEN** a change proposal has been synced once (issue created)
- **WHEN** sync is executed again
- **THEN** no duplicate issue is created
- **AND** existing issue is used for status updates
- **AND** sync result indicates "skipped" (issue already exists)

#### Scenario: Idempotent Status Update

- **GIVEN** a change proposal status has been synced (issue status updated)
- **WHEN** sync is executed again with same status
- **THEN** issue status is not changed
- **AND** no duplicate comments are added
- **AND** sync result indicates "no change"

#### Scenario: Status Update When Issue Already Closed

- **GIVEN** a change proposal with status "applied" has been synced (issue closed)
- **AND** issue is already closed in GitHub
- **WHEN** sync is executed again
- **THEN** issue remains closed
- **AND** no duplicate comments are added
- **AND** sync result indicates "no change"

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

### Requirement: Azure DevOps Backlog Sync Support

The system SHALL support Azure DevOps work items as a backlog adapter in the DevOps sync workflow.

#### Scenario: Selective ADO import preserves native payload for proposal import

- **GIVEN** a user runs `specfact project sync bridge --adapter ado --mode bidirectional --backlog-ids 123456`
- **WHEN** bridge sync fetches that single ADO work item for import as an OpenSpec change proposal
- **THEN** the adapter returns the provider-native work item payload with a populated `fields` object
- **AND** the payload may include convenience keys such as `title`, `state`, or `description` without removing the native `fields` structure
- **AND** proposal import does not fail for a valid work item with `ADO work item must have fields`

#### Scenario: Selective ADO import derives a human-readable change ID when metadata is absent

- **GIVEN** an imported ADO work item has no existing OpenSpec change ID embedded in its description or comments
- **AND** the work item title is `Selective import keeps ADO payload`
- **WHEN** the adapter generates the OpenSpec change proposal during import
- **THEN** the resulting change ID is derived from the title as kebab-case
- **AND** the work item numeric ID remains in source tracking metadata instead of becoming the entire change name

#### Scenario: Duplicate title slug appends deterministic source suffix

- **GIVEN** a title-derived slug already exists in `openspec/changes/`
- **AND** another imported ADO work item with ID `123456` resolves to the same title slug
- **WHEN** the second proposal is created
- **THEN** the final change ID keeps the readable title slug and appends a deterministic suffix such as `-123456`
- **AND** the system does not fall back to using only the raw numeric work item ID as the change name

### Requirement: Azure DevOps Sync Configuration

The system SHALL use explicit Azure DevOps configuration options for DevOps sync and derive sensible defaults when optional values are not provided.

#### Scenario: Configure ADO sync via explicit options

- **WHEN** the user provides `--ado-org`, `--ado-project`, `--ado-base-url`, `--ado-token`, and `--ado-work-item-type`
- **THEN** the adapter uses these values for all ADO API interactions
- **AND** secrets are not persisted in BridgeConfig

#### Scenario: Derive work item type from process template

- **WHEN** `--ado-work-item-type` is not provided
- **THEN** the adapter derives the default work item type from the process template
- **AND** Scrum defaults to "Product Backlog Item"
- **AND** Agile defaults to "User Story"
- **AND** Kanban defaults to "User Story"

### Requirement: Selective Backlog Import into Project Bundles

The system SHALL support importing selected backlog items into a project bundle AND create complete OpenSpec change artifacts (proposal.md, tasks.md, spec deltas) when importing.

#### Scenario: Import specific backlog items by ID

- **WHEN** the user provides explicit backlog item IDs or URLs for import
- **THEN** only those items are imported into the target project bundle
- **AND** OpenSpec change directory is created: `openspec/changes/<change-id>/`
- **AND** `proposal.md` file is created with proper OpenSpec format:
  - Title: `# Change: {title}` (removes `[Change]` prefix if present)
  - Section: `## Why` with rationale content
  - Section: `## What Changes` with description content (formatted as bullet list)
  - Section: `## Impact` (generated or placeholder)
  - Section: `## Source Tracking` with backlog item tracking information
- **AND** `tasks.md` file is created with hierarchical numbered format:
  - Extracted from proposal acceptance criteria if available
  - Placeholder structure if no tasks found
  - Format: `## 1. Implementation`, `- [ ] 1.1 [Description]`
- **AND** spec deltas are created in `specs/<capability>/spec.md`:
  - Affected specs determined from proposal content analysis
  - `## ADDED Requirements` sections with extracted or placeholder requirements
- **AND** OpenSpec validation can be run on the created change
- **AND** no other backlog items are imported

#### Scenario: Create OpenSpec files from imported proposal

- **GIVEN** a backlog item (GitHub issue #111) is imported via `specfact sync bridge --adapter github --bidirectional --backlog-ids 111`
- **WHEN** import completes successfully
- **THEN** `ChangeProposal` object is created and stored in project bundle
- **AND** OpenSpec change directory is created: `openspec/changes/implement-sso-device-code-auth/`
- **AND** `proposal.md` file is written with:
  - Proper title format (no `[Change]` prefix)
  - All required sections (Why, What Changes, Impact)
  - Source Tracking section with GitHub issue reference
- **AND** `tasks.md` file is written with implementation tasks
- **AND** spec deltas are created in `specs/` subdirectory
- **AND** created change can be validated with `openspec validate implement-sso-device-code-auth --strict`

#### Scenario: Handle missing proposal content gracefully

- **GIVEN** a backlog item is imported with minimal content (title only, no body)
- **WHEN** OpenSpec files are created
- **THEN** `proposal.md` is created with:
  - Title from backlog item
  - Placeholder "Why" section if rationale is missing
  - Placeholder "What Changes" section if description is missing
  - Generated "Impact" section with default affected specs
- **AND** `tasks.md` is created with placeholder structure
- **AND** spec deltas are created with placeholder requirements
- **AND** user can manually fill in missing content later

#### Scenario: Handle file creation errors

- **GIVEN** backlog import attempts to create OpenSpec files
- **WHEN** file creation fails (permissions, disk space, invalid path)
- **THEN** error is logged with clear message
- **AND** import continues (proposal still stored in bundle)
- **AND** error is reported in sync result
- **AND** user is informed that OpenSpec files were not created

#### Scenario: Support cross-repo OpenSpec

- **GIVEN** backlog import is executed with `external_base_path` in bridge config
- **WHEN** OpenSpec files are created
- **THEN** files are created in external OpenSpec repository (not code repository)
- **AND** `external_base_path/openspec/changes/<change-id>/` directory structure is used
- **AND** files are created in correct location

### Requirement: Azure DevOps Device Code

The system SHALL use Azure DevOps device code authentication for sync operations with Azure DevOps.

#### Scenario: Azure

- **WHEN** a user requests azure devops device code authentication
- **THEN** the system uses Azure DevOps device code authentication for sync operations with Azure DevOps.
- **AND** uses `azure-identity` library's `DeviceCodeCredential`.
- **AND** zero-configuration (Entra ID integration automatic).
- **AND** leverages corporate SSO/MFA automatically.
- **AND** supported for all Azure DevOps organizations with Entra ID.

### Requirement: GitHub Device Code

The system SHALL use GitHub device code authentication for sync operations with GitHub.

#### Scenario: GitHub

- **WHEN** a user requests github device code authentication
- **THEN** the system uses GitHub device code authentication for sync operations with GitHub.
- **AND** custom RFC 8628 device code flow implementation (no first-party GitHub SDK available).
- **AND** uses GitHub OAuth device authorization endpoint.
- **AND** can use official SpecFact GitHub App (client_id embedded) or user-provided client_id via `--client-id` flag.
- **AND** supports enterprise-grade GitHub instances.

### Requirement: Token Storage & Management

The system SHALL use stored authentication tokens for DevOps sync operations when available.

#### Scenario: Token

- **WHEN** a user requests token storage & management
- **THEN** the system uses stored authentication tokens for DevOps sync operations when available.
- **AND** stores tokens at `~/.specfact/tokens.json` (user home directory).
- **AND** uses format JSON with provider-specific token metadata.
- **AND** enforces permissions 0o600 (owner read/write only).

### Requirement: CLI Integration

The system SHALL provide CLI authentication commands for DevOps sync operations.

#### Scenario: CLI

- **WHEN** a user requests cli integration
- **THEN** the system provides CLI authentication commands for DevOps sync operations.
- **AND** provides command group `specfact auth`.
- **AND** supports `specfact auth azure-devops` command.
- **AND** supports `specfact auth github` command.
- **AND** supports `specfact auth github --client-id YOUR_CLIENT_ID` command.
- **AND** supports `specfact auth status` command.
- **AND** supports `specfact auth clear [--provider azure-devops|github]` command.

### Requirement: Key Architectural Decisions

The system SHALL follow documented authentication architecture decisions for DevOps sync operations.

#### Scenario: Key

- **WHEN** the system performs authentication operations
- **THEN** the system follows documented authentication architecture decisions for DevOps sync operations.
- **AND** Azure uses `azure-identity` SDK; GitHub requires custom RFC 8628 implementation.
- **AND** Plaintext JSON storage for MVP. Encryption added Phase 2.
- **AND** No token auto-refresh in MVP. Phase 2 adds background refresh.
- **AND** allows users to still use `--pat` flag; existing workflows preserved.
- **AND** Auto-detects configured provider; users can override with flags.

### Requirement: Backlog Dependency Graph Analysis

The system SHALL support analyzing logical dependencies in backlog items (epic → feature → story → task hierarchies) using a provider-agnostic dependency graph model.

#### Scenario: Build dependency graph from backlog items

- **GIVEN** backlog items from a provider (GitHub, ADO, Jira)
- **WHEN** `BacklogGraphBuilder` processes the items with a template (ado_scrum, github_projects, jira_kanban)
- **THEN** items are converted to unified `BacklogItem` model with inferred types (epic, feature, story, task)
- **AND** dependencies are extracted as `Dependency` edges (parent_child, blocks, relates_to, implements)
- **AND** a `BacklogGraph` is built with items, dependencies, and analysis metadata
- **AND** graph includes transitive closure, cycles_detected, and orphans

#### Scenario: GitHub relationship enrichment for dependency graph

- **GIVEN** GitHub issues include link/reference metadata in issue bodies, timeline, or linked issue relations
- **WHEN** `GitHubAdapter.fetch_relationships(project_id)` is executed for backlog graph building
- **THEN** dependency edges are emitted for supported relations (`blocks`, `blocked_by`, `parent_child`, `relates_to`)
- **AND** emitted relation types are normalized to `DependencyType`-compatible values consumed by `BacklogGraphBuilder`
- **AND** resulting graph metrics (`with_dependencies`, `orphans`) reflect discovered relations instead of all-orphan fallback for linked issues.

#### Scenario: ADO relationship extraction parity

- **GIVEN** ADO work items include relation links (hierarchy, predecessor/successor, related)
- **WHEN** `AdoAdapter.fetch_relationships(project_id)` is executed
- **THEN** relations are normalized into the same dependency model used by other providers
- **AND** parent-child and blocker semantics are preserved for release-readiness and impact analysis.

#### Scenario: Analyze dependencies with custom template

- **GIVEN** a user provides custom YAML config to override template rules
- **WHEN** `BacklogGraphBuilder` is initialized with custom config
- **THEN** custom type mapping rules override built-in template rules
- **AND** custom dependency rules override built-in template rules
- **AND** custom status mapping rules override built-in template rules

#### Scenario: Detect circular dependencies

- **GIVEN** a backlog graph with circular dependencies (e.g., Task A blocks Task B, Task B blocks Task A)
- **WHEN** `DependencyAnalyzer.detect_cycles()` is called
- **THEN** all circular dependency chains are detected and returned
- **AND** cycles are stored in `graph.cycles_detected` as lists of item IDs

#### Scenario: Compute critical path

- **GIVEN** a backlog graph with dependency chains
- **WHEN** `DependencyAnalyzer.critical_path()` is called
- **THEN** the longest dependency chain is identified
- **AND** critical path is returned as a list of item IDs
- **AND** computation completes in < 1 second for graphs with 1000+ items

#### Scenario: Analyze impact of item changes

- **GIVEN** a backlog graph and a specific item ID
- **WHEN** `DependencyAnalyzer.impact_analysis(item_id)` is called
- **THEN** returns direct_dependents (items directly depending on this one)
- **AND** returns transitive_dependents (all items downstream)
- **AND** returns blockers (items blocking this one from completion)
- **AND** returns estimated_impact_count (total items affected)

### Requirement: Backlog Sync Command

The system SHALL provide a CLI command for synchronizing backlog state into SpecFact plan bundles with baseline comparison.

#### Scenario: Sync backlog to plan bundle

- **GIVEN** a backlog provider (GitHub, ADO) is configured
- **WHEN** user runs `specfact backlog sync --project-id owner/repo --adapter github --output-format plan`
- **THEN** adapter's `fetch_all_issues(project_id)` method is called to fetch all backlog items
- **AND** adapter's `fetch_relationships(project_id)` method is called to fetch all relationships
- **AND** dependency graph is built using `BacklogGraphBuilder` with fetched data
- **AND** graph is converted to plan bundle format
- **AND** plan bundle is saved to `.specfact/plans/backlog-<timestamp>.yaml` with `backlog_graph` field (optional, v1.2 format)
- **AND** plan bundle includes dependency graph data in `ProjectBundle.backlog_graph` field

#### Scenario: Sync with baseline comparison

- **GIVEN** a baseline file from previous sync exists (`.specfact/backlog-baseline.json` in JSON format)
- **WHEN** user runs `specfact backlog sync --project-id owner/repo --baseline-file .specfact/backlog-baseline.json`
- **THEN** baseline graph is loaded from JSON file using `BacklogGraph.from_json()` (JSON format for performance with large graphs)
- **AND** current graph is built using adapter's `fetch_all_issues()` and `fetch_relationships()` methods
- **AND** delta is computed comparing baseline vs current graph
- **AND** delta shows added, updated, deleted items
- **AND** delta shows new dependencies and status transitions

### Requirement: Backlog Delta Commands

The system SHALL provide CLI commands for analyzing backlog changes and their impact.

#### Scenario: Show backlog delta status

- **GIVEN** a backlog with changes since last sync
- **WHEN** user runs `specfact backlog delta status --project-id owner/repo --adapter github`
- **THEN** shows new items (added)
- **AND** shows modified items (field changes)
- **AND** shows deleted items
- **AND** shows status transitions
- **AND** shows new dependencies

#### Scenario: Analyze backlog delta impact

- **GIVEN** backlog changes have been detected
- **WHEN** user runs `specfact backlog delta impact --project-id owner/repo --adapter github`
- **THEN** uses dependency graph to trace from changed items
- **AND** shows directly changed items count
- **AND** shows downstream affected items count
- **AND** shows total blast radius (changed + affected)

#### Scenario: Estimate delta cost

- **GIVEN** backlog changes have been detected
- **WHEN** user runs `specfact backlog delta cost-estimate --project-id owner/repo --adapter github`
- **THEN** estimates effort of delta changes based on item types and dependencies
- **AND** provides effort breakdown by item type

#### Scenario: Analyze rollback impact

- **GIVEN** backlog changes have been detected
- **WHEN** user runs `specfact backlog delta rollback-analysis --project-id owner/repo --adapter github`
- **THEN** analyzes what breaks if changes are reverted
- **AND** identifies dependent items that would be affected
- **AND** shows potential conflicts or blockers

### Requirement: Impact-Oriented Command Discoverability

The system SHALL present backlog command help in an impact-oriented order where command groups are listed before leaf commands and high-frequency flows appear before lower-frequency operations.

#### Scenario: Backlog help lists groups first

- **GIVEN** a user opens backlog help
- **WHEN** `specfact backlog -h` (or module-local `backlog --help`) is rendered
- **THEN** command groups (e.g., `ceremony`, `delta`) appear before leaf commands
- **AND** high-impact workflow commands (`sync`, `verify-readiness`, `analyze-deps`) appear before lower-frequency commands.

### Requirement: Release Readiness Verification

The system SHALL provide a CLI command for verifying backlog items are ready for release.

#### Scenario: Verify release readiness

- **GIVEN** backlog items targeted for release
- **WHEN** user runs `specfact backlog verify-readiness --project-id owner/repo --adapter github --target-items "FEATURE-1,FEATURE-2"`
- **THEN** checks all blockers are resolved (no blocking items with open status)
- **AND** checks no circular dependencies exist
- **AND** checks all child items are completed (if parent specified)
- **AND** checks status transitions are valid
- **AND** exits with code 0 if ready, 1 if blockers found

#### Scenario: Verify readiness for all closed items

- **GIVEN** backlog items with status "closed" or "resolved"
- **WHEN** user runs `specfact backlog verify-readiness --project-id owner/repo --adapter github` (no target-items)
- **THEN** checks all closed/resolved items for blockers
- **AND** checks all closed/resolved items for incomplete children
- **AND** reports any issues found

### Requirement: Project Backlog Integration

The system SHALL support linking projects to backlog providers and integrating backlog features into project workflows.

#### Scenario: Link project to backlog provider

- **GIVEN** a SpecFact project exists with `ProjectBundle`
- **WHEN** user runs `specfact project link-backlog --project-name my-project --adapter github --project-id owner/repo`
- **THEN** backlog configuration is stored in `ProjectMetadata` module extension `backlog_core.backlog_config` (not separate config file):

  ```python
  metadata.set_extension("backlog_core", "backlog_config", {
      "adapter": "github",
      "project_id": "owner/repo",
  })
  ```

- **AND** bundle is saved with updated metadata (atomic write)
- **AND** backlog commands auto-use this project's backlog configuration via metadata extension lookup.

#### Scenario: Project health check with backlog metrics

- **GIVEN** a project is linked to a backlog provider (config in `ProjectMetadata` extension `backlog_core.backlog_config`)
- **WHEN** user runs `specfact project health-check --project-name my-project`
- **THEN** adapter's `fetch_all_issues()` and `fetch_relationships()` methods are called to build graph
- **AND** shows spec-code alignment (from existing enforce command)
- **AND** shows backlog maturity metrics (from `DependencyAnalyzer.coverage_analysis()`)
- **AND** shows dependency graph health (cycles, orphans, coverage)
- **AND** shows release readiness status
- **AND** provides action items for improvement
- **AND** output uses `rich.table.Table` for metrics and `rich.panel.Panel` for sections (consistent with existing console patterns)

#### Scenario: Regenerate reports concise mismatch summary by default

- **GIVEN** a project is linked to a backlog provider and plan/backlog mismatches exist
- **WHEN** user runs `specfact project regenerate --project-name my-project`
- **THEN** the command reports a single mismatch summary count
- **AND** does not print per-item mismatch lines by default
- **AND** exits successfully unless strict mode is requested

#### Scenario: Regenerate strict mode fails with detailed mismatch output

- **GIVEN** a project is linked to a backlog provider and plan/backlog mismatches exist
- **WHEN** user runs `specfact project regenerate --project-name my-project --strict --verbose`
- **THEN** the command prints per-item mismatch lines
- **AND** exits with code `1`

#### Scenario: Integrated DevOps workflow

- **GIVEN** a project is linked to a backlog provider (config in `ProjectMetadata` extension `backlog_core.backlog_config`)
- **WHEN** user runs `specfact project devops-flow --project-name my-project --stage plan --action generate-roadmap`
- **THEN** adapter's `fetch_all_issues()` and `fetch_relationships()` methods are called to build graph
- **AND** uses backlog dependency graph to create release timeline
- **AND** identifies critical path from dependency graph using `DependencyAnalyzer.critical_path()`
- **AND** estimates timeline duration based on critical path
- **AND** generates roadmap markdown file with console output using `rich.table.Table` and `rich.panel.Panel`

#### Scenario: DevOps workflow - develop stage

- **GIVEN** a project is linked to a backlog provider
- **WHEN** user runs `specfact project devops-flow --project-name my-project --stage develop --action sync`
- **THEN** syncs spec plan + backlog state
- **AND** detects conflicts between spec and backlog
- **AND** reports conflicts if found
- **AND** shows sync status

#### Scenario: DevOps workflow - review stage

- **GIVEN** a project is linked to a backlog provider
- **WHEN** user runs `specfact project devops-flow --project-name my-project --stage review --action validate-pr`
- **THEN** extracts backlog item references from PR description
- **AND** verifies items are implemented in spec plan
- **AND** runs enforce command to validate contracts
- **AND** reports validation results

#### Scenario: DevOps workflow - release stage

- **GIVEN** a project is linked to a backlog provider
- **WHEN** user runs `specfact project devops-flow --project-name my-project --stage release --action verify`
- **THEN** runs full health check
- **AND** gets items targeted for release
- **AND** checks readiness using `verify-readiness` command
- **AND** generates release notes if ready
- **AND** exits with code 0 if ready, 1 if blockers found

#### Scenario: DevOps workflow - monitor stage

- **GIVEN** a project is linked to a backlog provider
- **WHEN** user runs `specfact project devops-flow --project-name my-project --stage monitor --action health-check`
- **THEN** runs continuous health metrics check
- **AND** alerts on drift (spec-code misalignment, backlog issues)
- **AND** reports current project status

### Requirement: Backlog Configuration in Spec YAML

The system SHALL support backlog configuration in `.specfact/spec.yaml` for provider linking, type mapping, and auto-sync.

#### Scenario: Configure backlog in spec YAML

- **GIVEN** a `.specfact/spec.yaml` file (project-level defaults, separate from bundle-specific project metadata extension)
- **WHEN** backlog_config section is added:

  ```yaml
  backlog_config:
    version: "1.0"
    provider:
      adapter: "github"
      project: "owner/repo"
    type_mapping:
      template: "github_projects"
      overrides:
        - labels: ["epic", "meta"]
          type: epic
    dependency_rules:
      template: "github_projects"
    auto_sync:
      enabled: true
      interval: "hourly"
      baseline_file: ".specfact/backlog-baseline.json"
  ```

- **THEN** backlog commands use this configuration as defaults (can be overridden by bundle-specific config)
- **AND** auto-sync runs according to interval setting
- **AND** type mapping overrides are applied
- **AND** baseline file path is specified (JSON format for performance)

### Requirement: DevOps Stages Configuration

The system SHALL support DevOps flow stages configuration in `.specfact/spec.yaml`.

#### Scenario: Configure DevOps stages in spec YAML

- **GIVEN** a `.specfact/spec.yaml` file
- **WHEN** devops_stages section is added:

  ```yaml
  devops_stages:
    plan:
      - generate-roadmap
      - verify-dependencies
    develop:
      - sync-spec-backlog
      - detect-drift
    review:
      - validate-pr-items
      - enforce-contracts
    release:
      - verify-readiness
      - generate-release-notes
    monitor:
      - health-check
      - alert-on-drift
  ```

- **THEN** `devops-flow` command uses these stage definitions
- **AND** available actions for each stage are defined by configuration

### Requirement: Dependency review packet and coordination artifacts (E4 extension)

The system SHALL support exporting coordination artifacts from dependency analysis: "dependency contract" per edge (what/when/acceptance), ROAM list seed (for SAFe PI planning), and "critical path narrative" for humans (short, evidence-based). `specfact backlog analyze-deps` SHALL support `--export json|md` and SHALL be able to export a "dependency review packet" (Markdown).

**Rationale**: Plan E4—teams need dependency review packet for coordination and SAFe ROAM.

#### Scenario: Export dependency review packet

- **GIVEN** a backlog graph has been built and analyzed
- **WHEN** user runs `specfact backlog analyze-deps --export md` (or equivalent)
- **THEN** the system emits a dependency review packet (Markdown) that includes: dependency contract per edge (what/when/acceptance), ROAM list seed when applicable, and critical path narrative (short, evidence-based)
- **AND** `--export json` emits machine-readable equivalent when specified

**Acceptance Criteria**:

- `backlog analyze-deps` can export a "dependency review packet" (Markdown); coordination artifacts (dependency contract, ROAM seed, critical path narrative) are included when applicable.

