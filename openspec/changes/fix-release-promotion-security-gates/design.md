## Context

`origin/dev@4fd96d6d804da70cc7ceca83b8adce21f7da561c` is version
0.55.3. MCP is not a core dependency and is reachable only through the optional
Semgrep development/scanning graph. All 24 open CodeQL alerts share the cache
enabled by `.github/actions/setup-frozen-python/action.yml`; six of seven open
Dependabot alerts are the same three MCP advisories repeated across `uv.lock`
and `requirements/ci/locked.txt`. The seventh, Ruby JSON, is already fixed on
`dev`. During final verification, the hosted frozen audit additionally reported
four newly published GitPython 3.1.58 advisories in the shipped runtime graph.

## Goals / Non-Goals

**Goals:**

- Remove the obsolete MCP exception with a resolver-supported fixed graph.
- Move GitPython to the first fixed compatibility-restored release.
- Remove persistent cache restore/save from jobs that later execute a separately
  checked-out fixture.
- Keep native archive and isolated license decisions fail closed.
- Preserve test-first proof for bounded review-driven amendments after production
  commits already exist on the pull request.
- Preserve a small, reviewable, linear spec-to-test-to-code patch.

**Non-Goals:**

- Change other core runtime dependencies or public CLI/API behavior.
- Upgrade already-safe Twine, pip, Hatchling, Setuptools, or Ruby JSON versions.
- Rebuild PR #698's general amendment, provenance-parser, or process-isolation
  architecture.
- Claim containment of intentionally hostile mapped tests or production code
  inside the same pytest process; that requires a separately scoped isolation
  architecture.
- Change modules, internal wiki PR #38, or C14/C15 worktrees.

## Decisions

### Use the compatible Semgrep/MCP pair already reviewed by Socket and CI

Semgrep 1.175.0 declares `mcp==1.29.0`, above all three advisory floors. The
frozen graph and export move together, the MCP waiver is removed, and policy
enforces both Semgrep 1.175.0 and MCP 1.28.1 minimums before synchronization.
Semgrep 1.176.0 and MCP 1.29.1 add no required advisory fix compatible with the
current exact Semgrep binding, so they are outside this patch.

### Use GitPython 3.1.61 as the smallest safe compatible runtime floor

GitPython 3.1.59 closes CVE-2026-78675 through CVE-2026-78678 but remains
affected by three follow-on advisories fixed in 3.1.60. Release 3.1.60 also
accidentally removed the public `Actor.name_email_regex` attribute. GitPython
3.1.61 restores that attribute with deprecation and retains the security fixes,
so it is the narrowest supported target that avoids both known vulnerability
and compatibility regressions. The project does not enable GitPython's unsafe
option escape hatches.

### Validate the release bundle across the change branch

CI already supplies the pull-request base to the version checker. Local
pre-commit now uses the fetched `GITHUB_BASE_REF`, or the repository's normal
`dev` target outside `main`, when that ref is available. This preserves the
four-file version and changelog requirement across the complete change while
allowing a later dependency-metadata commit to remain in the same unreleased
patch. If the target ref is unavailable, the existing per-commit fail-closed
behavior remains. The branch-level exemption applies only while the candidate
version equals `HEAD`; a staged version change remains subject to the original
strict `HEAD`-relative increment and complete staged-bundle checks. Candidate
content comes from the index plus `HEAD`, so unstaged or deleted bytes cannot
satisfy the gate. An invalid explicit CI comparison ref is a hard error.

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

The executor and security validators disable Python site startup, add the exact
installed dependency directory without processing `.pth` files, and import
installed pytest before adding the repository root. Prefetched proof and
authority inputs are digest-bound across candidate test execution. Bootstrap
authority rejects nonlinear red history and parses Git paths through checked
NUL-delimited records. Local staged-path consumers use the same NUL-safe
inventory. The organization-required workflow supplies external exact-tree
authorization. For a late review correction, that authority binds the final
tree, whose committed manifest identifies one exact verified cycle base and
failed RED artifact. The fresh consumer must revalidate its live run and
artifact metadata, linear ancestry, test-only RED segment, selected failing
cases, mapping, plan, and artifact digests. This is a bounded recovery lane,
not a reusable amendment engine.

