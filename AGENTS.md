# AGENTS.md

This file provides guidance to coding agents when working with code in this repository.

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

Use `from specfact_cli.common import get_bridge_logger` and avoid `print()` in production command paths. Debug logs go to `~/.specfact/logs/specfact-debug.log` when `--debug` is passed.

## Development Workflow

### Branch Protection

`dev` and `main` are protected. Always work on feature/bugfix/hotfix branches and submit PRs:
- `feature/your-feature-name`
- `bugfix/your-bugfix-name`
- `hotfix/your-hotfix-name`

### Git Worktree Policy (Parallel Development)

Use git worktrees for parallel development branches only.

- Allowed branch types in worktrees: `feature/*`, `bugfix/*`, `hotfix/*`, `chore/*`
- Forbidden in worktrees: `dev`, `main`
- The primary checkout remains the canonical `dev` workspace

Canonical layout:

- Primary checkout: `.../specfact-cli` (tracks `dev`)
- Worktrees root: `.../specfact-cli-worktrees/<branch-type>/<branch-slug>`
- Worktree folder name MUST reflect the branch slug

Preferred helper commands (from repository root):

```bash
scripts/worktree.sh create feature/<branch-slug>
scripts/worktree.sh list
scripts/worktree.sh cleanup feature/<branch-slug>
```

Create a new worktree from `origin/dev`:

```bash
git fetch origin
git worktree add ../specfact-cli-worktrees/feature/<branch-slug> -b feature/<branch-slug> origin/dev
```

Attach an existing local branch to a worktree:

```bash
git fetch origin
git worktree add ../specfact-cli-worktrees/feature/<branch-slug> feature/<branch-slug>
```

Operational rules:

- Never create a worktree for `dev` or `main`
- One branch maps to exactly one worktree path at a time
- Keep branch naming consistent: `<type>/<ticket>-<short-topic>`
- Keep one active OpenSpec change scope per branch where possible
- Create a separate virtual environment inside each worktree (for example, `.venv/`)
- Bootstrap Hatch once per new worktree before running quality gates: `hatch env create`
- Run quick pre-flight checks from the worktree root: `hatch run smart-test-status` and `hatch run contract-test-status`
- If Hatch cannot write to default home/cache paths, set writable overrides (for example `HATCH_DATA_DIR=/tmp/hatch-data` and `HATCH_CACHE_DIR=/tmp/hatch-cache`)
- Run all quality gates from inside the active worktree before commit/PR

Conflict avoidance:

- Check `openspec/CHANGE_ORDER.md` before creating new parallel branches
- Avoid concurrent branches editing the same `openspec/changes/<change-id>/` directory
- Rebase frequently on `origin/dev` in each worktree
- Use `git worktree list` daily to detect stale or incorrect branch/path attachments

Local cleanup after merge to `dev`:

```bash
git fetch origin
git worktree remove ../specfact-cli-worktrees/feature/<branch-slug>
git branch -d feature/<branch-slug>
git worktree prune
```

If remote cleanup is needed:

```bash
git push origin --delete feature/<branch-slug>
```

### Pre-Commit Checklist

Run all steps in order before committing. Every step must pass with no errors.

1. `hatch run format`                # ruff format + autofix
2. `hatch run type-check`            # basedpyright strict
3. `hatch run lint`                  # full lint suite
4. `hatch run yaml-lint`             # YAML + markdown validation
5. `hatch run contract-test`         # contract-first validation
6. `hatch run smart-test`            # targeted test run (use `smart-test-full` for larger modifications)

### OpenSpec Workflow

Before modifying application code, **always** verify that an active OpenSpec change in `openspec/changes/` **explicitly covers the requested modification**. This is the spec-driven workflow defined in `openspec/config.yaml`. Skip only when the user explicitly says `"skip openspec"` or `"implement without openspec change"`.

**Agent MUST NOT apply any code edits** when a fix, change, modification, or edit to any codebase file is requested unless an active OpenSpec change exists that explicitly covers the requested scope. If no such change exists, ask for clarification:

- **a) New change** — create a new OpenSpec change proposal (`/opsx:new`)
- **b) Modify existing** — select and continue an existing change in `openspec/changes/`
- **c) Delta** — add a targeted delta to an existing change's specs

The existence of *any* open change is not sufficient — the change must specifically address the requested modification. Do not proceed until one of the above is resolved.

### Hard Gate: Strict TDD Order (Non-Negotiable)

For any behavior change, the implementation order is mandatory and must be auditable:

1. Update or add spec deltas first.
2. Add/modify tests next, mapped to spec scenarios.
3. Run tests and capture a **failing** result before implementation.
4. Only then modify production code.
5. Re-run tests and quality gates until passing.

Required evidence:

- Create/update `openspec/changes/<change-id>/TDD_EVIDENCE.md` with:
  - test command(s) and timestamp for the pre-implementation failing run
  - short failure summary
  - test command(s) and timestamp for the post-implementation passing run

Agent enforcement:

- Agents MUST NOT edit production code for new/changed behavior until failing-test evidence is recorded.
- If this order cannot be followed, stop and ask the user for explicit override before proceeding.

#### Change Order (`openspec/CHANGE_ORDER.md`)

`openspec/CHANGE_ORDER.md` is the **single source of truth** for change sequencing, module grouping, and inter-change dependencies. Always use it to avoid redundant analysis of `openspec/changes/` folders.

**Read it first** — before creating, implementing, or archiving any change, consult `CHANGE_ORDER.md` to:
- Check which changes are already archived (implemented) and their dates
- Verify hard blockers are resolved before starting implementation
- Understand where a new change fits in module order and wave sequencing

