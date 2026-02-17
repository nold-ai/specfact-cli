# Tasks: Backlog Scrum — Story Complexity and splitting hints support

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. **Spec deltas** define behavior (Given/When/Then) in `openspec/changes/backlog-scrum-03-story-complexity/specs/story-complexity/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet).
3. **Code last**: Implement until tests pass and behavior satisfies the spec.

Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

---

## 1. Create git worktree branch from dev

- [ ] 1.1 Ensure primary checkout is on dev and up to date: `git checkout dev && git pull origin dev`
- [ ] 1.2 Create dedicated worktree branch (preferred): `scripts/worktree.sh create feature/backlog-scrum-03-story-complexity`; if issue exists, link branch to issue with `gh issue develop 171 --repo nold-ai/specfact-cli --name feature/backlog-scrum-03-story-complexity`
- [ ] 1.3 Or create worktree branch without issue link: `scripts/worktree.sh create feature/backlog-scrum-03-story-complexity` (if no issue yet)
- [ ] 1.4 Verify branch in worktree: `git worktree list` includes the branch path; then run `git branch --show-current` inside that worktree.

## 2. Create GitHub issue in nold-ai/specfact-cli (mandatory)

- [ ] 2.1 Create issue in nold-ai/specfact-cli: `gh issue create --repo nold-ai/specfact-cli --title "[Change] Story complexity and splitting hints support" --body-file <path> --label "enhancement" --label "change-proposal"`
- [ ] 2.2 Use body from proposal (Why, What Changes, Acceptance Criteria); add footer `*OpenSpec Change Proposal: story-complexity-splitting-hints-support*`
- [ ] 2.3 Update `proposal.md` Source Tracking section with issue number, issue URL, repository nold-ai/specfact-cli, Last Synced Status: proposed
- [ ] 2.4 Link issue to project (optional): `gh project item-add 1 --owner nold-ai --url <issue-url>` (requires `gh auth refresh -s project` if needed)

## 3. Verify spec deltas (SDD: specs first)

- [ ] 3.1 Confirm `specs/story-complexity/spec.md` exists and is complete (ADDED requirements, Given/When/Then for complexity score, needs_splitting, splitting suggestion in refinement output).
- [ ] 3.2 Map scenarios to implementation: complexity score, needs_splitting(threshold), splitting suggestion generator, integration into backlog refine output and export-to-tmp.

## 4. Tests first (TDD: write tests from spec scenarios; expect failure)

- [ ] 4.1 Write unit or integration tests from `specs/story-complexity/spec.md` scenarios: complexity score (story_points, business_value); needs_splitting predicate (above/below threshold); splitting suggestion (rationale + split points); refinement output includes suggestion for complex items only.
- [ ] 4.2 Run tests: `hatch run smart-test-unit` (or equivalent); **expect failure** (no implementation yet).
- [ ] 4.3 Document which scenarios are covered by which test modules.

## 5. Implement complexity and splitting (TDD: code until tests pass)

- [ ] 5.1 Add helper(s) for complexity score and needs_splitting(item, threshold); configurable threshold (default 13); ensure @icontract and @beartype on new public APIs.
- [ ] 5.2 Add splitting suggestion logic (rationale + optional split points from acceptance_criteria or heuristic); integrate into refinement result type/output.
- [ ] 5.3 In `specfact backlog refine`, when emitting refined item output (and export-to-tmp), append "Story splitting suggestion" section for items above threshold; no top-level scrum/refine command.
- [ ] 5.4 Run tests again; **expect pass**; fix until all tests pass.

## 6. Quality gates

- [ ] 6.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [ ] 6.2 Run contract test: `hatch run contract-test`.
- [ ] 6.3 Run full test suite: `hatch run smart-test` (or `hatch run smart-test-full`).
- [ ] 6.4 Ensure any new or modified public APIs have @icontract and @beartype where applicable.

## 7. Documentation research and review

- [ ] 7.1 Identify affected documentation: docs/guides/backlog-refinement.md, docs/reference as needed.
- [ ] 7.2 Update backlog-refinement.md: document complexity score, needs-splitting threshold, and splitting hints in refinement output.
- [ ] 7.3 If adding a new doc page: set front-matter (layout, title, permalink, description) and update docs/_layouts/default.html sidebar if needed.

## 8. Version and changelog (patch bump; required before PR)

- [ ] 8.1 Bump **patch** version in `pyproject.toml` (e.g. X.Y.Z → X.Y.(Z+1)).
- [ ] 8.2 Sync version in `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py` to match pyproject.toml.
- [ ] 8.3 Add CHANGELOG.md entry under new [X.Y.Z] - YYYY-MM-DD section: **Added** – Story complexity and splitting hints in `specfact backlog refine` (complexity score, needs-splitting flag, splitting suggestion in output/export).

## 9. Create Pull Request to dev

- [ ] 9.1 Ensure all changes are committed: `git add .` and `git commit -m "feat(backlog): add story complexity and splitting hints to refine"`
- [ ] 9.2 Push to remote: `git push origin feature/backlog-scrum-03-story-complexity`
- [ ] 9.3 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/backlog-scrum-03-story-complexity --title "feat(backlog): add story complexity and splitting hints to refine" --body-file <path>` (use repo PR template; add OpenSpec change ID `backlog-scrum-03-story-complexity` and summary; reference GitHub issue with `Fixes nold-ai/specfact-cli#171`).
- [ ] 9.4 Verify PR and branch are linked to issue in Development section.
