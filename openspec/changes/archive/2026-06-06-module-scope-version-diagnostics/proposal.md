## Why

A key user reported module conflicts and version mismatches when SpecFact modules exist in both project-local and user scopes across split repositories and monorepos. Today project scope correctly wins, but lower-priority copies and implicit development source roots are hard to see, and declared module dependency version ranges are not enforced consistently.

## What Changes

- Add a user-facing module diagnostics command that shows effective and shadowed module copies across project, user, marketplace, custom, and development source roots.
- Surface exact module versions, origins, paths, and recovery guidance when duplicate module ids exist.
- Enforce versioned module dependency requirements from module manifests during marketplace install and command registration.
- Preserve current project-over-user precedence; this change makes mismatches visible and prevents incompatible dependency sets from loading silently.

## Capabilities

### New Capabilities

- `module-scope-diagnostics`: Diagnose effective module origin, shadowed duplicates, development source roots, and version mismatch recovery steps.

### Modified Capabilities

- `module-packages`: Module registration enforces declared module dependency version ranges instead of checking presence only.
- `module-installation`: Module install enforces declared bundle dependency version ranges after dependency discovery/install.

## Impact

- Affected code: module discovery diagnostics, `specfact module` command surface, module dependency validation, and marketplace install dependency handling.
- Affected tests: unit tests for module diagnostics output, registration skip behavior, and install-time dependency version mismatch handling.
- Documentation: module installation/marketplace docs should mention diagnostics and duplicate-scope remediation.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **Parent Feature**: [#353](https://github.com/nold-ai/specfact-cli/issues/353)
- **Change User Story**: [#565](https://github.com/nold-ai/specfact-cli/issues/565)
- **GitHub Issue**: [#565](https://github.com/nold-ai/specfact-cli/issues/565)
- **Issue Relationships**: `#565` is a sub-issue of Feature `#353`; Feature `#353` is a sub-issue of Epic `#194`.
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: GitHub story, labels, parent relationship, and source tracking synced
- **Sanitized**: false
