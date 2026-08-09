## Context

The current pre-commit runner invokes released Requirements evidence before
Code Review and contract tests when staged active OpenSpec sources exist. The
pull-request workflow verifies an immutable modules fixture, evaluates the PR
base diff, retains JSON/Markdown reports, and fails only after artifacts are
available. This is the correct delivery boundary, but the report currently
establishes declared traceability rather than current-run test execution.

Modules #379 owns the released two-phase 0.5.1 contract: a structured scenario proof plan
and reconciliation of trusted JUnit results. Core owns safe process execution,
timeouts, the frozen environment, artifact retention, job ordering, and branch
protection. Core must not reinterpret Requirements findings or manufacture a
passing verdict.

This change is narrower than `validation-02-full-chain-engine`; it delivers one
Requirements proof packet and a review handoff, not a cross-domain evidence
graph.

## Goals and Non-Goals

### Goals

- Make every relevant change produce either a deterministic Requirements proof
  decision or an explicit no-impact result.
- Keep pre-commit fast while blocking missing scenario/touchpoint/test-plan
  declarations before later local gates.
- Execute exact module-produced test selectors safely in CI and retain JUnit.
- Reconcile results through the pinned module and pass finalized proof to Code
  Review before contract checks.

### Non-Goals

- Define scenario proof semantics, parse JUnit into verdicts, or infer
  requirements in core.
- Execute arbitrary commands from repository metadata.
- Replace the repository's full test/contract/security matrix with selected
  proof tests.
- Implement the future full-chain validation graph.

## Decisions

### Always produce a pull-request decision

The Requirements proof check runs for pull requests rather than relying on a
narrow OpenSpec-only path filter. Module-owned planning receives the PR base
reference and returns a selected plan, findings, or a deterministic skipped
result. Relevant product paths without mapped scenarios cannot silently skip;
they require a mapped active change or an explicit, auditable no-impact
declaration governed by repository policy. A no-impact declaration includes a
bounded reason and changed-path digest and is rejected for policy-designated
product-interface, contract, requirement-source, or proof-test paths.

### Keep staged enforcement static and index-isolated

Pre-commit validates only the Git index snapshot. It verifies source revisions,
touchpoints, exact selectors, and plan completeness before ordinary Code Review
and contract gates. It does not run the potentially expensive targeted suite or
reuse proof produced for different index bytes. Finalized proof context is a CI
handoff unless a future bounded local-execution contract is specified.

### Treat the plan as untrusted structured input

Core accepts only the released schema and supported runner kinds. For the
initial pytest runner, every selector must be an exact repository-contained
node ID whose file exists in the checked-out snapshot. Core rejects absolute or
escaping paths, control characters, option-like selectors, wildcard/glob
expansion, duplicates, excessive plan size, and unsupported runners before
starting a process.

Selectors are passed as an argument array after the runner's option boundary;
they are never concatenated into a command string or evaluated by a shell.
Timeouts, resource limits, environment allowlisting, and result paths are
core-owned. A repository-controlled pytest result plugin records the exact
collected node ID as a dedicated canonical selector property on each JUnit test
case; core does not ask the module to guess identity from display names.

### Reconcile with the same immutable module release

After targeted execution, core passes the original plan and retained JUnit XML
to the same verified module release. The module returns the final authoritative
Requirements JSON/Markdown proof. Core validates that both reports exist,
publishes them, and translates only the process exit code into delivery status.

### Migrate the historical R07 proof ledger without fabricating red JUnit

Normal delivery remains strict: a new governed production change requires a
runner-generated, git-bound red JUnit proof. This already-active R07 change is
the one explicit migration exception. Its historical failing-first evidence is
recorded in its committed `TDD_EVIDENCE.md`, predating the released red-JUnit
wire format. Final reconciliation therefore receives a generated
`legacy-tdd-ledger` record only when the selected change is
`requirements-07-runtime-proof-delivery`. Core hashes the committed ledger and
binds that digest plus the module-produced mapping and plan digests to the
record. It never creates a synthetic red artifact, and it never supplies both
legacy-ledger and red-JUnit proof bases.

The migration reads that ledger with `git show` from the approved immutable
historical commit, not from the mutable pull-request checkout. Normal red proof
uses the same core-owned Git boundary: the current pull-request base must be
an ancestor of the red report source, the red source must be a strict ancestor
of the final source, and no governed production path (including either endpoint
of a rename) may change between the base and red source. Each selected test
file must remain unchanged through final reconciliation.

### Build a dependency-complete runtime smoke registry

The runtime-discovery smoke check keeps its explicit root module set so its
command-surface coverage remains bounded. Before creating its temporary local
registry, core reads each root manifest and recursively stages every declared
`bundle_dependencies` entry. This makes the fixture match normal marketplace
resolution without hard-coding a changing dependency list in core. Malformed or
missing dependency metadata fails while assembling the isolated fixture, before
any launcher is exercised.

### Hand finalized proof to review without verdict fusion

CI invokes the released Code Review interface with the finalized Requirements
report as optional context. Review may add deterministic coverage findings and
provenance, but core retains both reports and their separate verdicts. A green
review cannot override red Requirements proof, and a green Requirements report
cannot override red review or contract checks.

### Preserve evidence before enforcement

The plan, raw JUnit, finalized JSON/Markdown, and review report are uploaded
under `always()` behavior. The job summary states selected scenarios,
touchpoints, execution counts, and remediation paths before the final enforcing
step exits non-zero.

## Risks and Mitigations

- **Selector injection**: strict schema/path/option/control validation and
  subprocess argument arrays; no shell interpretation.
- **False proof from stale results**: fresh artifact paths plus module-owned
  plan/source/result binding.
- **Excessive local latency**: planning only in pre-commit; execution in CI.
- **Partial CI replacing broad validation**: selected proof tests are additive;
  existing contract, full-test, static-analysis, and security jobs remain.
- **Silent non-coverage**: every PR emits selected, failed, or explicit skipped
  evidence; relevant paths cannot disappear through workflow path filters.
- **Cross-repo release skew**: pin repository, exact commit, package versions,
  and signatures before command execution.

## Rollout and Rollback

1. Modules #379 released signed `nold-ai/specfact-requirements` 0.5.1 with compatibility fixtures.
2. Record that release's immutable main-branch SHA in `ci/module-fixture.lock.json` and its allowlist before manually rerunning core PR #663; never pre-pin a feature-branch SHA.
3. Pin that release in core and enable always-reporting advisory proof CI.
4. Baseline mappings and remediation, then enable strict blocking by profile.
5. Enable finalized proof context in Code Review without verdict fusion.
6. Roll back to the existing static gate by reverting the fixture/wiring; keep
   retained artifacts for audit and do not alter upstream sources.
