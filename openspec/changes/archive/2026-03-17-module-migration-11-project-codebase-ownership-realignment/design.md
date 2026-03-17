# Design: Project And Codebase Ownership Realignment

## Context

The migration wave established five grouped bundle families:

- `project`
- `backlog`
- `code`
- `spec`
- `govern`

But the `project` family inherited two different meanings:

1. the old plan/bundle artifact workflow
2. the brownfield code-ingestion entrypoint currently exposed as `import from-code`

That mix became unstable during follow-up migration work. Archived artifacts disagree about where the brownfield analysis internals belong:

- migration-01 and migration-02 put `import_cmd` in `specfact-project`
- migration-02 dependency analysis mapped `analyzers`, `comparators`, and `parsers` to `specfact-codebase`
- migration-05 later copied those subsystems into `specfact_project`
- migration-06 removal planning still describes those subsystems as `specfact-codebase` targets

So the current system has a command path and code layout that are internally consistent enough to run, but not conceptually coherent enough to guide future work.

## Goals

- Define a stable rule for `project` versus `codebase` ownership that is easy to apply in code, docs, prompts, and future migrations.
- Make command ownership follow the command's primary domain, not just the artifact it happens to emit.
- Reduce the chance that pending changes keep reinforcing the wrong bundle boundary.

## Non-Goals

- Revisit the full five-bundle architecture.
- Fold backlog, spec, or govern ownership cleanup into this change.
- Reintroduce flat top-level command shims.

## Design Decisions

### 1. Ownership is based on primary input domain

Command ownership SHALL follow the command's primary domain of analysis or manipulation:

- If the command primarily inspects or derives behavior from source code, tests, or runtime codebase evidence, it belongs to `code`.
- If the command primarily manipulates an existing SpecFact project bundle, its files, or its editable artifacts, it belongs to `project`.

This rule is more stable than deciding ownership from the output artifact. Many code-first commands emit project-bundle state, but that does not make them project-lifecycle commands.

### 2. `specfact code import` is codebase-owned in the target state

The brownfield import workflow is fundamentally code-analysis-driven:

- primary input: repository source tree
- core work: analyze code, derive features/contracts/relationships, compare inferred structure
- output: a SpecFact project bundle

The command therefore belongs to `specfact code ...` in the target state.

Target public path:

```text
specfact code import <bundle-name> --repo .
```

Compatibility transition:

- `specfact project import from-code ...` MAY remain temporarily as a deprecation alias during the migration window
- `specfact code import from-code ...` MAY exist temporarily as an internal compatibility shim if needed during rename rollout, but SHALL NOT be documented as canonical
- docs, prompts, and validation inventory SHALL treat `specfact code import ...` as the canonical path once this change lands
- mode distinctions such as bridge-driven import, shadow-only runs, enrichment, or future source-type variants SHALL be expressed as options or explicit alternate subcommands only when they represent materially different workflows

### 3. `project` is narrowed to bundle/workspace artifact lifecycle

`specfact project ...` SHALL mean:

- commands that manage SpecFact project bundles/workspaces directly
- plan/project artifact review and editing flows
- import/export/migrate/select/list operations whose primary subject is the bundle itself, not the external codebase

This keeps `project` aligned with the renamed successor of the original plan bundle lifecycle instead of turning it into a generic catch-all for anything that eventually writes bundle files.

### 4. Brownfield analysis internals move with the codebase owner

The following subsystem families SHALL be treated as codebase-owned unless a narrower exception is documented:

- `analyzers`
- `comparators`
- brownfield-oriented `parsers`
- code-analysis-specific agents/helpers used by the brownfield import workflow

Project-owned helpers remain in `specfact-project` only when they are about bundle transformation, editable artifact generation, or project lifecycle orchestration rather than codebase inspection.

### 5. Pending changes must not finalize conflicting import paths

Until this ownership change is resolved, other active changes must not hard-code contradictory assumptions:

- `module-migration-10-bundle-command-surface-alignment` must not treat `specfact project import from-code` or `specfact code import from-code` as the final public command contract without referencing this decision
- docs/prompt alignment fixes must avoid re-asserting the old project-owned path as canonical
- future decoupling or cleanup work must use the canonical owner defined here when moving internals

## Implementation Outline

1. Create an ownership matrix for current `project` and `codebase` commands, prompts, tests, helpers, and docs references.
2. Add spec deltas defining the canonical ownership rule and target command topology.
3. Add failing runtime/docs validation for the target canonical import path and ownership boundaries.
4. Move brownfield import command ownership from `project` to `code`, including internal subsystem ownership updates.
5. Introduce a temporary compatibility alias only if needed for release transition.
6. Update active pending changes and validation inventories so they point at the canonical owner.

## Risks

- Reclassifying the public import path can affect docs, tests, IDE prompts, and existing user habits at the same time.
- A temporary alias may require a short-lived dependency edge or compatibility layer between `project` and `codebase`.
- Some helpers currently living under `specfact_project` may be mixed-purpose and need explicit triage instead of bulk movement.

## Open Questions

- Which existing `project` subcommands, if any, should remain nested under `project import ...` for bundle-artifact import/export cases unrelated to code analysis?
- Whether the transition should ship a deprecation alias for one release line or switch directly if the grouped path is still pre-stable.