The Requirements workflow resolves one merge-base object ID, removes GitHub
credentials before proof execution, and persists only the bounded evidence
artifact. Code Review then starts on a separate fresh runner, authenticates the
exact head commit, validates and installs frozen tools, and only then downloads
the producer output by immutable artifact ID. Both Code Review installation
sites run the existing reproducible-delivery checker, which regenerates the
constrained lock closure and rejects graph-extraneous packages before
installation.

The fresh consumer materializes the proof selector validator and JUnit plugin
from that immutable merge-base, imports installed pytest before repository
paths, and independently executes every selector in its regenerated plan. Final
reconciliation consumes only this consumer-generated JUnit. The producer plan
must still match the independently regenerated plan, but producer report and
JUnit bytes are transport evidence rather than the final execution authority.
Candidate `conftest.py` discovery and candidate pytest configuration are disabled
so repository hooks and `addopts` cannot rewrite pytest outcomes. The consumer
selects the changed active OpenSpec change with the same path basis as the
producer, both frozen-closure checks use the isolated trusted interpreter, and
the combined execution/reconciliation step has a 12-minute fail-closed timeout.
The CLI launchers also override `HOME` and `SPECFACT_REPO_ROOT` with the fresh
runner's temporary root before importing the CLI. Consequently, implicit user
and workspace discovery cannot select a module from the pull-request checkout;
the commit-and-tree-authenticated `SPECFACT_MODULES_ROOTS` fixture remains the
only project-supplied module root.

Retained-proof dependency discovery follows Python namespace semantics for
literal `pytest_plugins` declarations: module-scope assignments and explicit
`global pytest_plugins` assignments remain bound, while ordinary function- and
class-local declarations that cannot affect the imported module namespace are
excluded. This removes false stale-proof results without dropping a reachable
plugin binding.

This is not a Python sandbox. The approved mapped tests and the candidate
production code they intentionally import execute with the same process
authority as pytest and its JUnit writer. They are therefore review-trusted and
assumed not to deliberately tamper with pytest, its exit status, or the JUnit
channel. The fresh-consumer boundary protects against producer-uploaded results,
repository pytest configuration and plugins, Python startup injection,
credential inheritance, stale external evidence, and mutation of the later
Code Review runner. Containing intentionally hostile same-process Python would
require a separately designed external isolation boundary and is outside this
patch release.

### Publish bundled snapshot entries only after the release asset exists

The bundled registry is a CI comparison snapshot rather than the runtime
marketplace index, but its absolute URLs still claim public artifacts that do
not currently exist. Both publisher lanes derive the release tag from the
validated module slug and version, require the source commit to be reachable
from `dev` or `main`, create the release without overwriting an existing version,
redownload and checksum the archive, and only then update the snapshot. The
existing `module-registry` 0.1.35 Actions artifact remains comparison evidence.
After this publisher correction merges, the protected source is packaged
reproducibly and its verified release checksum replaces the stale snapshot
checksum and URL; no module payload or version is changed.

## Risks / Trade-offs

- CI may be slower without persistent caches. Frozen installs remain
  deterministic; rollback requires a separately designed trusted cache scope.
- Semgrep behavior may change. Run the repository Semgrep gate, full tests,
  package matrix, frozen audit, and Socket checks before merge.
- GitPython behavior may change. Run focused analyzer/versioning and linked
  worktree tests, the packaged-wheel smoke test, full suite, and frozen audit.
- Git archive logic can reject unusual-but-legitimate moves. Exact positive and
  negative fixtures cover ordinary edits, native archives, partial moves,
  fabricated copies, and command failures.
- Intentionally hostile mapped tests or imported production code can interfere
  with their own pytest process. Mandatory static and human review enforce the
  non-hostile-code assumption; a future hostile-code threat model requires an
  external execution boundary rather than additional in-process guards.

## Release and rollback

Merge the issue-linked PR to `dev` only after all required and trusted checks
pass. Promote the focused security/release delta through the normal protected
main flow and publish `v0.55.4`. Roll back through PR reverts and a forward
patch; never rewrite published history.
