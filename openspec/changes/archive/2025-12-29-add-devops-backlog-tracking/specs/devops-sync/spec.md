# DevOps Backlog Tracking Capability

## ADDED Requirements

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

The system SHALL support updating existing issue bodies when proposal content changes, leveraging tool-native change tracking.

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

#### Scenario: Skip Update When Flag Disabled

- **GIVEN** a change proposal with existing GitHub issue
- **AND** proposal content has changed (hash differs)
- **AND** `--update-existing` flag is NOT enabled (default: False)
- **WHEN** DevOps sync is executed
- **THEN** issue body is not updated
- **AND** sync result indicates "skipped" (update disabled)
- **AND** user must explicitly enable with `--update-existing` flag

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

#### Scenario: Optional Comment for Significant Changes

- **GIVEN** a change proposal with existing GitHub issue
- **AND** proposal content contains "BREAKING" or "major" scope change keywords
- **AND** content has changed and `--update-existing` is enabled
- **WHEN** DevOps sync is executed
- **THEN** issue body is updated
- **AND** optional comment is added indicating significant change
- **AND** comment highlights breaking changes or major scope changes
- **NOTE**: Comment is optional, not required - tool-native history is primary tracking