**Keep it updated** — whenever a change lifecycle event occurs, update `CHANGE_ORDER.md` in the same commit:
- **New change created**: add a row to the correct module group table with folder name, GitHub issue link, and blocked-by dependencies
- **Change archived**: move the entry from "Pending" to "Implemented (archived)" with the archive date; update wave status if a wave is now complete
- **Change modified/renamed**: update the folder name and any affected dependency references
- **Blocker resolved**: update the "Blocked by" column (append ✅ to resolved blockers)

Use the `specfact-openspec-workflows` skill as the default execution path for OpenSpec lifecycle work.

- When a Markdown plan exists and the intent is to create a change from that plan, use `.cursor/commands/wf-create-change-from-plan.md` (`/wf-change-from-plan`) to generate the proposal/tasks/spec deltas.
- For plans targeting an internal repository, still run the same workflow but follow its repo rules (for example, skip public GitHub issue creation where required).
- After any change is created or modified, run `.cursor/commands/wf-validate-change.md` (`/wf-validate-change`) and capture its output in `openspec/changes/<change-id>/CHANGE_VALIDATION.md`.
- Treat validation output as required context for dependency and interface impact, including any workflow-provided GitHub issue sync context.

### Version Updates

When bumping version, sync across: `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`. CI/CD auto-publishes to PyPI on merge to `main` only if version exceeds the published one.

**Version semantics (SemVer):**
- `feature/*` branches → **minor** increment (e.g. `0.5.0 → 0.6.0`)
- `bugfix/*` / `hotfix/*` branches → **patch** increment (e.g. `0.5.0 → 0.5.1`)
- Breaking changes or major milestones → **major** increment (requires explicit confirmation)

Always propose the increment type based on the branch name and ask for confirmation before applying the bump.

### Changelog

Keep `CHANGELOG.md` updated with every meaningful change. Update it in the same commit that bumps the version and do not let them diverge.

- Follow [Keep a Changelog](https://keepachangelog.com/) format: `Added`, `Changed`, `Fixed`, `Removed`, `Security`
- Each version entry must match the version in `pyproject.toml`
- Unreleased changes accumulate under `## [Unreleased]` until a version bump

### Commits

Follow Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.

#### Commit Signing (GPG)

- This repository may enforce signed commits (`commit.gpgsign=true`).
- If an agent-run commit fails with `gpg failed to sign the data` in a non-interactive shell, the agent MUST:
  1. Stage all intended files.
  2. Provide the exact `git commit -S -m "<message>"` command for the user to run locally.
  3. Continue with push/PR steps after the user confirms the signed commit exists.
- Agents MUST NOT bypass signing with `--no-gpg-sign` unless the user explicitly requests that override.

### Documentation

Keep docs current with every code change that affects user-facing behaviour.

- Docs source lives in `docs/` and is published to [docs.specfact.io](https://docs.specfact.io) via GitHub Pages (Jekyll)
- **Preserve all front-matter** on every edit (`title`, `layout`, `nav_order`, `permalink`, etc.) and check `docs/_layouts/default.html` and `docs/index.md` before adding or removing front-matter keys
- When a command, option, or behaviour changes, update the corresponding doc page in the same PR
- Broken or outdated docs for users are P0; prefer a small doc fix over shipping undocumented changes

### README Maintenance

`README.md` (repo root) and the docs landing page (`docs/index.md` or `docs/README.md`) must stay in sync with what SpecFact actually does.

- On larger refactorings or feature additions, reconsider the README from an **external/new-user perspective** and lead with value and USP, not internal architecture
- A first-time reader should understand what SpecFact does, why they'd use it, and how to get started within the first screen
- Do not let the README drift from the actual CLI interface or command list

## Code Conventions

- Python 3.11+, line length 120, Google-style docstrings
- `snake_case` for files/modules, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants
- All data structures use Pydantic `BaseModel` with `Field(...)` and descriptions
- CLI commands use `typer.Typer()` + `rich.console.Console()`
- Only write high-value comments and avoid verbose or redundant commentary
- `rich~=13.5.2` is pinned for semgrep compatibility and should not be upgraded without validation

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

## Backlog Command Topology

Keep backlog functionality grouped under the common top-level `backlog` command:

- `specfact backlog ceremony standup`
- `specfact backlog ceremony refinement`
- `specfact backlog analyze-deps`
- `specfact backlog delta status|impact|cost-estimate|rollback-analysis`
- `specfact backlog verify-readiness`

Project-scoped orchestration belongs under `project`:

- `specfact project link-backlog`
- `specfact project health-check`
- `specfact project devops-flow --stage <plan|develop|review|release|monitor> --action <...>`
- `specfact project snapshot|regenerate|export-roadmap`

## Testing

**Contract-first approach**: `@icontract` contracts on public APIs are the primary coverage mechanism (target 80%+ API coverage). Redundant unit tests that only assert input validation or type checks should be removed because contracts and beartype already cover them.

Test structure mirrors source: `tests/unit/`, `tests/integration/`, `tests/e2e/`. Use `@pytest.mark.asyncio` for async tests. Guard environment-sensitive logic with `os.environ.get("TEST_MODE") == "true"`.

## CI/CD

Key workflows in `.github/workflows/`:
- `tests.yml` — contract-first test execution
- `specfact.yml` — contract validation on PR/push (`hatch run specfact repro --verbose`)
- `pr-orchestrator.yml` — coordinates PR workflows
- `build-and-push.yml` — Docker image building (depends on all above passing)
