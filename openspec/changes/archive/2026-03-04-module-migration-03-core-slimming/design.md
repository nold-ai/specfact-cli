# Design: Core Package Slimming and Mandatory Profile Selection

## Context

**State after module-migration-02:**

- All 17 non-core module sources are extracted to `specfact-cli-modules/packages/` with correct bundle namespaces
- Five signed official-tier bundles are published in `specfact-cli-modules/registry/index.json`
- Re-export shims (`__getattr__` delegation) remain in `src/specfact_cli/modules/*/src/` for the migration window
- Backward-compat flat command shims are still registered in `bootstrap.py`
- `pyproject.toml` still includes all 21 module directories in the wheel
- `specfact --help` still shows all 21 commands (or 9 category groups) because modules are bundled
- `specfact init --profile <name>` works cosmetically but modules are always available even without it

**After this change:**

- 17 module directories deleted from `src/specfact_cli/modules/`
- Re-export shims deleted (one major version cycle elapsed)
- `pyproject.toml` includes only 3 core module directories
- `bootstrap.py` registers only 3 core modules
- `specfact --help` on a fresh install shows ≤ 5 commands (3 core + at most `module` and `upgrade`)
- `specfact init` enforces bundle selection before workspace use completes

**Constraints:**

- NEVER delete module source before the gate script confirms the bundle is published and verifiable
- `specfact init --install all` in CI/CD must produce a fully-functional install identical to pre-slimming
- All 21 commands must remain reachable post-migration (via category groups after bundle install)
- Offline-first: gate script must support `--skip-download-check` + `SPECFACT_BUNDLE_CACHE_DIR` for air-gapped environments
- All new public APIs: `@icontract` (`@require`, `@ensure`) + `@beartype`

## Goals / Non-Goals

**Goals:**

- Deliver a `specfact-cli` wheel that is 3-module lean
- Make `specfact --help` show ≤ 5 commands on a fresh install
- Enforce mandatory bundle selection in `specfact init`
- Remove the 17 module directories and all backward-compat shims
- Write and run the `scripts/verify-bundle-published.py` gate before any deletion
- Update `pyproject.toml`, `setup.py`, `bootstrap.py`, `cli.py`, and `init/commands.py`

**Non-Goals:**

- Publishing bundles to PyPI as installable Python packages (out of scope for this change)
- Adding new module features (no feature scope, pure extraction and cleanup)
- Changing the marketplace registry schema (module-migration-02 owns that)
- Implementing per-bundle changelogs (future work)

## Decisions

### Decision 1: Shim removal timing

**Question:** Remove re-export shims in the same commit as module directory deletion, or in a separate prior commit?

**Options:**

- **A**: Same commit — source deletion and shim removal in one atomic change
- **B**: Separate prior commit for shim removal only, then deletion commit

#### Choice: A (same commit)

**Rationale:**

- The shims only exist to keep `specfact_cli.modules.*` import paths alive while the module source is still in the package. Once the module directory is deleted, the shim is meaningless — the module doesn't exist in core at all, so there is nothing to re-export.
- Deleting them together is semantically coherent: the moment the source is gone, the shim is gone.
- Having a separate shim-removal commit adds no value because neither the shim nor the source serves any purpose after the bundle is the canonical install path.

### Decision 2: Backward-compat flat shim removal strategy

**Question:** Remove flat shims from `bootstrap.py` by deleting the registration logic, or by making registration conditional on a `legacy_commands_enabled` flag?

**Options:**

- **A**: Hard delete — remove all shim registration code from `bootstrap.py`
- **B**: Conditional flag — add `legacy_commands_enabled: false` to config, allow re-enabling for one more version
- **C**: DeprecationError — register the old commands but raise a `DeprecationError` immediately

#### Choice: A (hard delete)

**Rationale:**

- One major version cycle (from module-migration-01) has elapsed. The deprecation window is closed.
- Keeping a flag adds maintenance surface and signals the shims might come back; they will not.
- Option C is worse UX than a clean "command not found" error with an actionable install message.
- The gate script and actionable error in `cli.py` provide the migration path; shim re-registration does not.

### Decision 3: Mandatory bundle selection enforcement mechanism in `specfact init`

**Question:** How should `specfact init` enforce that at least one bundle is installed?

**Options:**

- **A**: Hard error — exit 1 if no bundles are installed after init completes in CI/CD mode; prompt loop in interactive mode
- **B**: Warning only — print a prominent warning but allow workspace init to complete
- **C**: Post-init check — separate `specfact doctor` command validates bundle state

#### Choice: A (hard error in CI/CD, prompt loop in interactive)

**Rationale:**

- A warning is not an enforcement gate; users will ignore it and then file bugs about missing commands.
- In CI/CD mode, a pipeline that does not install a bundle is misconfigured — hard error surfaces the misconfiguration immediately and is easy to fix.
- In interactive mode, the prompt loop gives the user a chance to confirm core-only intentionally without blocking them completely.
- Option C adds a new command and does not address the root cause at init time.

