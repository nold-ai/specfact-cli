## Context

Registration already separates categorized commands from flat commands in `_register_commands_for_package`. Grouped mode is the default, but the function currently ignores that mode and routes every category-less manifest to `_register_command_flat_path`.

## Decision

Make `_register_commands_for_package` skip category-less packages when grouping is enabled. Do not change discovery, manifest parsing, package loading, integrity policy, or legacy mode in this focused remediation.

This is the smallest guard at the trust boundary immediately before root registry mutation. It also avoids relying on a denylist of former flat aliases, so an attacker cannot squat any other unoccupied root name.

## Alternatives Considered

- **Restore removed flat shims:** rejected because it reintroduces unsupported command behavior and only protects names supplied by installed official bundles.
- **Reserve only former flat names:** rejected because it leaves arbitrary root command squatting possible.
- **Require signatures for all workspace modules:** broader trust-policy change that may be valuable separately but would alter installation and local-development workflows beyond this vulnerability.

## Compatibility and Rollback

Categorized modules and canonical grouped commands are unchanged. Category-less modules continue to register at root only when callers explicitly disable category grouping. Rollback is a single registration-guard revert.

