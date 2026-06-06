## Why

Primary tester reports `#585` through `#593` show that first real-use adoption is blocked by stale command guidance, ambiguous CLI errors, and package-manager runtime mismatches. The failures cut across core runtime behavior, generated documentation, package-manager detection, stale launcher repair, and module command discovery.

Core owns the shared CLI contract, command inventory, documentation validation, upgrade/tool environment detection, and PR-blocking runtime simulation. Module-owned command implementations are tracked in paired modules issue `nold-ai/specfact-cli-modules#306`.

## What Changes

- Add a shared CLI error contract: unknown commands, missing subcommands, and missing required parameters show relevant help plus explicit actionable missing/invalid information.
- Generate deterministic command overview artifacts for core commands and installed official module command groups, including `llms.txt`, Markdown, and JSON forms.
- Validate docs, prompts, templates, and code guidance against the generated command contract instead of accepting prefix-only command matches.
- Streamline `init ide` so slash-command targets receive prompt files while skill-based targets such as Codex CLI, Claude Code Skills, and Mistral Vibe receive grouped capability-oriented `SKILL.md` files per source/module.
- Prefer the effective active runner/environment for upgrade and tool diagnostics so `uv run`, hatch, pip, and pipx do not misclassify each other.
- Validate and repair stale pipx console launchers after successful pipx upgrades so a reported successful upgrade cannot leave `specfact` broken.
- Extend PR validation with a package-manager runtime matrix covering uv, pip, pipx, and hatch execution paths.

## Capabilities

### New Capabilities

- `cli-error-guidance`
- `generated-command-overview`
- `runtime-tool-probing`

### Modified Capabilities

- `core-cli-reference`
- `command-package-runtime-validation`
- `ci-integration`

## Impact

- Affected code: root CLI command resolution/error rendering, docs command validation, command audit/inventory generation, IDE prompt/skill export, upgrade install-method detection and pipx launcher validation, environment/tool probing helpers, CI workflow wiring.
- Affected docs: `README.md`, `llms.txt`, generated command references, core CLI pages, IDE setup docs, prompt/template guidance that mentions command paths.
- Affected tests: CLI error-contract tests, generated command artifact tests, IDE prompt/skill export tests, docs/prompt/template command validation tests, upgrade/env probing tests, runtime package-manager smoke tests.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **Parent Features**: [#375](https://github.com/nold-ai/specfact-cli/issues/375), [#356](https://github.com/nold-ai/specfact-cli/issues/356), [#353](https://github.com/nold-ai/specfact-cli/issues/353), [#355](https://github.com/nold-ai/specfact-cli/issues/355), [#404](https://github.com/nold-ai/specfact-cli/issues/404)
- **Change User Story**: [#594](https://github.com/nold-ai/specfact-cli/issues/594)
- **Source Bugs**: [#585](https://github.com/nold-ai/specfact-cli/issues/585), [#587](https://github.com/nold-ai/specfact-cli/issues/587), [#588](https://github.com/nold-ai/specfact-cli/issues/588), [#589](https://github.com/nold-ai/specfact-cli/issues/589), [#590](https://github.com/nold-ai/specfact-cli/issues/590), [#593](https://github.com/nold-ai/specfact-cli/issues/593)
- **Module-owned Bugs**: [#586](https://github.com/nold-ai/specfact-cli/issues/586), [#591](https://github.com/nold-ai/specfact-cli/issues/591), [#592](https://github.com/nold-ai/specfact-cli/issues/592) tracked by [nold-ai/specfact-cli-modules#306](https://github.com/nold-ai/specfact-cli-modules/issues/306)
- **Paired Modules Change**: `tester-module-cli-reliability`
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: GitHub story created; project/parent fields may need project-board field sync if CLI auth lacks project scope.
- **Sanitized**: false
