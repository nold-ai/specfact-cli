# Change: Ceremony Cockpit — Ceremony Aliases and Framework Mode Switch

## Why

Teams think in ceremonies ("standup," "refinement," "planning"). Without ceremony entry points, adoption friction remains high — users must remember `backlog daily`, `backlog refine`, `backlog sprint-summary` instead of `backlog ceremony standup`, `backlog ceremony refinement`, `backlog ceremony planning`. Ceremony aliases plus mode switch (scrum|kanban|safe) and exceptions-first defaults are a pure UX/ergonomics win with minimal implementation cost.

This change establishes the **`ceremony-cockpit` module** — the UX alias layer that wraps all installed backlog framework modules (backlog-scrum, backlog-kanban, backlog-safe) with ceremony-oriented entry points.

## Module Package Structure

```
modules/ceremony-cockpit/
  module-package.yaml          # name: ceremony-cockpit; commands: [backlog] (extends backlog with ceremony subgroup)
  src/ceremony_cockpit/
    __init__.py
    main.py                    # typer.Typer app — extends backlog with ceremony subgroup
    commands/
      standup.py               # backlog ceremony standup → backlog daily (with --mode scrum)
      refinement.py            # backlog ceremony refinement → backlog refine
      planning.py              # backlog ceremony planning → backlog sprint-summary (with --mode scrum)
      flow.py                  # backlog ceremony flow → backlog flow (with --mode kanban; when backlog-kanban installed)
      pi_summary.py            # backlog ceremony pi-summary → backlog pi-summary (with --mode safe; when backlog-safe installed)
    discovery/
      module_probe.py          # detect which backlog modules are installed; omit missing aliases
```

**`module-package.yaml` declares:**

- `name: ceremony-cockpit`
- `version: 0.1.0`
- `commands: [backlog]` (module extends backlog command with `ceremony` subgroup aliases)
- `dependencies: []` (no hard deps; probes installed backlog modules at runtime)
- `optional_dependencies: [backlog-scrum, backlog-kanban, backlog-safe]`
- `publisher:` + `integrity:` — arch-06 marketplace readiness

**Important**: Backlog ceremony subcommands are dynamically available based on which backlog framework modules are installed. `backlog ceremony flow` only appears if `backlog-kanban` is installed; `backlog ceremony pi-summary` only if `backlog-safe` is installed. Module probe uses the registry to detect installed modules.

## Module Package Structure

```
modules/ceremony-cockpit/
  module-package.yaml          # name: ceremony-cockpit; commands: [backlog] (extends backlog with ceremony subgroup)
  src/ceremony_cockpit/
    __init__.py
    main.py                    # typer.Typer app — extends backlog with ceremony subgroup
    commands/
      standup.py               # backlog ceremony standup → backlog daily (with --mode scrum)
      refinement.py            # backlog ceremony refinement → backlog refine
      planning.py              # backlog ceremony planning → backlog sprint-summary (with --mode scrum)
      flow.py                  # backlog ceremony flow → backlog flow (with --mode kanban; when backlog-kanban installed)
      pi_summary.py            # backlog ceremony pi-summary → backlog pi-summary (with --mode safe; when backlog-safe installed)
    discovery/
      module_probe.py          # detect which backlog modules are installed; omit missing aliases
```

**`module-package.yaml` declares:**

- `name: ceremony-cockpit`
- `version: 0.1.0`
- `commands: [backlog]` (module extends backlog command with `ceremony` subgroup aliases)
- `dependencies: []` (no hard deps; probes installed backlog modules at runtime)
- `optional_dependencies: [backlog-scrum, backlog-kanban, backlog-safe]`
- `publisher:` + `integrity:` — arch-06 marketplace readiness

**Important**: Backlog ceremony subcommands are dynamically available based on which backlog framework modules are installed. `backlog ceremony flow` only appears if `backlog-kanban` is installed; `backlog ceremony pi-summary` only if `backlog-safe` is installed. Module probe uses the registry to detect installed modules.

## What Changes

- **NEW**: Ceremony-oriented entry points in `modules/ceremony-cockpit/src/ceremony_cockpit/commands/`:
  - `specfact backlog ceremony standup` → `backlog daily` (delegates with `--mode scrum` default)
  - `specfact backlog ceremony refinement` → `backlog refine`
  - `specfact backlog ceremony planning` → `backlog sprint-summary` (delegates with `--mode scrum`)
  - `specfact backlog ceremony flow` → `backlog flow` (delegates with `--mode kanban`; present only if backlog-kanban installed)
  - `specfact backlog ceremony pi-summary` → `backlog pi-summary` (delegates with `--mode safe`; present only if backlog-safe installed)
- **NEW**: Each ceremony command emits: human view (Markdown/table), machine view (JSON when underlying command supports `--output json`), and optional Copilot prompt export; output formats inherited/forwarded from underlying backlog command.
- **NEW**: `--mode scrum|kanban|safe` at ceremony level — sets defaults for filters and sections; forwarded to underlying backlog command.
- **EXTEND**: Exceptions-first default section order (blockers, policy failures, aging, normal) when applicable; inherits from backlog-scrum-01 (E1) and policy-engine-01.
- **NEW**: Module probe at startup via registry: `ceremony-cockpit` inspects which modules are registered and only surfaces ceremony aliases for installed modules — zero-impact if optional modules are absent.
- **No changes to `cli.py`** — module extends existing `backlog` command group via module registry composition.

## Capabilities

- **ceremony-cockpit**: Backlog ceremony aliases (`backlog ceremony standup`, `backlog ceremony refinement`, optional planning/flow/pi-summary); dynamic availability based on installed modules; mode switch (scrum|kanban|safe); exceptions-first defaults; output format forwarding.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #185
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/185>
- **Last Synced Status**: in-progress
- **Sanitized**: false
