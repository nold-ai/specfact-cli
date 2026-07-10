# Change Validation: cli-val-05-ci-integration

- **Validated on:** 2026-07-10 Europe/Berlin
- **Workflow:** implementation-readiness review and strict OpenSpec validation
- **Strict command:** `openspec validate cli-val-05-ci-integration --strict`
- **Result:** PASS

## Scope Summary

- **Extended capability:** `documentation-accountability`
- **Source issue:** [#643](https://github.com/nold-ai/specfact-cli/issues/643),
  open and unblocked under parent [#375](https://github.com/nold-ai/specfact-cli/issues/375)
- **Outcome:** derive official module package and grouped-command ownership from
  the paired modules repository; fail closed when core catalogues, generated
  command metadata, or ownership statements drift.

## Breaking-Change Analysis

This is a validation and documentation hardening change. It adds no public CLI
command, removes no supported interface, and leaves the requirements profile
explicit-opt-in behavior unchanged. The only operational change is deliberate:
contributors and PRs must provide a valid modules checkout for documentation
validation rather than silently accepting incomplete documentation evidence.

## Dependency and Ownership Review

- `specfact-cli-modules` manifests and `registry/index.json` are the source of
  truth for official package IDs and grouped command roots.
- Core owns the generated command overview, command contract, catalogue pages,
  and the fail-closed validation integration.
- Modules own package manifests, marketplace registry entries, package runtime,
  and deep module workflow documentation.
- The change order now lists `cli-val-05` with issue #643 and its validation
  predecessors.

## Internal Wiki Status

The sibling internal checkout already has an uncommitted modification to
`wiki/sources/cli-val-05-ci-integration.md` outside this worktree. It was not
overwritten. Before merge, its owner must reconcile this scope update and run
`wiki_rebuild_graph.py` from the internal repository root; this preserves that
checkout's existing work while keeping the public OpenSpec source authoritative.

## Validation Outcome

- Required change artifacts are present and parseable.
- Strict OpenSpec validation passes.
- The change records source authority, fail-closed local/PR enforcement,
  catalogue completeness, generated-command ownership, and architecture
  handoff consistency.
