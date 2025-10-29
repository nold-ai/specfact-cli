# Description

Please include a summary of the change and which issue is fixed. Include relevant motivation and context.

**Fixes** #(issue)

**New Features** #(issue)

**Contract References**: List any contracts (`@icontract` decorators) that this change affects or implements.

## Type of Change

Please check all that apply:

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔒 Contract enforcement (adding/updating `@icontract` decorators)
- [ ] 🧪 Test enhancement (scenario tests, property-based tests)
- [ ] 🔧 Refactoring (code improvement without functionality change)

## Contract-First Testing Evidence

**Required for all changes affecting CLI commands or public APIs:**

### Contract Validation

- [ ] **Runtime contracts added/updated** (`@icontract` decorators on public APIs)
- [ ] **Type checking enforced** (`@beartype` decorators applied)
- [ ] **CrossHair exploration** completed: `hatch run contract-test-exploration`
- [ ] **Contract violations** reviewed and addressed

### Test Execution

- [ ] **Contract validation**: `hatch run contract-test-contracts` ✅
- [ ] **Contract exploration**: `hatch run contract-test-exploration` ✅
- [ ] **Scenario tests**: `hatch run contract-test-scenarios` ✅
- [ ] **Full test suite**: `hatch run contract-test-full` ✅

### Test Quality

- [ ] **CLI commands tested** with typer test client
- [ ] **Edge cases covered** with Hypothesis property tests
- [ ] **Error handling tested** with invalid inputs
- [ ] **Rich console output verified** manually or with snapshots

## How Has This Been Tested?

**Contract-First Approach**: Describe how contracts and scenario tests validate your changes.

### Manual Testing

- [ ] Tested CLI commands manually
- [ ] Verified rich console output
- [ ] Tested with different input scenarios
- [ ] Checked error messages for clarity

### Automated Testing

- [ ] Contract validation passes
- [ ] Property-based tests cover edge cases
- [ ] Scenario tests cover user workflows
- [ ] All existing tests still pass

### Test Environment

- Python version: (e.g., 3.11, 3.12, 3.13)
- OS: (e.g., Ubuntu 22.04, macOS 14, Windows 11)

## Checklist

- [ ] My code follows the style guidelines (PEP 8, Black, isort)
- [ ] I have performed a self-review of my code
- [ ] I have added/updated contracts (`@icontract`, `@beartype`)
- [ ] I have added/updated docstrings (Google style)
- [ ] I have made corresponding changes to documentation
- [ ] My changes generate no new warnings (basedpyright, ruff, pylint)
- [ ] All tests pass locally
- [ ] I have added tests that prove my fix/feature works
- [ ] Any dependent changes have been merged

## Quality Gates Status

- [ ] **Type checking** ✅ (`hatch run type-check`)
- [ ] **Linting** ✅ (`hatch run lint`)
- [ ] **Contract validation** ✅ (`hatch run contract-test-contracts`)
- [ ] **Contract exploration** ✅ (`hatch run contract-test-exploration`)
- [ ] **Scenario tests** ✅ (`hatch run contract-test-scenarios`)

## Screenshots/Recordings (if applicable)

Add screenshots or recordings of CLI output, especially for new commands or UI changes.
