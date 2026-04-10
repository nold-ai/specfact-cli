## ADDED Requirements

### Requirement: Normalize HTML and Markdown for summarize output

The system SHALL normalize all backlog item descriptions and comments included in `specfact backlog daily --summarize` and `--summarize-to` output so that the resulting prompt contains **only Markdown-formatted text** (no raw HTML tags or HTML entities), regardless of whether the underlying provider stores content as HTML (e.g. ADO) or Markdown (e.g. GitHub, Markdown-style ADO comments).

#### Scenario: HTML comments from ADO are converted to Markdown

- **WHEN** `specfact backlog daily --summarize` or `--summarize-to` includes work items whose description or comments are stored as HTML (e.g. ADO discussion/comments)
- **THEN** the system converts that HTML content into readable Markdown before including it in the summarize prompt
- **AND** the resulting output does not contain raw HTML tags or un-decoded HTML entities (e.g. `&lt;div&gt;`, `<p>`, `<br />`)

#### Scenario: Existing Markdown comments are preserved as Markdown

- **WHEN** `specfact backlog daily --summarize` or `--summarize-to` includes items whose description or comments are already stored as Markdown (e.g. GitHub issues, Markdown-formatted ADO comments)
- **THEN** the system preserves the original Markdown semantics when building the summarize prompt (headings, lists, code fences, emphasis)
- **AND** the system does not degrade Markdown into a less structured format (e.g. by stripping list markers or collapsing headings)

#### Scenario: Mixed HTML and Markdown sources produce a consistent Markdown prompt

- **WHEN** the daily summarize command aggregates items from sources that use different underlying formats (HTML and Markdown)
- **THEN** the combined summarize output is a single, consistent Markdown document suitable for LLM consumption
- **AND** no raw HTML tags or entities appear anywhere in the per-item body or comments sections

### Requirement: Environment-aware rendering for summarize output

The system SHALL render the same normalized Markdown summarize content differently depending on whether it is running in an interactive terminal session or in a non-interactive / CI environment, while always preserving a prompt-ready Markdown representation that tools can consume.

#### Scenario: Interactive terminal shows rich Markdown view

- **WHEN** a user runs `specfact backlog daily --summarize` in an interactive terminal that supports rich output (e.g. TTY, not redirected to a file)
- **THEN** the CLI MAY render the summarize content using a Markdown-aware terminal view (for example, Rich Markdown rendering)
- **AND** the user sees a readable, formatted standup summary prompt (headings, lists, emphasis) instead of raw Markdown or HTML
- **AND** the underlying content remains logically the same as the Markdown text used for `--summarize-to` (same sections and text, just rendered differently)

#### Scenario: Non-interactive or CI environments emit plain Markdown

- **WHEN** `specfact backlog daily --summarize` or `--summarize-to` is run in a non-interactive environment (e.g. CI/CD job, output redirected to a file or piped)
- **THEN** the system emits plain, prompt-ready Markdown text without ANSI color codes or interactive formatting controls
- **AND** the output still satisfies the existing summarize requirement to include instruction text, filter context, and per-item data (including normalized body and comments)

#### Scenario: Summarize-to file output is always Markdown-only

- **WHEN** the user runs `specfact backlog daily --summarize-to <path>`
- **THEN** the file at `<path>` contains only normalized Markdown content (no raw HTML tags or entities, no terminal control codes)
- **AND** the file is suitable for direct copy/paste into IDE slash commands or Copilot prompts without additional cleanup
