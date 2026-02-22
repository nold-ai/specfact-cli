# git-worktree-lifecycle Specification

## Purpose
TBD - created by archiving change workflow-01-git-worktree-management. Update Purpose after archive.
## Requirements
### Requirement: Worktree Branch Guardrails

The system SHALL enforce branch policy when managing git worktrees.

#### Scenario: Reject protected branches for create

- **GIVEN** a user runs the helper with `create dev` or `create main`
- **WHEN** branch policy validation runs
- **THEN** the command fails with a clear error
- **AND** no worktree is created.

#### Scenario: Reject unsupported branch type

- **GIVEN** a user runs `create release/1.2.0`
- **WHEN** branch policy validation runs
- **THEN** the command fails with an allowed-types message.

### Requirement: Deterministic Worktree Paths

The system SHALL map each branch to a deterministic worktree folder.

#### Scenario: Create feature branch worktree path

- **GIVEN** branch `feature/abc-123-test-flow`
- **WHEN** the helper computes the target path
- **THEN** the path is `../specfact-cli-worktrees/feature/abc-123-test-flow`
- **AND** `git worktree add` uses that path.

### Requirement: Safe Local Cleanup After Merge

The system SHALL provide a cleanup command for local worktree lifecycle management.

#### Scenario: Cleanup removes mapped worktree and prunes records

- **GIVEN** a merged branch with an existing mapped worktree
- **WHEN** the user runs `cleanup <branch>`
- **THEN** the helper removes the mapped worktree path
- **AND** runs local prune cleanup
- **AND** reports completion steps.

