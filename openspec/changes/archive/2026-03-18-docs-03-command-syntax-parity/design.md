# Design: Audit And Correct Docs Command Syntax After Core/Modules Split

## Context

The current executable CLI in `dev` exposes this high-level surface:

- Core commands: `init`, `module`, `upgrade`
- Bundle groups: `backlog`, `code`, `govern`, `project`, `spec`

Verified current group surfaces from live help:

- `backlog`: `ceremony`, `delta`, `auth`, `sync`, `verify-readiness`, `analyze-deps`, `diff`, `promote`, `refine`, `daily`, `init-config`, `map-fields`, `add`
- `project`: `link-backlog`, `health-check`, `devops-flow`, `snapshot`, `regenerate`, `export-roadmap`, `export`, `import`, `lock`, `unlock`, `locks`, `init-personas`, `merge`, `resolve-conflict`, `version`, `sync`
- `code`: `review`, `import`, `analyze`, `drift`, `validate`, `repro`
- `spec`: `validate`, `backward-compat`, `generate-tests`, `mock`
- `govern`: `enforce`, `patch`

The authored docs still contain older or transitional syntax families that no longer match that surface, including:

1. `specfact project plan ...`
2. `specfact project import from-bridge ...`
3. `specfact backlog policy ...`
4. `specfact spec contract ...`, `specfact spec api ...`, `specfact spec sdd ...`, `specfact spec generate ...`
5. migration guidance that maps removed flat shims to equally removed intermediate commands

## Goals

- Produce one exhaustive audit of authored docs that still reference removed or transitional syntax after the split.
- Update every affected doc page to either:
  - use a verified current command path and parameter form, or
  - remove/reframe the example when there is no direct replacement.
- Add parity checks that fail when removed syntax families reappear in authored docs.

## Non-Goals

- Change the runtime CLI implementation in this proposal stage
- Promise that all current CLI help prose is already canonical; some help text still contains stale wording and should not be treated as authoritative without verification
- Edit generated `docs/_site/` output directly

## Verified Replacement Principles

- `project plan` is not an executable `project` subcommand and must not appear as current syntax.
- Root `plan` is not installed as a workflow command in the shipped lean-core surface and must not be presented as a current workflow entrypoint.
- `project import` is now persona Markdown import, not external bridge import.
- Backlog workflows should use the current `backlog` groups such as `ceremony`, `refine`, `daily`, `auth`, `sync`, `analyze-deps`, and `verify-readiness`, not `backlog policy`.
- `govern enforce sdd [BUNDLE]` remains a valid current surface and should be documented with its current positional bundle form when examples require SDD validation.
- `spec` documentation should use the shipped Specmatic surface: `validate`, `backward-compat`, `generate-tests`, and `mock`.

## Documentation Audit Strategy

The implementation should use the audit inventory in `COMMAND_SYNTAX_AUDIT.md` and remediate the docs in clusters:

1. Entry and landing docs
2. Reference and migration docs
3. Getting-started and workflow guides
4. Brownfield/examples/tutorial content
5. Prompt-oriented docs and internal command cheat sheets

For each stale example, implementation must choose one of three outcomes:

- Replace with a verified current command
- Reframe as historical migration context
- Remove if the workflow is no longer supported as a user-facing path

## Validation Strategy

Implementation should add or extend docs parity tests that:

- scan authored docs only (`README.md` and `docs/`, excluding generated/vendor output)
- fail when removed syntax families reappear
- assert the command reference and selected landing/reference pages continue to show the shipped core and bundle groups
- verify bridge-import and backlog docs use the correct command families after remediation
