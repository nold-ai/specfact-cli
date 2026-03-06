# Design: Module Grouping and Category Command Groups

## Context

SpecFact CLI ships 21 modules as flat top-level commands in `src/specfact_cli/modules/`. The marketplace foundation (marketplace-01 archived, marketplace-02 in progress) enables signed, versioned, installable module packages. This change introduces the grouping layer that organises those 21 modules into 5 workflow-domain categories, exposes them through category umbrella commands, and replaces the first-run experience with VS Code-style bundle selection.

**Current State:**

- 21 flat top-level commands registered in bootstrap.py
- No category concept in module-package.yaml
- `specfact init` performs workspace setup with no bundle selection
- `specfact --help` is overwhelming for new users

**Constraints:**

- Must not break existing `specfact <module>` invocations during migration window
- Must work offline (no cloud dependency for grouping logic)
- Must remain backward-compatible with CI/CD pipelines that call flat commands
- Must depend on marketplace-02 dependency resolver for bundle-level dep graph (spec → project, govern → project)
- All new public APIs must carry `@icontract` and `@beartype` decorators

## Goals / Non-Goals

**Goals:**

- Add category metadata to all 21 module-package.yaml files (Phase 1)
- Implement 5 category group Typer apps in `src/specfact_cli/groups/` (Phase 2)
- Update bootstrap.py to mount groups with compat shims for flat commands (Phase 2)
- Add `category_grouping_enabled` config flag (default `true`)
- Add first-run bundle selection to `specfact init` with `--profile` and `--install` flags
- Preserve all existing command paths via deprecation shims

**Non-Goals:**

- Extracting module source code to separate packages (module-migration-02)
- Removing bundled modules from pyproject.toml (module-migration-03)
- Publishing bundles to the marketplace registry (module-migration-02)
- Removing backward-compat shims (module-migration-03)

## Decisions

### Decision 1: Category group architecture — separate `groups/` layer

**Options:**

- **A**: Embed grouping logic directly in bootstrap.py
- **B**: New `src/specfact_cli/groups/` package with one file per category

**Choice: B (dedicated `groups/` layer)**

**Rationale:**

- Clean separation of concerns — bootstrap orchestrates, groups define aggregation
- Each group file is independently testable
- Mirrors the `modules/` structure, making the pattern predictable
- Easier to remove in module-migration-03 (delete groups/ directory)

**Structure:**

```text
src/specfact_cli/groups/
  __init__.py
  project_group.py    # aggregates: project, plan, import_cmd, sync, migrate
  backlog_group.py    # aggregates: backlog, policy_engine
  codebase_group.py   # aggregates: analyze, drift, validate, repro
  spec_group.py       # aggregates: contract, spec (as 'api'), sdd, generate
  govern_group.py     # aggregates: enforce, patch_mode
```

**Group file pattern:**

```python
import typer
from beartype import beartype
from icontract import require

app = typer.Typer(name="code", help="Codebase quality commands.")

@require(lambda: True)  # placeholder; real contracts on member loaders
@beartype
def _register_members() -> None:
    """Lazy-register member module sub-apps."""
    ...
```

### Decision 2: Backward-compat shim strategy

**Options:**

- **A**: Register both flat and grouped commands permanently
- **B**: Register flat commands as shims that delegate to grouped commands
- **C**: Remove flat commands immediately (breaking)

#### Choice: B (shim delegation)

**Rationale:**

- Zero breaking changes for existing scripts
- Deprecation warning in Copilot mode trains users to migrate
- Silent in CI/CD mode (detected from environment)
- Clean removal path: delete shim registrations in module-migration-03

**Implementation:**

```python
# In bootstrap.py, after mounting category groups:
def _register_compat_shims(app: typer.Typer) -> None:
    """Register flat-command shims that delegate to category group equivalents."""
    from specfact_cli.common.modes import is_cicd_mode
    ...
```

### Decision 3: Spec module name collision resolution

The `spec` module's command name (`specfact spec`) collides with the `spec` category group command.

**Choice: Mount the `spec` module as `api` sub-command within the `spec` group**

**Rationale:**

- `specfact spec api validate` is semantically clear (API spec validation)
- The flat shim `specfact spec validate` continues to work during migration window
- Avoids any namespace recursion (spec inside spec group)

**Manifest change in `modules/spec/module-package.yaml`:**

```yaml
bundle_sub_command: api
```

### Decision 4: `category_grouping_enabled` config flag storage

**Choice: Stored in `~/.specfact/config.yaml` under key `category_grouping_enabled: true`**

**Rationale:**

- Consistent with existing specfact config conventions
- Easy to disable per-machine during rollout
- Read once at CLI startup, passed down to bootstrap

### Decision 5: First-run detection mechanism

#### Choice: Check whether any category bundle is installed; if none, treat as first-run

**Rationale:**

- Simple and reliable — no additional state file needed
- Idempotent: re-running init after bundles are installed skips selection
- Compatible with `--install all` legacy flag (bypasses first-run UI)

### Decision 6: Bundle-level dependency resolution at init time

#### Choice: Delegate to marketplace-02 dependency resolver

**Rationale:**

- marketplace-02 owns the dependency resolution contract
- Avoids duplicating resolution logic in init
- At init time, spec and govern bundles automatically pull project bundle as dep
- If marketplace-02 is not yet complete, init can warn and skip dep resolution (graceful degradation)

## Architecture

### Data flow: CLI startup with grouping enabled

