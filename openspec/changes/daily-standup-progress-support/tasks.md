# Tasks: Daily standup and progress support

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. **Spec deltas** define behavior (Given/When/Then) in `openspec/changes/daily-standup-progress-support/specs/daily-standup/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet).
3. **Code last**: Implement until tests pass and behavior satisfies the spec.

Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

---

## 1. Create git branch from dev

- [x] 1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
- [x] 1.2 Create branch with Development link to issue (if exists): `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name feature/daily-standup-progress-support --checkout`
- [x] 1.3 Or create branch without issue link: `git checkout -b feature/daily-standup-progress-support` (if no issue yet)
- [x] 1.4 Verify branch was created: `git branch --show-current`

## 2. Create GitHub issue in nold-ai/specfact-cli (mandatory)

- [x] 2.1 Create issue in nold-ai/specfact-cli: `gh issue create --repo nold-ai/specfact-cli --title "[Change] Daily standup and progress support" --body-file <path> --label "enhancement" --label "change-proposal"`
- [x] 2.2 Use body from proposal (Why, What Changes, Acceptance Criteria); add footer `*OpenSpec Change Proposal: daily-standup-progress-support*`
- [x] 2.3 Update `proposal.md` Source Tracking section with issue number, issue URL, repository nold-ai/specfact-cli, Last Synced Status: proposed
- [x] 2.4 Link issue to project (optional): `gh project item-add 1 --owner nold-ai --url <issue-url>` (requires `gh auth refresh -s project` if needed)

## 3. Verify spec deltas (SDD: specs first)

- [x] 3.1 Confirm `specs/daily-standup/spec.md` exists and is complete (ADDED requirements, Given/When/Then scenarios for standup view and post standup comment).
- [x] 3.2 Map scenarios to implementation: list my items with status/last activity, assignee filter, post standup comment via GitHub, adapter does not support comments.

## 4. Tests first (TDD: write tests from spec scenarios; expect failure)

- [x] 4.1 Write unit or integration tests from `specs/daily-standup/spec.md` scenarios: standup view lists items with status and last-updated; optional standup summary lines; assignee filter; post standup comment (mock adapter); adapter without comment support reports clearly.
- [x] 4.2 Run tests: `hatch run smart-test-unit` (or equivalent); **expect failure** (no implementation yet).
- [x] 4.3 Document which scenarios are covered by which test modules.

## 5. Implement standup view and optional comment (TDD: code until tests pass)

- [x] 5.1 Implement standup view: query change proposals and/or backlog items by assignee or filter; display item id, title, status, last-updated; optional standup fields (yesterday/today/blockers) when present in source.
- [x] 5.2 Expose via `specfact backlog daily` (backlog command group); keep scope minimal (read-only view from existing data). Do not add a top-level `specfact standup` command.
- [x] 5.3 Optional: implement post standup comment: when user opts in and adapter supports comments (e.g. GitHub), add comment to linked issue with standup text (format: Yesterday / Today / Blockers); use existing GitHub adapter comment API if available.
- [x] 5.4 When adapter does not support comments, report clearly; do not attempt to post.
- [x] 5.5 Add or extend bridge/adapters to support posting comment (e.g. GitHub issue comment); ensure @icontract and @beartype on new public APIs.
- [x] 5.6 Run tests again; **expect pass**; fix until all tests pass.

## 6. Tests first (TDD): default scope, iteration/sprint, unassigned

- [x] 6.1 Write tests from `specs/daily-standup/spec.md` for default standup scope: when no `--state`/`--limit` given, applied defaults exclude closed items and cap count; explicit options override defaults.
- [x] 6.2 Write tests for current iteration/sprint: when `--sprint current` or `--iteration current` is used and adapter supports it, only items in current sprint/iteration are listed; when unsupported, no crash and clear behavior.
- [x] 6.3 Write tests for unassigned items: standup view shows unassigned items in a separate table or section when enabled; `--unassigned-only` shows only unassigned; same scope (state, iteration) applies to unassigned.
- [x] 6.4 Write tests for sprint/iteration end date: when current sprint is in use and adapter or config provides end date, view displays it (e.g. "Sprint ends: DATE (N days)"); optional config fallback when adapter does not provide it.
- [x] 6.5 Write tests for blockers-first and optional priority: when `--blockers-first` or sort is used, items with non-empty blockers appear first; when config enables priority/value column and BacklogItem has it, column is shown.
- [x] 6.6 Run tests: `hatch run smart-test-unit` (or equivalent); **expect failure** (implementation not yet done).

## 7. Implement: default scope, iteration/sprint, unassigned view (TDD: code until tests pass)

- [x] 7.1 Implement default standup scope: read defaults from env (e.g. `SPECFACT_STANDUP_STATE`, `SPECFACT_STANDUP_LIMIT`) and/or optional `.specfact/standup.yaml`; apply default state (e.g. open), optional default assignee (me when resolvable), default limit (e.g. 20) when user does not pass options. CLI options override config/env.
- [x] 7.2 Add `--iteration` and `--sprint` to `specfact backlog daily`; pass through to `_fetch_backlog_items` and `_apply_filters`. When value is `current`, resolve via adapter when supported; otherwise use literal. Document which adapters support iteration/sprint.
- [x] 7.2a When `--sprint current` or config sprint is used, display sprint/iteration end date when provided by adapter or config (e.g. header line "Sprint ends: YYYY-MM-DD (N days)"); support optional config (e.g. `standup.sprint_end_date`) when adapter does not provide it; document adapter support.
- [x] 7.3 Implement unassigned items: after the main standup table, add a second table "Pending / open for commitment" with unassigned items in the same scope (state, iteration, sprint). Add option `--show-unassigned` (default true for standup) and `--unassigned-only` to show only unassigned. Omit unassigned section when none in scope.
- [x] 7.3a Optional: add `--blockers-first` or sort rows with non-empty blockers first so time-critical issues are visible at a glance; optional: show priority or value column when available on BacklogItem and enabled by config (for value-driven/SAFe teams).
- [x] 7.4 Run tests again; **expect pass**; fix until all pass.

## 8. Quality gates

- [x] 8.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [x] 8.2 Run contract test: `hatch run contract-test`.
- [x] 8.3 Run full test suite: `hatch run smart-test` (or `hatch run smart-test-full`).
- [x] 8.4 Ensure any new or modified public APIs have @icontract and @beartype where applicable.

## 9. Documentation research and review

- [x] 9.1 Identify affected documentation: docs/guides/agile-scrum-workflows.md, docs/guides/devops-adapter-integration.md.
- [x] 9.2 Update agile-scrum-workflows.md: add section or subsection for daily standup with SpecFact (`specfact backlog daily` view, default scope, iteration/sprint, sprint end date, unassigned items, blockers-first, optional priority/value, Kanban vs Scrum/SAFe usage, optional post standup comment to linked issue). Note out-of-scope: sprint goal (see board/sprint settings), stale/at-risk flags (use last updated + blockers), structured blocked_by (free-text blockers only).
- [x] 9.3 Update devops-adapter-integration.md: document standup comment posting when using GitHub/ADO adapter; document standup config (env, standup.yaml), iteration/sprint and sprint end date support per adapter, and blockers-first/priority options. Note: sprint goal is in board/sprint settings; not displayed by CLI.
- [x] 9.4 If adding a new doc page: set front-matter (layout, title, permalink, description) and update docs/_layouts/default.html sidebar if needed.
- [x] 9.5 Add daily standup tutorial to docs: create docs/getting-started/tutorial-daily-standup-sprint-review.md; add link in docs/_layouts/default.html (Getting Started sidebar) and in docs/index.md (Quick Start and DevOps & Backlog Sync sections).

## 10. Version and changelog (patch bump; required before PR)

- [x] 10.1 Bump **patch** version in `pyproject.toml` (e.g. X.Y.Z → X.Y.(Z+1)).
- [x] 10.2 Sync version in `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py` to match pyproject.toml.
- [x] 10.3 Add CHANGELOG.md entry under new [X.Y.Z] - YYYY-MM-DD section: **Added** – Daily standup defaults (state/limit/config), current iteration/sprint focus, unassigned/pending items view for commitment.

## 11. Verify spec deltas (interactive selection and Copilot export)

- [x] 11.1 Confirm `specs/daily-standup/spec.md` includes ADDED requirements and Given/When/Then scenarios for interactive step-by-step review (selection UI, detail view, navigation, optional next-best suggestion and sprint goal hint) and for export to file for Copilot.
- [x] 11.2 Map scenarios to implementation: interactive questionary selection, refine-like detail + comments, next/previous/back/exit; Copilot export same scope, Markdown sections per item, idempotent write.

## 12. Tests first (TDD): interactive selection and Copilot export

- [x] 12.1 Write unit or integration tests from `specs/daily-standup/spec.md` for interactive mode: when `--interactive` is used, items are presented (e.g. questionary or mock); selecting an item shows detail (refine-like, comments when adapter supports); navigation choices (next/previous/back/exit) behave as specified.
- [x] 12.2 Write tests for Copilot export: when `--copilot-export <path>` is used, file is written with one section per item, Markdown headings and bullets, same scope as daily; idempotent overwrite.
- [x] 12.3 Write tests for optional value score and next-best suggestion: when story_points, business_value, priority are available and suggestion enabled, value score is computed (e.g. business_value / max(1, story_points * priority)); when data missing, score omitted.
- [x] 12.4 Run tests: `hatch run smart-test-unit` (or equivalent); **expect failure** (no implementation yet).
- [x] 12.5 Document which spec scenarios are covered by which test modules.

## 13. Implement interactive selection and Copilot export (TDD: code until tests pass)

- [x] 13.1 Implement interactive mode: add `--interactive` to `specfact backlog daily`; after fetching items (same scope as daily), present questionary.select (or equivalent) with one choice per item (e.g. `{id} - {title} [{status}] ({assignee})`); on selection, display full detail (reuse refine output or build same content: description, acceptance criteria, standup fields, comments via adapter when available); highlight blocked when blockers non-empty.
- [x] 13.2 Implement navigation: after detail view, present choices "Next story", "Previous story", "Back to list", "Exit"; next/previous use current list index without re-fetch; back returns to item selector; exit ends command.
- [x] 13.3 Optional: implement next-best-item suggestion (config or `--suggest-next`): compute value_score = business_value / max(1, story_points * priority) for pending items; show "Suggested next: …" in interactive view when enabled; optional sprint goal hint when adapter/config provides it.
- [x] 13.4 Implement Copilot export: add `--copilot-export <path>` to `specfact backlog daily`; build Markdown content (one section per item: ID, title, status, assignees, last updated, progress summary, blockers, optional value score); write to path (overwrite); use same fetched list when combined with `--interactive`.
- [x] 13.5 Ensure new public helpers (interactive walkthrough, detail renderer, export builder) have @icontract and @beartype.
- [x] 13.6 Run tests again; **expect pass**; fix until all pass.

## 14. Quality gates (interactive and export)

- [x] 14.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [x] 14.2 Run contract test: `hatch run contract-test`.
- [x] 14.3 Run full test suite: `hatch run smart-test` (or `hatch run smart-test-full`).
- [x] 14.4 Ensure any new public APIs have @icontract and @beartype where applicable.

## 15. Documentation (interactive and Copilot export)

- [x] 15.1 Identify affected documentation: docs/guides/agile-scrum-workflows.md, docs/guides/devops-adapter-integration.md.
- [x] 15.2 Update agile-scrum-workflows.md: add subsection for interactive step-by-step review (`--interactive`, questionary selection, detail view, navigation, optional next-best suggestion and sprint goal hint) and for Copilot export (`--copilot-export <path>`, format, use with Copilot slash command during standup). Note: complementary aid, not replacement for backlog.
- [x] 15.3 Update devops-adapter-integration.md: document comment fetch for interactive detail view; document which adapters provide story_points, business_value, priority, sprint goal for value score and suggestions.
- [x] 15.4 If adding a new doc page: set front-matter and update docs/_layouts/default.html sidebar if needed. Daily standup tutorial added to sidebar and docs/index.md (see 9.5).
- [x] 15.5 Document ADO git remote formats in docs and code: SSH key auth uses `git@ssh.dev.azure.com:v3/...`; other SSH auth uses `user@dev.azure.com:v3/...` (no `ssh.` subdomain). Updated devops-adapter-integration.md, agile-scrum-workflows.md, tutorial-daily-standup-sprint-review.md, tutorial-backlog-refine-ai-ide.md, and docstring in backlog_commands.py.

## 16. Version and changelog (patch bump for interactive and export)

- [x] 16.1 Bump **patch** version in `pyproject.toml` (e.g. X.Y.Z → X.Y.(Z+1)). (Skipped: use existing 0.26.16 per user request.)
- [x] 16.2 Sync version in `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py` to match pyproject.toml.
- [x] 16.3 Add CHANGELOG.md entry under new [X.Y.Z] - YYYY-MM-DD section: **Added** – Interactive step-by-step review (`specfact backlog daily --interactive`) with arrow-key selection and refine-like detail including comments; export to file for Copilot (`--copilot-export <path>`); optional next-best-item suggestion (value score) and sprint goal hint.

## 17. Verify spec deltas (project backlog context)

- [x] 17.1 Confirm `specs/daily-standup/spec.md` includes ADDED requirement and Given/When/Then for project backlog context (`.specfact/backlog.yaml`, org/project per adapter, no secrets, resolution order CLI > env > file).
- [x] 17.2 Map scenarios to implementation: `_load_backlog_config()`, `_build_adapter_kwargs()` merge with config and env.

## 18. Tests first (TDD): project backlog context

- [x] 18.1 Write unit tests for `_load_backlog_config()`: when `.specfact/backlog.yaml` exists with `github.repo_owner`/`repo_name` or `ado.org`/`project`/`team`, config is returned; when file missing or empty, empty dict; when file has top-level `backlog` key, nested structure is used.
- [x] 18.2 Write unit tests for `_build_adapter_kwargs()`: when CLI args are None, values are taken from config then env (e.g. `SPECFACT_GITHUB_REPO_OWNER`); when CLI args are set, they override; tokens are never read from config.
- [x] 18.3 Run tests: `hatch run smart-test-unit` (or equivalent); **expect failure** (implementation not yet done).

## 19. Implement project backlog context (TDD: code until tests pass)

- [x] 19.1 Implement `_load_backlog_config()`: same search path as standup (SPECFACT_CONFIG_DIR, .specfact); read `.specfact/backlog.yaml`; return dict with keys e.g. `github`, `ado` and nested repo_owner/repo_name or org/project/team; no tokens or users in file.
- [x] 19.2 Update `_build_adapter_kwargs()`: load backlog config; for each adapter, resolve org/project/repo_owner/repo_name/team in order: explicit arg > env (SPECFACT_GITHUB_REPO_OWNER, etc.) > config; pass resolved values into kwargs; tokens only from args (env handled by caller).
- [x] 19.3 Run tests again; **expect pass**; fix until all pass.
- [x] 19.4 Document `.specfact/backlog.yaml` format and env vars in devops-adapter-integration.md.

## 20. Verify spec deltas (comments, backlog-daily prompt, --summarize)

- [x] 20.1 Confirm spec explicitly states that interactive detail view shows **comments** annotated to each issue (adapter-supported); document in tutorial.
- [x] 20.2 Confirm `specs/daily-standup/spec.md` includes ADDED requirements: slash-command prompt `specfact.backlog-daily.md` (story-by-story walkthrough, focus, issues/open questions, discussion notes as comments) and `--summarize` (prompt with filters + filtered output for LLM standup summary).
- [x] 20.3 Map scenarios to implementation: prompt file under `resources/prompts/specfact.backlog-daily.md`; `--summarize` (stdout) and `--summarize-to <path>` on `backlog daily` outputting prompt (instruction + filter context + per-item data).

## 21. Tests first (TDD): backlog-daily prompt and --summarize

- [x] 21.1 Write unit tests for `--summarize`: when `--summarize` is used, output (stdout or file) contains filter context (adapter, state, sprint, assignee, limit) and per-item data consistent with copilot-export; when path given (--summarize-to), file is written; idempotent overwrite.
- [x] 21.2 Write test that prompt file `resources/prompts/specfact.backlog-daily.md` exists and contains expected sections (purpose, parameters, workflow for story-by-story review, discussion notes as comments).
- [x] 21.3 Run tests: `hatch run smart-test-unit` (or equivalent); expect pass after implementation.

## 22. Implement backlog-daily prompt and --summarize (TDD: code until tests pass)

- [x] 22.1 Create `resources/prompts/specfact.backlog-daily.md`: structure analogous to `specfact.backlog-refine.md`; purpose = daily standup interactive walkthrough with DevOps team; story-by-story review, highlight current focus, surface issues/open questions, allow adding discussion notes as annotation comments; reference `specfact backlog daily` and options (--interactive, --copilot-export, --summarize, --summarize-to).
- [x] 22.2 Add `--summarize` (stdout) and `--summarize-to PATH` to `specfact backlog daily`: when set, build prompt content (instruction to generate standup summary + filter context + same per-item data as copilot-export); use same fetched list as standup view.
- [x] 22.3 Run tests again; expect pass; fix until all pass.

## 23. Documentation (comments, prompt, --summarize)

- [x] 23.1 Update tutorial-daily-standup-sprint-review.md: state explicitly that **interactive detail view shows comments** on each issue (when adapter supports it); add step or note for `--summarize` (prompt for slash command / Copilot to generate standup summary); mention `specfact.backlog-daily` slash prompt.
- [x] 23.2 Update agile-scrum-workflows.md and devops-adapter-integration.md: document that interactive daily shows issue comments; document `specfact.backlog-daily` prompt and `--summarize`/`--summarize-to` flag.

## 24. Create Pull Request to dev

- [x] 24.1 Ensure all changes are committed: `git add .` and `git commit -m "feat(backlog): daily standup defaults, iteration/sprint, unassigned items view"`
- [x] 24.2 Push to remote: `git push origin feature/daily-standup-progress-support`
- [x] 24.3 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/daily-standup-progress-support --title "feat(backlog): daily standup defaults, iteration/sprint, unassigned items view" --body-file <path>` (use repo PR template; add OpenSpec change ID `daily-standup-progress-support` and summary; reference GitHub issue with `Fixes nold-ai/specfact-cli#168`). **Created**: <https://github.com/nold-ai/specfact-cli/pull/174>
- [x] 24.4 Verify PR and branch are linked to issue in Development section.
