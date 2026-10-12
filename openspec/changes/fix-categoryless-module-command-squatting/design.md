## Context

Registration already separates categorized commands from flat commands in `_register_commands_for_package`. Grouped
mode is the default, but the function currently ignores that mode and routes every category-less manifest to
`_register_command_flat_path`.

## Decision

Reject ineligible packages before schema, bridge, protocol, active-import-root and category-mount side effects. Make
registration skip category-less project packages when grouping is enabled. Discovery already preserves the computed
source in metadata; do not trust a YAML source field. Preserve category-less non-project sources and explicit legacy
registration. For permanent core commands, require `_is_builtin_module_package(package_dir)` before creating any loader
in both modes. That check resolves paths against the effective built-in discovery root selected by operator
configuration, so forged categories, names and source labels or escaping symlinks cannot grant authority.

This is the smallest guard at the trust boundary before package registration side effects. It also avoids relying on a
denylist of former flat aliases, so an attacker cannot squat any other unoccupied root name.

## Alternatives Considered

- **Restore removed flat shims:** rejected because it reintroduces unsupported command behavior and only protects names
supplied by installed official bundles.
- **Reserve only former flat names:** rejected because it leaves arbitrary root command squatting possible.
- **Require signatures for all workspace modules:** broader trust-policy change that may be valuable separately but
would alter installation and local-development workflows beyond this vulnerability.

## Compatibility and Rollback

Eligible categorized modules and canonical grouped commands are unchanged. Project packages claiming official category
roots are rejected entirely in both modes. Category-less project modules continue to register unreserved root names
only when callers explicitly disable grouping. Other legacy discovery sources remain compatible. External packages
cannot extend permanent core commands in either mode. This does not sandbox intentionally invoked categorized module
code or make arbitrary workspaces trusted. The related category-command-groups delta reconciles the shipped categorized
behavior; disabled grouping never restores removed flat bundle shims. Rollback restores the coherent registration
patch.