```text
specfact <command> <args>
  │
  ├─ cli.py: cli_main()
  │    └─ loads root typer.Typer app
  │
  ├─ registry/bootstrap.py: bootstrap_cli(app)
  │    ├─ reads category_grouping_enabled from config
  │    ├─ if enabled:
  │    │    ├─ groups/codebase_group.app  → app.add_typer(name="code")
  │    │    ├─ groups/backlog_group.app   → app.add_typer(name="backlog")
  │    │    ├─ groups/project_group.app  → app.add_typer(name="project")
  │    │    ├─ groups/spec_group.app     → app.add_typer(name="spec")
  │    │    ├─ groups/govern_group.app   → app.add_typer(name="govern")
  │    │    └─ _register_compat_shims(app)  ← flat shims
  │    └─ core modules always mounted flat: init, auth, module, upgrade
  │
  └─ registry/registry.py: lazy-load member module on invocation
```

### Category group file structure (example: codebase_group.py)

```python
"""Codebase quality category group."""
import typer
from beartype import beartype
from icontract import ensure, require

from specfact_cli.registry.registry import get_module_app

app = typer.Typer(
    name="code",
    help="Codebase quality commands: analyze, drift, validate, repro.",
    no_args_is_help=True,
)

_MEMBERS = ("analyze", "drift", "validate", "repro")

@require(lambda: True)
@ensure(lambda result: result is None)
@beartype
def _register_members() -> None:
    for name in _MEMBERS:
        member_app = get_module_app(name)
        if member_app is not None:
            app.add_typer(member_app, name=name)

_register_members()
```

### module-package.yaml additions

```yaml
# Example: modules/validate/module-package.yaml (additions only)
category: codebase
bundle: specfact-codebase
bundle_group_command: code
bundle_sub_command: validate
```

### Compat shim pattern (bootstrap.py)

```python
def _make_shim(category_group_cmd: str, sub_cmd: str) -> Callable[..., Any]:
    """Return a callback that delegates to the category group sub-command."""
    from specfact_cli.common.modes import is_cicd_mode
    from specfact_cli.common import get_bridge_logger

    logger = get_bridge_logger(__name__)

    def shim(*args: Any, **kwargs: Any) -> None:
        if not is_cicd_mode():
            console.print(
                f"[yellow]Note: `specfact {sub_cmd}` is deprecated. "
                f"Use `specfact {category_group_cmd} {sub_cmd}` instead.[/yellow]"
            )
        # delegate to the group sub-command
        ...

    return shim
```

### First-run init flow

```text
specfact init
  │
  ├─ detect first-run: any category bundle installed? → No
  │
  ├─ Copilot mode?
  │    ├─ Yes → show interactive multi-select UI (rich prompt)
  │    │         user picks bundles or profile preset
  │    │         confirm → install selected bundles via module_installer
  │    └─ No  → skip selection (core-only install)
  │
  └─ --profile / --install flags?
       ├─ --profile <name> → resolve canonical bundle list → install
       └─ --install <list> → parse comma-separated bundle names → install
```

## Risks / Trade-offs

### Risk 1: Spec module name collision causes routing confusion

**Mitigation**: Mount spec module as `api` sub-command within spec group; flat shim `specfact spec <sub>` delegates correctly. Covered by explicit spec in `category-command-groups`.

### Risk 2: CLI startup time regression from group loading

**Mitigation**: Groups use the same lazy-loading pattern as the existing registry — member sub-apps are imported only on first invocation of a sub-command, not at startup.

### Risk 3: `sync` ↔ `plan` circular-ish dependency across group files

**Mitigation**: Both `sync` and `plan` are in the `project` category group — no cross-group dependency. The circular import is intra-group and resolved by Typer's deferred registration.

### Risk 4: Compat shims add noise to `specfact --help`

**Mitigation**: Shim entries are marked `deprecated=True` in Typer; displayed with visual annotation. Users who want a clean help can set `category_grouping_enabled: true` (already default) and accept the new group layout.

### Risk 5: marketplace-02 not yet complete when this change is implemented

**Mitigation**: Phase 1 (metadata only) has no dependency on marketplace-02. Phase 2 (group commands) can be implemented and merged without marketplace-02 bundle dep resolution as long as the bundle dependency installation at init time gracefully degrades to a warning.

## Migration Plan

### Phase 1 — Metadata only (no code movement, no behavior change)

1. Add `category`, `bundle`, `bundle_group_command`, `bundle_sub_command` to all 21 module-package.yaml files
2. Add manifest validation in registry/module_packages.py for new fields
3. Run module signing gate: `hatch run ./scripts/verify-modules-signature.py --require-signature`
4. Re-sign all 21 manifests

### Phase 2 — Category group commands

1. Create `src/specfact_cli/groups/` with 5 group files + `__init__.py`
2. Update `bootstrap.py` to mount groups when `category_grouping_enabled` is `true`
3. Add `_register_compat_shims()` for all 17 non-core flat commands
4. Update `cli.py` to register category groups

### Phase 3 — First-run init enhancement

1. Add `--profile` and `--install` parameters to `specfact init`
2. Implement first-run detection and interactive bundle selection UI
3. Wire bundle installation through existing `module_installer`

### Rollback

1. Set `category_grouping_enabled: false` in `~/.specfact/config.yaml` (immediate, no code change)
2. If code rollback needed: revert `bootstrap.py` (remove group mounting) and delete `groups/` directory

## Open Questions

**Q1: Should the migration window be one major version or time-boxed?**

- Recommendation: One major version (e.g., v0.x → v1.0 removes shims). Easier to communicate in changelog.

**Q2: Should `specfact --help` show shim commands alongside group commands by default?**

- Recommendation: Yes for the migration window, to avoid breaking muscle memory. Add deprecation annotation to shim entries.

**Q3: Should first-run selection be skippable with a `--no-interactive` flag?**

- Recommendation: CI/CD mode auto-detection handles this. Add `--no-interactive` as an explicit opt-out for edge cases.
