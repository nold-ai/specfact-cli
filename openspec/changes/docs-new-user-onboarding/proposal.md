## Why

User feedback and direct testing reveal two distinct user cohorts arriving at docs.specfact.io with
very different mental models:

**Vibe coders** (new, non-Python-expert audience): heard "validate your vibe code with specfact",
want one command, want to see results in seconds, have no patience for install guides, module
concepts, or architecture diagrams. Their question is: *what do I run right now?*

**Experienced developers**: understand pip, virtual envs, profiles, and module systems. They can
navigate the existing docs. The current docs already work for them — the problem is these users
are not the ones being lost.

The current docs are built entirely for the second group. The first group bounces immediately
because: (1) the homepage hero uses platform-internal vocabulary before showing any command,
(2) the `code review run` command — the single highest-impact entry point for vibe coders — is
not mentioned on the homepage at all, (3) the uvx path is listed under "Option 1" with an
immediate "Limitations" warning that actively discourages it, (4) the path cards group users by
persona and product dimension rather than by what they want to do right now.

The intended vibe-coder entry sequence is:
```bash
uvx specfact-cli init --profile solo-developer           # once — should install modules
uvx specfact-cli code review run --path . --scope full   # the "wow" command
```
This sequence should work in ~10 seconds with no pip install and no virtual environment. However,
direct testing reveals it is **completely broken** due to three bugs:

**Bug 1 — `init --profile solo-developer` installs nothing**: Running this command reports
"Bootstrap complete. Modules discovered: 8 (enabled=8)" but installs no workflow modules.
`code review run` still fails with "Command 'code' is not installed" immediately after.

**Bug 2 — `module install` fails via uvx**: Running `specfact module install nold-ai/specfact-code-review`
under uvx fails with "No module named pip" because the uvx-isolated environment has no pip.
There is currently no working path to install modules via uvx on a fresh machine.

**Bug 3 — profile `solo-developer` is incomplete**: Even if install were working, `solo-developer`
maps to `specfact-codebase` in the docs, but `code review run` requires TWO modules:
`nold-ai/specfact-codebase` AND `nold-ai/specfact-code-review`. The profile does not include
the code-review module.

A fourth UX problem: running `uvx specfact-cli code review run --path .` without `--scope full`
produces a confusing git-diff error. Vibe coders will stop there and think the tool is broken.

**This means the "wow" path does not exist yet.** All four issues must be fixed before the docs
can truthfully describe a vibe-coder entry sequence.

## What Changes

**Bug fixes (blocking the "wow" path):**
- **Fix `init --profile` module installation**: `specfact init --profile solo-developer` must
  actually install the modules defined for that profile, not just bootstrap the runtime
- **Fix `module install` under uvx**: module installation must work without pip in the uvx
  environment (use the bundled package approach or a pip-free install path)
- **Update `solo-developer` profile**: include `nold-ai/specfact-code-review` alongside
  `nold-ai/specfact-codebase` so the profile delivers a working `code review run` command
- **Fix `code review run --path .` without `--scope full`**: either default to full scope when
  no git diff is available, or emit an error that includes the corrective command

**Docs improvements (unlocked once bugs are fixed):**
- **Homepage hero completely rewritten**: opens with the vibe-coder outcome statement, immediately
  followed by the working 2-command uvx sequence
- **`code review run` is explicitly named on the homepage** as the primary entry command
- **uvx path promoted from "Option 1 with limitations" to the hero path** on the installation page
- **3 outcome-oriented path cards** replace the 4 topic/persona cards
- **Architectural jargon deferred** to Architecture/Reference sections
- **Progressive disclosure preserved**: all advanced content remains, reordered

## Capabilities

### New Capabilities
- `dependency-resolution`: Version-aware bundle dependency resolution for `module install` and
  `module upgrade` — versioned specifiers in registry `index.json` and `module-package.yaml`,
  user prompts on missing/mismatched deps, `--yes` for auto-resolve, `--dry-run` for preview,
  circular dep detection, actionable `core_compatibility` errors
- `docs-aha-moment-entry`: Homepage and installation page are restructured so a vibe coder can
  reach a scored `code review run` result in under 2 commands and ~10 seconds, without pip install
  or prior SpecFact knowledge
