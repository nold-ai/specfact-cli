# SpecFact CLI Development Project

## Purpose

SpecFact CLI is a **brownfield-first** legacy code modernization tool that:

- **Reverse engineers** legacy Python code into executable contracts
- **Enforces contracts at runtime** to prevent regressions during refactoring
- Uses **symbolic execution (CrossHair)** to discover edge cases and counterexamples
- Provides **gap discovery** and quality scoring for legacy codebases
- Works **offline-first** with no vendor lock-in or cloud dependencies

**Philosophy**: Modernize existing codebases by extracting contracts from legacy code, then enforcing those contracts to prevent regressions. Designed for teams working with legacy systems, not greenfield projects.

## Development Standards References

**For detailed development standards and conventions**, refer to:

- **`AGENTS.md`** (root-level): Repository guidelines, coding style, testing guidelines, CLI command patterns, data model conventions, and commit/PR guidelines
- **`.cursor/rules/`** (root-level): Detailed development rules including:
  - `spec-fact-cli-rules.mdc`: Core development principles, testing requirements, quality gates
  - `testing-and-build-guide.mdc`: Comprehensive testing and build procedures
  - `python-github-rules.mdc`: Python development standards and conventions
  - `clean-code-principles.mdc`: Clean code enforcement rules
  - `session_startup_instructions.mdc`: Session workflow reminders

This `project.md` provides a high-level overview for OpenSpec-driven development. For implementation details, coding patterns, and quality gates, consult the root-level documentation.

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: Typer (CLI), Pydantic (data models)
- **Contracts**: `@icontract` (runtime contract validation), `@beartype` (runtime type checking)
- **Testing**: pytest, CrossHair (symbolic execution), Hypothesis
- **Build**: hatch
- **Distribution**: uvx, PyPI, Docker

## Architecture Patterns

### Bridge Adapter Pattern

Tool-agnostic adapters for external tools (GitHub, GitLab, Linear, Jira, Spec-Kit, OpenSpec, etc.). Each adapter implements the `BridgeAdapter` interface to provide consistent integration without vendor lock-in.

### Plugin Registry Pattern

Dynamic plugin-based adapter registry (`AdapterRegistry`) enables:

- Built-in adapters (GitHub, OpenSpec, Spec-Kit)
- External plugin adapters (register at runtime)
- No hardcoded tool dependencies
- Extensible architecture for new tool integrations

### Sidecar Validation Pattern

External validation workspace pattern:

