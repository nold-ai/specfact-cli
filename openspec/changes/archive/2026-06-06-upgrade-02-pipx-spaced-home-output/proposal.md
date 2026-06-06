## Why

Issue #570 shows `specfact upgrade` printing pipx's macOS warning about spaces in `PIPX_HOME` after a successful upgrade. That upstream warning makes a valid SpecFact upgrade look unhealthy, even though the command completed and the user cannot fix it from inside SpecFact.

## What Changes

- Suppress the known benign pipx spaced-home warning block when `pipx upgrade specfact-cli` exits successfully.
- Preserve pipx stdout and stderr on failed upgrades and replay partial child output on timeouts so real diagnostics are not hidden.
- Keep existing SpecFact OS-error handling unchanged.
- Add unit coverage and real-world validation with a macOS-style path containing spaces.
- Preserve existing pip, uv, and uvx upgrade behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `upgrade-command`: `specfact upgrade` output handling distinguishes benign successful pipx environment warnings from actionable upgrade diagnostics.

## Impact

- Affected code: `src/specfact_cli/modules/upgrade/src/commands.py`.
- Affected tests: upgrade command unit tests and a subprocess-backed validation scenario.
- Public behavior: successful pipx upgrades no longer show the known spaced-home warning; failed upgrades and timeouts still show child-process diagnostics when the child process provides them.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **Parent Feature**: [#375](https://github.com/nold-ai/specfact-cli/issues/375)
- **Parent Epic**: [#285](https://github.com/nold-ai/specfact-cli/issues/285)
- **Change Issue**: [#572](https://github.com/nold-ai/specfact-cli/issues/572)
- **GitHub Issue**: [#570](https://github.com/nold-ai/specfact-cli/issues/570)
- **Issue Relationships**: `#572` is a sub-issue of Feature `#375`; `#570` is blocked by `#572`.
- **Project Assignment**: SpecFact CLI project, Todo
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: GitHub story, labels, parent relationship, dependency relationship, and source tracking synced
- **Sanitized**: false
