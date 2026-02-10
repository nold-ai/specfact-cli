# Change: Backlog Scrum — Definition of Done Support

## Why


SpecFact CLI has Definition of Ready (DoR) for backlog refinement. Teams also need Definition of Done (DoD) to ensure items moved to "Done" meet completion criteria. DoD is not modeled or validated today; there is no way to define team DoD rules (e.g. checklist: tests pass, docs updated, code reviewed) and run them against items in Done state.

This change is part of the **`backlog-scrum` module** — delivered alongside standup, sprint planning, and story complexity capabilities. DoD is a Scrum-native concept shared by all sprint-based teams.

## Module Package Structure

```
modules/backlog-scrum/
  module-package.yaml          # updated: add 'backlog dod' command; DoD integrates with policy-engine
  src/backlog_scrum/
    dod/
      config.py                # DoD config loading from .specfact/scrum.yaml
      validator.py             # DoD rule evaluation for Done-state items
    commands/
      dod.py                   # specfact backlog dod (optional dedicated subcommand)
```

**Config**: DoD rules stored in `.specfact/scrum.yaml` under `dod.rules` (or as a named template). All Scrum-specific config (sprint capacity, complexity threshold, DoD) consolidated under `.specfact/scrum.yaml`.

**Integration with policy-engine-01**: When policy-engine-01 is installed, DoD validation is surfaced as a policy rule set so `policy validate` includes DoD checks for Done items. DoD can also be used standalone without policy-engine-01.

## Module Package Structure

```
modules/backlog-scrum/
  module-package.yaml          # updated: add 'backlog dod' command; DoD integrates with policy-engine
  src/backlog_scrum/
    dod/
      config.py                # DoD config loading from .specfact/scrum.yaml
      validator.py             # DoD rule evaluation for Done-state items
    commands/
      dod.py                   # specfact backlog dod (optional dedicated subcommand)
```

**Config**: DoD rules stored in `.specfact/scrum.yaml` under `dod.rules` (or as a named template). All Scrum-specific config (sprint capacity, complexity threshold, DoD) consolidated under `.specfact/scrum.yaml`.

**Integration with policy-engine-01**: When policy-engine-01 is installed, DoD validation is surfaced as a policy rule set so `policy validate` includes DoD checks for Done items. DoD can also be used standalone without policy-engine-01.

## What Changes


- **NEW**: Model DoD as a checklist or rule set in `modules/backlog-scrum/src/backlog_scrum/dod/` — stored in `.specfact/scrum.yaml` under `dod` section; similar in structure to DoR but for completion criteria.
- **NEW**: When listing or exporting backlog items in "Done" (or equivalent) state, optionally run DoD validation via `modules/backlog-scrum/src/backlog_scrum/dod/validator.py` and attach DoD status (pass/fail + which criteria failed).
- **EXTEND**: Integrate into `backlog list`, `backlog refine`, or a dedicated `specfact backlog dod` subcommand: for items in done state, show DoD status in output and export. Declared in `module-package.yaml`; no changes to `cli.py`.
- **EXTEND** (policy-engine-01): When policy-engine-01 is present, register DoD rules as a policy rule set so `policy validate` covers completion criteria for Done items.

## Capabilities
- **backlog-scrum** (DoD): DoD config load from `.specfact/scrum.yaml`; DoD validation for done items; DoD status in CLI/export when enabled; optional policy-engine-01 integration for unified `policy validate` coverage.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #169
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/169>
- **Last Synced Status**: proposed
- **Sanitized**: false