**Implementation pattern for CI/CD gate in `commands.py`:**

```python
@app.command()
@require(lambda profile: profile is None or profile in VALID_PROFILES, "profile must be a valid preset name")
@beartype
def init_command(
    profile: Optional[str] = typer.Option(None, "--profile", help="Workflow profile preset"),
    install: Optional[str] = typer.Option(None, "--install", help="Comma-separated bundle list or 'all'"),
    # ...
) -> None:
    if _is_cicd_mode() and profile is None and install is None:
        console.print("[red]Error:[/red] In CI/CD mode, --profile or --install is required.")
        console.print("Example: specfact init --profile solo-developer")
        raise typer.Exit(1)
    # ...
```

### Decision 4: Category group mount gating mechanism

**Question:** How should `cli.py` / `bootstrap.py` decide whether to mount a category group?

**Options:**

- **A**: Check installed module registry at startup — mount only groups whose bundle is in the installed registry
- **B**: Attempt import from bundle namespace — if `from specfact_codebase import app` succeeds, mount it
- **C**: Configuration file — user-managed list of enabled groups in `~/.specfact/config.yaml`

#### Choice: A (check installed module registry at startup)

**Rationale:**

- The module registry (marketplace-01) already tracks which bundles are installed. Using it as the authority is consistent with the overall architecture.
- Option B creates an implicit dependency on the bundle being importable from the Python environment — fragile if the bundle is installed to a different virtualenv or path.
- Option C is user-managed and would diverge from the actual installed state; the registry is the source of truth.

**Implementation:**

```python
# In bootstrap.py or cli.py
from specfact_cli.registry.module_registry import get_installed_bundles

def _mount_installed_category_groups(app: typer.Typer) -> None:
    installed = get_installed_bundles()
    for bundle_id, group_factory in CATEGORY_GROUP_FACTORIES.items():
        if bundle_id in installed:
            group_app = group_factory()
            app.add_typer(group_app, name=BUNDLE_GROUP_COMMANDS[bundle_id])
```

### Decision 5: verify-bundle-published.py gate design

**Question:** Should the gate script be a standalone script or integrated into the existing `verify-modules-signature.py`?

**Options:**

- **A**: Separate script (`scripts/verify-bundle-published.py`) — focused on bundle registry verification
- **B**: Extend `verify-modules-signature.py` with `--check-bundle-published` flag
- **C**: Hatch task alias in `pyproject.toml` that runs both scripts

#### Choice: A (separate script) + C (hatch task alias)

**Rationale:**

- The gate's concern (is the bundle published and installable?) is different from the existing script's concern (does the local manifest signature match?). Separate scripts have single-responsibility.
- A Hatch task alias (`hatch run verify-removal-gate`) composites both scripts, making the pre-deletion checklist a single command.

```toml
# pyproject.toml [tool.hatch.envs.default.scripts]
verify-removal-gate = [
    "python scripts/verify-bundle-published.py --modules project,plan,import_cmd,sync,migrate,backlog,policy_engine,analyze,drift,validate,repro,contract,spec,sdd,generate,enforce,patch_mode",
    "python scripts/verify-modules-signature.py --require-signature",
]
```

## Architecture

### Module directory deletion sequence

```text
Pre-deletion:
  1. Run: hatch run verify-removal-gate  (gate exits 0)
  2. Record gate output in TDD_EVIDENCE.md

Deletion (in one commit per bundle):
  Commit A: Delete specfact-project modules (project, plan, import_cmd, sync, migrate)
  Commit B: Delete specfact-backlog modules (backlog, policy_engine)
  Commit C: Delete specfact-codebase modules (analyze, drift, validate, repro)
  Commit D: Delete specfact-spec modules (contract, spec, sdd, generate)
  Commit E: Delete specfact-govern modules (enforce, patch_mode)

  Each commit: also update pyproject.toml + setup.py includes for that bundle's modules.

Post-deletion:
  Final commit: Update bootstrap.py (shim removal, 3-core-only), cli.py (conditional mount),
                init/commands.py (mandatory selection gate), CHANGELOG.md, version bump.
```

### bootstrap.py after slimming

```python
# BEFORE (module-migration-02 state): registers 21 modules + flat shims
# AFTER (this change): registers 3 core modules only

from specfact_cli.modules.init.src.init import app as init_app
from specfact_cli.modules.module_registry.src.module_registry import app as module_registry_app
from specfact_cli.modules.upgrade.src.upgrade import app as upgrade_app


@beartype
def bootstrap_modules(cli_app: typer.Typer) -> None:
    """Register the 3 permanent core modules."""
    cli_app.add_typer(init_app, name="init")
    cli_app.add_typer(module_registry_app, name="module")
    cli_app.add_typer(upgrade_app, name="upgrade")
    _mount_installed_category_groups(cli_app)
```

### verify-bundle-published.py high-level flow

