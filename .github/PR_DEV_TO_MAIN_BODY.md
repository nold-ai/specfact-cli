# Description

Release PR: **dev → main** to promote changes from the development branch to production. This brings all dev-only changes into main for release (PyPI/container).

**Summary of changes (since last main):**

- **0.26.13** – Debug log parity for `specfact upgrade`: "up to date" success path now writes to `~/.specfact/logs/specfact-debug.log` when `--debug` is set.
- **0.26.12** – Debug logs under `~/.specfact/logs`: `debug_print()` and `debug_log_operation()`; log file at `~/.specfact/logs/specfact-debug.log`; adapters and commands log operation metadata when `--debug`; docs and tests. Closes #158.
- **0.26.11** – Backlog refine `--import-from-tmp`: parser and import flow; unit tests.
- **0.26.10** – OpenSpec OPSX migration docs; config.yaml (OPSX) vs project.md (legacy); version bump fix.
- **0.26.9** – GitHub remote detection (`ssh://`, `git://`); code scanning mitigations (ReDoS, URL sanitization, workflow permissions).
- **0.26.8** – ADO field mappings (acceptance criteria, assignee); `backlog map-fields`; compare SSH hostnames case-insensitively.
- **Earlier** – Startup performance (metadata tracking, update command); OpenSpec/workflow commands; contribution standards.

**Fixes** #158 (via #159), #148, #145, #142, #156

**New Features** #158 (debug logging)

**Contract References**: No new `@icontract` decorators in this release; existing contracts unchanged. Debug helpers are no-ops when debug is off.

## Type of Change

Please check all that apply:

- [x] 🐛 Bug fix (non-breaking change which fixes an issue)
- [x] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [ ] 🔒 Contract enforcement (adding/updating `@icontract` decorators)
- [x] 🧪 Test enhancement (scenario tests, property-based tests)
- [ ] 🔧 Refactoring (code improvement without functionality change)

## Contract-First Testing Evidence

### Contract Validation

- [ ] **Runtime contracts added/updated** (`@icontract` decorators on public APIs)
- [ ] **Type checking enforced** (`@beartype` decorators applied)
- [ ] **CrossHair exploration** completed: `hatch run contract-test-exploration`
- [x] **Contract violations** reviewed and addressed

### Test Execution

- [x] **Contract validation**: `hatch run contract-test-contracts` ✅
- [ ] **Contract exploration**: `hatch run contract-test-exploration` ✅
- [x] **Scenario tests**: `hatch run contract-test-scenarios` ✅
- [x] **Full test suite**: `hatch run contract-test-full` ✅

### Test Quality

- [x] **CLI commands tested** with typer test client
- [ ] **Edge cases covered** with Hypothesis property tests
- [x] **Error handling tested** with invalid inputs
- [x] **Rich console output verified** manually or with snapshots

## How Has This Been Tested?

All changes were tested and reviewed on dev via PRs (#159, #156, #148, #145, #142). Contract validation and scenario tests pass. Debug logging verified manually (`specfact --debug sdd list`, `specfact --debug upgrade --check-only`) and log file inspected at `~/.specfact/logs/specfact-debug.log`.

### Manual Testing

- [x] Tested CLI commands manually
- [x] Verified rich console output
- [x] Tested with different input scenarios
- [x] Checked error messages for clarity

### Automated Testing

- [x] Contract validation passes
- [x] Scenario tests cover user workflows
- [x] All existing tests still pass

### Test Environment

- Python version: 3.12
- OS: Linux (Ubuntu)

## Checklist

- [x] My code follows the style guidelines (PEP 8, ruff format, isort)
- [x] I have performed a self-review of my code
- [x] I have added/updated contracts (`@icontract`, `@beartype`) — N/A for this release PR
- [x] I have added/updated docstrings (Google style)
- [x] I have made corresponding changes to documentation
- [x] My changes generate no new warnings (basedpyright, ruff, pylint)
- [x] All tests pass locally
- [x] I have added tests that prove my fix/feature works
- [x] Any dependent changes have been merged (all merged to dev)

## Quality Gates Status

- [x] **Type checking** ✅ (`hatch run type-check`)
- [x] **Linting** ✅ (`hatch run lint`)
- [x] **Contract validation** ✅ (`hatch run contract-test-contracts`)
- [ ] **Contract exploration** ✅ (`hatch run contract-test-exploration`)
- [x] **Scenario tests** ✅ (`hatch run contract-test-scenarios`)

## Screenshots/Recordings (if applicable)

N/A for release PR. Debug log output was verified in #159.
