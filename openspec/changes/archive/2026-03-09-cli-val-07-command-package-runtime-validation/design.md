## Context

`specfact-cli` now ships a lean core with workflow bundles loaded from bundled artifacts and marketplace-style installs. The released command surface spans:

- Core commands: `specfact`, `init`, `module`, `upgrade`
- Official bundles from `specfact-cli-modules`: `backlog`, `project`, `spec`, `code`, `govern`
- Nested command families: `backlog ceremony`, `backlog auth`, `project sync`, `project version`, `project plan`, `project import`, `project migrate`, `spec contract`, `spec generate`, `spec sdd constitution`, `code validate sidecar`, `govern enforce`, `govern patch`

The current bug report is not just about one startup message. It highlights that release validation is still too coarse: normal users can hit internal logging noise during command bootstrap, especially when running from their home directory with `~/.specfact/modules` populated. The validation change therefore needs both a complete command inventory and an output policy that distinguishes real warnings from internal diagnostics.

The newly reproduced backlog regressions show a second class of release-time failure: the shipped runtime now spans both built-in backlog-core commands and a marketplace backlog bundle, but the two sides do not share a single adapter contract or a single end-to-end custom-field validation path. The validation change therefore also needs to verify bundle/core interop, not just per-command help output.

## Goals / Non-Goals

**Goals:**

- Define one authoritative validation matrix covering every shipped core command, every official bundle root, and every leaf command reachable from those bundles.
- Execute the matrix in a deterministic order that mirrors user setup: core startup, module bootstrap/install, then grouped bundle commands.
- Capture stdout, stderr, exit code, and emitted warnings for each command run.
- Treat internal module-discovery diagnostics as forbidden output during normal runs unless `--debug` is enabled.
- Ensure backlog commands still work when command ownership is split between core and marketplace packages.
- Ensure `backlog map-fields` visibly progresses after work-item-type selection and persists metadata that `backlog add` actually consumes.
- Leave an implementation plan that can fix current startup-noise regressions and prevent repeats in future releases.

**Non-Goals:**

- Redesign the bundle architecture or command taxonomy.
- Replace existing acceptance/snapshot infrastructure with a new framework.
- Require network-only validation; the workflow must remain usable with bundled/local registry artifacts.
- Redesign backlog ownership across all packages; this change is limited to making the current split behave coherently.

## Decisions

### 1. Use a repo-derived command inventory instead of a hand-maintained checklist

The validation matrix should be built from:

- Core `module-package.yaml` files under `src/specfact_cli/modules/`
- Official bundle `module-package.yaml` files under `../specfact-cli-modules/packages/`
- Typer app command trees for nested subcommands

This keeps the plan aligned with the shipped code surface and reduces drift when new commands are added.

Alternative considered:

- A static markdown checklist only. Rejected because it will drift as soon as bundle commands change.

### 2. Validate commands in user-realistic phases

The execution order should be:

1. Root/core startup and help surface
2. Core module lifecycle commands (`init`, `module`, `upgrade`)
3. Bundle bootstrap/install into canonical user scope
4. Bundle root groups in dependency order:
   - `project`
   - `spec`
   - `code`
   - `backlog`
   - `govern`
5. Nested command families and leaf commands within each group

This order front-loads setup failures and ensures dependent groups are validated after their owning bundle is installed.

Alternative considered:

- Alphabetical execution across all commands. Rejected because it hides setup dependencies and makes failures harder to triage.

### 3. Define a safe validation argv for every leaf command

Each command must have a deterministic validation invocation recorded in the matrix. The invocation can be:

- A real low-risk execution against fixture data
- A non-destructive dry-run path
- `--help` only as a fallback when no safe deterministic execution path exists yet

The matrix must explicitly mark which category each command uses so gaps are visible.

Alternative considered:

- Execute only `--help` for all commands. Rejected because it would not catch runtime bootstrap/output regressions like the current one.

### 4. Separate forbidden diagnostic noise from actionable warnings

