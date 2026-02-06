# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SpecFact CLI is a Python CLI tool for agile DevOps teams. It keeps backlogs, specs, tests, and code in sync with contract-driven development, validation, and enforcement. Built with Typer + Rich, using Hatch as the build system. Python 3.11+.

## Essential Commands

```bash
# Development environment
pip install -e ".[dev]"
hatch shell

# Format & lint (run after every code change, in this order)
hatch run format                    # ruff format + fix
hatch run type-check                # basedpyright strict mode
hatch run contract-test             # contract-first validation (primary)
hatch test --cover -v               # full pytest suite

# Contract-first testing layers
hatch run contract-test-contracts   # runtime contract validation only
hatch run contract-test-exploration # CrossHair symbolic execution
hatch run contract-test-scenarios   # integration/E2E with contract refs
hatch run contract-test-full        # all layers
hatch run contract-test-status      # coverage status report

# Run a single test file
hatch test -- tests/unit/specfact_cli/test_example.py -v

# Lint subsystems
hatch run lint                      # full lint suite
hatch run governance                # pylint detailed analysis
hatch run yaml-lint                 # YAML validation
hatch run lint-workflows            # GitHub Actions actionlint

# Code scanning
hatch run scan-all                  # semgrep analysis
```

## Architecture

### Modular Command Registry with Lazy Loading

The CLI uses a module package system in `src/specfact_cli/modules/`. Each module is a self-contained package:

```
modules/{name}/
  module-package.yaml    # metadata: name, version, commands, dependencies
  src/{name}/
    __init__.py
    main.py              # typer.Typer app with command definitions
```

The registry (`src/specfact_cli/registry/`) discovers modules at startup but defers imports until a command is actually invoked. `bootstrap.py` registers all modules; `registry.py` manages lazy loading; `module_packages.py` handles discovery from `module-package.yaml` files.

**Entry flow**: `cli.py:cli_main()` → Typer app with global options → `ProgressiveDisclosureGroup` for help → lazy-loaded command groups from registry.

### Contract-First Development

All public APIs must use `@icontract` decorators (`@require`, `@ensure`, `@invariant`) and `@beartype` for runtime type checking. CrossHair discovers counterexamples via symbolic execution. Contracts are the primary validation mechanism; traditional unit tests are secondary.

### Key Subsystems

- **`models/`** - Pydantic BaseModel classes for all data structures
- **`parsers/`**, **`analyzers/`** - Code analysis
- **`generators/`** - Code/spec generation using Jinja2 templates from `resources/templates/`
- **`validators/`** - Schema, contract, FSM validation
- **`adapters/`** - Bridge pattern for tool integrations (GitHub, Azure DevOps, Jira, Linear)
- **`modes/`** - Operational modes: CICD (fast, deterministic, non-interactive) vs Copilot (interactive, IDE-aware). Auto-detected from environment.
- **`resources/`** - Bundled prompts, templates, schemas, mappings (force-included in wheel)

### Logging

Use `from specfact_cli.common import get_bridge_logger` — never `print()`. Debug logs go to `~/.specfact/logs/specfact-debug.log` when `--debug` is passed.

## Development Workflow

### Branch Protection

`dev` and `main` are protected. Always work on feature/bugfix/hotfix branches and submit PRs:
- `feature/your-feature-name`
- `bugfix/your-bugfix-name`
- `hotfix/your-hotfix-name`

### Post-Change Checklist

1. `hatch run format`
2. `hatch run type-check`
3. `hatch run contract-test`
4. `hatch test --cover -v`

### OpenSpec Workflow

Before modifying application code, check if an OpenSpec change exists in `openspec/`. This is the spec-driven workflow defined in `openspec/config.yaml`. Skip only when explicitly told ("skip openspec", "direct implementation", "simple fix").

### Version Updates

When bumping version, sync across: `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`. CI/CD auto-publishes to PyPI on merge to `main` only if version exceeds the published one.

### Commits

Follow Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.

## Code Conventions

- Python 3.11+, line length 120, Google-style docstrings
- `snake_case` for files/modules, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants
- All data structures use Pydantic `BaseModel` with `Field(...)` and descriptions
- CLI commands use `typer.Typer()` + `rich.console.Console()`
- Only write high-value comments; avoid verbose or redundant commentary
- `rich~=13.5.2` is pinned for semgrep compatibility — do not upgrade without checking

## CLI Command Pattern

```python
import typer
from beartype import beartype
from icontract import require, ensure
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@beartype
def my_command(
    repo_path: Path = typer.Argument(..., help="Path to repository"),
) -> None:
    """Command docstring."""
    console.print("[bold]Processing...[/bold]")
```

## Testing

**Contract-first approach**: `@icontract` contracts on public APIs are the primary coverage mechanism (target 80%+ API coverage). Redundant unit tests that merely assert input validation or type checks should be removed — contracts and beartype handle that.

Test structure mirrors source: `tests/unit/`, `tests/integration/`, `tests/e2e/`. Use `@pytest.mark.asyncio` for async tests. Guard environment-sensitive logic with `os.environ.get("TEST_MODE") == "true"`.

## CI/CD

Key workflows in `.github/workflows/`:
- `tests.yml` — contract-first test execution
- `specfact.yml` — contract validation on PR/push (`hatch run specfact repro --verbose`)
- `pr-orchestrator.yml` — coordinates PR workflows
- `build-and-push.yml` — Docker image building (depends on all above passing)
