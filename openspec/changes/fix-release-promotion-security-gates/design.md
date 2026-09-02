## Context

`origin/dev@4fd96d6d804da70cc7ceca83b8adce21f7da561c` is version
0.55.3. MCP is not a core dependency and is reachable only through the optional
Semgrep development/scanning graph. All 24 open CodeQL alerts share the cache
enabled by `.github/actions/setup-frozen-python/action.yml`; six of seven open
Dependabot alerts are the same three MCP advisories repeated across `uv.lock`
and `requirements/ci/locked.txt`. The seventh, Ruby JSON, is already fixed on
`dev`.

## Goals / Non-Goals

**Goals:**

- Remove the obsolete MCP exception with a resolver-supported fixed graph.
- Remove persistent cache restore/save from jobs that later execute a separately
  checked-out fixture.
- Keep native archive and isolated license decisions fail closed.
- Preserve a small, reviewable, linear spec-to-test-to-code patch.

**Non-Goals:**

- Change core runtime dependencies or public CLI/API behavior.
- Upgrade already-safe Twine, pip, Hatchling, Setuptools, or Ruby JSON versions.
- Rebuild PR #698's amendment, cycle, provenance-parser, or process-isolation
  architecture.
- Change modules, internal wiki PR #38, or C14/C15 worktrees.

## Decisions

### Use the compatible Semgrep/MCP pair already reviewed by Socket and CI

Semgrep 1.175.0 declares `mcp==1.29.0`, above all three advisory floors. The
frozen graph and export move together, the MCP waiver is removed, and policy
enforces both Semgrep 1.175.0 and MCP 1.28.1 minimums before synchronization.
Semgrep 1.176.0 and MCP 1.29.1 add no required advisory fix compatible with the
current exact Semgrep binding, so they are outside this patch.

### Remove cache capability rather than attempt cache authentication

Set `enable-cache: false` in the shared action and remove npm caches restored
after fixture execution. This eliminates restore and post-job save. Existing
PR cache scoping and immutable fixture checks make exploitation unproven today,
but disabling persistence prevents future trigger or trust-boundary drift.

### Keep fixture execution schedule-only and immutable

The PR orchestrator has no manual dispatch. The scheduled compatibility lane
reads the repository, commit, and tree from the committed lock, checks both Git
objects, then exports the path. A future manual lane belongs in trusted central
workflow code, not a branch-selected definition.

### Treat absence as proved state, never as a failed Git command

Active-change selection accepts an archive only when source/destination paths,
modes, blob IDs, counts, and dated directory identity match exactly. Every Git
enumeration is status-checked so an error cannot become an empty successful set.

### Keep proof hardening narrow

The executor uses isolated-path mode and imports installed pytest before adding
the repository root. Bootstrap authority preserves only stable public
diagnostics. The organization-required workflow supplies external exact-tree
authorization, so no PR-local amendment subsystem is introduced.

The Requirements workflow resolves one merge-base object ID, removes GitHub
credentials before proof execution, and persists only the bounded evidence
artifact. Code Review then starts on a separate fresh runner, authenticates the
exact head commit, validates and installs frozen tools, and only then downloads
the producer output by immutable artifact ID. Both Code Review installation
sites run the existing reproducible-delivery checker, which regenerates the
constrained lock closure and rejects graph-extraneous packages before
installation.

## Risks / Trade-offs

- CI may be slower without persistent caches. Frozen installs remain
  deterministic; rollback requires a separately designed trusted cache scope.
- Semgrep behavior may change. Run the repository Semgrep gate, full tests,
  package matrix, frozen audit, and Socket checks before merge.
- Git archive logic can reject unusual-but-legitimate moves. Exact positive and
  negative fixtures cover ordinary edits, native archives, partial moves,
  fabricated copies, and command failures.

## Release and rollback

Merge the issue-linked PR to `dev` only after all required and trusted checks
pass. Promote the focused security/release delta through the normal protected
main flow and publish `v0.55.4`. Roll back through PR reverts and a forward
patch; never rewrite published history.
