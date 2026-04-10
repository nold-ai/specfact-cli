# Change: Policy Engine — Unified Policy Framework (DoR/DoD/Flow/PI)

## Why

Teams love tools that enforce working agreements consistently. Today DoR/DoD are fragmented across features; Kanban/SAFe policies are not first-class. A single Policy framework with `policy.validate` (hard failures; deterministic) and `policy.suggest` (AI-assisted; confidence-scored; patch-ready) gives one mechanism for DoR, DoD, Kanban entry/exit, and SAFe PI readiness so refinement, planning, and standup share the same quality gates.

This change establishes the **`policy-engine` module** — a foundational cross-cutting module that all backlog framework modules (backlog-scrum, backlog-kanban, backlog-safe) depend on for policy evaluation. It must be available before those modules can use it.

## Module Package Structure

```
modules/policy-engine/
  module-package.yaml          # name: policy-engine; commands: policy validate, policy suggest
  src/policy_engine/
    __init__.py
    main.py                    # typer.Typer app — policy command group
    engine/
      validator.py             # policy.validate (hard failures; deterministic)
      suggester.py             # policy.suggest (AI-assisted; confidence-scored; patch-ready)
    policies/
      scrum.py                 # DoR + DoD policies
      kanban.py                # entry/exit policies per column
      safe.py                  # PI readiness policy hooks
    models/
      policy_result.py         # PolicyResult (rule id, severity, evidence pointer, recommended action)
    config/
      policy_config.py         # .specfact/policy.yaml loader
    registry/
      policy_registry.py       # Allows other modules to register their policies (arch-05 bridge)
```

**`module-package.yaml` declares:**

- `name: policy-engine`
- `version: 0.1.0`
- `commands: [policy validate, policy suggest]`
- `dependencies: []` (no module deps; foundational)
- `schema_extensions:` — see arch-07 section below
- `publisher:` + `integrity:` — arch-06 marketplace readiness

Commands are auto-discovered by the registry and lazy-loaded; no registration in `cli.py` required.

## Module Package Structure

```
modules/policy-engine/
  module-package.yaml          # name: policy-engine; commands: policy validate, policy suggest
  src/policy_engine/
    __init__.py
    main.py                    # typer.Typer app — policy command group
    engine/
      validator.py             # policy.validate (hard failures; deterministic)
      suggester.py             # policy.suggest (AI-assisted; confidence-scored; patch-ready)
    policies/
      scrum.py                 # DoR + DoD policies
      kanban.py                # entry/exit policies per column
      safe.py                  # PI readiness policy hooks
    models/
      policy_result.py         # PolicyResult (rule id, severity, evidence pointer, recommended action)
    config/
      policy_config.py         # .specfact/policy.yaml loader
    registry/
      policy_registry.py       # Allows other modules to register their policies (arch-05 bridge)
```

**`module-package.yaml` declares:**

- `name: policy-engine`
- `version: 0.1.0`
- `commands: [policy validate, policy suggest]`
- `dependencies: []` (no module deps; foundational)
- `schema_extensions:` — see arch-07 section below
- `publisher:` + `integrity:` — arch-06 marketplace readiness

Commands are auto-discovered by the registry and lazy-loaded; no registration in `cli.py` required.

## What Changes

- **NEW**: Policy framework in `modules/policy-engine/src/policy_engine/engine/`:
  - `policy.validate` (hard failures; deterministic; offline-capable against snapshots)
  - `policy.suggest` (AI-assisted; confidence-scored; patch-ready output for patch-mode-01)
- **NEW**: First policies shipped:
  - Scrum (DoR + DoD policies) — in `modules/policy-engine/src/policy_engine/policies/scrum.py`; DoD policies also consumed by backlog-scrum-04
  - Kanban (entry/exit policies per column) — consumed by backlog-kanban-01
  - SAFe (PI readiness policy hooks, minimal baseline) — consumed by backlog-safe-01
- **NEW**: Machine-readable output: JSON for CI gates; Markdown for humans.
- **NEW**: Config: `.specfact/policy.yaml`; `specfact policy validate` runs without network access (against snapshots when applicable).
- **NEW**: CLI commands `specfact policy init`, `specfact policy validate`, and `specfact policy suggest` declared in `module-package.yaml`.
- **NEW**: `policy init` scaffolds `.specfact/policy.yaml` from common framework templates (Scrum, Kanban, SAFe, Mixed baseline) with interactive or `--template` selection.
- **NEW**: Policy template assets are sourced from `resources/templates/policies/` to ensure built-in templates ship with wheel/sdist.
- **EXTEND**: `policy validate` error output includes a docs hint for policy YAML format when config is missing or invalid.
- **EXTEND**: `policy validate` and `policy suggest` auto-discover policy input from existing `.specfact` artifacts when `--snapshot` is omitted (prefer `.specfact/backlog-baseline.json`, then latest `.specfact/plans/backlog-*`).
- **EXTEND**: Policy input loader normalizes existing foundation artifact shapes (`items` list/dict and `backlog_graph.items`) into policy-evaluable item arrays.
- **EXTEND**: Compatibility mapping resolves common provider/raw-data aliases and description sections into canonical policy fields (`acceptance_criteria`, `business_value`, `definition_of_done`) before validation.
- **EXTEND**: `policy validate` and `policy suggest` support `--rule`, `--limit`, and optional `--group-by-item` output for high-volume snapshots.
- **EXTEND**: In grouped mode, `--limit` caps the number of backlog item groups (not per-item field findings), and grouped payloads avoid duplicate flat arrays.
- **EXTEND**: Policy results include: rule id, severity, evidence pointer (field/path), and recommended action.
- **NEW** (policy registry): `PolicyRegistryProtocol` via arch-05 bridge registry — allows other modules (backlog-scrum-04, backlog-kanban-01, backlog-safe-01) to register additional policy rule sets without modifying the policy-engine module.
- **EXTEND** (arch-07 schema extensions): Register `policy_engine.policy_status` extension on `BacklogItem` via `module-package.yaml` — stores last policy validation result (pass/fail, failed rules) for each item; access via `item.get_extension("policy_engine", "policy_status")`.

## Arch-06 Marketplace Readiness

```yaml
publisher:
  name: nold-ai
  url: https://github.com/nold-ai/specfact-cli-modules
integrity:
  checksum_algorithm: sha256
```

## Capabilities

- **policy-engine**: Policy framework (validate, suggest); DoR/DoD/Flow/PI policies; JSON and Markdown output; config-driven rules; evidence and recommended action per result; `PolicyRegistryProtocol` for module-contributed policies; arch-07 schema extension on BacklogItem.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #176
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/176>
- **Last Synced Status**: proposed
- **Sanitized**: false
