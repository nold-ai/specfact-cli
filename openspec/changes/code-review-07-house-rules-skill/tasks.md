# Tasks: house_rules Skill and Auto-Updater

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktree

- [x] 1.1 `git fetch origin`
- [x] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-07-house-rules-skill -b feature/code-review-07-house-rules-skill origin/dev`
- [x] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-07-house-rules-skill`
- [x] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

## 2. Verify blockers resolved

- [x] 2.1 Confirm `code-review-01-module-scaffold` is merged
- [x] 2.2 Confirm `code-review-06-reward-ledger` is merged (updater reads ledger data)

## 3. Write tests BEFORE implementation (TDD-first)

- [x] 3.1 Write `tests/unit/specfact_code_review/rules/test_updater.py`
  - [x] 3.1.1 Test rule >= 3 hits surfaced in TOP VIOLATIONS
  - [x] 3.1.2 Test rule < 3 hits NOT added to TOP VIOLATIONS
  - [x] 3.1.3 Test rule with 0 hits for 10 consecutive runs pruned
  - [x] 3.1.4 Test version header increments
  - [x] 3.1.5 Test timestamp updated to current date
  - [x] 3.1.6 Test 35 line cap enforced (oldest/lowest-frequency pruned)
  - [x] 3.1.7 Test DO and DON'T sections unchanged after update
  - [x] 3.1.8 Test `@ensure` assertion fires if output > 35 lines
- [x] 3.2 Run tests → expect failure; record in `TDD_EVIDENCE.md`

## 4. Create default SKILL.md

- [x] 4.1 Create `skills/specfact-code-review/SKILL.md` in `specfact-cli` repo with:
  - [x] 4.1.1 Valid ai-integration-01 YAML frontmatter (`name`, `description`, `allowed-tools`)
  - [x] 4.1.2 Default DO section (7 rules from plan)
  - [x] 4.1.3 Default DON'T section (7 rules from plan)
  - [x] 4.1.4 TOP VIOLATIONS auto-managed section (empty initially)
  - [x] 4.1.5 Verify line count <= 35

## 5. Implement updater and commands

- [x] 5.1 Implement `rules/updater.py` — full update algorithm with `@require`/`@ensure`/`@beartype`
- [x] 5.2 Implement `rules/commands.py` — `show`, `update`, `init` Typer commands
- [x] 5.3 Create `rules/__init__.py`
- [x] 5.4 Verify `rules init` creates correct SKILL.md
- [x] 5.5 Verify no CLAUDE.md modification occurs

## 6. Quality gates and CLI checks

- [x] 6.1 Run tests → expect passing; record in `TDD_EVIDENCE.md`
- [x] 6.2 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`
- [x] 6.3 `specfact code review rules show` — verify output
- [x] 6.4 `specfact code review rules init` — verify SKILL.md created correctly

## 7. Module signing, docs, version, changelog

- [x] 7.1 Verify/re-sign module
- [x] 7.2 Update `docs/modules/code-review.md` with rules commands and house_rules skill section
- [x] 7.3 Bump patch version; update CHANGELOG.md

## 8. Create GitHub issue and PR

- [x] 8.1 Create issue: `[Change] Add house_rules skill (ai-integration-01 compliant) and auto-updater`
- [x] 8.2 Update proposal.md Source Tracking; commit, push, create PR

## Post-merge cleanup

- [x] Remove worktree, delete branch, prune
