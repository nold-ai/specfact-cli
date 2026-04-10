---
description: Bootstrap Cursor sessions through the canonical agent governance docs instead of relying on stale inline reminders.
globs:
alwaysApply: true
---

# Session Startup Instructions

1. Read `AGENTS.md`.
2. Read `docs/agent-rules/INDEX.md`.
3. Read `docs/agent-rules/05-non-negotiable-checklist.md`.
4. Detect repository root, branch, and worktree state before implementation.
5. Load any additional rule files selected by the applicability matrix in `docs/agent-rules/INDEX.md`.
6. If a sibling internal checkout (for example `../specfact-cli-internal/`) exists and you are designing or scoping an OpenSpec change, follow the internal wiki guidance in `docs/agent-rules/40-openspec-and-tdd.md` (section **Internal wiki and strategic context**): read `wiki/hot.md`, `wiki/graph.md`, and relevant `wiki/concepts/*.md` via absolute paths; do not import wiki text into this repo. When you materially change an active `openspec/changes/<change-id>/` artifact, mirror those semantics to `wiki/sources/<change-id>.md` in the sibling repo (then `cd` there and run `python3 scripts/wiki_rebuild_graph.py`); if the sibling checkout is absent, leave a merge checklist or follow-up instead of claiming the wiki is updated.
7. After merges that ship OpenSpec- or GitHub-related work, when a sibling `specfact-cli-internal` checkout exists, run wiki scripts only with that repo as the **current working directory** (for example `cd ../specfact-cli-internal && python3 scripts/wiki_openspec_gh_status.py`); running from `specfact-cli` or other cwd breaks script logic. If many `docs/agent-rules/` frontmatter files changed, also `cd ../specfact-cli-internal && python3 scripts/wiki_rebuild_graph.py` (details under **Internal wiki maintenance** in `docs/agent-rules/40-openspec-and-tdd.md`).

Do not treat this file as a complete workflow handbook. The canonical repository governance now lives in `docs/agent-rules/`.
