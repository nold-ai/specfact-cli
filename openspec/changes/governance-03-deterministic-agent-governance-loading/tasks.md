# Tasks: governance-03-deterministic-agent-governance-loading

## 1. Branch and governance preparation

- [x] 1.1 Create dedicated worktree branch `feature/governance-03-deterministic-agent-governance-loading` from `origin/dev` before implementation work: `scripts/worktree.sh create feature/governance-03-deterministic-agent-governance-loading`.
- [x] 1.2 In the new worktree directory, bootstrap Python tooling with `hatch env create`.
- [x] 1.3 Run pre-flight checks from the worktree root: `hatch run smart-test-status` and `hatch run contract-test-status`.
- [x] 1.4 Confirm governance-01 and governance-02 outputs remain the dependency baseline for this change and update `openspec/CHANGE_ORDER.md` metadata if sequencing notes need adjustment.
- [x] 1.5 Review current `AGENTS.md`, related instruction surfaces, and existing docs/frontmatter validators to identify the files that must participate in the compact-governance migration.
- [ ] 1.6 After the PR merges: run `git worktree remove`, `git branch -d`, and `git worktree prune` per `AGENTS.md`; delete the worktree-local `.venv` (or other env path) if you no longer need that checkout.

## 2. Spec-first and test-first preparation

- [x] 2.1 Finalize the `agent-governance-loading` and `github-hierarchy-cache` spec deltas and cross-check scenario completeness.
- [x] 2.2 Add or update tests/validators that cover rule-file frontmatter, deterministic always-load behavior, precedence handling, cache-refresh bootstrap rules, and GitHub metadata completeness / `in progress` ambiguity handling.
- [x] 2.3 Run targeted tests to capture failing-first behavior and record the results in `TDD_EVIDENCE.md` before production edits.

## 3. Governance implementation

- [x] 3.1 Replace the long-form `AGENTS.md` body with a compact bootstrap/governance contract that points to canonical rule artifacts.
- [x] 3.2 Create `docs/agent-rules/INDEX.md`, `docs/agent-rules/05-non-negotiable-checklist.md`, and the first domain rule files needed to cover bootstrap, change validation, TDD, quality gates, docs/versioning, and finalization.
- [x] 3.3 Implement or extend validation so governance rule files enforce the required frontmatter schema and deterministic metadata fields.
- [x] 3.4 Update related instruction surfaces and workflow guidance so they reference the canonical governance rule system instead of duplicating long-form policy text.
- [x] 3.5 Update cache-first governance guidance so session bootstrap refreshes `.specfact/backlog/github_hierarchy_cache.md` when it is missing or stale.
- [x] 3.6 Implement or extend governance logic and docs so public-work readiness checks cover parent resolution, labels, project assignment, blockers / blocked-by relationships, and `in progress` issue-state clarification.

## 4. Validation and documentation

- [x] 4.1 Re-run targeted and required quality gates until the compact-governance behavior and docs validation pass.
- [x] 4.2 Run `hatch run specfact code review run --json --out .specfact/code-review.json` and resolve all findings, including warnings.
Blocked in the current worktree environment because the `nold-ai/specfact-codebase` module that provides `specfact code review` is not installed.
- [x] 4.3 Update user-facing documentation and navigation for the new governance artifact layout and explain how `AGENTS.md` now delegates to canonical rule files.
- [x] 4.4 Run `openspec validate governance-03-deterministic-agent-governance-loading --strict` and resolve all issues.

## 5. Delivery

- [x] 5.1 Refresh `TDD_EVIDENCE.md` with passing-after commands and timestamps.
- [x] 5.2 Update `openspec/CHANGE_ORDER.md` implementation status or dependency notes if anything changed during delivery.
- [x] 5.3 Open a PR from `feature/governance-03-deterministic-agent-governance-loading` to `dev` with spec/test/code/docs/code-review evidence.
