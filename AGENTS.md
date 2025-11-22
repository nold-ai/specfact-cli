# SpecFact CLI - Repository Guidelines

## Project Structure & Module Organization

- `src/specfact_cli/` contains the CLI command implementation
  - `cli.py` - Main Typer application entry point
  - `commands/` - Command modules (import, analyze, plan, compare, enforce, repro)
  - `models/` - Pydantic data models (plan, protocol, deviation)
  - `generators/` - Code generators (protocol, plan, report)
  - `validators/` - Validation logic (schema, contract, FSM)
  - `utils/` - Shared utilities (git, YAML, console)
- `src/common/` contains shared utilities (logger_setup, platform_base)
- `tests/` mirrors CLI modules via `unit/`, `integration/`, and `e2e/`
- `tools/` hosts contract automation and semgrep rules
- `resources/` contains templates, schemas, and mapping files

## Build, Test, and Development Commands

### YAML and Workflows: Formatting and Linting

- Format everything: `hatch run yaml-fix-all`
- Check everything: `hatch run yaml-check-all`
- Format workflows only: `hatch run workflows-fmt`
- Lint workflows (actionlint): `hatch run workflows-lint`

### Contract-First Testing (Recommended)

- `hatch run contract-test` runs the contract-first test workflow (auto-detect best level)
- Contract validation: `hatch run contract-test-contracts` (runtime contract validation)
- Contract exploration: `hatch run contract-test-exploration` (CrossHair exploration)
- Scenario tests: `hatch run contract-test-scenarios` (integration/E2E with contract references)
- Full contract suite: `hatch run contract-test-full` (all contract-first layers)
- Status check: `hatch run contract-test-status`

### Legacy Smart Testing (Backward Compatibility)

- `hatch test --cover -v` runs tests with coverage
- Incremental levels: `hatch run smart-test-unit`, `hatch run smart-test-folder`, `hatch run smart-test-integration`

### Development Tools

- Lint/format: `hatch run lint` (black, isort, basedpyright, ruff, pylint)
- Format only: `hatch run format`
- Type check: `hatch run type-check` (basedpyright)
- Dev shell: `hatch shell`

## Coding Style & Naming Conventions

- Python 3.11+ with 4-space indentation and Black line length 120
- Apply Google-style docstrings and full type hints
- Use `common.logger_setup.get_logger()` for logging, avoid `print()`
- Name files and modules in `snake_case`; classes stay `PascalCase`, constants `UPPER_SNAKE_CASE`

## Testing Guidelines

### Contract-First Approach (Recommended)

- **Runtime contracts**: Use `@icontract` decorators on all public APIs
- **Type validation**: Use `@beartype` for runtime type checking
- **Contract exploration**: Use CrossHair to discover counterexamples
- **Scenario tests**: Focus on CLI command workflows with contract references
- **Test diet**: Remove redundant unit tests as contracts provide the same coverage

### Unit Testing (Backward Compatibility)

- Place tests alongside modules (`tests/unit/specfact_cli/test_<component>.py`)
- Use pytest with `@pytest.mark.asyncio` for async tests
- Ensure environment-sensitive logic guards `os.environ.get("TEST_MODE") == "true"`

## Commit & Pull Request Guidelines

- **Branch Protection**: This repository has branch protection enabled for `dev` and `main` branches. All changes must be made via Pull Requests:
  - **Never commit directly to `dev` or `main`** - create a feature/bugfix/hotfix branch instead
  - Create a feature branch: `git checkout -b feature/your-feature-name`
  - Create a bugfix branch: `git checkout -b bugfix/your-bugfix-name`
  - Create a hotfix branch: `git checkout -b hotfix/your-hotfix-name`
  - Push your branch and create a PR to `dev` or `main`
  - All PRs must pass CI/CD checks before merging
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)
- **Contract-first workflow**: Before pushing, run `hatch run format`, `hatch run lint`, and `hatch run contract-test`
- PRs should link to CLI-First Strategy docs, describe contract impacts, and include tests
- Attach contract validation notes and screenshots/logs when behavior changes
- **Version Updates**: When updating the version in `pyproject.toml`, ensure it's newer than the latest PyPI version. The CI/CD pipeline will automatically publish to PyPI after successful merge to `main` only if the version is newer. Sync versions across `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__py`

## CLI Command Development Notes