- Validation runs in separate workspace (not in user's repo)
- No modifications required to target repository
- Works with repositories that don't adopt SpecFact CLI
- Supports multi-repository configurations

### Multi-Repository Support

First-class support for cross-repository workflows:

- Code and project specifications can live in different repos
- External base paths for cross-repo OpenSpec integration
- No hardcoded repository assumptions
- Bridge adapters support remote repository access

### Contract-First Enforcement

Runtime contract validation prevents regressions:

- `@icontract` decorators on all public APIs (`@require`, `@ensure`)
- `@beartype` for automatic runtime type checking
- Contracts replace redundant unit tests (test diet)
- CrossHair explores contracts to discover edge cases

### Offline-First Architecture

No cloud dependencies or vendor lock-in:

- Works entirely locally
- No account required
- No external service dependencies
- CLI-first design (no web UI required)

## Project Conventions

> **Note**: This section summarizes key conventions. For complete details, see `AGENTS.md` and `.cursor/rules/` in the SpecFact CLI root repository.

### Code Style

- 4-space indentation, Black line length 120
- Google-style docstrings
- Full type hints (basedpyright strict mode)
- Contract-first development: `@icontract` and `@beartype` on all public APIs
- Use `common.logger_setup.get_logger()` for logging (avoid `print()`)

### Naming Conventions

- Files and modules: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Functions: `snake_case` with contract decorators

### Contract Naming

- Use `@require` for preconditions
- Use `@ensure` for postconditions
- Use `@beartype` for type validation
- Document contract violations in error messages

## Testing Strategy

> **Note**: For detailed testing procedures, commands, and quality gates, see `.cursor/rules/testing-and-build-guide.mdc` and `AGENTS.md` in the SpecFact CLI root repository.

### Contract-First Testing (Recommended)

**Primary approach**: Contracts provide runtime validation and edge case discovery:

- **Runtime contracts**: `@icontract` decorators on all public APIs
- **Type validation**: `@beartype` for automatic runtime type checking
- **Contract exploration**: CrossHair discovers counterexamples and edge cases
- **Scenario tests**: Focus on CLI command workflows with contract references
- **Test diet**: Remove redundant unit tests as contracts provide the same coverage

### Unit Testing (Backward Compatibility)

- Minimum 80% test coverage
- TDD workflow with quality gates
- Smart test system (incremental testing)
- Place tests alongside modules: `tests/unit/specfact_cli/test_<component>.py`

### Mandatory Testing Requirements for All Changes

**Every change MUST include:**

1. **Unit tests** - Test individual functions and components in isolation
   - Location: `tests/unit/specfact_cli/test_<component>.py`
   - Coverage: All new public functions and edge cases
   - Pattern: Use pytest with `@pytest.mark.asyncio` for async tests

2. **Integration tests** - Test component interactions and workflows
   - Location: `tests/integration/<category>/test_<feature>.py`
   - Coverage: Command workflows, adapter integrations, cross-module interactions
   - Pattern: Test real workflows with actual file I/O and external dependencies

3. **E2E tests** - Test complete user workflows from CLI command to final result
   - Location: `tests/e2e/test_<workflow>.py`
   - Coverage: Full command execution, error handling, output validation
   - Pattern: Test actual CLI commands with real repositories and artifacts

4. **Test updates** - Update existing tests when behavior changes
   - Review all existing tests in affected areas
   - Update tests that depend on changed behavior
   - Ensure all existing tests still pass

5. **Test execution** - Run full test suite before completion
   - Command: `hatch test --cover -v`
   - Requirement: All tests must pass (unit, integration, E2E)
   - Coverage: Must meet or exceed 80% total coverage

## Code Quality Requirements

**Every change MUST pass all quality gates:**

1. **Code formatting** - Apply consistent formatting
   - Command: `hatch run format`
   - Tools: black (formatting), isort (import sorting)
   - Requirement: Zero formatting errors

2. **Linting** - Check code quality and style
   - Command: `hatch run lint`
   - Tools: pylint, ruff, basedpyright
   - Requirement: Zero linting errors

3. **Type checking** - Verify type annotations
   - Command: `hatch run type-check`
   - Tool: basedpyright (strict mode)
   - Requirement: Zero type errors

4. **Final validation** - Run all checks one final time
   - Commands: `hatch run format`, `hatch run lint`, `hatch run type-check`, `hatch test --cover -v`
   - Requirement: All checks must pass with zero errors

## Contract Decorator Requirements

**Every new public function MUST have:**

1. **`@beartype` decorator** - Runtime type checking
   - Applied to: All public functions (not private `_` functions)
   - Purpose: Automatic runtime type validation
   - Pattern: Place before function definition

2. **`@icontract` decorators** - Runtime contract validation
   - `@require` - Preconditions (input validation)
   - `@ensure` - Postconditions (output validation)
   - Applied to: All public functions with non-trivial logic
   - Purpose: Prevent regressions and document contracts
   - Pattern: Place before `@beartype` decorator

**Example:**

```python
from beartype import beartype
from icontract import require, ensure

@require(lambda x: x > 0, "Input must be positive")
@ensure(lambda result: result > 0, "Output must be positive")
@beartype
def calculate_square(x: int) -> int:
    """Calculate square of positive integer."""
    return x * x
```

**When to add contracts:**

- ✅ Public API functions (exported from modules)
- ✅ Command handlers (CLI command functions)
- ✅ Adapter methods (bridge adapter interface methods)
- ✅ Complex business logic (non-trivial algorithms)
- ❌ Private functions (`_` prefix) - Optional, but recommended for complex logic
- ❌ Simple getters/setters - Optional unless they have validation logic

## Domain Context

- **Brownfield-first**: Designed for legacy code modernization, not greenfield. Reverse-engineer specs from existing code, then enforce contracts to prevent regressions.
- **CLI-first**: Works offline, no account required, no vendor lock-in. No cloud dependencies.
- **Contract-driven**: Runtime enforcement prevents regressions during refactoring. Contracts are extracted from legacy code, not written from scratch.
- **Tool-agnostic**: Bridge adapters support GitHub, GitLab, Linear, Jira, Spec-Kit, OpenSpec, etc. No vendor lock-in.
- **Multi-repository**: Code and specifications can live in different repos. Supports cross-repo workflows.
- **No escape validation**: Quality gates enforced via contracts, not just linting. Contracts prevent regressions that linting cannot catch.

## Important Constraints

- **External repositories**: Must support external repositories (no hardcoded paths)
- **No adoption required**: Must work without SpecFact CLI adoption in target repo
- **Multi-repo support**: Must support multi-repository configurations (code and specs in different repos)
- **Backward compatibility**: Must maintain backward compatibility during modernization
- **Regression prevention**: Must prevent regressions during legacy modernization (via contracts)
- **Offline-first**: Must not require vendor lock-in (offline, local-first, no cloud dependencies)

## External Dependencies

- **OpenSpec**: Specification management (cross-repo support, bridge adapter)
- **Spec-Kit**: Greenfield SDD tool (bridge adapter for compatibility)
- **CrossHair**: Symbolic execution for contract exploration and edge case discovery
- **Specmatic**: API contract testing (future integration)
