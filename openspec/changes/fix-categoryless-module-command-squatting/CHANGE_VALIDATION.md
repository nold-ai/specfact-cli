# Change Validation: fix-categoryless-module-command-squatting

## Result

The source finding is present on HEAD. `_register_commands_for_package` routes category-less packages to flat root registration even when category grouping is enabled, so the proposed registration guard matches current repository reality.

The change scope is minimal and preserves explicitly disabled category-grouping compatibility. It does not overlap the completed `cli-removed-flat-alias-diagnostics` change, which controls error diagnostics after command resolution rather than module registration trust.

## Interface and dependency impact

- **Breaking impact:** category-less package commands stop registering at root in default grouped mode. This is intentional because that surface is undocumented and violates the grouped command contract.
- **Preserved behavior:** categorized modules and explicitly disabled grouping remain unchanged.
- **Dependencies:** no package dependency or public Python API changes.
- **Security boundary:** the guard prevents root registry mutation before a package loader can execute via a squatted command.

## Readiness

- Strict OpenSpec format validation passes.
- GitHub issue #718 is open, labeled, and linked to parent feature #352.
- GitHub project assignment is incomplete because the available token cannot access the organization project. Repository governance therefore blocks production-code implementation until that metadata is completed.
- The sibling internal wiki checkout is unavailable; its source mirror and graph rebuild remain an explicit follow-up task.

