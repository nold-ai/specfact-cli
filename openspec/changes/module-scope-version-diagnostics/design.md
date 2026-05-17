## Overview

Keep module precedence deterministic while making the effective runtime explainable. The CLI will continue to select the first discovered module id by source priority, but diagnostics will expose duplicate copies and version drift. Dependency enforcement will use manifest metadata already parsed by the runtime.

## Decisions

- Add `specfact module doctor [MODULE_ID] [--repo PATH]` as the focused diagnostic entrypoint instead of overloading `module list`.
- Use metadata-only discovery with shadowed duplicates retained, so diagnostics do not import module command code.
- Report development source roots from `SPECFACT_MODULES_REPO`, `SPECFACT_CLI_MODULES_REPO`, and `SPECFACT_MODULES_ROOTS` when configured because those can affect Python import resolution even when install manifests come from `.specfact/modules`.
- Enforce versioned module dependencies with `packaging.specifiers.SpecifierSet` and `packaging.version.Version`; malformed specifiers remain non-blocking with debug logging, matching existing `core_compatibility` tolerance.
- Install-time enforcement checks existing dependencies before accepting them, installs missing dependencies as today, then validates the installed manifest version.

## Risks

- Users with stale duplicate installs may see new warnings or skipped modules. Mitigation: diagnostics include exact uninstall/reinstall guidance.
- Marketplace install cannot select the newest version satisfying a range yet. Mitigation: install the normal resolved artifact, then fail with an actionable version mismatch if it does not satisfy the manifest requirement.
