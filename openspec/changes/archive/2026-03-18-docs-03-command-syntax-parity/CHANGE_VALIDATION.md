# Change Validation Report: docs-03-command-syntax-parity

## Summary

This proposed change is a docs-governance and validation change. It does not introduce a runtime API or contract change in production code, but it does correct a large set of user-facing command examples that currently point to removed or transitional CLI surfaces.

## Artifacts Reviewed

- `openspec/changes/docs-03-command-syntax-parity/proposal.md`
- `openspec/changes/docs-03-command-syntax-parity/design.md`
- `openspec/changes/docs-03-command-syntax-parity/tasks.md`
- `openspec/changes/docs-03-command-syntax-parity/COMMAND_SYNTAX_AUDIT.md`
- `openspec/changes/docs-03-command-syntax-parity/specs/documentation-alignment/spec.md`
- `openspec/changes/docs-03-command-syntax-parity/specs/cli-output/spec.md`

## Live CLI Surface Checked

Validated from the current executable CLI in this repo:

- `specfact --help`
- `specfact backlog --help`
- `specfact project --help`
- `specfact code --help`
- `specfact spec --help`
- `specfact govern --help`
- `specfact project sync bridge -h`
- `specfact govern enforce sdd -h`
- `specfact spec validate -h`
- `specfact project plan --help` → fails with `No such command 'plan'`
- `specfact plan --help` → reports command not installed

Additional bridge-import evidence was taken from:

- `tests/integration/importers/test_speckit_import_integration.py`

## Dependency And Breaking-Change Analysis

- Runtime/API breaking change risk: none in proposal stage; the change targets docs and docs-validation only.
- Behavioral risk during implementation: low to medium.
  - Low for pages that simply replace removed syntax with verified current groups.
  - Medium for pages that describe workflows whose former command family no longer has a direct one-to-one replacement (`project plan ...`, old `spec` subgroup trees, and some migration docs).
- Cross-repo dependency risk: low.
  - The docs ownership split from `docs-01` and `docs-02` is already established.
  - This proposal is local to `specfact-cli` docs and tests, though any replacement examples that point to bundle-owned deep docs must continue to respect the modules-site handoff model.

## Scope Validation

The audit found stale syntax in all of the following authored docs clusters:

- repo entry and landing docs
- reference docs
- getting-started docs
- workflow and migration guides
- examples and brownfield walkthroughs
- prompt docs

The full file inventory is captured in `COMMAND_SYNTAX_AUDIT.md`.

## Recommendation

Proceed.

This change is appropriately scoped as a documentation-alignment and docs-parity change. During implementation, any example whose current replacement remains ambiguous should be removed or reframed as historical context rather than publishing an unverified command.

## Validation Status

- Command: `openspec validate docs-03-command-syntax-parity --strict`
- Result: passed
