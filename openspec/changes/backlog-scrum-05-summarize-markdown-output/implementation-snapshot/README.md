# Implementation snapshot for backlog-scrum-05-summarize-markdown-output

These files are copies of the **implementation artifacts** that were modified on dev for change `backlog-scrum-05-summarize-markdown-output` (summarize Markdown normalization, TTY/CI rendering). They live here so you can restore them on the dev branch later (or apply them in a feature worktree) without losing the work.

## Contents (paths relative to repo root)

| Snapshot path | Repo path (restore to) |
|---------------|------------------------|
| `src/specfact_cli/modules/backlog/src/commands.py` | `src/specfact_cli/modules/backlog/src/commands.py` |
| `tests/unit/commands/test_backlog_daily.py` | `tests/unit/commands/test_backlog_daily.py` |
| `docs/getting-started/tutorial-daily-standup-sprint-review.md` | `docs/getting-started/tutorial-daily-standup-sprint-review.md` |
| `docs/guides/agile-scrum-workflows.md` | `docs/guides/agile-scrum-workflows.md` |

## How to restore on dev (or in a worktree)

From the **repository root** (e.g. after checking out dev or your feature branch):

```bash
# Restore all snapshot files into the repo
SNAPSHOT="openspec/changes/backlog-scrum-05-summarize-markdown-output/implementation-snapshot"
cp "$SNAPSHOT/src/specfact_cli/modules/backlog/src/commands.py" src/specfact_cli/modules/backlog/src/
cp "$SNAPSHOT/tests/unit/commands/test_backlog_daily.py" tests/unit/commands/
cp "$SNAPSHOT/docs/getting-started/tutorial-daily-standup-sprint-review.md" docs/getting-started/
cp "$SNAPSHOT/docs/guides/agile-scrum-workflows.md" docs/guides/
```

Or, to overwrite from the snapshot tree in one go (from repo root):

```bash
SNAPSHOT="openspec/changes/backlog-scrum-05-summarize-markdown-output/implementation-snapshot"
for f in src/specfact_cli/modules/backlog/src/commands.py \
         tests/unit/commands/test_backlog_daily.py \
         docs/getting-started/tutorial-daily-standup-sprint-review.md \
         docs/guides/agile-scrum-workflows.md; do
  cp "$SNAPSHOT/$f" "$f"
done
```

After restoring, run `hatch run format`, `hatch run type-check`, `hatch run contract-test`, and tests as per AGENTS.md.
