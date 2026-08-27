## Context

See [proposal.md](proposal.md). The shared frozen-environment action enables setup-uv persistence before later job steps can execute the separately checked-out module fixture. The fixture is currently immutable and verified, so external exploitability is unproven, but an approved malicious fixture could modify the writable cache and a later privileged run could restore it. PR #691 also demonstrates that the accumulated `main...dev` range contains active planning changes that do not have acceptance evidence; that is a legitimate gate failure, not a reason to add a bypass.

## Goals / Non-Goals

**Goals:**

- Remove both restore and save sides of the cross-run cache boundary at its single shared action.
- Preserve exact module repository, commit, and tree checks, and expose the advisory fixture lane only to the schedule trigger.
- Preserve Requirements evidence and finalized Code Review execution unchanged.
- Promote only the focused patch-release delta to `main` so unrelated active planning remains on `dev`.
- Remove the three exact MCP advisory exceptions now that an upstream-compatible
  Semgrep release resolves the fixed MCP line.

**Non-Goals:**

- Changing runtime dependencies, unrelated development tools, or PyPI artifacts.
- Dismissing CodeQL alerts or weakening immutable fixture verification.
- Redesigning all companion-module checkouts or adding workflow inputs for fixture selection.
- Changing user-facing CLI/API behavior or the C14/C15 implementation branches.

## Decisions

### Disable the shared uv cache completely

Set setup-uv caching to disabled in the existing shared action. This removes both cache restore and the post-job save hook for every caller, including scheduled, protected-branch, package-validation, and release jobs. Remove the later setup-node npm cache from the Requirements workflow because module-owned evidence code executes earlier in that job.

Alternatives considered:

- `save-cache: false` was rejected because it can still restore previously poisoned content.
- Keeping a manual-dispatch condition that checks `github.ref` was rejected because a dispatch against an older branch-selected workflow definition could authorize itself. The PR Orchestrator therefore has no manual trigger; its advisory compatibility lane is schedule-only.
- Replacing all dynamic checkout expressions with literal values was rejected as the primary cache fix because an intentionally approved malicious fixture could still write persistent state. The compatibility lane instead verifies both the selected commit and its expected tree before exporting the module path.
- Rotating only the cache key was rejected because it does not remove the vulnerable persistence capability.

### Preserve the gate and narrow the release diff

Do not change `.github/workflows/requirements-evidence.yml` to special-case PR #691. Its `acceptance-missing` result correctly identifies unrelated active planning sources in the accumulated release range. Close the broad promotion PR after the issue-linked fix is merged to `dev`, then create a `main`-based release branch containing only the exact dependency/security/version/changelog delta already validated on `dev` plus this cache fix. The normal main-bound Requirements, finalized Code Review, CodeQL, Socket, audit, signature, package, and publication gates must all execute.

### Keep review findings behavior-neutral

The authority parser will distinguish its own validation errors from metadata decoding/parsing failures so the existing metadata diagnostic remains reachable. The Bash test helper will make its post-skip control flow explicit without changing the skip outcome.

The license scanner will give the frozen Code Review interpreter a distinct scope so the exact Pylint exception cannot suppress a primary-environment or manifest violation. Active OpenSpec deletion checks will permit only deletions/renames that leave the change in the active namespace, and retained-proof discovery will include module-scope control flow while excluding function, class, and lambda bodies.

### Serialize the staged-index Markdown fixer

The Markdown auto-fix hook ignores pre-commit's filename arguments and instead
discovers the complete staged Markdown set before potentially running `git add`.
Without `pass_filenames: false`, pre-commit may split a large staged set into
concurrent filename batches, launching duplicate full-index fixers that contend
on `index.lock`. Disable filename passing for this stateful hook so exactly one
process owns the staged-index update. Keep its existing staged-file filter and
unstaged-hunk protections unchanged.

### Remove the obsolete MCP exception through Semgrep

The existing exception is valid only while the newest compatible Semgrep pins
vulnerable `mcp==1.23.3`. PyPI metadata for Semgrep 1.175.0 now pins
`mcp==1.29.0`, above all three advisory fix floors. A no-write targeted solve
changes only Semgrep 1.171.0 to 1.175.0 and MCP 1.23.3 to 1.29.0 in the existing
184-package graph. Raise the Semgrep floor on every repository-owned tool
surface, enforce `mcp>=1.28.1` in the pre-install frozen-lock policy, refresh
the lock/export, and remove the MCP exception entirely. The separate MCP floor
is required because lock/export consistency alone does not prove that a
transitive security binding remains above its advisory fix floor.

Installing MCP directly or overriding Semgrep metadata was rejected because it
would create an unsupported resolver state. Retaining the waiver was rejected
because its factual premise is no longer true.

## Risks / Trade-offs

- **Longer CI runs without uv persistence** → Accept the release-safety cost; frozen installs remain deterministic and can use runner-local state only within a job.
- **A focused release branch drifts from the validated dev security delta** → Compare every selected file and dependency artifact against the merged dev state, retain exact before/after audit evidence, and run the full main-bound gates.
- **Previously saved cache content remains stored in GitHub** → Disabling restore makes it unreachable. Delete old caches only as optional operational hygiene, not as proof of remediation.
- **Semgrep 1.175 changes scan behavior** → Run the repository SAST configuration,
  dependency audit, full test suite, and Python 3.11–3.13 package matrix; rollback
  by reverting the issue-linked PR if the tool upgrade regresses the gates.

## Migration Plan

1. Merge the issue-linked fix through protected `dev` after focused and full gates pass.
2. Close PR #691 only after the replacement release branch is prepared and its exact selected-file provenance is recorded.
3. Run the full protected-main gates on the focused release PR and merge only when policy permits, then verify the main-push package, PyPI, and GitHub release jobs.
4. Roll back by reverting the security-fix PR; if 0.55.2 is already published, use a normal follow-up patch release rather than rewriting history.
