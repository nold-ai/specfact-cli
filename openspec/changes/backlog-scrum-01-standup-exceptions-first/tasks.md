# Tasks: Backlog Scrum — Daily Standup Exceptions-First (E1 delta)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. **Spec deltas** define behavior in `openspec/changes/backlog-scrum-01-standup-exceptions-first/specs/daily-standup/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git branch from dev (linked to issue #175)

- [ ] 1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
- [x] 1.2 Create branch linked to #175: `gh issue develop 175 --repo nold-ai/specfact-cli --name feature/backlog-scrum-01-standup-exceptions-first --checkout` (or `git checkout -b feature/backlog-scrum-01-standup-exceptions-first` if no gh)
- [x] 1.3 Verify branch: `git branch --show-current`

## 2. Tests first (exceptions-first order, --mode, patch hook)

- [x] 2.1 Write tests from spec: exceptions-first section order, --mode scrum|kanban|safe, patch hook when available.
- [x] 2.2 Run tests: `hatch run smart-test-unit`; **expect failure**.

## 2b. Tests first (comment context, daily + refine)

- [x] 2b.1 Add unit tests for ADO comments retrieval via dedicated comments API with pagination (continuation token).
- [x] 2b.2 Add unit tests for `backlog daily` comment rendering controls: default full comment inclusion for export/summarize, `--first-comments N`, `--last-comments N`, and interactive last-comment-only view with hint.
- [x] 2b.3 Add unit tests for `backlog refine --export-to-tmp` to include comment context by default (full) and respect first/last comment limits.
- [x] 2b.4 Run targeted tests and expect failures before implementation.
- [x] 2b.5 Add unit tests for `backlog refine --preview` comment context: default last 2 comments, optional `--first-comments` / `--last-comments`.
- [x] 2b.6 Verify `backlog refine --export-to-tmp` always includes full comments even when preview comment-window options are set.
- [x] 2b.7 Add unit tests for refine preview comment-fetch progress text (`Fetching issue n/m ...`) and block-style comment rendering helpers.
- [x] 2b.8 Add unit tests for refine issue windowing: `--first-issues`, `--last-issues`, and mutual exclusivity validation.
- [x] 2b.9 Add unit tests ensuring issue windowing is based on numeric issue/work-item ID ordering (ascending).
- [x] 2b.10 Add unit tests for refine preview comments section when no comments are returned.
- [x] 2b.11 Add unit tests for refinement prompt generation to include comment context in `--write` workflows.
- [x] 2b.12 Add unit tests ensuring refine export includes a copilot instruction block before item sections.
- [x] 2b.13 Add unit tests ensuring refine export includes interactive-equivalent refinement rules and per-item template guidance.
- [x] 2b.14 Add unit tests for daily standup assignee column row data and GitHub `--assignee me` post-filter semantics.
- [x] 2b.15 Add unit tests for `backlog daily` issue-window CLI flags (`--first-issues`, `--last-issues`) and validation parity with refine.
- [x] 2b.16 Add unit tests for daily issue-window semantics over full filtered set (no default pre-limit truncation).
- [x] 2b.17 Add unit tests for interactive daily comment-window override (`--first-comments`/`--last-comments`) behavior.
- [x] 2b.18 Add unit tests for panel-style interactive comment rendering in daily mode.
- [x] 2b.19 Add unit tests for daily global filter parity flags (`--search`, `--release`, `--id`) and ID filter behavior.
- [x] 2b.20 Add unit tests for interactive daily navigation/post helpers to support posting comment on the selected story.

## 3. Implement exceptions-first and mode

- [x] 3.1 Implement default section order: blockers → policy failures → aging → normal (when data available).
- [x] 3.2 Add `--mode scrum|kanban|safe` to `specfact backlog daily`; adjust defaults per mode.
- [x] 3.3 Integrate patch hook when patch-mode-preview-apply available and `--patch` set.
- [x] 3.4 Run tests; **expect pass**.
- [x] 3.5 Implement refine preview comment rendering (default last 2, optional first/last windows) for adapters supporting `get_comments`.
- [x] 3.6 Ensure refine export ignores preview comment-window options and always exports full comments.
- [x] 3.7 Add preview-time progress spinner/action text while collecting comments (`Fetching issue n/m ...`).
- [x] 3.8 Render preview comments in block-style panels (clear start/end scope per comment).
- [x] 3.9 Implement refine issue-window controls (`--first-issues`, `--last-issues`) and validation.
- [x] 3.10 Fix refine issue-window ordering to use numeric ID semantics (lower first, higher last).
- [x] 3.11 Add explicit preview hint/panel for items with no comments.
- [x] 3.12 Include comments in write-mode refinement prompts (full by default, optional first/last windows).
- [x] 3.13 Add copilot instruction block at top of refine export files.
- [x] 3.14 Add interactive-equivalent instructions and template guidance to refine export item blocks.
- [x] 3.15 Add assignee column to daily standup table output (including pending/unassigned section).
- [x] 3.16 Implement GitHub `--assignee me`/`@me` handling without literal local post-filter mismatch.
- [x] 3.17 Add `--first-issues` / `--last-issues` support to `backlog daily` with numeric ID ordering and mutual exclusivity validation.
- [x] 3.18 Ensure daily issue-windowing is evaluated before default limit truncation (refine parity).
- [x] 3.19 Make interactive daily honor explicit comment-window flags while keeping latest-only as default.
- [x] 3.20 Render daily interactive comments in refine-like scoped panels outside the story body block.
- [x] 3.21 Add daily support for shared global filters `--search`, `--release`, and `--id` (refine parity).
- [x] 3.22 Add interactive standup post action to publish yesterday/today/blockers comment to the currently selected story.

## 4. Quality gates and documentation

- [x] 4.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [x] 4.2 Run contract test: `hatch run contract-test`.
- [x] 4.3 Update docs: agile-scrum-workflows.md, backlog-refinement.md, devops-adapter-integration.md (comment context behavior, first/last comment controls, export guidance).
- [x] 4.4 Update slash prompt templates: `resources/prompts/specfact.backlog-daily.md` and `resources/prompts/specfact.backlog-refine.md` for comment-context guidance.
- [x] 4.5 Add CHANGELOG entry; sync version.

## 5. Create Pull Request to dev

- [x] 5.1 Commit and push: `git add .` then `git commit -m "feat(backlog): daily standup exceptions-first and --mode scrum|kanban|safe (fixes #175)"` and `git push origin feature/backlog-scrum-01-standup-exceptions-first`
- [x] 5.2 Create PR to dev using repo PR template; PR body MUST include `Fixes nold-ai/specfact-cli#175` and this change ID for Development linking.