```text
scripts/verify-bundle-published.py --modules <comma-list>
  │
  ├─ @require: module_names is non-empty list of strings
  ├─ @require: index.json exists at SPECFACT_CLI_MODULES_REGISTRY_PATH
  │
  ├─ For each module_name:
  │   ├─ Read src/specfact_cli/modules/<name>/module-package.yaml → get `bundle` field
  │   ├─ Look up bundle in index.json → get entry (error if missing)
  │   ├─ Check entry has: checksum_sha256, signature_url, download_url, tier=official
  │   ├─ Verify Ed25519 signature (uses existing crypto_validator logic)
  │   ├─ Unless --skip-download-check: verify download_url returns 200
  │   └─ Append row to results table
  │
  ├─ Print Rich table: module | bundle | version | signature | download | status
  │
  └─ Exit 0 if all PASS, exit 1 if any FAIL
```

### Sequence: `specfact init` mandatory bundle selection (interactive mode)

```text
specfact init (interactive, fresh install)
  │
  ├─ Check: are any bundles installed? (get_installed_bundles() → empty)
  │
  ├─ Display welcome banner + bundle selection UI (from first-run-selection spec)
  │   └─ User interaction loop:
  │       ├─ User selects ≥1 bundle → proceed to install
  │       └─ User selects 0 bundles → display confirmation prompt:
  │           "Continue with core only? [y/N]:"
  │           ├─ 'y' → continue with core, show install tip, exit 0
  │           └─ 'n' / Enter → loop back to selection UI
  │
  ├─ For each selected bundle:
  │   ├─ Resolve bundle dependencies (marketplace-02 resolver)
  │   └─ module_installer.install_module(bundle_id)
  │
  ├─ Proceed with workspace directory setup
  └─ Print installed bundle summary, exit 0
```

### Sequence: `specfact init` in CI/CD mode

```text
specfact init --profile solo-developer (CI/CD mode)
  │
  ├─ _is_cicd_mode() → True (env var or --cicd flag)
  ├─ profile = "solo-developer" → bundles = [specfact-codebase]
  ├─ For each bundle: module_installer.install_module()
  ├─ Workspace setup
  └─ Exit 0

specfact init (CI/CD mode, no --profile / --install)
  │
  ├─ _is_cicd_mode() → True
  ├─ profile = None, install = None
  ├─ Console.print(error message with example)
  └─ Exit 1
```

## Risks / Trade-offs

### Risk 1: Users upgrade specfact-cli without running `specfact init` post-upgrade

**Impact:** All category group commands become unavailable after upgrade, even if user had them before.

**Mitigation:**

- CHANGELOG entry explicitly warns that upgrading to this version requires running `specfact init --install all` (or `specfact module install` for individual bundles).
- `specfact upgrade` command checks whether installed bundles are still present after the upgrade and prints an actionable warning if any are missing.
- Documentation update (getting-started, installation guide) prominently covers the upgrade path.

### Risk 2: The gate script falsely passes due to stale cached registry index

**Impact:** A module is deleted before the live marketplace bundle is available to users (e.g., index.json is cached from a prior state).

**Mitigation:**

- Gate script always reads from the live `specfact-cli-modules/registry/index.json` on disk (not from a network cache).
- When `--skip-download-check` is NOT set, the gate additionally resolves `download_url` to confirm the tarball is live.
- Running the gate after a fresh `git pull` of `specfact-cli-modules` ensures index.json is current.

### Risk 3: specfact-spec and specfact-govern users lose access if specfact-project is not auto-installed

**Impact:** `specfact init --profile api-first-team` installs `specfact-spec` but if the dependency resolver (marketplace-02) fails to auto-install `specfact-project`, the spec commands break.

**Mitigation:**

- Integration test explicitly covers this scenario (init api-first-team → verify project bundle auto-installed).
- The bundle install logic reads `bundle_dependencies` from the bundle manifest and fails loudly before installing the requested bundle if a dependency install fails.

### Risk 4: Existing CI/CD pipelines break after upgrade (no --profile or --install)

**Impact:** A pipeline that previously relied on bundled modules being always-available will fail after the upgrade.

**Mitigation:**

- The `specfact init` CI/CD mode gate exits 1 immediately with a clear error message and an example fix.
- The getting-started docs and upgrade guide are updated before this change ships.
- The CHANGELOG includes a migration section with before/after pipeline examples.

## Open Questions

**Q1: Should `specfact upgrade` automatically re-install bundles after a major version upgrade?**

- Recommendation: No automatic reinstall (that would require network access the user may not have at upgrade time). Instead, `specfact upgrade` warns about missing bundles and prints the `specfact init --install all` command. The user runs it explicitly.

**Q2: Should the gate script be run in CI as a required workflow step?**

- Recommendation: Yes, as a separate GitHub Actions step in the `build-and-push.yml` workflow that runs before the wheel is built. This ensures the gate is never bypassed even if a developer runs the deletion locally.

**Q3: Should bundle installation state be persisted across virtualenvs?**

- Recommendation: Bundle state is already tracked by the marketplace-01 module registry in `~/.specfact/modules/`. This is not virtualenv-scoped. No change needed for this question.