- `docs-vibecoder-entry-path`: Vibe-coder-specific entry path: uvx init → uvx code review run,
  with the scored output as the explicit "wow" proof point on the homepage

### Modified Capabilities
- `entrypoint-onboarding`: (1) Primary fast-start path must be inline on homepage; (2) path cards
  name user actions not personas; (3) `code review run` is the named primary command
- `first-contact-story`: Hero pairs identity with a plain-language outcome; no architectural
  vocabulary in the hero
- `first-run-selection`: `init --profile` MUST install the profile's modules; module-not-found
  error MUST include the exact corrective command
- `profile-presets`: `solo-developer` profile MUST include `nold-ai/specfact-code-review`
  alongside `nold-ai/specfact-codebase`
- `module-installation`: (1) `module upgrade` MUST distinguish actually-upgraded from
  already-up-to-date — showing `X -> X` when nothing changed is a bug; (2) `module upgrade`
  MUST accept multiple selective module names and MUST prompt before applying a major version
  bump (breaking change gate), skippable with `--yes` or auto-skipped in CI/CD mode;
  (3) `module install` and `module uninstall` MUST both accept multiple positional module IDs
  so users can act on several modules in one command (same UX as apt/pip/brew)

## Impact

**CLI changes:**
- `src/specfact_cli/modules/init/` — fix `--profile` to actually install profile modules
- `src/specfact_cli/modules/module-registry/` or install path — fix pip-free install under uvx
- Profile definition for `solo-developer` — add `specfact-code-review` to bundle list
- `src/specfact_cli/` review_run command or registry — fix `--scope` default / better error
- Module-not-found error path — include exact corrective command
- `src/specfact_cli/modules/module_registry/src/commands.py:_run_marketplace_upgrades` —
  distinguish actually-upgraded vs already-up-to-date; never show `X -> X`
- `src/specfact_cli/modules/module_registry/src/commands.py:upgrade` — accept multiple positional
  module names; check registry `latest_version` before installing; prompt on major version bumps;
  `--yes` flag to bypass prompt; auto-skip major bumps in CI/CD mode
- `src/specfact_cli/modules/module_registry/src/commands.py:install` — accept multiple module
  IDs as positional arguments (same UX as apt/pip/brew)
- `src/specfact_cli/modules/module_registry/src/commands.py:uninstall` — accept multiple module
  names as positional arguments
- `registry/index.json` (specfact-cli-modules repo) — extend `bundle_dependencies` schema to
  support `{"id": "...", "version": ">=x.y.z"}` objects alongside plain string entries
- `src/specfact_cli/registry/module_installer.py` — evaluate `module_dependencies_versioned`
  and versioned `bundle_dependencies`; prompt on missing/mismatched deps; `--yes` auto-resolve;
  `--dry-run` preview; circular dep detection
- `src/specfact_cli/registry/dependency_resolver.py` — add module-to-module resolution
  (analogous to existing pip resolution)
- `core_compatibility` error path — replace silent exception with actionable user-facing message

**Docs changes:**
- `docs/index.md` — primary rewrite (hero + uvx block + 3 cards)
- `docs/getting-started/installation.md` — promote uvx, restructure options
- `docs/getting-started/quickstart.md` — reframe for vibe-coder audience

**Spec changes:**
- `openspec/specs/entrypoint-onboarding/spec.md` — delta
- `openspec/specs/first-contact-story/spec.md` — delta
- `openspec/specs/first-run-selection/spec.md` — delta (profile install requirement)
- `openspec/specs/profile-presets/spec.md` — delta (solo-developer bundle list)
- New specs: `docs-aha-moment-entry`, `docs-vibecoder-entry-path`

## Source Tracking

- **GitHub Issue**: [#476](https://github.com/nold-ai/specfact-cli/issues/476)
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/476>
- **Parent Feature**: [#356](https://github.com/nold-ai/specfact-cli/issues/356) — Documentation & Discrepancy Remediation ([tracking comment](https://github.com/nold-ai/specfact-cli/issues/356#issuecomment-4180162525))
- **Related (overlap)**: [#466](https://github.com/nold-ai/specfact-cli/issues/466) — first-contact / onboarding ([cross-link comment](https://github.com/nold-ai/specfact-cli/issues/466#issuecomment-4180162609))
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: in-progress — issue created with labels `enhancement`, `change-proposal`, `documentation`, `openspec`