- All commands extend `typer.Typer()` for consistent CLI interface
- Use `rich.console.Console()` for beautiful terminal output
- Validate inputs with Pydantic models at command boundaries
- Apply `@icontract` decorators to enforce contracts at runtime
- Use `@beartype` for automatic type checking
- Handle errors gracefully with try/except and user-friendly error messages

## Data Model Conventions

- Use Pydantic `BaseModel` for all data structures
- Add contracts with `@require` and `@ensure` decorators
- Include `Field` validators for complex validation logic
- Document all models with docstrings and field descriptions

## CLI Command Pattern Example

```python
import typer
from pathlib import Path
from icontract import require, ensure
from beartype import beartype
from rich.console import Console
from pydantic import BaseModel

app = typer.Typer()
console = Console()

class AnalysisConfig(BaseModel):
    """Configuration for code analysis."""
    repo_path: Path
    confidence: float = 0.5
    shadow_only: bool = False

@app.command()
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@ensure(lambda result: result.success, "Analysis must succeed")
@beartype
def analyze(
    repo_path: Path = typer.Argument(..., help="Path to repository"),
    confidence: float = typer.Option(0.5, help="Minimum confidence score"),
    shadow_only: bool = typer.Option(False, help="Shadow mode only"),
) -> AnalysisResult:
    """
    Analyze repository and generate plan bundle.
    
    Args:
        repo_path: Path to the repository to analyze
        confidence: Minimum confidence score (0.0-1.0)
        shadow_only: If True, don't enforce, just observe
        
    Returns:
        Analysis result with generated plan bundle
    """
    config = AnalysisConfig(
        repo_path=repo_path,
        confidence=confidence,
        shadow_only=shadow_only
    )
    
    console.print(f"[bold]Analyzing {repo_path}...[/bold]")
    
    # Implementation here
    return AnalysisResult(success=True)
```

## Project-Specific Patterns

### Contract Decorators

```python
from icontract import require, ensure, invariant
from beartype import beartype

@invariant(lambda self: self.version == "1.0")
class PlanBundle:
    """Plan bundle with contract enforcement."""
    version: str
    features: list[Feature]
    
    @require(lambda feature: feature.key.startswith("FEATURE-"))
    @ensure(lambda result: result is not None)
    @beartype
    def add_feature(self, feature: Feature) -> bool:
        """Add feature with contract validation."""
        self.features.append(feature)
        return True
```

### Rich Console Output

```python
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

# Progress bars
for item in track(items, description="Processing..."):
    process(item)

# Tables
table = Table(title="Deviations")
table.add_column("Type", style="cyan")
table.add_column("Severity", style="magenta")
table.add_column("Description", style="green")

for deviation in deviations:
    table.add_row(deviation.type, deviation.severity, deviation.description)

console.print(table)

# Status messages
console.print("[bold green]✓[/bold green] Analysis complete")
console.print("[bold red]✗[/bold red] Validation failed")
```

## Distribution & Packaging

- Package name: `specfact-cli`
- CLI command: `specfact`
- PyPI distribution: `pip install specfact-cli`
- uvx usage: `uvx specfact-cli@latest <command>` (recommended) or `uvx --from specfact-cli specfact <command>`
- Container: `docker run ghcr.io/nold-ai/specfact-cli:latest`

## Success Criteria

### Code Quality

- **Type coverage**: 100% with basedpyright strict mode
- **Contract coverage**: All public APIs have `@icontract` decorators
- **Test coverage**: Scenario tests cover all CLI commands
- **Zero warnings**: Clean basedpyright, ruff, and pylint output

### CLI User Experience

- **Fast**: Commands complete in < 5 seconds for typical repos
- **Clear**: Rich console output with progress bars and tables
- **Helpful**: Comprehensive help text and error messages
- **Reliable**: Contract validation prevents invalid inputs

## Related Documentation

- **[README.md](./README.md)** - Project overview and quick start
- **[Contributing Guide](./CONTRIBUTING.md)** - Contribution guidelines and workflow
- **[Testing Guide](./.cursor/rules/testing-and-build-guide.mdc)** - Testing procedures
- **[Python Rules](./.cursor/rules/python-github-rules.mdc)** - Development standards

---

**Trademarks**: All product names, logos, and brands mentioned in this document are the property of their respective owners. NOLD AI (NOLDAI) is a registered trademark (wordmark) at the European Union Intellectual Property Office (EUIPO). See [TRADEMARKS.md](./TRADEMARKS.md) for more information.
