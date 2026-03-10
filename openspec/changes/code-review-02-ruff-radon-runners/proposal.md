# Change: Ruff and Radon Tool Runners for specfact code review run

## Why

`specfact code review run` needs a static analysis foundation before it can produce meaningful findings. Ruff provides style/complexity/security checks (C90, S/Bandit rules); radon provides cyclomatic complexity per function. Both are widely used in Python projects and map directly to the clean-code-principles.mdc rules enforced in this codebase.

Without these runners, the review command has no way to detect the most common violations (overly complex functions, insecure patterns, style regressions).

## What Changes

- **NEW**: `ruff_runner.py` — invokes `ruff check --output-format json` on given files; maps Bandit `S*` rules to `category=security`, C90 to `category=clean_code`, E/F to `category=style`; parses output to `List[ReviewFinding]`
- **NEW**: `radon_runner.py` — invokes `radon cc -j`; flags functions with complexity 12–15 as `severity=warning`, >15 as `severity=error`; maps to `category=clean_code`
- **CONSTRAINT**: Both runners filter to the provided file list only (no full-repo scan)
- **CONSTRAINT**: Parse error in tool output → `ReviewFinding` with `category=tool_error`
- **NEW**: Unit tests with mocked subprocess calls for both runners (TDD-first)

## Capabilities

### New Capabilities

- `ruff-runner`: Ruff-based finding extraction for style, complexity, and security rules, mapped to `ReviewFinding` list
- `radon-runner`: Radon-based cyclomatic complexity extraction per function, with severity thresholds

---

## Impact

- No breaking changes to existing commands
- Both runners are internal to the `specfact-code-review` module
- Depends on `code-review-01-module-scaffold` (`ReviewFinding`, `ReviewReport` models must exist)
- **Documentation**: Update `docs/modules/code-review.md` with tool runner details and rule mappings

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
