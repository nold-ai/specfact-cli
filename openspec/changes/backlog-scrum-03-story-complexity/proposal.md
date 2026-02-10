# Change: Backlog Scrum — Story Complexity and Splitting Hints

## Why


The backlog-refinement spec includes "Story Complexity Analysis" scenarios, but this behavior is not implemented. Teams need complexity scores considering story points and business value, flagging of stories >13 points for potential splitting, suggestions to split into multiple stories under the same feature with rationale, and splitting suggestion included in refinement output when a story is complex. Without this, refinement sessions do not surface size/scope risks.

This change is part of the **`backlog-scrum` module** — delivered alongside standup and sprint planning capabilities.

## Module Package Structure

```
modules/backlog-scrum/
  module-package.yaml          # complexity integrated into backlog refine extension
  src/backlog_scrum/
    complexity/
      scorer.py                # complexity score (story_points, business_value)
      splitter.py              # splitting suggestion (rationale, split points)
    commands/
      refine_hook.py           # integration hook into backlog refine output
```

**No new top-level command**: complexity is surfaced as an enhancement to `backlog refine` output when `backlog-scrum` module is loaded.

**Config**: Complexity threshold stored in `.specfact/scrum.yaml` under `complexity.threshold` (default 13 points).

## Module Package Structure

```
modules/backlog-scrum/
  module-package.yaml          # complexity integrated into backlog refine extension
  src/backlog_scrum/
    complexity/
      scorer.py                # complexity score (story_points, business_value)
      splitter.py              # splitting suggestion (rationale, split points)
    commands/
      refine_hook.py           # integration hook into backlog refine output
```

**No new top-level command**: complexity is surfaced as an enhancement to `backlog refine` output when `backlog-scrum` module is loaded.

**Config**: Complexity threshold stored in `.specfact/scrum.yaml` under `complexity.threshold` (default 13 points).

## What Changes


- **NEW**: Complexity calculation in `modules/backlog-scrum/src/backlog_scrum/complexity/scorer.py` — score from `story_points` + `business_value`; configurable threshold in `.specfact/scrum.yaml`.
- **NEW**: Splitting detection in `modules/backlog-scrum/src/backlog_scrum/complexity/splitter.py` — suggests split points and rationale (by acceptance criteria or logical boundaries).
- **EXTEND**: Integrate into `backlog refine` flow via command extension hook in module registry: when `backlog-scrum` is loaded and refinement completes for a complex story, include a "Story splitting suggestion" block in the output.
- **EXTEND** (plan E3): Splitting suggestions SHALL consider dependency edges from backlog-core-01 (minimize cross-team coupling) and blast radius signals. Provide patch output via patch-mode-01: "split proposal" as suggested child stories with titles + AC + links.

## Capabilities
- **backlog-scrum** (complexity): Complexity score; `needs_splitting` predicate (configurable threshold); splitting suggestion with rationale; integration into `backlog refine` output; dependency-aware splitting and patch output when backlog-core-01 and patch-mode-01 are available.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #171
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/171>
- **Last Synced Status**: proposed
- **Sanitized**: false
