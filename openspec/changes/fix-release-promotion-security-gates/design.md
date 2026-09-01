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
- Close the retained-proof boundary with an exact owner-approved SUT path policy
  and preserve repeatable same-PR amendment cycles after the externally
  authorized bootstrap.

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

### Bind retained proof with an exact SUT path policy

Evaluate the complete linear commit history from the authenticated red source
through the final source. Every touched repository path is stale by default,
including both rename/copy endpoints and paths whose bytes are later restored.
Permit a path only when the owner-approved Requirements mapping contains that
exact literal regular-file touchpoint with `mutable_after_red: true`. Reject
globs, prefixes, directories, missing/non-regular paths, duplicate or normalized
locator collisions, and touchpoint-role mismatches before granting authority.

Selected tests and support roots, including additions, pytest configuration,
repository-local plugins named by literal `pytest_plugins` declarations in
applicable conftests, the fixed proof executor and explicit plugin, `uv.lock`, applicable package
initializers, and exactly the four existing `NON_TRANSITIVE_PROOF_INPUTS` trust
anchors remain frozen regardless of mapping content. The archive regression's
exact Bash/Git fixture protocol remains freshness-bound; it is not a general
external-process bypass. Because the provenance implementation is itself one of
the four anchors, its final bytes must equal the authenticated red source. The
replacement validator therefore needs the existing externally authenticated
bootstrap at the red boundary; no fifth anchor or mutable self-exception is
introduced.

The live-revalidated external amendment receipt may replace only the stale
producer-authorship and verified-final producer-verdict predicates for one exact
raw green/red pair. Both reports must fail only with the bound
`stale-red-proof` diagnostic; each immutable plan is validated independently,
the green JUnit must show every green-plan selector passing, and the red JUnit
must show only the approved failures with all other red-plan selectors passing.
Repository, issue, pull request, branch, expiry, ancestry,
linear-history, test-only, artifact, plan, JUnit, and digest checks remain
mandatory. The fixed external pair is retained only as the final bootstrap
fallback.

Continuing construct-by-construct Python interpretation was rejected because it
creates an oversized security parser whose completeness cannot be defended and
whose clean-code regressions block the mandatory review gate. Inferring SUT
paths from imports, runtime behavior, directories, or globs was rejected because
it makes authority implicit or over-broad. Always reusing the fixed external
red/green pair was rejected because it makes future review amendments stale and
prevents an updateable non-default-branch PR.

### Isolate untrusted pytest execution from trusted evidence production

Keep plan validation, raw-JUnit canonicalization, reconciliation, provenance
validation, Code Review, and artifact publication in the trusted runner process.
Launch only the exact mapped pytest argument vector in a transient system
service with a dynamically allocated unprivileged identity, a dedicated cgroup,
and a private mount namespace. The service exposes the checkout and frozen
module fixture read-only, hides Git metadata and other runner-home content,
removes network and privilege-gain capabilities, and permits writes only in a
private temporary filesystem plus one fresh raw-JUnit handoff directory.

The service uses a finite runtime and control-group kill semantics. The trusted
executor does not read the handoff until the service is inactive and every
descendant has been terminated. It then treats raw JUnit as bounded untrusted
input, canonicalizes exact planned selectors and toolchain identities, and
publishes the canonical JUnit to a runner-owned path that was never writable by
the service. Stdout and stderr are captured with fixed bounds and replayed only
inside a host-generated workflow-command stop/resume boundary, or more narrowly
routed to null inside the service. The implementation chooses null routing so
canonical JUnit is the sole proof-data handoff and no custom output-draining
protocol is needed. Blocking CI requests this backend explicitly and fails
closed when the hosted runner cannot enforce it. The direct command-runner seam
remains for local unit tests; it is not an accepted blocking-workflow backend.

Per-file hard links, digests, or memory-backed JUnit alone were rejected because
a same-identity descendant can instead mutate the plan, checkout, verifier
scripts, module fixture, Git state, or a later artifact path. A fresh job alone
was rejected because an unisolated producer can forge its output before upload.
A new OCI proof image was rejected because the repository has no frozen proof
image and reusing the host virtual environment in an unrelated image is not a
reproducible compatibility contract.

## Risks / Trade-offs

- **Longer CI runs without uv persistence** → Accept the release-safety cost; frozen installs remain deterministic and can use runner-local state only within a job.
- **A focused release branch drifts from the validated dev security delta** → Compare every selected file and dependency artifact against the merged dev state, retain exact before/after audit evidence, and run the full main-bound gates.
- **Previously saved cache content remains stored in GitHub** → Disabling restore makes it unreachable. Delete old caches only as optional operational hygiene, not as proof of remediation.
- **Semgrep 1.175 changes scan behavior** → Run the repository SAST configuration,
  dependency audit, full test suite, and Python 3.11–3.13 package matrix; rollback
  by reverting the issue-linked PR if the tool upgrade regresses the gates.
- **An approved SUT path can influence pytest indirectly** → Keep authorization
  exact, digest-bound, owner-approved, and limited to regular-file mapping
  touchpoints; freeze every declared harness and proof-authority class and reject
  collisions or role mismatches.
- **Hosted-runner isolation primitives drift or are unavailable** → Pin the
  workflow to the supported hosted Linux class, validate every required service
  property before execution, and fail closed without producing canonical proof.
- **Mapped tests need ordinary scratch or Git fixture behavior** → Preserve a
  private writable temporary filesystem and installed Bash/Git tools while
  keeping the real checkout, module fixture, Git metadata, network, and trusted
  artifact paths inaccessible or read-only.

## Migration Plan

1. Merge the issue-linked fix through protected `dev` after focused and full gates pass.
2. Close PR #691 only after the replacement release branch is prepared and its exact selected-file provenance is recorded.
3. Run the full protected-main gates on the focused release PR and merge only when policy permits, then verify the main-push package, PyPI, and GitHub release jobs.
4. Roll back by reverting the security-fix PR; if 0.55.4 is already published, use a normal follow-up patch release rather than rewriting history or replacing the published artifact.
