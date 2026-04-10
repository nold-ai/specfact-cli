# AGENTS.md

This file is the mandatory bootstrap governance surface for coding agents working in this repository. It is intentionally compact. The detailed rules that used to live here have been preserved in `docs/agent-rules/` so new sessions do not pay the full context cost up front.

## Mandatory bootstrap

1. Read this file.
2. Read [docs/agent-rules/INDEX.md](docs/agent-rules/INDEX.md).
3. Read [docs/agent-rules/05-non-negotiable-checklist.md](docs/agent-rules/05-non-negotiable-checklist.md).
4. Detect repository root, active branch, and worktree state.
5. Reject implementation from the `dev` or `main` checkout unless the user explicitly overrides that rule.
6. If GitHub hierarchy metadata is needed and `.specfact/backlog/github_hierarchy_cache.md` is missing or stale, refresh it with `python scripts/sync_github_hierarchy_cache.py`.
7. Load any additional rule files required by the applicability matrix in [docs/agent-rules/INDEX.md](docs/agent-rules/INDEX.md) before implementation.

## Precedence

1. Direct system and developer instructions
2. Explicit user override where repository governance allows it
3. This file
4. [docs/agent-rules/05-non-negotiable-checklist.md](docs/agent-rules/05-non-negotiable-checklist.md)
5. Other selected files under `docs/agent-rules/`
6. Change-local OpenSpec artifacts and workflow notes

## Non-negotiable gates

- Work in a git worktree unless the user explicitly overrides that rule.
- Do not implement from the `dev` or `main` checkout by default.
- Treat a provided OpenSpec change id as candidate scope, not automatic permission to proceed.
- Verify the selected change against current repository reality and dependency state before implementation.
- Do not auto-refine stale or ambiguous changes without the user.
- Perform `spec -> tests -> failing evidence -> code -> passing evidence` in that order for behavior changes.
- Require public GitHub metadata completeness before implementation when linked issue workflow applies: parent, labels, project assignment, blockers, and blocked-by relationships.
- If a linked GitHub issue is already `in progress`, pause and ask for clarification before implementation.
- Run the required verification and quality gates for the touched scope before finalization.
- Fix SpecFact code review findings, including warnings, unless a rare explicit exception is documented.
- Treat the clean-code compliance gate as mandatory: the review surface enforces `naming`, `kiss`, `yagni`, `dry`, and `solid` categories and blocks regressions.
- Enforce module signatures and version bumps when signed module assets or manifests are affected.
- Finalize completed OpenSpec changes with `openspec archive <change-id>` (see [docs/agent-rules/40-openspec-and-tdd.md](docs/agent-rules/40-openspec-and-tdd.md)); do not manually move change folders under `openspec/changes/archive/`.

## Strategic context

Design and dependency context may live in a **sibling internal repository** (for example a checkout of `specfact-cli-internal` beside this repo, with wiki pages under `../specfact-cli-internal/wiki/`). Before designing or scoping a new OpenSpec change, read the wiki paths listed in [docs/agent-rules/40-openspec-and-tdd.md](docs/agent-rules/40-openspec-and-tdd.md#internal-wiki-and-strategic-context) using **absolute paths** to those files. Treat the wiki as read-only context; do not paste or commit wiki bodies into this public repository. Material edits to an **active** OpenSpec change (scope, design, tasks, dependencies) require updating the matching `wiki/sources/<change-id>.md` in the sibling internal repo when present, then running `wiki_rebuild_graph.py` from that repo’s root; if the sibling checkout is missing, record a follow-up instead of assuming the wiki was updated. After merges that ship OpenSpec or related work, run the internal wiki scripts only after `cd` into that sibling checkout (for example `cd ../specfact-cli-internal && python3 scripts/wiki_openspec_gh_status.py`); do not run them from an arbitrary working directory. Use `wiki_rebuild_graph.py` when frontmatter churn is large, as described in the same section.

## Canonical rule docs

- [docs/agent-rules/INDEX.md](docs/agent-rules/INDEX.md)
- [docs/agent-rules/05-non-negotiable-checklist.md](docs/agent-rules/05-non-negotiable-checklist.md)
- [docs/agent-rules/10-session-bootstrap.md](docs/agent-rules/10-session-bootstrap.md)
- [docs/agent-rules/20-repository-context.md](docs/agent-rules/20-repository-context.md)
- [docs/agent-rules/30-worktrees-and-branching.md](docs/agent-rules/30-worktrees-and-branching.md)
- [docs/agent-rules/40-openspec-and-tdd.md](docs/agent-rules/40-openspec-and-tdd.md)
- [docs/agent-rules/50-quality-gates-and-review.md](docs/agent-rules/50-quality-gates-and-review.md)
- [docs/agent-rules/60-github-change-governance.md](docs/agent-rules/60-github-change-governance.md)
- [docs/agent-rules/70-release-commit-and-docs.md](docs/agent-rules/70-release-commit-and-docs.md)
- [docs/agent-rules/80-current-guidance-catalog.md](docs/agent-rules/80-current-guidance-catalog.md)

Detailed guidance was moved by reference, not removed. If a rule seems missing here, consult the canonical rule docs before assuming the instruction was dropped.
