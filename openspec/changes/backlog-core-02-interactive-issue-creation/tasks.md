# Tasks: Add backlog add (interactive issue creation)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. **Spec deltas** define behavior (Given/When/Then) in `openspec/changes/backlog-core-02-interactive-issue-creation/specs/backlog-add/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet).
3. **Code last**: Implement until tests pass and behavior satisfies the spec.

Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

---

## 1. Create git worktree branch from dev

- [ ] 1.1 Ensure primary checkout is on dev and up to date: `git checkout dev && git pull origin dev`
- [ ] 1.2 Create dedicated worktree branch (preferred): `scripts/worktree.sh create feature/backlog-core-02-interactive-issue-creation`; if issue exists, link branch to issue with `gh issue develop 173 --repo nold-ai/specfact-cli --name feature/backlog-core-02-interactive-issue-creation`
- [ ] 1.3 Or create worktree branch without issue link: `scripts/worktree.sh create feature/backlog-core-02-interactive-issue-creation` (if no issue yet)
- [ ] 1.4 Verify branch in worktree: `git worktree list` includes the branch path; then run `git branch --show-current` inside that worktree.

## 2. Create GitHub issue in nold-ai/specfact-cli (mandatory)

- [ ] 2.1 If issue not yet created: create issue in nold-ai/specfact-cli: `gh issue create --repo nold-ai/specfact-cli --title "[Change] Add backlog add (interactive issue creation)" --body-file <path> --label "enhancement" --label "change-proposal"`. If issue already exists (e.g. #173), skip and ensure proposal.md Source Tracking is up to date.
- [ ] 2.2 Use body from proposal (Why, What Changes, Acceptance Criteria); add footer `*OpenSpec Change Proposal: add-backlog-add-interactive-issue-creation*`
- [ ] 2.3 Update `proposal.md` Source Tracking section with issue number, issue URL, repository nold-ai/specfact-cli, Last Synced Status: proposed
- [ ] 2.4 Link issue to project (optional): `gh project item-add 1 --owner nold-ai --url <issue-url>` (requires `gh auth refresh -s project` if needed)

## 3. Verify spec deltas (SDD: specs first)

- [ ] 3.1 Confirm `specs/backlog-add/spec.md` exists and is complete (ADDED requirements, Given/When/Then for create_issue, add command, creation hierarchy).
- [ ] 3.2 Map scenarios to implementation: create via GitHub/ADO, add command with parent validation, custom hierarchy from config, non-interactive mode.

## 4. Tests first (TDD: write tests from spec scenarios; expect failure)

- [ ] 4.1 Write unit tests for adapter create_issue: mock GitHub/ADO API; assert payload mapping and return shape (id, key, url).
- [ ] 4.2 Write unit or integration tests from `specs/backlog-add/spec.md` scenarios: add with parent validation, hierarchy from config, non-interactive add, DoR check when --check-dor.
- [ ] 4.3 Run tests: `hatch run smart-test-unit` (or equivalent); **expect failure** (no implementation yet).
- [ ] 4.4 Document which scenarios are covered by which test modules.

## 5. Extend BacklogAdapterMixin with create_issue (TDD: code until tests pass)

- [ ] 5.1 Add abstract method `create_issue(project_id: str, payload: dict) -> dict` to `BacklogAdapterMixin` in `src/specfact_cli/adapters/backlog_base.py` with @abstractmethod, @beartype, and @icontract.
- [ ] 5.2 Implement `create_issue` in GitHub adapter: map payload to GitHub Issues API (POST /repos/{owner}/{repo}/issues); return dict with id, key (number), url.
- [ ] 5.3 Implement `create_issue` in ADO adapter: map payload to ADO Create Work Item API; set parent relation when parent_id present; return dict with id, key, url.
- [ ] 5.4 Run adapter create tests; **expect pass**; fix until tests pass.

## 6. Implement creation hierarchy and add command (TDD: code until tests pass)

- [ ] 6.1 Define optional creation_hierarchy in template or backlog_config schema (child type → list of allowed parent types); implement loader (from ProjectBundle.metadata.backlog_config or .specfact/spec.yaml).
- [ ] 6.2 Implement add command: options --adapter, --project-id, --template, --type, --parent, --title, --body, --non-interactive, --check-dor; interactive prompts when key args missing (unless --non-interactive).
- [ ] 6.3 Implement flow: load graph (fetch_all_issues + fetch_relationships or BacklogGraphBuilder when available); resolve type and parent; validate parent exists and allowed type from creation_hierarchy; optional DoR check (reuse backlog refine DoR); build payload; call adapter.create_issue; output id, key, url.
- [ ] 6.4 Register `specfact backlog add` in backlog command group (same place as refine, analyze-deps).
- [ ] 6.5 Run add-command tests; **expect pass**; fix until tests pass.

## 7. Quality gates

- [ ] 7.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [ ] 7.2 Run contract test: `hatch run contract-test`.
- [ ] 7.3 Run full test suite: `hatch run smart-test` (or `hatch run smart-test-full`).
- [ ] 7.4 Ensure all new public APIs have @icontract and @beartype where applicable.

## 8. Documentation research and review

- [ ] 8.1 Identify affected documentation: docs/guides/agile-scrum-workflows.md, backlog-refinement or backlog guide.
- [ ] 8.2 Update agile-scrum-workflows (or backlog guide): add section for backlog add (`specfact backlog add`), interactive creation, DoR, slash prompt usage.
- [ ] 8.3 If adding a new doc page: set front-matter (layout, title, permalink, description) and update docs/_layouts/default.html sidebar if needed.

## 9. Version and changelog (patch bump; required before PR)

- [ ] 9.1 Bump **patch** version in `pyproject.toml` (e.g. X.Y.Z → X.Y.(Z+1)).
- [ ] 9.2 Sync version in `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py` to match pyproject.toml.
- [ ] 9.3 Add CHANGELOG.md entry under new [X.Y.Z] - YYYY-MM-DD section: **Added** – Backlog add (interactive issue creation): `specfact backlog add` with type/parent selection, DoR validation, and create via adapter.

## 10. Create Pull Request to dev

- [ ] 10.1 Ensure all changes are committed: `git add .` and `git commit -m "feat(backlog): add backlog add for interactive issue creation"`
- [ ] 10.2 Push to remote: `git push origin feature/backlog-core-02-interactive-issue-creation`
- [ ] 10.3 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/backlog-core-02-interactive-issue-creation --title "feat(backlog): add backlog add for interactive issue creation" --body-file <path>` (use repo PR template; add OpenSpec change ID `backlog-core-02-interactive-issue-creation` and summary; reference GitHub issue with `Fixes nold-ai/specfact-cli#173`).
- [ ] 10.4 Verify PR and branch are linked to issue in Development section.
