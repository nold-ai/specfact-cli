## TDD Evidence for backlog-scrum-05-summarize-markdown-output

### Failing-before run (new summarize normalization tests)

- **Command:**

  ```bash
  hatch test --cover -v tests/unit/commands/test_backlog_daily.py -k "summarize_prompt_normalizes_html"
  ```

- **Timestamp:** 2026-02-27 (see CI logs / local shell history for exact time)

- **Failure summary:**
  - `test_summarize_prompt_normalizes_html_description_to_markdown`:
    - Expected HTML `<p>` / `<br />` and `&amp;` entities to be removed from summarize prompt output.
    - Actual output still contained raw `<p>Line 1<br />Line 2 &amp; more</p>` in the Description section.
  - `test_summarize_prompt_normalizes_html_comments_to_markdown`:
    - Expected HTML `<div>` and `<br>` plus `&amp;` entities in comments to be removed.
    - Actual output still contained raw `<div>Comment &amp; note<br>next line</div>` in the Comments section.

These failures confirm current behavior violates the new spec delta: summarize prompts include raw HTML and entities from ADO-style bodies and comments instead of normalized Markdown-only content.

### Passing-after run (summarize normalization implemented)

- **Command:**

  ```bash
  hatch test --cover -v tests/unit/commands/test_backlog_daily.py -k "summarize_prompt_normalizes_html"
  ```

- **Result:** ✅ 2 passed (normalization tests), remaining tests deselected in this targeted run.

- **Behavior summary:**
  - `_build_summarize_prompt_content` now:
    - Normalizes HTML-based `body_markdown` values to Markdown-friendly text (no `<p>`, `<br>` tags or `&amp;` entities).
    - Normalizes HTML comments before including them under the "Comments (annotations)" section.
  - New helper `_normalize_markdown_text` (with `@beartype` and `@ensure`) enforces that the returned text does not contain raw HTML tags, satisfying the updated `daily-standup` summarize requirements.
