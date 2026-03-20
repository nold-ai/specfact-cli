## Context

Running `specfact review` against the specfact-cli repo (run `review-eb238209`, 2026-03-18) produced 2,539 findings and `overall_verdict: FAIL` with score 0 and reward_delta -80. The four tool categories are basedpyright (type safety, 1,616), semgrep (architecture, 352), contract_runner (contracts, 291), and radon (complexity, 279). A single pylint invocation error rounds it out.

This is a dogfooding gap: we cannot credibly ask customers to achieve zero-finding reviews while our own codebase fails. The fix is a structured, tool-by-tool remediation campaign, run on a dedicated `bugfix/code-review-zero-findings` branch with TDD evidence captured per behavior change.

No new user-facing CLI commands or API surface changes are introduced. This is a pure internal quality improvement.

## Goals / Non-Goals

**Goals:**
- Reduce basedpyright `reportUnknownMemberType` count from 1,531 to 0 by adding explicit type annotations to all untyped class members.
- Eliminate all 352 `print-in-src` semgrep findings by replacing every `print()` call with `get_bridge_logger()` or `get_logger()`.
- Add `@require` / `@ensure` / `@beartype` decorators to all 291 public functions flagged as `MISSING_ICONTRACT`.
- Refactor all 202 functions with CC≥16 to CC<16 (target CC<10 for new helpers, CC<13 for refactored legacy).
- Fix the 6 `get-modify-same-method` semgrep findings.
- Resolve the pylint invocation error.
- Establish a CI gate: `specfact review` must exit 0 on every PR targeting `dev` or `main`.

**Non-Goals:**
- Changing any user-facing CLI command name, option, or output format.
- Introducing new runtime dependencies.
- Achieving CC=0 for orchestration scripts — only bring them below the error threshold (CC<16).
- Fixing every warning in third-party generated or vendored files; scope is `src/specfact_cli/`, `scripts/`, and `tools/`.

## Decisions

### D1: Phase-by-phase remediation order (type safety → logging → contracts → complexity)

**Decision**: Address phases in this order: (1) type annotations, (2) print→logging, (3) contracts, (4) complexity, (5) toolchain.

