# Workflow: Create OpenSpec Change from Plan

## Table of Contents

- [Guardrails](#guardrails)
- [Step 1: Plan Selection](#step-1-plan-selection)
- [Step 2: Plan Review and Alignment](#step-2-plan-review-and-alignment)
- [Step 3: Integrity Re-Check](#step-3-integrity-re-check)
- [Step 4: OpenSpec Change Creation](#step-4-openspec-change-creation)
- [Step 5: Proposal Review and Improvement](#step-5-proposal-review-and-improvement)
- [Step 6: GitHub Issue Creation](#step-6-github-issue-creation)
- [Step 7: Create GitHub Issue via gh CLI](#step-7-create-github-issue-via-gh-cli)
- [Step 8: Completion](#step-8-completion)

## Guardrails

- Read `openspec/config.yaml` during the workflow (before or at Step 5) for project context and TDD/SDD rules.
- Favor straightforward, minimal implementations. Keep changes tightly scoped.
- Never proceed with ambiguities or conflicts — ask for clarification interactively.
- Do not write code during the proposal stage. Only create design documents (proposal.md, tasks.md, design.md, spec deltas).
- Always validate alignment against existing plans and implementation reality before proceeding.
- **CRITICAL**: Only create GitHub issues in the target repository specified by the plan.
- **CRITICAL Git Workflow (Worktree Policy)**: Use git worktrees for parallel development — never switch the primary checkout away from `dev`. Add a worktree creation task as the FIRST task, and PR creation as the LAST task. Never work on protected branches (`main`/`dev`) directly. Branch naming: `<branch-type>/<change-id>`. Worktree path: `../specfact-cli-worktrees/<branch-type>/<change-id>`. All subsequent tasks execute inside the worktree directory.
- **CRITICAL TDD**: Per config.yaml, test tasks MUST come before implementation tasks.

## Step 1: Plan Selection

**If plan path provided**: Resolve to absolute path, verify file exists.

**If no plan path provided**:
1. Search for plans in:
   - `specfact-cli-internal/docs/internal/brownfield-strategy/` (`*.md`)
   - `specfact-cli-internal/docs/internal/implementation/` (`*.md`)
   - `specfact-cli/docs/` (if accessible)
2. Display numbered list with file path, title (first heading), last modified date.
3. Prompt user to select.

## Step 2: Plan Review and Alignment

### 2.1: Read and Parse Plan

1. Read plan file completely.
2. Extract:
   - Title and purpose (first H1)
   - **Target repository** (look for `**Repository**:` in header metadata, e.g. `` `nold-ai/specfact-cli` ``)
   - Phases/tasks with descriptions
   - Files to create/modify (note repository prefixes)
   - Dependencies, success metrics, estimated effort
3. Identify referenced targets (files, directories, repositories).

### 2.2: Cross-Reference Check

1. Search `specfact-cli-internal/docs/internal/brownfield-strategy/` for overlapping plans.
2. Search `specfact-cli-internal/docs/internal/implementation/` for conflicting implementation plans.
3. Extract conflicting info, overlapping scope, dependency relationships, timeline conflicts.

### 2.3: Target Validation

For each target in the plan:
- **Files**: Check existence, readability, location, structure matches assumptions.
- **Directories**: Check existence, structure.
- **Repositories**: Verify in workspace, structure matches, access ok.
- **Code refs**: Verify functions/classes exist, structure matches.

### 2.4: Alignment Analysis

Check:
1. **Accuracy**: File paths correct? Repos referenced accurately? Commands valid?
2. **Correctness**: Technical details accurate? Implementation approaches align with codebase?
3. **Ambiguities**: Unclear requirements, vague acceptance criteria, missing context.
4. **Conflicts**: With other plans, overlapping scope, timeline/resource conflicts.
5. **Consistency**: With CLAUDE.md conventions, OpenSpec conventions, existing patterns.

### 2.5: Issue Detection and Interactive Resolution

**If issues found**:
1. Categorize: Critical (must resolve), Warning (should resolve), Info (non-blocking).
2. Present: `[CRITICAL/WARNING/INFO] <category>: <description>` with context and suggested resolutions.
3. Resolve interactively: For critical issues, prompt for clarification. For warnings, ask resolve or skip.
4. Re-validate after resolution. Loop until all critical issues resolved.

## Step 3: Integrity Re-Check

1. Re-run all checks from Step 2 with updated understanding.
2. Verify user clarifications are consistent.
3. Check for new issues introduced by clarifications.
4. If misalignments remain, go back to Step 2.5.

## Step 4: OpenSpec Change Creation

### 4.1: Determine Change Name

1. Extract from plan title, convert to kebab-case.
2. Ensure unique (check existing changes in `openspec/changes/`).

### 4.2: Execute OPSX Fast-Forward

Invoke the `opsx:ff` skill with the change name:
- Use the plan as source of requirements.
- Map plan phases/tasks to OpenSpec capabilities.
- The opsx:ff workflow creates: change directory, proposal.md, specs/, design.md, tasks.md.
- It reads `openspec/config.yaml` for project context and per-artifact rules.

### 4.3: Extract Change ID

1. Identify created change ID.
2. Verify change directory: `openspec/changes/<change-id>/`.
3. Verify artifacts created: proposal.md, tasks.md, specs/.

## Step 5: Proposal Review and Improvement

### 5.1: Review Against Config and Project Rules

1. **Read `openspec/config.yaml`**:
   - Project context: Tech stack, constraints, architecture patterns.
   - Development discipline (SDD + TDD): (1) Specs first, (2) Tests second (expect failure), (3) Code last.
   - Per-artifact rules: `rules.tasks` — TDD order, test-before-code.

2. **Read and apply project rules** from CLAUDE.md:
   - Contract-first development, testing requirements, code conventions.

3. **Verify config.yaml rules applied**:
   - Source Tracking section (if public-facing).
   - GitHub issue creation task (if public repo).
   - 2-hour maximum chunks.
   - TDD: test tasks before implementation.

### 5.2: Update Tasks with Quality Standards and Git Workflow

#### 5.2.1: Determine Branch Type

- `add-*`, `create-*`, `implement-*`, `enhance-*` -> `feature/`
- `fix-*`, `correct-*`, `repair-*` -> `bugfix/`
- `update-*`, `modify-*`, `refactor-*` -> `feature/`
- `hotfix-*`, `urgent-*` -> `hotfix/`
- Default: `feature/`

Branch name: `<branch-type>/<change-id>`. Target: `dev`.

#### 5.2.2: Add Git Worktree Creation Task (FIRST TASK)

Add as first task in tasks.md:

```markdown
## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/<branch-type>/<change-id> -b <branch-type>/<change-id> origin/dev`
  - [ ] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/<branch-type>/<change-id>`
  - [ ] 1.1.4 Create a virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.5 `git branch --show-current` (verify correct branch)
```

**If a GitHub issue exists**, use `gh issue develop` to link the branch before creating the worktree:

```markdown
  - [ ] 1.1.2a `gh issue develop <issue-number> --repo <target-repo> --name <branch-type>/<change-id>` (creates remote branch linked to issue)
  - [ ] 1.1.2b `git fetch origin && git worktree add ../specfact-cli-worktrees/<branch-type>/<change-id> <branch-type>/<change-id>`
```

All remaining tasks in tasks.md MUST run inside the worktree directory, not the primary checkout.

#### 5.2.3: Update Tasks with Quality Standards

For each task, ensure:
- Testing requirements (unit, contract, integration, E2E).
- Code quality checks: `hatch run format`, `hatch run type-check`, `hatch run contract-test`.
- Validation: `openspec validate <change-id> --strict`.

#### 5.2.4: Enforce TDD-first in tasks.md

1. **Add "TDD / SDD order (enforced)" section** at top of tasks.md (after title, before first numbered task):
   - State: per config.yaml, tests before code for any behavior-changing task.
   - Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last.
   - "Do not implement production code until tests exist and have been run (expecting failure)."
   - Separate with `---`.

2. **Reorder each behavior-changing section**: Test tasks before implementation tasks.

3. **Verify**: Scan tasks.md — any section with both test and implementation tasks must have tests first.

#### 5.2.5: Add PR Creation Task (LAST TASK)

Add as last task in tasks.md. Only create PR if target repo is public (specfact-cli, platform-frontend).

Key steps (run from inside the worktree directory):
1. Prepare commit: `git add .`, commit with conventional message, push with `-u`: `git push -u origin <branch-type>/<change-id>`.
2. Create PR body from `.github/pull_request_template.md`:
   - Use full repo path format for issue refs: `Fixes nold-ai/specfact-cli#<number>`
   - Include OpenSpec change ID in description.
3. Create PR: `gh pr create --repo <target-repo> --base dev --head <branch> --title "<type>: <desc>" --body-file <body-file>`
4. Link to project (specfact-cli only): `gh project item-add 1 --owner nold-ai --url <PR_URL>`
5. Verify Development link on issue, project board.
6. Update project status to "In Progress" (if applicable).

PR title format: `feat:` for feature/, `fix:` for bugfix/, etc.

#### 5.2.6: Add Worktree Cleanup Task (AFTER MERGE)

Add a note after the PR task for post-merge cleanup:

```markdown
## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd .../specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/<branch-type>/<change-id>`
- [ ] `git branch -d <branch-type>/<change-id>`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete <branch-type>/<change-id>`
```

### 5.3: Update Proposal with Quality Gates

Update proposal.md with: quality standards section, git workflow requirements, acceptance criteria (branch created, tests pass, contracts validated, docs updated, PR created).

### 5.4: Validate with OpenSpec

1. Verify format: proposal.md has `# Change:` title, `## Why`, `## What Changes`, `## Impact`. Tasks.md uses `## 1.` numbered format.
2. Check status: `openspec status --change "<change-id>" --json`.
3. Run: `openspec validate <change-id> --strict`. Fix and re-run until passing.

### 5.5: Markdown Linting

Run `markdownlint --config .markdownlint.json --fix` on all `.md` files in the change directory. Fix remaining issues manually.

## Step 6: GitHub Issue Creation

### 6.1: Determine Target Repository

1. Extract target repo from plan header (`**Repository**:` field).
2. Decision:
   - `specfact-cli` or `platform-frontend` (public) -> create issue, proceed to 6.2.
   - `specfact-cli-internal` (internal) -> skip issue creation, go to Step 8.
   - Not specified -> ask user.

### 6.2: Sanitize Proposal Content

For public issues:
- **Remove**: Competitive analysis, market positioning, internal strategy, effort estimates.
- **Preserve**: User-facing value, feature descriptions, acceptance criteria, API changes.

Format per config.yaml:
- Title: `[Change] <Brief Description>`
- Labels: `enhancement`, `change-proposal`
- Body: `## Why`, `## What Changes`, `## Acceptance Criteria`
- Footer: `*OpenSpec Change Proposal: <change-id>*`

Show sanitized content to user for approval before creating.

## Step 7: Create GitHub Issue via gh CLI

1. Write sanitized content to temp file.
2. Create issue:

```bash
gh issue create \
  --repo <target-repo> \
  --title "[Change] <title>" \
  --body-file /tmp/github-issue-<change-id>.md \
  --label "enhancement" \
  --label "change-proposal"
```

3. For specfact-cli: link to project `gh project item-add 1 --owner nold-ai --url <ISSUE_URL>`.
4. Update `proposal.md` Source Tracking section:

```markdown
## Source Tracking

<!-- source_repo: <target-repo> -->
- **GitHub Issue**: #<number>
- **Issue URL**: <url>
- **Last Synced Status**: proposed
```

5. Cleanup temp file.

## Step 8: Completion

Display summary:

```
Change ID: <change-id>
Location: openspec/changes/<change-id>/

Validation:
  - OpenSpec validation passed
  - Markdown linting passed
  - Config.yaml rules applied (TDD-first enforced)
  - Git workflow tasks added (branch + PR)

GitHub Issue (if public):
  - Issue #<number> created: <url>
  - Source tracking updated

Next Steps:
  1. Review: openspec/changes/<change-id>/proposal.md
  2. Review: openspec/changes/<change-id>/tasks.md
  3. Verify TDD order and git workflow in tasks
  4. Apply when ready: invoke opsx:apply skill
```

## Error Handling

- **Plan not found**: Search and suggest alternatives.
- **Validation failures**: Present clearly, allow interactive resolution.
- **OpenSpec validation fails**: Fix and re-validate, don't proceed until passing.
- **gh CLI unavailable**: Inform user, provide manual creation instructions.
- **Issue creation fails**: Log error, allow retry, don't fail entire workflow.
- **Project linking fails**: Log warning, continue (non-critical).
