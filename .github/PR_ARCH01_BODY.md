# Description

Implements the **CLI modular command registry** (OpenSpec change `arch-01-cli-modular-command-registry`): registry-based command registration, lazy loading, help cache, module packages with discovery, and init module state. All built-in commands are converted to the new module format (wrapper packages under `src/specfact_cli/modules/` with `module-package.yaml` and `command_help`). Root help is rendered by the full Typer app (options, defaults, formats). Version 0.27.0.

**Fixes** #193

**OpenSpec change**: `arch-01-cli-modular-command-registry`

**Contract References**: CommandRegistry (register, get_typer, list_commands, list_commands_for_help), ModulePackageMetadata, help_cache and module_state helpers; init command contracts unchanged.

## Type of Change

Please check all that apply:

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [x] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [x] 🔒 Contract enforcement (adding/updating `@icontract` decorators)
- [x] 🧪 Test enhancement (scenario tests, property-based tests)
- [x] 🔧 Refactoring (code improvement without functionality change)

## Contract-First Testing Evidence

**Required for all changes affecting CLI commands or public APIs:**

### Contract Validation

- [x] **Runtime contracts added/updated** (`@icontract` decorators on public APIs)
- [x] **Type checking enforced** (`@beartype` decorators applied)
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

**Contract-First Approach**: Registry, help_cache, module_state, and module_packages have dedicated unit tests (31 tests). CLI surface tests verify `specfact --help`, `specfact init --help`, `specfact backlog --help`. E2E test `test_cli_analyze_code2spec_on_self` runs full import-from-code (timeout 120s).

### Manual Testing

- [x] Tested CLI commands manually
- [x] Verified rich console output (root help: options + commands)
- [x] Tested with different input scenarios
- [x] Checked error messages for clarity

### Automated Testing

- [x] Contract validation passes
- [x] Scenario tests cover user workflows
- [x] All existing tests still pass

### Test Environment

- Python version: 3.11
- OS: Linux (Ubuntu)

## Checklist

- [x] My code follows the style guidelines (PEP 8, ruff format, isort)
- [x] I have performed a self-review of my code
- [x] I have added/updated contracts (`@icontract`, `@beartype`)
- [x] I have added/updated docstrings (Google style)
- [x] I have made corresponding changes to documentation
- [x] My changes generate no new warnings (basedpyright, ruff, pylint)
- [x] All tests pass locally
- [x] I have added tests that prove my fix/feature works
- [x] Any dependent changes have been merged

## Quality Gates Status

- [x] **Type checking** ✅ (`hatch run type-check`)
- [x] **Linting** ✅ (`hatch run lint`)
- [x] **Contract validation** ✅ (`hatch run contract-test-contracts`)
- [ ] **Contract exploration** ✅ (`hatch run contract-test-exploration`)
- [x] **Scenario tests** ✅ (`hatch run contract-test-scenarios`)

## Screenshots/Recordings (if applicable)

N/A – CLI help output unchanged in appearance (full Options + Commands panels).
