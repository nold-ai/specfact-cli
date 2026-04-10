# Change: Project-Specific Semgrep Rules for Clean Code Patterns

## Why

Ruff and pylint cover well-known generic patterns, but several project-specific anti-patterns require custom semgrep rules:

- **get+modify in same method** — violates single-responsibility; not detectable by ruff
- **Unguarded nested attribute access** (`a.b.c` without None guard) — silent NoneAttributeError risk
- **Cross-layer calls** (repository.*+ http_client.* in same function) — architecture boundary violation
- **Module-level network instantiation** — side effects at import time
- **print() in src/** — complement to ruff T201 for cases ruff misses with complex expressions

Each rule ships with a bad-example fixture and a good-example fixture to prove it fires/doesn't fire.

## What Changes

- **NEW**: `semgrep_runner.py` — invokes `semgrep --config .semgrep/clean_code.yaml --json`; maps findings to `List[ReviewFinding]` with `category=clean_code` or `category=architecture`
- **NEW**: `.semgrep/clean_code.yaml` — 5 custom rules: get+modify, nested access, cross-layer, module-level network, print-in-src
- **NEW**: Test fixtures: `bad_nested_access.py`, `good_nested_access.py` (and equivalents for each rule)
- **NEW**: Unit tests for `semgrep_runner.py` (TDD-first)

## Capabilities

### New Capabilities

- `semgrep-runner`: Project-specific semgrep rule execution and finding extraction
- `clean-code-semgrep-rules`: 5 custom semgrep rules covering get+modify, nested access, cross-layer calls, module-level network, print-in-src

---

## Impact

- Depends on `code-review-01-module-scaffold`
- semgrep must be installed in the environment (already a dependency in the codebase)
- Rules are scoped to `packages/specfact-code-review/` — no impact on existing semgrep config
- **Documentation**: Update `docs/modules/code-review.md` with semgrep rule descriptions and examples

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
