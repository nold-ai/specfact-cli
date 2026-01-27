## MODIFIED Requirements

### Requirement: Backlog Item Refinement Command

The system SHALL provide a `specfact backlog refine` command that enables teams to standardize backlog items using AI-assisted template matching and refinement.

#### Scenario: Limit refinement batch size

- **GIVEN** a backlog refinement session with more than N items
- **WHEN** the user specifies `--limit N`
- **THEN** the command processes at most N items in the session
- **AND** the summary output reflects the applied limit.

#### Scenario: Graceful cancel/skip during refinement

- **GIVEN** an interactive refinement session is waiting for pasted content
- **WHEN** the user enters `:skip`
- **THEN** the current item is skipped without updating the remote backlog.
- **WHEN** the user enters `:quit` or `:abort`
- **THEN** the command exits gracefully with a summary
- **AND** no additional items are processed.

#### Scenario: ADO sprint filter uses iteration path when provided

- **GIVEN** ADO items with iteration paths that share the same sprint name
- **WHEN** the user passes a full iteration path in `--sprint`
- **THEN** the command matches against `System.IterationPath` and does not fall back to name-only matching.
- **AND** ambiguous name-only matches require an explicit iteration path.

#### Scenario: Default to current ADO iteration when sprint omitted

- **GIVEN** an ADO backlog refinement session without `--sprint`
- **WHEN** a current active iteration is available for the team
- **THEN** the command defaults to that current iteration path for filtering
- **AND** reports a clear error if no current iteration can be resolved.

#### Scenario: Case-insensitive state and assignee filtering

- **GIVEN** backlog items with state "New" and assignee "Jane Doe"
- **WHEN** the user passes `--state new --assignee "jane doe"`
- **THEN** the items are matched without case sensitivity.

#### Scenario: ADO description preserves Markdown

- **GIVEN** a refined backlog item with Markdown body
- **WHEN** the item is written back to Azure DevOps
- **THEN** the description renders correctly (Markdown or HTML) without raw Markdown artifacts.
