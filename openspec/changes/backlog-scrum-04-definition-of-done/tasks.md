# Tasks: Backlog Scrum — Definition of Done (DoD) support

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. **Spec deltas** define behavior (Given/When/Then) in `openspec/changes/backlog-scrum-04-definition-of-done/specs/definition-of-done/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet).
3. **Code last**: Implement until tests pass and behavior satisfies the spec.

Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

---

## 1. Create git worktree branch from dev

- [ ] 1.1 Ensure primary checkout is on dev and up to date: `git checkout dev && git pull origin dev`
- [ ] 1.2 Create dedicated worktree branch (preferred): `scripts/worktree.sh create feature/backlog-scrum-04-definition-of-done`; if issue exists, link branch to issue with `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name feature/backlog-scrum-04-definition-of-done`
- [ ] 1.3 Or create worktree branch without issue link: `scripts/worktree.sh create feature/backlog-scrum-04-definition-of-done` (if no issue yet)
- [ ] 1.4 Verify branch in worktree: `git worktree list` includes the branch path; then run `git branch --show-current` inside that worktree.

## 2. Create GitHub issue in nold-ai/specfact-cli (mandatory)

- [ ] 2.1 Create issue in nold-ai/specfact-cli: `gh issue create --repo nold-ai/specfact-cli --title "[Change] Definition of Done (DoD) support" --body-file <path> --label "enhancement" --label "change-proposal"`
- [ ] 2.2 Use body from proposal (Why, What Changes, Acceptance Criteria); add footer `*OpenSpec Change Proposal: definition-of-done-support*`
- [ ] 2.3 Update `proposal.md` Source Tracking section with issue number, issue URL, repository nold-ai/specfact-cli, Last Synced Status: proposed
- [ ] 2.4 Link issue to project (optional): `gh project item-add 1 --owner nold-ai --url <issue-url>` (requires `gh auth refresh -s project` if needed)

## 3. Verify spec deltas (SDD: specs first)

- [ ] 3.1 Confirm `specs/definition-of-done/spec.md` exists and is complete (ADDED requirements, Given/When/Then for DoD config load, validation for done items, status in output).
- [ ] 3.2 Map scenarios to implementation: load DoD config, validate done items only, DoD status in CLI/export.

## 4. Tests first (TDD: write tests from spec scenarios; expect failure)

- [ ] 4.1 Write unit or integration tests from `specs/definition-of-done/spec.md` scenarios: DoD config load (present/missing); DoD validation for done item (pass/fail, failed criteria); non-done items skipped; DoD status in output.
- [ ] 4.2 Run tests: `hatch run smart-test-unit` (or equivalent); **expect failure** (no implementation yet).
- [ ] 4.3 Document which scenarios are covered by which test modules.

## 5. Implement DoD (TDD: code until tests pass)

- [ ] 5.1 Define DoD config schema and loader (e.g. `.specfact/dod.yaml`); load from project; handle missing/invalid config without crash.
- [ ] 5.2 Implement DoD validator: takes BacklogItem (state=Done) and config, runs checklist, returns pass/fail and failed criteria; ensure @icontract and @beartype on new public APIs.
- [ ] 5.3 Hook into backlog list/refine/export: when items in Done state and DoD enabled (e.g. `--dod`), run validator and attach DoD status. Expose under backlog group (e.g. `specfact backlog list --dod` or `specfact backlog dod`); do not add top-level DoD command.
- [ ] 5.4 Include DoD status in CLI output and export for done items when enabled.
- [ ] 5.5 Run tests again; **expect pass**; fix until all tests pass.

## 6. Quality gates

- [ ] 6.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [ ] 6.2 Run contract test: `hatch run contract-test`.
- [ ] 6.3 Run full test suite: `hatch run smart-test` (or `hatch run smart-test-full`).
- [ ] 6.4 Ensure any new or modified public APIs have @icontract and @beartype where applicable.

## 7. Documentation research and review

- [ ] 7.1 Identify affected documentation: docs/guides/agile-scrum-workflows.md, docs/guides/backlog-refinement.md.
- [ ] 7.2 Update agile-scrum-workflows.md: add section or subsection for DoD with SpecFact (config, validation for done items, status in output).
- [ ] 7.3 Update backlog-refinement.md: document DoD support and how it complements DoR.
- [ ] 7.4 If adding a new doc page: set front-matter (layout, title, permalink, description) and update docs/_layouts/default.html sidebar if needed.

## 8. Version and changelog (patch bump; required before PR)

- [ ] 8.1 Bump **patch** version in `pyproject.toml` (e.g. X.Y.Z → X.Y.(Z+1)).
- [ ] 8.2 Sync version in `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py` to match pyproject.toml.
- [ ] 8.3 Add CHANGELOG.md entry under new [X.Y.Z] - YYYY-MM-DD section: **Added** – Definition of Done (DoD) support (config, validation for done items, status in backlog output/export).

## 9. Create Pull Request to dev

- [ ] 9.1 Ensure all changes are committed: `git add .` and `git commit -m "feat(backlog): add Definition of Done (DoD) support for done items"`
- [ ] 9.2 Push to remote: `git push origin feature/backlog-scrum-04-definition-of-done`
- [ ] 9.3 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/backlog-scrum-04-definition-of-done --title "feat(backlog): add Definition of Done (DoD) support for done items" --body-file <path>` (use repo PR template; add OpenSpec change ID `backlog-scrum-04-definition-of-done` and summary; reference GitHub issue with `Fixes nold-ai/specfact-cli#<issue-number>`).
- [ ] 9.4 Verify PR and branch are linked to issue in Development section.
