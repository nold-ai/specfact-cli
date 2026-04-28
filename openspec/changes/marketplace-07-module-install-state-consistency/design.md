## Context

Module availability currently has several independent truth sources:

- physical artifacts under builtin, project, user, marketplace, and custom module roots;
- manifest identity and command metadata from `module-package.yaml`;
- lifecycle state in `~/.specfact/registry/modules.json`;
- runtime registration decisions after compatibility, dependency, schema, and integrity checks;
- user-facing install and missing-command diagnostics.

The bug appears when one layer reports success while a later layer refuses to expose the command. The most visible path is: command missing help says a module is not installed, `specfact module install` sees a manifest already present and returns early, and the disabled/skipped/shadowed state remains unresolved.

## Goals / Non-Goals

**Goals:**

- Make install no-op checks reconcile the selected module with lifecycle state and command availability.
- Make missing-command diagnostics identify installed-but-unavailable causes when they can be derived locally.
- Make `specfact init --repo ... --profile ...` refresh module state from the intended repository context, not an unrelated cwd.
- Preserve user disabled-module choices while preventing init/profile flows from silently dropping unrelated modules.
- Keep user and project scope behavior deterministic and offline-first.

**Non-Goals:**

- Replacing the module marketplace registry format.
- Removing project-scope precedence over user-scope modules.
- Installing Python package dependencies differently.
- Implementing remote registry changes in `specfact-cli-modules`.

## Decisions

1. Introduce a local module availability classification helper.

   Runtime diagnostics and install no-op paths need the same vocabulary. The helper should derive, for a requested command or module ID, whether the module is absent, installed-and-enabled, installed-but-disabled, shadowed by a higher-priority scope, skipped by compatibility/dependencies/schema/integrity, or ambiguous. This keeps CLI output consistent without loading module command apps eagerly.

   Alternative considered: leave install and missing-command diagnostics separate. That preserves current contradictions and forces each command path to rediscover partial state.

2. Canonicalize module identity before state or install decisions.

   A request such as `specfact-codebase`, `specfact/specfact-codebase`, and `nold-ai/specfact-codebase` should resolve to the same discovered module record when the manifest identifies the installed package as `nold-ai/specfact-codebase`. State updates should use manifest IDs, while user-facing commands may continue accepting bare names.

   Alternative considered: store aliases in `modules.json`. That makes state harder to reason about and risks duplicate rows for the same physical module.

3. Treat install no-op as lifecycle reconciliation, not a terminal success.

   If the target manifest exists and `--reinstall` is not set, install should check whether the manifest's module is enabled and eligible. If disabled, the command should either enable it for the selected module state workflow or report the exact `specfact module enable <id>` command. If skipped for integrity, compatibility, schema, or dependency reasons, install should print that reason and suggest the appropriate recovery path.

   Alternative considered: always reinstall when a command is unavailable. This hides disabled-state bugs and can mutate user/project scopes unnecessarily.

4. Make init state refresh repo-aware and merge-based.

   `specfact init --repo <repo>` should discover project modules relative to `<repo>` for state refresh and prompt audit. The write to `modules.json` should merge the current discovery view with existing state so user-disabled choices and modules outside the current view are not accidentally lost.

   Alternative considered: keep global replacement semantics. That remains fragile when users run init from different directories or environments.

5. Keep shadowing behavior but surface it at the point of confusion.

   Project modules should still take precedence over user modules. When the selected command or module is unavailable because a project copy shadows a user copy, diagnostics should identify both origins and the active origin.

   Alternative considered: remove project precedence. That would break intentional repo-local module overrides.

## Risks / Trade-offs

- [Risk] Availability classification duplicates parts of registration filtering. -> Mitigation: keep it metadata-only and share small helpers for state, dependencies, and integrity checks where practical.
- [Risk] Merging old state rows can preserve stale entries forever. -> Mitigation: preserve only rows with explicit disabled state or known source tracking; discovered rows remain the authoritative visible set for `module list`.
- [Risk] Enabling during install may surprise users who intentionally disabled a module. -> Mitigation: require explicit output and prefer an actionable message unless the command is clearly a user-requested install of that exact module.
- [Risk] Integrity checks can be expensive on startup diagnostics. -> Mitigation: only run deeper checks for requested missing-command/install paths, not every root help render.

## Migration Plan

1. Add regression tests for disabled modules, shadowed project/user modules, init/profile state refresh, and missing-command diagnostics.
2. Add the availability classification helper and route install skip checks through it.
3. Update missing-command help to use local classification when available.
4. Update init/profile state refresh to use the selected repo path and merge state deterministically.
5. Update user-facing docs for module install/list/init recovery guidance if command text changes.
6. Record failing-before and passing-after evidence in `TDD_EVIDENCE.md`.

Rollback is straightforward: these changes are local CLI behavior changes and can be reverted without data migration. Existing module roots and `modules.json` remain compatible.

## Open Questions

- Should install automatically re-enable an installed disabled module, or should it stop with an explicit `specfact module enable <id>` command? The implementation should choose the least surprising option and document it in tests.
- Should `module list --show-origin` expose unavailable/skipped reasons for all modules, or only missing-command and install paths?
