# Design

Docs generation consumes reviewed module source through a docs-only immutable lock. Docs Review validates repository, full commit and tree, then exports its checkout as SPECFACT_MODULES_REPO. Requirements keeps ci/module-fixture.lock.json and its independently approved commit/tree unchanged.

Core generates its own three artifacts. A focused regression compares Code Review-owned command paths, arguments, ordinary options and subgroup names with the module fixture's generated contract. Normalize only Typer completion switches associated with standalone versus mounted root contexts; missing ordinary options and subcommands must remain failures. Existing generator --check proves freshness from the selected source.

The core spec covers registration and documentation handoff, not a duplicate of the portable-runtime execution contract. No equality test over natural-language OpenSpec documents and no new global module publication blocker is introduced.

Final fixture input must be a clean, public immutable Git commit with the reviewed 0.50.0 module signature verified using existing tooling. That evidence is distinct from later registry installation acceptance.

For local canonical hooks, SPECFACT_DOCS_MODULES_REPO selects generator and live command-contract validator source independently while the parent process retains SPECFACT_MODULES_REPO for Requirements evidence. An explicit documentation source must exist and contain packages; invalid explicit context fails instead of falling back. Generator callers without the docs variable retain the existing discovery behavior. Click and Typer positional parameter classes are inspected explicitly, preserving display names, required status and arity in all generated artifacts.
