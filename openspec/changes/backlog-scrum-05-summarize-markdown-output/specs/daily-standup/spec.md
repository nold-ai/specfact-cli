## MODIFIED Requirements

### Requirement: Standup summary prompt (--summarize)

The system SHALL support a `--summarize` flag on `specfact backlog daily` that produces a **prompt** (instructions plus applied filters and filtered standup output) suitable for use in an interactive slash command (e.g. `specfact.daily`) or copy-paste to Copilot, so an LLM can generate a meaningful **summary of the daily standup status**. The prompt content for item bodies and comments SHALL be provided as normalized Markdown text only (no raw HTML tags or entities), regardless of how the underlying provider stores or formats those fields.

#### Scenario: --summarize outputs prompt with filters and data (Markdown-only content)
- **Given**: Backlog items in the current scope (same as standup: state, iteration/sprint, assignee, limit) and the user runs `specfact backlog daily --summarize` (stdout) or `--summarize-to <path>` (write to file)
- **When**: The command runs with the same filters as the standup view
- **Then**: The system outputs (to stdout or to the given path) a prompt that includes: (1) brief instruction that the following data is the current standup view and the LLM should generate a concise standup summary; (2) the applied filter context (adapter, state, sprint, assignee, limit); (3) per-item data including **body (description)** and **comments (annotations)** when available, plus ID, title, status, assignees, last updated, progress, blockers, optional value score, so the LLM can produce a **meaningful** summary
- **And**: The per-item body and comment fields in the prompt are formatted as Markdown without raw HTML tags or HTML entities (e.g. no `<p>`, `<br />`, `&lt;div&gt;`)
- **And**: The output is formatted so it can be pasted into Copilot or used as input to a slash command (e.g. `specfact.daily`) to produce a standup summary

