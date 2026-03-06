# Tasks: Intent Engineering Skills — SQUER Workflow for AI IDEs

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests MUST precede production code for any behavior-changing task.

Order:
1. Spec deltas (already in `specs/`)
2. Tests derived from spec scenarios — run and expect failure
3. Production code — implement until tests pass

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/ai-integration-04-intent-skills -b feature/ai-integration-04-intent-skills origin/dev`
  - [ ] 1.1.3 `cd ../specfact-cli-worktrees/feature/ai-integration-04-intent-skills`
  - [ ] 1.1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.5 `git branch --show-current` (verify `feature/ai-integration-04-intent-skills`)

## 2. Write tests for intent skills installation (TDD — expect failure)

- [ ] 2.1 Review `tests/unit/specfact_cli/` for existing ide skill install test patterns
- [ ] 2.2 Add `tests/unit/specfact_cli/test_intent_skills_install.py`:
  - [ ] 2.2.1 Test `specfact ide skill install --type intent` installs all 6 skill files
  - [ ] 2.2.2 Test `specfact ide skill install` (no `--type`) unchanged behaviour
  - [ ] 2.2.3 Test `specfact ide skill install --type all` installs both spec + intent skills
  - [ ] 2.2.4 Test `specfact ide skill list` shows both `spec` and `intent` types
- [ ] 2.3 Add `tests/unit/specfact_cli/test_intent_skills_content.py`:
  - [ ] 2.3.1 Test each skill file exists in the skills/ directory after install
  - [ ] 2.3.2 Test each skill file has valid YAML frontmatter (name, description, allowed-tools)
- [ ] 2.4 Run tests — expect failure: `hatch test -- tests/unit/specfact_cli/test_intent_skills*.py -v`
- [ ] 2.5 Record failing test evidence in `TDD_EVIDENCE.md`

## 3. Implement intent skill files

- [ ] 3.1 Create `skills/specfact-intent/SKILL.md` — umbrella router skill (~80 tokens at rest)
  - [ ] 3.1.1 YAML frontmatter: `name: specfact-intent`, `description`, `allowed-tools: [bash, terminal]`
  - [ ] 3.1.2 Brief activation instructions: detect intent-related tasks, load appropriate sub-skill
- [ ] 3.2 Create `skills/specfact-intent-capture/SKILL.md` — SQUER 7-question interview
  - [ ] 3.2.1 YAML frontmatter with activation description
  - [ ] 3.2.2 Exact SQUER 7 questions: What problem? Who has it? What happens today? What should change? How will we know? What must not break? What's the priority?
  - [ ] 3.2.3 Mapping table: each question → `BusinessOutcome` field
  - [ ] 3.2.4 CLI invocation: `specfact requirements capture` with YAML output path
  - [ ] 3.2.5 Prerequisite check block (verify `specfact requirements --help` succeeds)
- [ ] 3.3 Create `skills/specfact-intent-decompose/SKILL.md` — G/W/T decomposition
  - [ ] 3.3.1 YAML frontmatter
  - [ ] 3.3.2 Instructions: take BusinessOutcome → derive BusinessRules (BR-NNN, G/W/T) + ArchitecturalConstraints (AC-NNN)
  - [ ] 3.3.3 CLI invocation: `specfact requirements validate` for schema check
- [ ] 3.4 Create `skills/specfact-intent-architecture/SKILL.md` — ADR generation
  - [ ] 3.4.1 YAML frontmatter
  - [ ] 3.4.2 Instructions: invoke `specfact architecture derive --requirement {id}`, produce ADR with BO/AC links
- [ ] 3.5 Create `skills/specfact-intent-trace-validate/SKILL.md` — traceability gap validation
  - [ ] 3.5.1 YAML frontmatter
  - [ ] 3.5.2 Instructions: invoke `specfact validate --full-chain`, parse gap report, generate fix prompts per gap type
- [ ] 3.6 Create `skills/specfact-intent-evidence-check/SKILL.md` — evidence completeness check
  - [ ] 3.6.1 YAML frontmatter
  - [ ] 3.6.2 Instructions: invoke `specfact validate --full-chain --evidence-dir .specfact/evidence/`, report missing envelopes

## 4. Implement `--type` flag on `specfact ide skill install`

- [ ] 4.1 Locate `specfact ide skill install` command (from ai-integration-01 module)
- [ ] 4.2 Add `--type` option: `Literal["spec", "intent", "all"]`, default `"spec"`
- [ ] 4.3 Implement intent skill install path: copy `skills/specfact-intent*/SKILL.md` to IDE location
- [ ] 4.4 Add `@require` contract: type must be one of the valid values; `@beartype` on all new params
- [ ] 4.5 Update `specfact ide skill list` to enumerate all skill types with install status

## 5. Passing tests and quality gates

- [ ] 5.1 Run tests — expect passing: `hatch test -- tests/unit/specfact_cli/test_intent_skills*.py -v`
- [ ] 5.2 Record passing test evidence in `TDD_EVIDENCE.md`
- [ ] 5.3 `hatch run format`
- [ ] 5.4 `hatch run type-check`
- [ ] 5.5 `hatch run lint`
- [ ] 5.6 `hatch run yaml-lint`
- [ ] 5.7 `hatch run contract-test`
- [ ] 5.8 `hatch run smart-test`
- [ ] 5.9 Module signing: `hatch run ./scripts/verify-modules-signature.py --require-signature`; re-sign if any module changed

## 6. Documentation

- [ ] 6.1 Create `docs/guides/intent-capture-workflow.md`:
  - [ ] 6.1.1 Jekyll front-matter (layout, title, permalink, description, nav_order, parent)
  - [ ] 6.1.2 Sections: Overview, Prerequisites, SQUER interview pattern, Installing intent skills, Workflow walkthrough, Prompt-validate-feedback loop
- [ ] 6.2 Update `docs/guides/ai-ide-workflow.md` — add Intent Skills section linking to new guide
- [ ] 6.3 Update `docs/_layouts/default.html` sidebar navigation — add `intent-capture-workflow` under Guides

## 7. Version and changelog

- [ ] 7.1 Bump minor version in `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py`
- [ ] 7.2 Add CHANGELOG.md entry under new `[X.Y.Z] - 2026-XX-XX` with Added section

## 8. GitHub issue creation

- [ ] 8.1 Create GitHub issue:
  ```bash
  gh issue create \
    --repo nold-ai/specfact-cli \
    --title "[Change] Intent Engineering Skills — SQUER Workflow for AI IDEs" \
    --body-file /tmp/github-issue-ai-integration-04.md \
    --label "enhancement" \
    --label "change-proposal"
  ```
- [ ] 8.2 Link issue to project: `gh project item-add 1 --owner nold-ai --url <ISSUE_URL>`
- [ ] 8.3 Update `proposal.md` Source Tracking section with issue number and URL
- [ ] 8.4 Link branch to issue: `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name feature/ai-integration-04-intent-skills`

## 9. Pull request

- [ ] 9.1 `git add` all changed files; commit with `feat: add SQUER intent engineering skills for AI IDEs`
- [ ] 9.2 `git push -u origin feature/ai-integration-04-intent-skills`
- [ ] 9.3 Create PR:
  ```bash
  gh pr create \
    --repo nold-ai/specfact-cli \
    --base dev \
    --head feature/ai-integration-04-intent-skills \
    --title "feat: SQUER intent engineering skills for AI IDEs" \
    --body-file /tmp/pr-body-ai-integration-04.md
  ```
- [ ] 9.4 Link PR to project: `gh project item-add 1 --owner nold-ai --url <PR_URL>`
- [ ] 9.5 Set project status to "In Progress"

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd .../specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/ai-integration-04-intent-skills`
- [ ] `git branch -d feature/ai-integration-04-intent-skills`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/ai-integration-04-intent-skills`