**Rationale**: Type annotation fixes cascade — once `bridge_sync.py` and adapter classes are properly annotated, many downstream `reportAttributeAccessIssue` and `reportUnknownMemberType` findings disappear. Contracts are easier to add once types are correct (beartype's runtime enforcement is meaningless on untyped signatures). Complexity refactoring is last because splitting functions may introduce new public APIs that then need contracts.

**Alternative considered**: All phases in parallel — rejected because untyped code causes false positives in contract and complexity analysis.

### D2: Type annotation strategy — Protocol + TypedDict for dynamic dicts

**Decision**: Use `TypedDict` for structured dict shapes passed through adapters and sync, and `Protocol` for duck-typed interfaces (e.g., adapter contracts). Avoid `Any` escapes except where third-party SDKs genuinely cannot be typed.

**Rationale**: `basedpyright` strict mode flags `Any`-typed members as `reportUnknownMemberType`. TypedDict and Protocol produce concrete types that satisfy strict mode without runtime overhead. Using `dict[str, Any]` everywhere just moves the noise downstream.

**Alternative considered**: Suppression comments (`# type: ignore`) — rejected; suppressions hide real bugs and accumulate tech debt.

### D3: Logging migration — use `get_bridge_logger()` uniformly

**Decision**: Replace all `print()` calls with `get_bridge_logger()` from `specfact_cli.common`. In `scripts/` and `tools/` (which run as standalone scripts), use `logging.getLogger(__name__)` with a StreamHandler if `get_bridge_logger()` is unavailable.

**Rationale**: Structured logging is already the project standard (CLAUDE.md). Bridge logger routes to the debug log file when `--debug` is active. Script-layer logging uses stdlib so scripts remain standalone without specfact_cli import.

**Alternative considered**: Rich console print with stderr routing — rejected; semgrep rule `print-in-src` fires on any `print()` call regardless of stream.

### D4: Contract strategy — minimal viable contracts, no over-specification

**Decision**: Add `@require` for preconditions that prevent clearly invalid calls (e.g., non-empty path, non-None model) and `@ensure` only where the return value invariant is architecturally important. Do NOT add contracts that merely restate the type annotation — beartype handles that.

**Rationale**: Over-contracting produces brittle code. The contract_runner rule `MISSING_ICONTRACT` fires on any public function without at least one `@require` or `@ensure`. A minimal, meaningful contract per function satisfies the rule without creating maintenance burden.

**Alternative considered**: Auto-generate stub contracts — rejected; auto-generated `@require(lambda x: x is not None)` for every argument is noise and undermines the contract-first philosophy.

### D5: Complexity refactoring — extract helpers, not classes

**Decision**: Reduce cyclomatic complexity by extracting named helper functions (not new classes). Helpers live in the same module as the refactored function (private, prefixed `_`). New classes are only introduced if multiple helpers share state.

**Rationale**: Functions with CC≥16 are typically orchestration chains (a sequence of `if`/`for`/`try` blocks). Extracting helpers with descriptive names acts as inline documentation and makes each branch independently testable. A new class for what is essentially a procedure introduces unnecessary OOP ceremony.

**Alternative considered**: Early-return guard clauses only — insufficient for CC≥30 outliers; structural decomposition is required.

### D6: CI gate implementation — `specfact review` in `specfact.yml`

**Decision**: Add `specfact review` as a blocking step in `.github/workflows/specfact.yml`, running after lint and before build. Exit code must be 0.

**Rationale**: CI enforcement prevents regressions. Running in `specfact.yml` keeps review-related CI together and avoids a new workflow file.

**Alternative considered**: Pre-commit hook only — insufficient; pre-commit is local and bypassable.

## Risks / Trade-offs

- **[Risk] Type annotation effort is large (1,531 occurrences).** → Mitigation: Prioritise the five worst files (bridge_sync.py 205, ado.py 150, github.py 139, harness_generator.py 122, smart_test_coverage.py 157). These 5 files account for ~50% of findings. Fix worst first, re-run review after each file.
- **[Risk] Adding contracts to 291 functions introduces runtime overhead.** → Mitigation: `@icontract` has near-zero overhead for simple lambda preconditions. CrossHair coverage ensures contracts are sound. Contracts that add measurable overhead will be flagged in TDD evidence.
- **[Risk] Complexity refactoring in bridge_sync.py and spec_to_code.py may introduce regressions.** → Mitigation: Strict TDD order — failing tests first, refactor, passing tests after. TDD_EVIDENCE.md required per function.
- **[Risk] Some `print()` calls in scripts are intentional progress output to stdout.** → Mitigation: Scripts using `print()` for user-facing progress should use `rich.console.Console()` directly (which is not a `print()` call). The semgrep rule targets the stdlib `print` builtin only.
- **[Risk] Pylint invocation error may surface additional findings once fixed.** → Mitigation: Fix pylint first, triage new findings before counting CI gate status.

## Migration Plan

1. Create `bugfix/code-review-zero-findings` branch from `origin/dev`.
2. **Phase 1 (type safety)**: Fix type annotations file-by-file, worst-first. Run `hatch run type-check` after each file. Track TDD evidence.
3. **Phase 2 (logging)**: Bulk-replace `print()` → `get_bridge_logger()` using automated refactor. Review each replacement for intent (progress vs. debug vs. error). Run `hatch run lint` to confirm semgrep clean.
4. **Phase 3 (contracts)**: Add contracts to 291 functions, grouped by module. Run `hatch run contract-test` after each module.
5. **Phase 4 (complexity)**: Refactor CC≥16 functions. Run `hatch run smart-test` after each file.
6. **Phase 5 (toolchain)**: Fix pylint invocation, verify no new pylint findings.
7. **Phase 6 (CI gate)**: Add `specfact review` step to `specfact.yml`. Run CI and confirm exit 0.
8. Open PR to `dev`. All quality gates must pass.

**Rollback**: All changes are on a single branch. If a refactor introduces an unexpected regression, `git revert` the specific commit. No database migrations or external state changes.

## Open Questions

- OQ1: Should `specfact review` be run in `--changed-only` mode in CI (comparing to `origin/dev`) or full-repo? Full-repo is the gold standard for dogfooding but may be slow. → Decision deferred to CI gate implementation step.
- OQ2: Are there any `print()` calls in `src/` that intentionally write to stdout for machine-readable output (e.g., piped JSON)? These must not be migrated to the logger. → Audit required in Phase 2 before bulk replacement.
- OQ3: The radon CC thresholds used by specfact review (CC≥16 = error, CC13–15 = warning) — are these the same thresholds we recommend to customers? If not, adjust specfact's own thresholds to match. → Review `openspec/specs/clean-code-semgrep-rules/spec.md` before Phase 4.
