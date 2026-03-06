# Migration gate: findings and how to pass

## Expected result when running the gate

When you run:

```bash
SPECFACT_MODULES_REPO=~/git/nold-ai/specfact-cli-modules python scripts/validate-modules-repo-sync.py --gate
```

you will see:

- **Worktree files (migrated modules): 74** — all 17 modules’ source files under `src/specfact_cli/modules/*/src/`.
- **Present in modules repo: 74** — every file exists in specfact-cli-modules at the correct bundle path.
- **Missing in modules repo: 0** — nothing left only in the worktree.
- **CONTENT DIFFERS (migration gate)** — a long list of worktree file vs modules-repo file pairs.

## Why content differs (expected)

- **Worktree** (specfact-cli): Those files are the in-repo copy that still contains shim-era code, e.g. `bootstrap_local_bundle_sources(__file__)`, `import_module("specfact_backlog.backlog.commands")`, and `specfact_cli.modules.*` imports or re-exports.
- **Modules repo**: The same modules have been migrated with bundle imports (`specfact_codebase.*`, `specfact_backlog.*`, etc.) and without the shim boilerplate.

So “all 74 content differ” does **not** mean logic is missing in the modules repo; it means the modules repo has the migrated (bundle) version and the worktree has the pre-migration/shim version.

## What to verify before passing the gate

1. **File presence** — Gate already checks this: 74/74 present, 0 missing.
2. **Logic parity** — Confirm that no functional changes exist only in the worktree (e.g. recent bug fixes or features that were never copied to specfact-cli-modules). Spot-check a few modules or rely on the fact that migration was done from this worktree into the modules repo.
3. **Non-reversibility** — You are accepting that after closing this change, the 17 modules are maintained only in specfact-cli-modules.

## How to pass the gate when closing the change

After the above verification, run:

```bash
SPECFACT_MIGRATION_CONTENT_VERIFIED=1 SPECFACT_MODULES_REPO=~/git/nold-ai/specfact-cli-modules python scripts/validate-modules-repo-sync.py --gate
```

- Exit code **0** and “Gate passes (content differences accepted)” means the migration-complete gate is satisfied.
- You can then close the change; canonical source for the 17 modules is specfact-cli-modules only (non-reversible).

## One-liner for CI or checklist

```bash
SPECFACT_MIGRATION_CONTENT_VERIFIED=1 SPECFACT_MODULES_REPO=~/git/nold-ai/specfact-cli-modules python scripts/validate-modules-repo-sync.py --gate
```

Requires that `SPECFACT_MODULES_REPO` points at a clone of specfact-cli-modules (e.g. on `dev`) that contains the five bundles and all 74 files.
