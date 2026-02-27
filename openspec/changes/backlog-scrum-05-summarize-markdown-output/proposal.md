## Why

The current `specfact backlog daily --summarize/--summarize-to` output often contains raw HTML fragments and entities from ADO work item comments, mixed with Markdown-formatted text from GitHub and ADO. This makes the standup summary prompt hard to read for humans and noisy for LLMs, even though the underlying data is correct.

## What Changes

- Normalize backlog comments and descriptions used by `specfact backlog daily --summarize/--summarize-to` so that:
  - HTML-formatted content is converted into clean Markdown before it is included in the prompt.
  - Existing Markdown content is preserved as Markdown (no lossy reformatting).
- For interactive terminal sessions:
  - Render the summarized standup prompt using a Markdown-aware terminal view (e.g. Rich Markdown rendering) so users see a readable, formatted view instead of raw Markdown or HTML.
- For non-interactive / CI environments and plain terminals:
  - Fall back to emitting structured Markdown text directly (never raw HTML), preserving prompt-ready formatting for copy/paste into Copilot or slash commands.
- Ensure the summarize output logic can distinguish between:
  - Interactive rich terminal usage (formatted view, still based on the same Markdown text).
  - Non-interactive/CI usage (plain Markdown text, no color/control codes).

## Capabilities

### New Capabilities
- `backlog-daily-markdown-normalization`: Normalize backlog item bodies and comments into Markdown-only text for daily standup summarize prompts, with environment-aware rendering (rich Markdown view in interactive terminals, plain Markdown in CI/non-interactive mode).

### Modified Capabilities
- `daily-standup`: Clarify that the `--summarize/--summarize-to` scenarios must:
  - Include only Markdown (no raw HTML fragments or entities) in per-item body/comment fields.
  - Prefer a Markdown-formatted view in interactive terminals while keeping the underlying output prompt-ready for LLMs.

## Impact

- Affects backlog daily summarize/export plumbing in the backlog module package (daily standup flows and prompt builders).
- Touches comment/body normalization logic for ADO and GitHub adapters where they feed into `backlog daily` summarize/export paths.
- May require:
  - New or updated utility for HTML-to-Markdown conversion with predictable, testable output.
  - Environment/TTY detection to decide between rich Markdown rendering and plain Markdown output.
- Requires updates to:
  - Contract/spec for `daily-standup` summarize behavior (normalization and rendering expectations).
  - Tests that assert summarize outputs contain no raw HTML and behave deterministically across interactive vs CI modes.

