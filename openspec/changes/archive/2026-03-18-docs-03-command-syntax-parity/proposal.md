# Change: Audit And Correct Docs Command Syntax After Core/Modules Split

## Why

The authored docs still contain a large amount of pre-split and transitional CLI syntax that no longer matches the executable command surface in `dev`. After the lean-core and modules split, command groups, ownership boundaries, and some parameter forms changed, but many examples in `README.md`, `docs/`, and prompt-oriented docs still point readers to removed paths such as `specfact project plan ...`, `specfact project import from-bridge ...`, `specfact backlog policy ...`, and retired `specfact spec ...` subgroup trees.

That drift now creates direct user harm: copied commands fail, migration guidance points to non-existent groups, and docs blur the difference between current core/runtime commands and removed or relocated workflow syntax. This change establishes one audited source of truth for required doc rewrites and updates every affected authored doc page to the shipped command surface.

## What Changes

- Audit authored docs against the currently shipped CLI implementation and classify every stale command-syntax family introduced or exposed by the core/modules split.
- Update all affected authored docs, examples, guides, reference pages, getting-started pages, and prompt docs so command examples use current supported groups, subcommands, and parameter forms.
- Replace transitional mappings that currently point from one removed syntax family to another removed syntax family with verified current surfaces or with explicit historical context when no direct replacement exists.
- Expand lightweight docs parity coverage so future releases fail fast when authored docs reintroduce removed command groups or stale parameter examples.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `documentation-alignment`: docs command examples, migration guidance, and command reference content must reflect the current executable core/bundle command topology and supported parameter forms.
- `cli-output`: docs parity validation must enforce command-syntax correctness for authored docs, not just spot-check a single reference page.

## Impact

- Affected docs: `README.md`, `docs/index.md`, `docs/README.md`, selected files in `docs/reference/`, `docs/getting-started/`, `docs/guides/`, `docs/examples/`, and `docs/prompts/`.
- Affected validation: docs parity tests must expand beyond current release-doc checks to guard against removed syntax families such as `project plan`, `project import from-bridge`, `backlog policy`, and retired `spec` subgroup paths.
- User-facing impact: command examples copied from docs will match the real CLI again, especially for bundle install/bootstrap, backlog workflows, bridge import/sync, project workflows, SDD enforcement, and Specmatic commands.
- Rollback plan: if a specific replacement path remains ambiguous during implementation, remove or label the example as historical context instead of publishing an unverified command.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: pending
- **Issue URL**: pending
- **Last Synced Status**: local-proposal
- **Sanitized**: true
