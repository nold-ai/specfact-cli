# Change: icontract AST Scan and TDD Gate Runners for specfact code review run

## Why

Contract-first development (icontract/beartype decorators) and TDD-first order (test file exists before feature file) are the two highest-value quality gates in this codebase. Without automated enforcement, these rules are advisory only. This change makes them structurally enforced: any public function missing `@require`/`@ensure` triggers a BLOCK finding; any changed `src/` file with no corresponding test file triggers `TEST_FILE_MISSING` (BLOCK).

CrossHair fast-pass (2s timeout per path) provides property-based counterexample discovery as a bonus layer.

## What Changes

- **NEW**: `contract_runner.py` — AST-scans changed files for public functions missing `@require`/`@ensure` icontract decorators; also runs `crosshair check` in fast mode (2s/path); both mapped to `category=contracts`
- **NEW**: `runner.py` — orchestrates all tool runners in sequence; merges findings; invokes scorer; returns `ReviewReport`
- **CONSTRAINT**: Missing test file for any changed `src/` module → `TEST_FILE_MISSING` finding, `severity=error`, verdict=BLOCK
- **CONSTRAINT**: Test runner invokes `hatch run smart-test-unit` on changed modules, parses pytest-json, validates coverage >= 80%
- **NEW**: Unit tests for `contract_runner.py` and `runner.py` (TDD-first)

## Capabilities

### New Capabilities

- `contract-runner`: AST-based icontract decorator presence check + CrossHair fast-pass for changed files
- `test-tdd-gate`: TDD gate — BLOCK if test file missing or coverage < 80% for changed modules

### Modified Capabilities

- `review-runner`: `runner.py` assembled here as the orchestrator for all tool runners

---

## Impact

- Depends on `code-review-01-module-scaffold`, `code-review-02-ruff-radon-runners`, `code-review-03-type-governance-runners`
- `crosshair` must be available in the environment; noted as an open question for the coding-automation container
- **Documentation**: Update `docs/modules/code-review.md` with contract and TDD gate runner details

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
