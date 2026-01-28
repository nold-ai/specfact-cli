# Description

Promote `dev` to `main` for release. This PR merges all changes from `dev` that have been reviewed and tested, including:

- **Backlog refine import** (#156): Implement `specfact backlog refine --import-from-tmp` / `--tmp-file` for export/import round-trip; fence-aware body parser so bodies containing code blocks are not truncated; type-check fixes (questionary import, icontract ViolationError).
- **OpenSpec / OSPX**: Workflow and config migration, opsx commands, contribution standards.
- **ADO**: Canonical user-friendly work item URL, field mappings, assignee display (#145).
- **Other**: Startup performance optimization (#142), code scanning mitigations (#148), GitHub remote detection (SSH/git URLs, case-insensitive hostnames), version/changelog updates.

**Contract References**: No new contracts in this merge; existing backlog and CLI contracts unchanged.

## Type of Change

Please check all that apply:

- [x] 🐛 Bug fix (non-breaking change which fixes an issue)
- [x] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [ ] 🔒 Contract enforcement (adding/updating `@icontract` decorators)
- [x] 🧪 Test enhancement (scenario tests, property-based tests)
- [x] 🔧 Refactoring (code improvement without functionality change)

## Contract-First Testing Evidence

**Required for all changes affecting CLI commands or public APIs:**

### Contract Validation

- [x] **Runtime contracts** (existing; no new decorators in this merge)
- [x] **Type checking** (errors fixed on dev)
- [x] **CrossHair exploration** completed on dev
- [x] **Contract violations** reviewed and addressed on dev

### Test Execution

- [x] **Contract validation**: `hatch run contract-test-contracts` ✅
- [x] **Contract exploration**: `hatch run contract-test-exploration` ✅
- [x] **Scenario tests**: `hatch run contract-test-scenarios` ✅
- [x] **Full test suite**: `hatch run contract-test-full` ✅

### Test Quality

- [x] **CLI commands tested** (backlog refine, map-fields, etc.)
- [x] **Edge cases covered** (nested fenced code in import parser)
- [x] **Error handling tested**
- [x] **Rich console output verified**

## How Has This Been Tested?

All changes were tested and reviewed on `dev` via feature PRs. CI runs on this branch (dev) before merge to main.

### Automated Testing

- [x] Contract validation passes
- [x] Scenario tests cover user workflows
- [x] All existing tests pass

### Test Environment

- Python version: 3.11, 3.12, 3.13
- OS: Linux (Ubuntu), macOS, Windows (CI)

## Checklist

- [x] Code follows style guidelines (PEP 8, ruff format, isort)
- [x] Self-review performed
- [x] Contracts/docstrings in place where applicable
- [x] Documentation updated (CHANGELOG, CONTRIBUTING)
- [x] No new warnings (basedpyright, ruff, pylint)
- [x] All tests pass
- [x] Dependent changes merged (feature PRs merged to dev)

## Quality Gates Status

- [x] **Type checking** ✅ (`hatch run type-check`)
- [x] **Linting** ✅ (`hatch run lint`)
- [x] **Contract validation** ✅ (`hatch run contract-test-contracts`)
- [x] **Contract exploration** ✅ (`hatch run contract-test-exploration`)
- [x] **Scenario tests** ✅ (`hatch run contract-test-scenarios`)

## Screenshots/Recordings (if applicable)

N/A — merge/release PR.
