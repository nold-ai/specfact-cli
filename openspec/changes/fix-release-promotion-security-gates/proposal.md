## Why

The protected `dev` head now contains the intervening 0.55.3 module-scope changes, while release promotion remains blocked by cache-persistence and Requirements-proof authority findings. The security release must remove those sinks, preserve the newer dev work, and use a focused 0.55.4 promotion rather than weakening the Requirements gate.

## What Changes

- Disable both restore and save behavior for shared uv and npm caches after companion-module fixture code can execute in privileged jobs.
- Remove the PR Orchestrator manual-dispatch entrypoint so a branch-selected workflow definition cannot authorize its own fixture execution; retain the schedule-only compatibility lane and exact commit/tree verification.
- Keep the Requirements evidence and finalized Code Review gates fail-closed; replace the over-broad release PR with the smallest `main`-based patch-release PR containing only the dev-validated 0.55.4 security delta.
- Add a focused regression for the cache boundary before changing the shared action.
- Correct the two actionable PR #691 code-quality findings without changing public behavior.
- Bind local dependency-trust triggers and license exceptions to the exact frozen Code Review environment.
- Correct review-confirmed false positives in active OpenSpec authoring and retained pytest-plugin proof discovery.
- Replace construct-by-construct Python interpretation with an exact,
  owner-approved `mutable_after_red` SUT path policy over every red-to-final
  commit. Freeze selected test/support inputs, pytest configuration, proof
  producers, `uv.lock`, package initializers, and the four existing trust
  anchors; fail closed on ambiguous or unmapped paths.
- Preserve the externally authorized verified green as an ordinary amendment
  cycle base so later review fixes can complete fresh red-to-green proof on the
  same non-default-branch pull request.
- Isolate mapped pytest proof execution and every descendant from the trusted
  evidence producer with a transient unprivileged Linux service, read-only
  proof inputs, private scratch space, and cgroup-bounded teardown before the
  trusted host canonicalizes the raw JUnit handoff.
- Keep repository-local pytest plugins named by applicable conftests frozen;
  mapping metadata cannot relabel those harness modules as mutable SUT.
- Run the staged-index Markdown auto-fixer once per pre-commit invocation so
  multiple filename batches cannot race on the Git index lock.
- Finalize the completed retained-red-proof bugfix with the normal OpenSpec archive command when strict validation confirms it is complete.
- Replace the now-obsolete MCP vulnerability waiver by raising the opt-in
  static-analysis/development Semgrep floor to 1.175.0, whose published metadata
  pins fixed `mcp==1.29.0`;
  refresh only the frozen dependency artifacts affected by that solve, and
  enforce `mcp>=1.28.1` before synchronization.
- Do not change public CLI/API behavior, runtime dependency membership, or package
  contents; advance the four synchronized core version sources only from 0.55.3
  to the next patch, 0.55.4.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `trustworthy-green-checks`: prohibit persistent dependency caches across privileged companion-module execution.

## Impact

- **Affected surfaces**: the shared frozen setup action, frozen development-tool
  graph, dependency/license gates, Requirements proof provenance and amendment
  authority, OpenSpec pre-commit helpers, the staged Markdown hook, focused
  tests, and OpenSpec evidence.
- **Security**: removes the persistent cache sink reported by CodeQL and replaces
  the obsolete MCP waiver with a fixed transitive release plus a pre-install MCP
  floor while retaining exact module repository, commit, and tree verification.
  It also prevents mapped tests or their detached descendants from modifying the
  plan, checkout, proof producers, module fixture, canonical reports, or later
  verifier inputs under the runner identity. No alert is dismissed.
- **Compatibility**: frozen and hash-locked dependency synchronization remains
  unchanged; CI may take longer because uv artifacts are downloaded without a
  persistent Actions cache. Blocking Requirements proof on GitHub's hosted
  Linux runner gains an explicit system-service isolation backend; local
  executor unit seams remain available, and mapped tests retain private
  temporary filesystem and Bash/Git fixture behavior without network access.
- **Release safety**: Requirements and finalized Code Review remain fail-closed.
  Only exact, regular-file mapping touchpoints explicitly approved as mutable
  may change after red; all proof authority and harness inputs remain frozen.
  The broad PR is replaced by a focused patch-release PR so unrelated planning
  changes are not promoted or used to justify a gate exception.
- **Documentation**: no user-facing CLI/API or documentation behavior changes. Repository governance and release evidence are recorded in the change and PR.
- **Rollback**: revert the security-fix PR. If a published release later needs rollback, use the normal follow-up patch release; yank only a demonstrably unsafe PyPI artifact and never rewrite the tag or published history.

## Source Tracking

- **GitHub Issue**: #692
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/692>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: in progress
