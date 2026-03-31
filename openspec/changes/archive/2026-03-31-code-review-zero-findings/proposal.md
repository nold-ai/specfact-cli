# Change: Zero-finding code review — dogfooding specfact review on specfact-cli

## Why

SpecFact CLI's `specfact review` command is our flagship code-quality enforcement tool — yet when run against our own repo, it reports 2,539 findings and returns `overall_verdict: FAIL` (score: 0, reward_delta: -80). This is a credibility and leadership gap: we cannot recommend customers adopt a zero-finding standard while our own codebase fails it. Fixing this now closes the dogfooding loop and proves the tool works end-to-end on a real, mature Python CLI project.

## What Changes

- **MODIFY — Type annotations**: Add explicit type annotations to 1,616 locations flagged by `basedpyright` — primarily untyped class member access (`reportUnknownMemberType` × 1,531), attribute access on opaque objects, and `__all__` mismatches. Key files: `sync/bridge_sync.py`, `adapters/ado.py`, `adapters/github.py`, `validators/sidecar/harness_generator.py`.
- **MODIFY — Logging migration**: Replace 352 `print()` calls in `src/`, `scripts/`, and `tools/` with `get_bridge_logger()` structured logging. Fix 6 `get-modify-same-method` anti-patterns flagged by semgrep.
- **MODIFY — Contract coverage**: Add `@require` / `@ensure` (icontract) and `@beartype` decorators to 291 public functions identified by `contract_runner` as `MISSING_ICONTRACT`.
- **MODIFY — Complexity refactoring**: Split 202 functions with cyclomatic complexity CC≥16 into smaller, testable helpers (target CC<10 for new code, CC<13 for refactored legacy). Reduce an additional 77 functions in the CC13–CC15 warning band. Extreme outliers (CC127, CC120, CC118, CC101) in orchestration entry points must be prioritised.
- **MODIFY — Toolchain fix**: Resolve the single `pylint` invocation error (missing binary or Hatch env PATH issue).
- **NEW — CI gate**: Add `specfact review run --ci` as a blocking step in `.github/workflows/specfact.yml` (after lint, before build); exit code 0 required on every PR targeting `dev` or `main`.
- **No new user-facing CLI commands or API surface changes.** All changes are internal quality improvements.

## Capabilities

### New Capabilities
- `dogfood-self-review`: Specification for running and passing `specfact review` against the specfact-cli repo itself — defines the self-review policy, acceptance criteria (0 findings, `overall_verdict: PASS`), and the CI gate that enforces it.

### Modified Capabilities
- `code-review-module`: The review tool must be able to scan itself; any self-referential edge cases (e.g., reviewing files that implement the reviewer) must be handled.
- `debug-logging`: Logging migration extends the `get_bridge_logger()` contract to cover all `print()` replacement sites, including adapter and scripts layers.
- `contract-runner`: The `MISSING_ICONTRACT` contract must produce actionable output for the 291 currently-uncovered public APIs. No rule changes — this is coverage expansion.
- `review-cli-contracts`: Contracts on the review CLI commands must be consistent with the updated type-annotated codebase (no phantom attribute access post-type-annotation).

## Impact

- **Files**: 261 unique files affected across `src/specfact_cli/`, `scripts/`, and `tools/`.
- **CI**: After this change, `specfact review` will be added to the CI pre-commit and PR gates as a blocking check (exit code 0 required).
- **No API breakage**: All changes are internal quality improvements with no public interface modifications.
- **Dependencies**: No new runtime dependencies. `icontract`, `beartype`, and `basedpyright` are already in the dev toolchain.
- **Sequencing**: Independent of other pending changes — no hard blockers. Can be implemented in parallel worktree alongside module-migration work.
- **Documentation**: `docs/` (code review guide, CI reference page) will be updated to document the self-review CI gate and zero-finding policy.

## Source Tracking

- **GitHub Issue**: #423
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/423
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
