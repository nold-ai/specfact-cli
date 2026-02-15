## MODIFIED Requirements

### Requirement: Devops Sync
The existing sync behavior SHALL be mediated by unified sync-kernel sessions.

#### Scenario: Existing sync entry uses session orchestration
- **GIVEN** sync operation starts from supported sync command path
- **WHEN** operation executes
- **THEN** a sync session is created with session ID
- **AND** status can be queried until completion.

#### Scenario: Sync writes require explicit apply mode
- **GIVEN** sync preview is generated
- **WHEN** apply mode is not requested
- **THEN** no upstream writes are performed
- **AND** output clearly indicates preview-only execution.
