# Tasks: Add backlog add (interactive issue creation)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. **Spec deltas** define behavior (Given/When/Then) in `openspec/changes/backlog-core-02-interactive-issue-creation/specs/backlog-add/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet).
3. **Code last**: Implement until tests pass and behavior satisfies the spec.

Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

---

## 1. Create git worktree branch from dev

- [x] 1.1 Ensure primary checkout is on dev and up to date: `git checkout dev && git pull origin dev`
- [x] 1.2 Create dedicated worktree branch (preferred): `scripts/worktree.sh create feature/backlog-core-02-interactive-issue-creation`; if issue exists, link branch to issue with `gh issue develop 173 --repo nold-ai/specfact-cli --name feature/backlog-core-02-interactive-issue-creation`
- [x] 1.3 Or create worktree branch without issue link: `scripts/worktree.sh create feature/backlog-core-02-interactive-issue-creation` (if no issue yet)
- [x] 1.4 Verify branch in worktree: `git worktree list` includes the branch path; then run `git branch --show-current` inside that worktree.

## 2. Create GitHub issue in nold-ai/specfact-cli (mandatory)

- [x] 2.1 If issue not yet created: create issue in nold-ai/specfact-cli: `gh issue create --repo nold-ai/specfact-cli --title "[Change] Add backlog add (interactive issue creation)" --body-file <path> --label "enhancement" --label "change-proposal"`. If issue already exists (e.g. #173), skip and ensure proposal.md Source Tracking is up to date.
- [x] 2.2 Use body from proposal (Why, What Changes, Acceptance Criteria); add footer `*OpenSpec Change Proposal: add-backlog-add-interactive-issue-creation*`
- [x] 2.3 Update `proposal.md` Source Tracking section with issue number, issue URL, repository nold-ai/specfact-cli, Last Synced Status: proposed
- [ ] 2.4 Link issue to project (optional): `gh project item-add 1 --owner nold-ai --url <issue-url>` (requires `gh auth refresh -s project` if needed)

## 3. Verify spec deltas (SDD: specs first)

- [x] 3.1 Confirm `specs/backlog-add/spec.md` exists and is complete (ADDED requirements, Given/When/Then for create_issue, add command, creation hierarchy).
- [x] 3.2 Map scenarios to implementation: create via GitHub/ADO, add command with parent validation, custom hierarchy from config, non-interactive mode.
- [x] 3.3 Confirm `specs/backlog-map-fields/spec.md` is complete for multi-provider map-fields setup behavior.

## 4. Tests first (TDD: write tests from spec scenarios; expect failure)

- [x] 4.1 Write unit tests for adapter create_issue: mock GitHub/ADO API; assert payload mapping and return shape (id, key, url).
- [x] 4.2 Write unit/integration tests from `specs/backlog-add/spec.md` scenarios: parent validation, hierarchy rules, non-interactive add, DoR check, multiline body sentinel, description format selection, and ADO sprint/iteration selection.
- [x] 4.3 Run tests: `hatch run smart-test-unit` (or equivalent); **expect failure** (no implementation yet).
- [x] 4.4 Document which scenarios are covered by which test modules.
- [x] 4.5 Add unit tests for centralized retry behavior (retries on transient failures, no retry on non-transient failures).
- [x] 4.6 Add regression tests for duplicate-safe create retry behavior and ADO parent candidate resolution when template is omitted.
- [x] 4.7 Add regression tests for shared retry policy usage in additional write paths (non-idempotent comments and idempotent updates).
- [x] 4.8 Add regression tests for ADO parent candidate fetch without implicit sprint default and duplicate-safe create warning behavior.
- [x] 4.9 Add regression test for ADO sprint option discovery with project_id-resolved context.
- [x] 4.10 Add regression test for backlog add provider_fields forwarding for GitHub ProjectV2 Type field updates.
- [x] 4.11 Add regression test for backlog-config.yaml provider settings forwarding of GitHub ProjectV2 Type mapping metadata.
- [x] 4.12 Add regression test for missing GitHub ProjectV2 config warning in backlog add output.
- [x] 4.13 Add regression tests for multi-provider map-fields flow (provider selection, auth/discovery checks, config persistence, verification output).
- [x] 4.14 Add regression tests for `backlog init-config` scaffolding behavior (create, no-overwrite, force/override path).
- [x] 4.15 Add regression tests for GitHub repository issue-type discovery and fallback behavior when ProjectV2 has only Status field.
- [x] 4.16 Add regression tests ensuring ADO `create_issue` persists `sprint` to `System.IterationPath` and GitHub `create_issue` returns canonical issue-number identity (`id == key == number`).

## 5. Extend BacklogAdapterMixin with create_issue (TDD: code until tests pass)

- [x] 5.1 Add abstract method `create_issue(project_id: str, payload: dict) -> dict` to `BacklogAdapterMixin` in `src/specfact_cli/adapters/backlog_base.py` with @abstractmethod, @beartype, and @icontract.
- [x] 5.2 Implement `create_issue` in GitHub adapter: map payload to GitHub Issues API (POST /repos/{owner}/{repo}/issues); return dict with id, key (number), url.
- [x] 5.3 Implement `create_issue` in ADO adapter: map payload to ADO Create Work Item API; set parent relation when parent_id present; return dict with id, key, url.
- [x] 5.4 Run adapter create tests; **expect pass**; fix until tests pass.
- [x] 5.5 Fix create-issue regressions: map ADO sprint payload to `System.IterationPath` and normalize GitHub create return identity to issue number.

## 6. Implement creation hierarchy and add command (TDD: code until tests pass)

- [x] 6.1 Define optional creation_hierarchy in template or backlog_config schema (child type → list of allowed parent types); implement loader (from ProjectBundle.metadata.backlog_config or .specfact/backlog-config.yaml).
- [x] 6.2 Implement add command: options --adapter, --project-id, --template, --type, --parent, --title, --body, --non-interactive, --check-dor; interactive prompts when key args missing (unless --non-interactive).
- [x] 6.3 Implement flow: load graph (fetch_all_issues + fetch_relationships or BacklogGraphBuilder when available); resolve type and parent; validate parent exists and allowed type from creation_hierarchy; optional DoR check (reuse backlog refine DoR); build payload; call adapter.create_issue; output id, key, url.
- [x] 6.4 Register `specfact backlog add` in backlog command group (same place as refine, analyze-deps).
- [x] 6.5 Run add-command tests; **expect pass**; fix until tests pass.
- [x] 6.6 Add interactive field collection where appropriate: acceptance criteria (multiline), priority, story points; map to provider payload fields when supported.
- [x] 6.7 Add interactive sprint/iteration selection (ADO) and explicit progress messages after multiline input capture and before create API call.
- [x] 6.8 Add interactive parent assignment flow: ask whether to set parent, then choose from hierarchy-allowed existing issues; apply provider-aware type mapping (including GitHub custom/epic labels via mapping).
- [x] 6.9 Add centralized retry policy in backlog adapter core logic and route GitHub/ADO create operations through it (retry transient failures only).
- [x] 6.10 Guard non-idempotent create operations against ambiguous automatic replay on timeout/connection failure to prevent duplicates.
- [x] 6.11 Resolve adapter-aware default template (ADO -> ado_scrum, GitHub -> github_projects) when --template is not provided.
- [x] 6.12 Apply shared retry policy to additional adapter write operations with per-operation ambiguity safety (non-idempotent vs idempotent).
- [x] 6.13 Disable implicit current-iteration filtering for parent candidate discovery flows (ADO) so hierarchy-valid parents are not hidden.
- [x] 6.14 Add duplicate-safe create failure warning in CLI for ambiguous transport errors (verify backlog before manual retry).
- [x] 6.15 Bind ADO org/project context before interactive sprint lookup so iteration options are discoverable from project_id.
- [x] 6.16 Forward GitHub Projects-v2 Type field configuration from template/custom config into create payload provider_fields.
- [x] 6.17 Resolve GitHub ProjectV2 provider field config from .specfact/backlog-config.yaml backlog provider settings when custom config is not provided.
- [x] 6.18 Add user-facing warning when GitHub ProjectV2 Type mapping config is missing or incomplete.
- [x] 6.19 Extend backlog map-fields into multi-provider guided setup (provider selection and sequential execution).
- [x] 6.20 Implement GitHub ProjectV2 discovery and type-option mapping flow in map-fields.
- [x] 6.21 Persist map-fields outputs into `.specfact/backlog-config.yaml` provider settings and verify required keys post-write.
- [x] 6.22 Add `specfact backlog init-config` command to scaffold `.specfact/backlog-config.yaml` defaults under backlog scope.
- [x] 6.23 Use GitHub repository issue types as source-of-truth in map-fields; keep ProjectV2 Type mapping optional when field/options are unavailable.
- [x] 6.24 Auto-load `.specfact/templates/backlog/field_mappings/github_custom.yaml` for `backlog add` when `--adapter github` and `--custom-config` is omitted; fall back to defaults when absent.
- [x] 6.25 Link GitHub parent selection using native issue relationship (`addSubIssue`) so parent appears in issue sidebar metadata.

## 7. Quality gates

- [x] 7.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [x] 7.2 Run contract test: `hatch run contract-test`.
- [x] 7.3 Run full test suite: `hatch run smart-test` (or `hatch run smart-test-full`).
- [x] 7.4 Ensure all new public APIs have @icontract and @beartype where applicable.

## 8. Documentation research and review

- [x] 8.1 Identify affected documentation: docs/guides/agile-scrum-workflows.md, backlog-refinement or backlog guide.
- [x] 8.2 Update agile-scrum-workflows (or backlog guide): add section for backlog add (`specfact backlog add`), interactive creation, DoR, slash prompt usage.
- [ ] 8.3 If adding a new doc page: set front-matter (layout, title, permalink, description) and update docs/_layouts/default.html sidebar if needed.

## 9. Version and changelog (patch bump; required before PR)

- [x] 9.1 Bump **patch** version in `pyproject.toml` (e.g. X.Y.Z → X.Y.(Z+1)).
- [x] 9.2 Sync version in `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py` to match pyproject.toml.
- [x] 9.3 Add CHANGELOG.md entry under new [X.Y.Z] - YYYY-MM-DD section: **Added** – Backlog add (interactive issue creation): `specfact backlog add` with type/parent selection, DoR validation, and create via adapter.

## 10. Create Pull Request to dev

- [ ] 10.1 Ensure all changes are committed: `git add .` and `git commit -m "feat(backlog): add backlog add for interactive issue creation"`
- [ ] 10.2 Push to remote: `git push origin feature/backlog-core-02-interactive-issue-creation`
- [ ] 10.3 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/backlog-core-02-interactive-issue-creation --title "feat(backlog): add backlog add for interactive issue creation" --body-file <path>` (use repo PR template; add OpenSpec change ID `backlog-core-02-interactive-issue-creation` and summary; reference GitHub issue with `Fixes nold-ai/specfact-cli#173`).
- [ ] 10.4 Verify PR and branch are linked to issue in Development section.
