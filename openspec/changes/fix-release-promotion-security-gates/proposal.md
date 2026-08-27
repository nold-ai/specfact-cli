## Why

The protected `dev` head for the 0.55.2 security release is blocked by a cache-persistence dataflow, while the broad `dev -> main` PR correctly rejects accumulated planning-only OpenSpec changes without acceptance evidence. The release must remove the cache sink and use a focused patch-release promotion rather than weakening the Requirements gate.

## What Changes

- Disable both restore and save behavior for shared uv and npm caches after companion-module fixture code can execute in privileged jobs.
- Remove the PR Orchestrator manual-dispatch entrypoint so a branch-selected workflow definition cannot authorize its own fixture execution; retain the schedule-only compatibility lane and exact commit/tree verification.
- Keep the Requirements evidence and finalized Code Review gates unchanged; replace the over-broad release PR with the smallest `main`-based patch-release PR containing only the already-validated 0.55.2 security delta.
- Add a focused regression for the cache boundary before changing the shared action.
- Correct the two actionable PR #691 code-quality findings without changing public behavior.
- Bind local dependency-trust triggers and license exceptions to the exact frozen Code Review environment.
- Correct review-confirmed false positives in active OpenSpec authoring and retained pytest-plugin proof discovery.
- Run the staged-index Markdown auto-fixer once per pre-commit invocation so
  multiple filename batches cannot race on the Git index lock.
- Finalize the completed retained-red-proof bugfix with the normal OpenSpec archive command when strict validation confirms it is complete.
- Replace the now-obsolete MCP vulnerability waiver by raising the opt-in
  static-analysis/development Semgrep floor to 1.175.0, whose published metadata
  pins fixed `mcp==1.29.0`;
  refresh only the frozen dependency artifacts affected by that solve, and
  enforce `mcp>=1.28.1` before synchronization.
- Do not change public CLI/API behavior, runtime dependency membership, package
  contents, or the 0.55.2 version.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `trustworthy-green-checks`: prohibit persistent dependency caches across privileged companion-module execution.

## Impact

- **Affected surfaces**: the shared frozen setup action, frozen development-tool
  graph, dependency/license gates, Requirements proof and OpenSpec pre-commit
  helpers, the staged Markdown hook, focused tests, and OpenSpec evidence.
- **Security**: removes the persistent cache sink reported by CodeQL and replaces
  the obsolete MCP waiver with a fixed transitive release plus a pre-install MCP
  floor while retaining exact module repository, commit, and tree verification.
  No alert is dismissed.
- **Compatibility**: frozen and hash-locked dependency synchronization remains unchanged; CI may take longer because uv artifacts are downloaded without a persistent Actions cache.
- **Release safety**: Requirements and finalized Code Review remain fail-closed. The broad PR is replaced by a focused patch-release PR so unrelated planning changes are not promoted or used to justify a gate exception.
- **Documentation**: no user-facing CLI/API or documentation behavior changes. Repository governance and release evidence are recorded in the change and PR.
- **Rollback**: revert the security-fix PR. If a published release later needs rollback, use the normal follow-up patch release; yank only a demonstrably unsafe PyPI artifact and never rewrite the tag or published history.

## Source Tracking

- **GitHub Issue**: #692
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/692>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: in progress
