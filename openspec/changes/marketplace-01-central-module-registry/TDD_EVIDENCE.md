# TDD Evidence: marketplace-01-central-module-registry

## Pre-implementation failing runs

- 2026-02-20 23:06:47 +0100
  - Command: `hatch test --cover -v tests/unit/registry/test_module_discovery.py`
  - Result: failed during collection with `ModuleNotFoundError: specfact_cli.registry.module_discovery`.

- 2026-02-20 23:08:34 +0100
  - Command: `hatch test -- tests/unit/registry/test_marketplace_client.py -v`
  - Result: failed during collection with `ModuleNotFoundError: specfact_cli.registry.marketplace_client`.

- 2026-02-20 23:10:22 +0100
  - Command: `hatch test -- tests/unit/registry/test_module_installer.py -v`
  - Result: failed during collection with `ImportError: cannot import name 'install_module'`.

- 2026-02-20 23:11:42 +0100
  - Command: `hatch test -- tests/unit/modules/module/test_commands.py -v`
  - Result: failed during collection with `ModuleNotFoundError: specfact_cli.modules.module`.

- 2026-02-21 01:23:06 +0100
  - Command: `hatch test -- tests/unit/registry/test_module_installer.py -v`
  - Result: 2 failures before implementation updates:
    - `test_install_module_replaces_existing_module_on_reinstall` remained on version `0.1.0` because installer returned early for existing installs.
    - `test_install_module_rejects_archive_path_traversal` did not raise; unsafe archive member `../outside.txt` was extracted.

## Post-implementation passing runs

- 2026-02-20 23:08:58 +0100
  - Command: `hatch test -- tests/unit/registry/test_marketplace_client.py -v`
  - Result: all tests passed.

- 2026-02-20 23:11:09 +0100
  - Command: `hatch test -- tests/unit/registry/test_module_installer.py -v`
  - Result: all tests passed.

- 2026-02-20 23:12:05 +0100
  - Command: `hatch test -- tests/unit/modules/module/test_commands.py -v`
  - Result: all tests passed.

- 2026-02-20 23:12:38 +0100
  - Command: `hatch test -- tests/unit/registry/test_module_discovery.py tests/unit/registry/test_marketplace_client.py tests/unit/registry/test_module_installer.py tests/unit/modules/module/test_commands.py -v`
  - Result: 20 tests passed.

- 2026-02-21 01:24:00 +0100
  - Command: `hatch test -- tests/unit/registry/test_module_installer.py tests/unit/modules/module_registry/test_commands.py -v`
  - Result: 37 tests passed, including new coverage for reinstall-on-upgrade and archive path traversal rejection.
