# Change: IDE Prompt Source Selection

## Why

`specfact init ide` is now downstream of two separate realities:

- official bundle-owned prompts and templates are being moved into `specfact-cli-modules`
- users can install modules into different runtime roots (`~/.specfact/modules`, `<repo>/.specfact/modules`, built-in core package roots, and optional custom roots)

The original proposal treated this as only a simple prompt selector. That is no longer sufficient. The remaining core-side work is to make prompt and resource export aware of installation scope, ownership, and provenance without reintroducing payload ownership into `specfact-cli`.

## What Changes

- MODIFY: Narrow this change to `specfact-cli` orchestration only. Prompt/template payload migration stays in `specfact-cli-modules` change `packaging-01-bundle-resource-payloads` (`nold-ai/specfact-cli-modules#101`).
- EXTEND: Build an installation-aware prompt/resource catalog for `specfact init ide` from core built-ins plus discovered installed modules across user, project, and configured custom module roots.
- ADD: Default `specfact init ide` behavior exports all discovered prompt sources, while interactive and non-interactive selection can target `core` and specific installed module ids.
- ADD: Exported prompt files remain attributable to their owning source so collisions are deterministic and later ownership changes do not silently overwrite unrelated prompts.
- ADD: `specfact init ide` remains an anytime re-sync command. It discovers and copies installed resources; it does not download, install, or extract module archives itself.
- ADD: When selected resources are missing, the command reports the missing owner/root and points users to the relevant core install/bootstrap flows such as `specfact module init --scope <user|project>` and `specfact module install --scope <user|project>`.

## Capabilities

### New Capabilities

- `init-ide-prompt-selection`: `specfact init ide` can export prompts from core and selected installed modules with consistent interactive and non-interactive behavior.
- `init-ide-installed-resource-orchestration`: `specfact init ide` can discover installed prompt/resource payloads from the effective module roots and direct users to the correct install/bootstrap command when those payloads are absent.

## Acceptance Criteria

- `specfact init ide` builds its prompt-source catalog from the effective installed module roots for the current repository context, including user scope, project scope, built-in core modules, and configured custom roots.
- Default execution exports all discovered prompt sources by default rather than only the first matching root.
- Interactive mode shows a source picker containing `core` plus installed module ids that actually contribute prompt resources.
- Non-interactive mode accepts `--prompts all`, `--prompts core`, and comma-separated full module ids.
- The command does not download or install module archives. Missing sources produce actionable guidance to run the correct core install/bootstrap command for the relevant scope.
- Exported prompt files are grouped or namespaced by source so prompt provenance remains visible and collisions stay deterministic.
- The scope respects canonical command ownership from active migration changes and must not reintroduce obsolete command paths into prompt export or recommendations.

## Dependencies

- `backlog-module-ownership-cleanup` must land first so backlog prompt ownership is no longer split across core and module.
- `packaging-02-cross-platform-runtime-and-module-resources` provides the installed-resource discovery foundation in `specfact-cli` and must stay the owner of payload discovery mechanics.
- `specfact-cli-modules/packaging-01-bundle-resource-payloads` (`nold-ai/specfact-cli-modules#101`) must provide the bundle-owned prompt/template payloads that this change selects and exports.
- `module-migration-11-project-codebase-ownership-realignment` must be treated as command-surface alignment context so exported prompts do not preserve obsolete grouped command ownership.
- Existing `specfact module init` and `specfact module install` commands in `specfact-cli` remain the install/bootstrap path for user/project module roots; `init ide` extends only the post-install discovery/export path.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #382
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/382>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: fc82ab6be9832592 -->
