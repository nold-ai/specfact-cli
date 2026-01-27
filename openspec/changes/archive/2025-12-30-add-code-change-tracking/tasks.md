# Implementation Tasks: Add Code Change Tracking and Progress Comments

## Prerequisites

- [x] **Dependency Check**: Verify required changes are implemented
  - [x] DevOps backlog tracking (`add-devops-backlog-tracking`) exists and is applied
  - [x] Can read OpenSpec change proposals via adapter
  - [x] Can create and update GitHub issues

## 1. Code Change Detection

- [x] 1.1 Add code change detection logic (`src/specfact_cli/sync/bridge_sync.py`)
  - [x] 1.1.1 Detect git commits related to change proposals (via commit messages, file paths)
  - [x] 1.1.2 Track file modifications related to implementation
  - [x] 1.1.3 Generate progress summaries from code changes
  - [x] 1.1.4 Store last detection timestamp in source tracking metadata
  - [x] 1.1.5 Add type hints and contract decorators

- [x] 1.2 Add git integration utilities (`src/specfact_cli/utils/code_change_detector.py`)
  - [x] 1.2.1 Parse git commit messages for change proposal references
  - [x] 1.2.2 Match file paths to change proposal scope
  - [x] 1.2.3 Extract commit metadata (author, date, message)
  - [x] 1.2.4 Handle git repository detection (cross-repository support)

## 2. Progress Comment Generation

- [x] 2.1 Add progress comment formatting (`src/specfact_cli/utils/code_change_detector.py`)
  - [x] 2.1.1 Format implementation progress details (files changed, commits, milestones)
  - [x] 2.1.2 Include code change summary in comment
  - [x] 2.1.3 Add timestamp and author information
  - [x] 2.1.4 Support markdown formatting in comments

- [x] 2.2 Extend GitHubAdapter for progress comments (`src/specfact_cli/adapters/github.py`)
  - [x] 2.2.1 Add `_add_progress_comment()` method
  - [x] 2.2.2 Extend `export_artifact()` to handle `artifact_key="code_change_progress"`
  - [x] 2.2.3 Support progress comment formatting with implementation details
  - [x] 2.2.4 Handle comment errors gracefully

## 3. Bridge Sync Integration

- [x] 3.1 Extend BridgeSync for code change tracking (`src/specfact_cli/sync/bridge_sync.py`)
  - [x] 3.1.1 Add code change detection to `export_change_proposals_to_devops()`
  - [x] 3.1.2 Compare detected changes with last detection timestamp
  - [x] 3.1.3 Generate progress comments when code changes detected
  - [x] 3.1.4 Store progress comment history in source tracking metadata

- [x] 3.2 Add progress comment tracking
  - [x] 3.2.1 Store progress comments in `source_tracking.source_metadata.progress_comments`
  - [x] 3.2.2 Track last code change detection timestamp
  - [x] 3.2.3 Support multiple progress comments per issue
  - [x] 3.2.4 Prevent duplicate comments (check comment history)

## 4. CLI Command Extensions

- [x] 4.1 Extend sync bridge command (`src/specfact_cli/commands/sync.py`)
  - [x] 4.1.1 Add `--track-code-changes` flag to enable code change detection
  - [x] 4.1.2 Add `--add-progress-comment` flag to add comments to existing issues
  - [x] 4.1.3 Support code change detection via git history or file monitoring
  - [x] 4.1.4 Update command docstring to document new flags

- [x] 4.2 Add command examples and documentation
  - [x] 4.2.1 Document `--track-code-changes` usage
  - [x] 4.2.2 Document `--add-progress-comment` usage
  - [x] 4.2.3 Add examples for different scenarios

## 5. Testing

- [x] 5.1 Unit tests for code change detection (`tests/unit/utils/test_code_change_detector.py`)
  - [x] 5.1.1 Test git commit parsing
  - [x] 5.1.2 Test file path matching
  - [x] 5.1.3 Test progress summary generation
  - [x] 5.1.4 Test timestamp tracking

- [x] 5.2 Unit tests for progress comments (`tests/unit/adapters/test_github.py`)
  - [x] 5.2.1 Test progress comment formatting
  - [x] 5.2.2 Test comment addition via GitHubAdapter
  - [x] 5.2.3 Test error handling

- [x] 5.3 Integration tests
  - [x] 5.3.1 Test end-to-end code change detection and comment addition
  - [x] 5.3.2 Test with real git repository
  - [x] 5.3.3 Test with real GitHub issues
  - [x] 5.3.4 Test idempotency (multiple syncs)

## 6. Documentation

- [x] 6.1 Update CLI command documentation
  - [x] 6.1.1 Document `--track-code-changes` flag
  - [x] 6.1.2 Document `--add-progress-comment` flag
  - [x] 6.1.3 Add usage examples

- [x] 6.2 Update architecture documentation
  - [x] 6.2.1 Document code change detection approach
  - [x] 6.2.2 Document progress comment workflow
  - [x] 6.2.3 Document source tracking metadata extensions

- [x] 6.3 Update CHANGELOG.md
  - [x] 6.3.1 Add entry for code change tracking feature
  - [x] 6.3.2 Note progress comment capability
