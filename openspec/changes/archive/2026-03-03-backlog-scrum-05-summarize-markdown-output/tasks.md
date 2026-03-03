## 1. Normalize summarize output to Markdown-only

- [x] 1.1 Identify backlog daily summarize/export code path and call sites for `--summarize` / `--summarize-to`
- [x] 1.2 Introduce a normalization utility that converts HTML-based bodies/comments to Markdown while preserving existing Markdown semantics
- [x] 1.3 Wire the normalization utility into the summarize builder so all per-item body/comment fields are normalized before inclusion
- [x] 1.4 Add icontract/beartype contracts around the normalization entry point to enforce non-HTML output

## 2. Environment-aware rendering and behavior

- [x] 2.1 Add TTY / CI detection around `backlog daily --summarize` output (interactive vs non-interactive decision)
- [x] 2.2 Implement rich Markdown rendering for interactive terminals while keeping the underlying Markdown text stable
- [x] 2.3 Ensure `--summarize-to <path>` always writes plain Markdown with no ANSI control codes or HTML

## 3. Adapter integration and tests

- [x] 3.1 Adjust ADO adapter/comment plumbing so HTML bodies/comments are routed through the normalization utility for summarize flows
- [x] 3.2 Verify GitHub/Markdown-native flows still behave correctly when passing through normalization
- [x] 3.3 Add tests that prove summarize output contains no raw HTML or HTML entities for mixed ADO/GitHub scenarios
- [x] 3.4 Add tests that prove interactive vs CI/non-interactive summarize behavior matches spec (rendered view vs plain Markdown)

## 4. Documentation and OpenSpec validation

- [x] 4.1 Update any relevant docs/guides that mention `specfact backlog daily --summarize` / `--summarize-to` to note Markdown-only, normalized behavior
- [x] 4.2 Run `openspec validate backlog-scrum-05-summarize-markdown-output --strict` and fix any validation issues
- [x] 4.3 Run `/wf-validate-change backlog-scrum-05-summarize-markdown-output` from the specfact-openspec workflow and record results in CHANGE_VALIDATION.md

