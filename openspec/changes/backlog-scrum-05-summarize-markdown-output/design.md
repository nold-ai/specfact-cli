## Context

`specfact backlog daily` already supports a `--summarize` / `--summarize-to` flow that builds a prompt-ready view of the current standup scope (filters, per-item data, body, comments). When used against ADO, the underlying work item body and comments are often stored as HTML, while GitHub and some ADO comments use Markdown. Today the summarize builder can emit raw HTML fragments and entities into the prompt, which is noisy for both humans and LLMs and inconsistent with Markdown-centric flows elsewhere in SpecFact.

At the same time, SpecFact needs to support both interactive, rich terminal sessions (for humans running standup from a shell) and non-interactive / CI environments where summarize output is consumed by other tools or stored as artifacts.

## Goals / Non-Goals

**Goals:**

- Normalize all descriptions and comments included in summarize output into clean Markdown text, regardless of provider format.
- Ensure summarize prompts never contain raw HTML tags or HTML entities.
- Provide a Markdown-aware, readable view of the summarize content in interactive terminals (e.g. Rich Markdown rendering), while keeping the underlying Markdown text stable and prompt-ready.
- Preserve existing summarize semantics: same filters, same per-item data fields, same `--summarize` vs `--summarize-to` behavior.

**Non-Goals:**

- Do not change which items are included in standup or summarize scope (filters and selection logic remain as defined in `daily-standup`).
- Do not change how comments or bodies are stored in providers; normalization is applied only at summarize/export time.
- Do not introduce a hard dependency on any particular HTML-to-Markdown library that would block offline usage; implementation must remain Python-only and bundle-safe.

## Decisions

- Introduce a small normalization utility (e.g. in the backlog module package) that:
  - Accepts raw body/comment text and a hint about source format (HTML vs Markdown when known).
  - Converts HTML to Markdown using a deterministic, testable strategy.
  - Always returns Markdown-only text suitable for inclusion in prompts.
- Extend the summarize builder for `backlog daily` so that:
  - Before assembling the per-item section, it passes body and comment text through the normalization utility.
  - It treats GitHub/Markdown-native content as Markdown but still routes through the same normalization path for consistency.
- Add a simple environment/TTY detection layer around summarize output:
  - If running in an interactive TTY and not explicitly in CI mode, render the normalized Markdown using Rich (or an equivalent Markdown-capable view) for the user.
  - If output is redirected, piped, or CI mode is detected, emit plain Markdown text without terminal control codes.

## Risks / Trade-offs

- HTML-to-Markdown conversion can be lossy if not carefully tuned; we must verify typical ADO HTML patterns (paragraphs, lists, bold, links) produce acceptable Markdown for standup prompts.
- Rich or similar libraries must be used in a way that does not leak ANSI control codes into `--summarize-to` files or CI logs; separation between rendered view and underlying text needs to be clear in implementation.
- Normalization adds a processing step per item/comment; for very large backlogs this can affect performance, so implementation should be efficient and optionally short-circuit when input is already clean Markdown.

