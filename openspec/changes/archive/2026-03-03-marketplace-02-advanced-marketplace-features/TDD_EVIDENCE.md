# TDD Evidence: marketplace-02-advanced-marketplace-features

## 2. Dependency resolution (dependency_resolver + tests)

### Pre-implementation (failing tests)

- **Command**: `hatch run python -m pytest tests/unit/registry/test_dependency_resolver.py -v`
- **Result**: ImportError (module dependency_resolver did not exist).

### Post-implementation (passing tests)

- **Command**: `hatch run python -m pytest tests/unit/registry/test_dependency_resolver.py -v`
- **Result**: 5 passed.
- **Summary**: Created `src/specfact_cli/registry/dependency_resolver.py` with `resolve_dependencies()`, `DependencyConflictError`, pip-compile integration, fallback to basic resolver, and `tests/unit/registry/test_dependency_resolver.py` with aggregation, conflict detection, fallback, and error message tests.

## 2.3 Install command integration (skip_deps, force)

### Post-implementation (passing)

- **Command**: `hatch test tests/unit/registry/test_dependency_resolver.py tests/unit/registry/test_module_installer.py -v`
- **Result**: 28 passed.
- **Summary**: Extended `install_module()` with `skip_deps` and `force`; added dependency resolution after manifest parse (discover_all_modules + new module, then resolve_dependencies; on DependencyConflictError re-raise unless force). Added `--skip-deps` and `--force` to module registry install command. Tests patched to mock _pip_tools_available where pip-tools path is required.


## 3. Alias system (alias_manager + module_registry + CLI resolution)

### Post-implementation (passing)

- **Tests**: `hatch test tests/unit/registry/test_alias_manager.py -v` — 9 passed.
- **Summary**: Added `src/specfact_cli/registry/alias_manager.py` (get_aliases_path, create_alias, list_aliases, remove_alias, resolve_command; JSON under ~/.specfact/registry/aliases.json; shadow built-in check with --force). Added alias subcommand group to module_registry (alias create/list/remove). Integrated resolve_command into cli.py lazy delegate so aliased command names resolve to module command before get_typer.


## 4. Custom registries (custom_registries + marketplace_client + commands)

### Post-implementation (passing)

- **Tests**: `hatch test tests/unit/registry/test_custom_registries.py -v` — 8 passed.
- **Summary**: Added `src/specfact_cli/registry/custom_registries.py` (get_registries_config_path, add_registry, list_registries, remove_registry, fetch_all_indexes; YAML at ~/.specfact/config/registries.yaml; official registry always first; trust always/prompt/never). Extended `marketplace_client.fetch_registry_index(index_url=None, registry_id=None)` to resolve registry by id from custom_registries. Added add-registry, list-registries, remove-registry commands to module_registry. Search command uses fetch_all_indexes() and shows Registry column.


## 5. Namespace enforcement (module_installer)

### Post-implementation (passing)

- **Tests**: New tests in test_module_installer.py: test_install_module_rejects_invalid_namespace_format, test_install_module_accepts_valid_namespace_format, test_install_module_namespace_collision_raises. All 26 module_installer tests pass.
- **Summary**: Added _validate_marketplace_namespace_format(module_id) (regex ^[a-z][a-z0-9-]*/[a-z][a-z0-9-]+$), _check_namespace_collision(module_id, final_path, reinstall) using .specfact-registry-id; call both in install_module(); write REGISTRY_ID_FILE after successful install. Marketplace modules must use namespace/name; collision raises ValueError with message suggesting alias or uninstall.


## 6. Module publishing automation (publish-module.py + workflow)

### Pre-implementation (failing tests)

- **Timestamp**: `2026-02-27T07:43:31Z`
- **Command**: `hatch run pytest tests/unit/scripts/test_update_registry_index.py -q`
- **Result**: 2 failed (`FileNotFoundError: scripts/update-registry-index.py` did not exist).

### Post-implementation (passing + workflow simulation)

- **Script**: `scripts/publish-module.py` — validates manifest (name, version, commands; optional namespace/publisher/tier), builds tarball, writes `.sha256`, optional `--sign` and `--index-fragment`. Contract fixes: `@require` lambdas use correct parameter names (`manifest_path`, `tarball_path`).
- **Script**: `scripts/update-registry-index.py` — upserts entry fragment into `registry/index.json`, keeps module IDs deterministic via sorted order, and emits change flag for workflow branching.
- **Timestamp**: `2026-02-27T07:42:08Z`
- **Command**: `hatch run pytest tests/unit/scripts/test_update_registry_index.py -q`
- **Result**: 2 passed.
- **Workflow (implemented)**: `.github/workflows/publish-modules.yml` now writes `dist/registry-entry.yaml`, checks out `nold-ai/specfact-cli-modules`, updates `registry/index.json`, and creates a registry PR via `gh pr create` when index changed.
- **Local repo simulation**:
  - Publish command: `python scripts/publish-module.py <sample-module> -o <dist> --index-fragment <dist>/registry-entry.yaml`
  - Index update command: `python scripts/update-registry-index.py --index-path <test-repo>/registry/index.json --entry-fragment <dist>/registry-entry.yaml --changed-flag <tmp>/changed.txt`
  - Result: `CHANGED=true`, branch `auto/publish-nold-ai-backlog-test`, commit `chore(registry): publish nold-ai/backlog v0.1.0`, index contains `nold-ai/backlog@0.1.0`.


### Re-signing module_registry for full tests

To run `test_cli_module_help_exits_zero` and `test_module_discovery_registers_commands_from_manifests` without skip/verify patch (e.g. after changing module_registry), set:

- `SPECFACT_MODULE_PRIVATE_SIGN_KEY` – PEM private key (inline)
- `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE` – passphrase if the key is encrypted

Then run:

```bash
hatch run python scripts/sign-modules.py src/specfact_cli/modules/module_registry/module-package.yaml
```

The publish-modules workflow uses the same env vars (via repository secrets) to optionally sign the manifest before packaging.