Normal output must suppress:

- duplicate-module notices for canonical default user roots
- protocol-compliance summary chatter
- internal discovery/debug traces

Normal output must still preserve:

- security/integrity warnings
- real shadowing conflicts between project and user scope
- command-level validation errors the user can act on

Alternative considered:

- Silence all startup warnings. Rejected because it would hide legitimate security or precedence problems.

### 5. Reuse existing acceptance test infrastructure where possible

Implementation should extend the existing CLI validation approach rather than inventing a parallel system. The likely shape is:

- inventory helper(s) that enumerate command paths from core and official bundles
- acceptance/smoke tests that parameterize over the inventory
- fixture workspaces for safe command execution categories

Alternative considered:

- A standalone shell script outside pytest. Rejected because it weakens repeatability and CI integration.

### 6. Treat marketplace bundle code and core backlog code as one runtime surface for validation

Backlog commands are currently split:

- built-in `backlog-core` owns create/sync/graph-oriented flows such as `backlog add`
- the published `nold-ai/specfact-backlog` bundle owns refine/auth/mapping-oriented flows such as `backlog refine` and `backlog map-fields`

Validation and fixes therefore need to cover both repositories together. In practice:

- the backlog bundle must use the core `BacklogAdapter` contract rather than a duplicate bundle-local type
- the runtime validator must allow expected overlap between the two packages without leaking duplicate-command warnings
- saved provider metadata from the bundle must be consumed by `backlog add` in core

Alternative considered:

- Move all backlog behavior into one package as part of this change. Rejected because it is a larger architectural migration than the current release-stabilization scope.

### 7. Make long metadata fetches observable instead of silent

`backlog map-fields` now fetches required-field and picklist metadata after the user selects an ADO work item type. That can trigger many API calls before the next prompt appears. The command should therefore emit a progress/status message before this post-selection fetch so the CLI does not appear hung.

Alternative considered:

- Keep the current behavior and rely on faster networks. Rejected because the current silent gap is already confusing users and obscures whether the command is still working.

## Risks / Trade-offs

- **Risk:** Some commands require external services or credentials and cannot be fully exercised offline. → **Mitigation:** classify commands as fixture-backed, dry-run, or help-only; require explicit justification for help-only coverage.
- **Risk:** The inventory can miss nested subcommands if it relies on manifest data alone. → **Mitigation:** derive leaf commands from Typer app trees in addition to manifest command roots.
- **Risk:** Tightening startup output could suppress warnings that users still need. → **Mitigation:** encode the distinction in specs: suppress internal diagnostics, preserve actionable security/conflict warnings.
- **Risk:** The modules repo and core repo can drift. → **Mitigation:** derive the audit matrix from both repositories in the same workspace and fail validation if expected official bundles are missing.
- **Risk:** The backlog bundle and core backlog code may evolve incompatible interfaces again. → **Mitigation:** add regression tests that instantiate core adapters through the bundle command path and fail on contract mismatches.
- **Risk:** Persisted provider metadata may remain write-only. → **Mitigation:** add create-path tests that read saved required-field and allowed-values metadata and fail before adapter creation when the user input is incomplete or invalid.

## Migration Plan

1. Finalize spec deltas for runtime validation coverage and clean-output rules.
2. Build the command inventory helper and fixture-backed execution matrix.
3. Add failing tests for the current canonical-user-root startup noise.
4. Add failing interop and metadata-consumption tests for backlog runtime regressions.
5. Fix discovery/logging behavior plus backlog interop and metadata hand-off findings uncovered by the matrix.
6. Document the release-validation workflow for contributors and release engineering.

## Open Questions

- Which leaf commands currently have a safe fixture path versus `--help`-only coverage, and which should be upgraded first?
- Should the full command-package audit run in every PR gate, or remain a release/stabilization gate with a lighter smoke subset for normal CI?
- Should backlog command ownership be consolidated later so `backlog-core` and `nold-ai/specfact-backlog` no longer overlap on the same public command names?
