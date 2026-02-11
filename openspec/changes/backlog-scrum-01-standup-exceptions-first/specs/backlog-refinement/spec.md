# Backlog refinement comment context (E1 scoped delta)

## MODIFIED Requirements

### Requirement: Export refine context includes comments without truncation by default

The system SHALL include issue/work item comments in `specfact backlog refine --export-to-tmp` output so exported refinement context is complete by default. Comment content SHALL not be truncated unless explicitly requested by the user.

**Rationale**: Refinement quality depends on full historical discussion context, especially for ADO work items where key decisions are often in comments.

#### Scenario: Refine export contains full comments by default

**Given**: The user runs `specfact backlog refine --export-to-tmp` for an adapter that supports comments

**And**: A backlog item has comments in the provider

**When**: No explicit comment-window options are provided

**Then**: The exported markdown includes all comments for the item

**And**: Comment text is preserved without truncation

#### Scenario: Refine export includes copilot instruction block

**Given**: The user runs `specfact backlog refine --export-to-tmp`

**When**: The export file is generated

**Then**: The file starts with a clear copilot instruction/prompt block before item entries

**And**: The instruction block tells the user/copilot how to process item sections consistently

**And**: The instruction block explicitly states that the refined artifact for import must omit the instruction block and contain only item sections

#### Scenario: Refine export instructions match interactive refinement rules

**Given**: The user runs `specfact backlog refine --export-to-tmp`

**When**: Copilot reads the exported file

**Then**: The exported instruction block includes the same refinement rules used in interactive mode (preserve scope, required-section completion, ambiguity notes, provider-aware formatting)

**And**: Each item includes template guidance (target template, required sections, optional sections) so export processing can follow the same structure as interactive prompts

### Requirement: Refine preview includes scoped comment context

The system SHALL include issue/work item comments in `specfact backlog refine --preview` output with a scoped default to keep terminal output readable.

**Rationale**: Refinement decisions depend on discussion history, but preview output must stay concise for day-to-day CLI usage.

#### Scenario: Refine preview shows last two comments by default

**Given**: The user runs `specfact backlog refine --preview` for an adapter that supports comments

**And**: A backlog item has multiple comments

**When**: No explicit comment-window options are provided

**Then**: The preview shows the two newest comments for that item

#### Scenario: First-comments limit on refine preview

**Given**: The user runs `specfact backlog refine --preview --first-comments 5`

**When**: A backlog item has more than five comments

**Then**: The preview comment section contains only the first five comments for that item

#### Scenario: Last-comments limit on refine preview

**Given**: The user runs `specfact backlog refine --preview --last-comments 4`

**When**: A backlog item has more than four comments

**Then**: The preview comment section contains only the last four comments for that item

#### Scenario: Preview shows comment-fetch progress for large batches

**Given**: The user runs `specfact backlog refine --preview` for many backlog items

**When**: The command fetches comments across adapters

**Then**: The CLI shows progress feedback with item position (for example `Fetching issue n/m ...`) until comment fetch completes

#### Scenario: Preview comment output is clearly scoped

**Given**: The preview includes comments for an item

**When**: The command renders preview detail

**Then**: Each comment is rendered in a clearly scoped block-style container so users can distinguish comment boundaries from body/metadata

#### Scenario: Preview indicates when no comments exist

**Given**: The preview fetches comments for an item

**When**: No comments are available for that issue/work item

**Then**: The preview still shows a comments section with an explicit "no comments found" hint

**Acceptance Criteria**:

- Default refine preview includes the last two comments per item.
- Limits are optional and deterministic for preview output.
- If both first and last limits are provided, command fails with a clear validation error.
- `--export-to-tmp` always includes full comments, independent of preview comment-window options.
- Preview provides visible comment-fetch progress for multi-item runs.
- Preview comment rendering uses block-style formatting to make comment boundaries explicit.
- Preview explicitly indicates when an item has no comments.

### Requirement: Refine write prompts include comment context

The system SHALL include issue/work item comments in generated refinement prompts during `specfact backlog refine --write` so AI-assisted refinement reflects the latest discussion state.

**Rationale**: Comment threads are the living source of truth; prompt context must include them to avoid refining against stale issue bodies.

#### Scenario: Write-mode prompt includes full comments by default

**Given**: The user runs `specfact backlog refine --write`

**And**: The selected issue/work item has comments

**When**: No explicit comment-window options are provided

**Then**: The generated refinement prompt includes all available comments for that item

#### Scenario: Write-mode prompt applies comment-window options

**Given**: The user runs `specfact backlog refine --write --last-comments 5`

**When**: The item has more than five comments

**Then**: The generated refinement prompt includes only the configured comment window

### Requirement: Refine supports first/last issue windowing

The system SHALL support optional issue window controls for `specfact backlog refine` so users can process the first or last subset of currently filtered backlog items.

**Rationale**: Teams often need a deterministic window over a larger result set (for example oldest/newest slice) without re-running broad filters manually.

#### Scenario: First-issues limit on refine

**Given**: The user runs `specfact backlog refine --first-issues 10`

**When**: More than ten items match after filters/refinement eligibility rules

**Then**: The command sorts items by issue/work-item number ascending and processes only the first ten (lowest IDs / oldest)

#### Scenario: Last-issues limit on refine

**Given**: The user runs `specfact backlog refine --last-issues 10`

**When**: More than ten items match after filters/refinement eligibility rules

**Then**: The command sorts items by issue/work-item number ascending and processes only the last ten (highest IDs / newest)

#### Scenario: First/last issues flags are mutually exclusive

**Given**: The user runs `specfact backlog refine --first-issues 5 --last-issues 5`

**When**: The command validates options

**Then**: The command exits with a clear validation error

### Requirement: ADO comments are fetched from dedicated comments API

For Azure DevOps, the system SHALL fetch work item comments via the dedicated comments endpoint and handle comment pagination to collect complete history.

**Rationale**: ADO work item retrieval and comments retrieval are separate API resources and versions.

#### Scenario: ADO comment pagination retrieves complete history

**Given**: An ADO work item has comments spanning multiple comment pages

**When**: The adapter fetches comments for refine or daily context

**Then**: The adapter calls the ADO comments API and follows continuation tokens until complete

**And**: All comments are returned in stable order for downstream rendering/export
