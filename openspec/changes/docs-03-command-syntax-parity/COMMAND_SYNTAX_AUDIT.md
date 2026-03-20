# Command Syntax Audit

## Verified Current Command Surface (2026-03-20)

Verified from live CLI help in the active worktree:

- Core commands: `specfact init`, `specfact module`, `specfact upgrade`
- Installed workflow groups: `specfact backlog`, `specfact code`, `specfact govern`, `specfact project`, `specfact spec`

Verified notable current groups and parameters:

- `specfact module`
  - supports `init`, `install`, `uninstall`, `add-registry`, `list-registries`, `remove-registry`, `enable`, `disable`, `search`, `list`, `show`, `upgrade`, `alias`
- `specfact project`
  - supports `link-backlog`, `health-check`, `devops-flow`, `snapshot`, `regenerate`, `export-roadmap`, `export`, `import`, `lock`, `unlock`, `locks`, `init-personas`, `merge`, `resolve-conflict`, `version`, `sync`
  - does not expose `project plan`
  - `project import` is persona Markdown import, not bridge import
- `specfact project sync bridge`
  - remains the current bridge synchronization path
- `specfact backlog`
  - supports `ceremony`, `delta`, `auth`, `sync`, `verify-readiness`, `analyze-deps`, `diff`, `promote`, `refine`, `daily`, `init-config`, `map-fields`, `add`
  - preferred ceremony entrypoints are `backlog ceremony standup` and `backlog ceremony refinement`
  - compatibility aliases `backlog daily` and `backlog refine` still exist
  - does not expose `backlog policy`
- `specfact code`
  - supports `review`, `import`, `analyze`, `drift`, `validate`, `repro`
  - bridge import lives under `code import`, not `project import`
- `specfact govern`
  - supports `enforce`, `patch`
  - `govern enforce sdd [BUNDLE]` remains valid with positional bundle input
- `specfact spec`
  - supports `validate`, `backward-compat`, `generate-tests`, `mock`
  - does not expose `spec contract`, `spec api`, `spec sdd`, or `spec generate`

## Authored Docs Syntax Status

The authored docs review now confirms:

- removed syntax families such as `specfact project plan`, `project import from-bridge`, `backlog policy`, and retired `spec` subgroup trees are absent as current syntax
- any remaining mentions are intentionally historical notes, blockquotes, or code comments explicitly marked as removed/transitional context
- current grouped command families are present in the core command reference and landing docs

## Docs Ownership Audit

The sibling modules repository already contains the canonical deep bundle docs inventory under `/home/dom/git/nold-ai/specfact-cli-modules/docs`, including:

- backlog workflow guides
- project and bridge-sync guides
- spec/govern deep guides
- adapter references
- module development, publishing, signing, marketplace, and registry docs

That means the core docs in this repository should stay focused on:

- overall SpecFact process and navigation
- core CLI lifecycle and grouped command topology
- runtime, contracts, registry, trust, and architecture
- explanation of how official modules integrate into the core platform

The canonical modules docs site should continue to own:

- module-specific deep functionality
- adapter-specific operational runbooks
- detailed official bundle workflows
- module authoring and publishing guidance

## Required Changes Applied In This Session

### Core topology and ownership pages updated

- `README.md`
- `docs/index.md`
- `docs/README.md`
- `docs/reference/README.md`
- `docs/reference/commands.md`

These now:

- reflect the exact grouped command surface
- explain the core-vs-modules ownership boundary explicitly
- use the canonical modules docs site as the deep-docs handoff target
- prefer current ceremony-style backlog entrypoints while acknowledging compatibility aliases

### Docs integrity fixes applied

Added missing Jekyll front matter to the published Markdown pages that previously lacked it, including examples, guides, prompts, technical docs, architecture deep dives, legal/reference pages, and other published docs under `docs/`.

## Outcome

The docs tree is now aligned with the real command surface, the core/modules ownership split, and GitHub Pages front-matter requirements.
