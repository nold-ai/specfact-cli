# Change: Patch Mode — Previewable and Confirmable Patch Pipeline

## Why

Reporting findings is not enough; teams love tools that propose fixes they can safely apply. A patch pipeline that generates unified diffs for backlog body updates, OpenSpec proposal/spec updates, and config updates — with `--apply` (local) and `--write` (upstream) gating and idempotency for posted comments/updates — ensures zero accidental writes and trust by design.

This change establishes the **`patch-mode` module** — a foundational cross-cutting module consumed by policy-engine-01 (suggest → patch), backlog-scrum-01 (standup notes patch), backlog-scrum-03 (split proposal patch), and backlog-core-02 (interactive issue preview).

## Module Package Structure

```
modules/patch-mode/
  module-package.yaml          # name: patch-mode; commands: patch apply
  src/patch_mode/
    __init__.py
    main.py                    # typer.Typer app — patch command group
    pipeline/
      generator.py             # unified diff generation (backlog body, OpenSpec, config)
      applier.py               # --apply (local) and --write (upstream) gating
      idempotency.py           # no-duplicate posted comments/updates
    commands/
      apply.py                 # specfact patch apply <patchfile> [--write]
    integrations/
      backlog_hook.py          # backlog refine --patch integration hook
      policy_hook.py           # policy suggest → patch output hook
```

**`module-package.yaml` declares:**

- `name: patch-mode`
- `version: 0.1.0`
- `commands: [patch apply]`
- `dependencies: []` (no module deps; foundational cross-cutting)
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## Module Package Structure

```
modules/patch-mode/
  module-package.yaml          # name: patch-mode; commands: patch apply
  src/patch_mode/
    __init__.py
    main.py                    # typer.Typer app — patch command group
    pipeline/
      generator.py             # unified diff generation (backlog body, OpenSpec, config)
      applier.py               # --apply (local) and --write (upstream) gating
      idempotency.py           # no-duplicate posted comments/updates
    commands/
      apply.py                 # specfact patch apply <patchfile> [--write]
    integrations/
      backlog_hook.py          # backlog refine --patch integration hook
      policy_hook.py           # policy suggest → patch output hook
```

**`module-package.yaml` declares:**

- `name: patch-mode`
- `version: 0.1.0`
- `commands: [patch apply]`
- `dependencies: []` (no module deps; foundational cross-cutting)
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## What Changes

- **NEW**: Patch pipeline in `modules/patch-mode/src/patch_mode/pipeline/generator.py` — generates unified diffs for: backlog issue body updates (AC improvements, missing fields), OpenSpec proposal/spec updates, config updates (policy config, mapping templates).
- **NEW**: `--apply` + `--write` gating in `modules/patch-mode/src/patch_mode/pipeline/applier.py`: default = generate patch only; `--apply` = apply locally; `--write` = push to GitHub/ADO only with explicit confirmation.
- **NEW**: Idempotency in `modules/patch-mode/src/patch_mode/pipeline/idempotency.py` — no duplicate posted comments/updates.
- **NEW**: CLI commands declared in `module-package.yaml`:
  - `specfact patch apply <patchfile>` — applies locally with preflight check
  - `specfact patch apply --write` — updates upstream with explicit confirmation
- **NEW**: Integration hook `PatchModeProtocol` via arch-05 bridge registry — allows other modules to generate patches using patch-mode without hard-importing it:
  - `backlog refine --patch` → generates patch file + summary (via backlog_hook.py)
  - `policy suggest` → generates patch-ready output (via policy_hook.py)
- **No changes to `cli.py`** — `patch` command group declared in `module-package.yaml`.

## PatchModeProtocol (arch-05)

Other modules consume patch generation via bridge registry:

```python
# In backlog-scrum-03 (story complexity splitting):
patch_mode = bridge_registry.resolve(PatchModeProtocol)
if patch_mode:
    patch_file = patch_mode.generate_patch(diff_content, description)
```

Graceful no-op when patch-mode module is not installed.

## Capabilities

- **patch-mode**: Patch pipeline (generate diffs for backlog body, OpenSpec, config); `--apply` (local) and `--write` (upstream) gating; idempotent posts; `patch apply <file>`, `patch apply --write` with confirmation; `PatchModeProtocol` for bridge registry consumers.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #177
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/177>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
