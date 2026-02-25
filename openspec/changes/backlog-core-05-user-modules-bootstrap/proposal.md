# Change: Backlog Core — User Modules Bootstrap and Prompt Resource Sync

## Why







`specfact backlog add` is still missing in installed-runtime contexts when command discovery depends on repository-local `modules/` folders. This makes behavior vary by working directory and machine.

For production usage, shipped modules and their resources should be managed as user-level artifacts. We need a reliable path where `specfact module init` prepares a per-user module root (not repo-local) so command availability is stable.

## What Changes







- **MODIFY**: Add a canonical user module root at `<user-home>/.specfact/modules` for installed module artifacts.
- **MODIFY**: Ensure discovery and installer flows prefer `<user-home>/.specfact/modules` and stop treating workspace `./modules` as an automatic discovery root.
- **MODIFY**: Add workspace-local module discovery only under `<repo>/.specfact/modules` to avoid claiming ownership of non-SpecFact repository paths.
- **NEW**: Add a `specfact module init` bootstrap step that seeds user module root from packaged/workspace module artifacts so shipped modules (for example `backlog-core`) are available after bootstrap.
- **NEW**: Add a target-scope switch for `specfact module init` so bootstrap defaults to per-user root but can explicitly seed per-project modules under `<repo>/.specfact/modules` (repo defaults to current directory).
- **NEW**: Add startup module freshness checks (same optimization model as template/version checks): run on first execution of a new CLI version and at most once per 24h otherwise.
- **NEW**: Startup freshness guidance SHALL check both scopes and recommend the exact command to run: project scope (`specfact module init --scope project`) and user scope (`specfact module init`).
- **MODIFY**: Make workspace project modules (`<repo>/.specfact/modules`) higher precedence than user modules so project-specific module intent is honored.
- **NEW**: Add `specfact module list` option to show bundled modules available from local package artifacts but not yet installed in active discovery roots, rendered in a separate section with install guidance.
- **MODIFY**: Extend `specfact module install` to resolve module ids from bundled sources as well as marketplace, so users can install only a subset of shipped modules.
- **MODIFY**: Extend `specfact module install`/`uninstall` with explicit target scope handling (`user` or `project`) to avoid ambiguous writes/removals.
- **NEW**: Add uninstall conflict protection when same module id exists in both `<repo>/.specfact/modules` and `<user-home>/.specfact/modules`; command must require explicit scope selection instead of guessing.
- **NEW**: Enforce module denylist checks before install/bootstrap from any source (bundled, project, user, marketplace, legacy roots) to prevent silently installing known-bad modules.
- **NEW**: Add local trust gate for non-official publishers on first install/enable (one-time explicit acknowledgment persisted in user config).
- **NEW**: Require signature/checksum verification for shipped/bundled modules using release-generated signatures (not publisher-name trust alone).
- **NEW**: Add release signing automation for bundled modules in this repository so module signatures are generated during release orchestration without exposing private keys.
- **NEW**: Support encrypted signing keys with passphrase input via CLI flag, stdin, or environment variable, and wire CI signing steps to dedicated secrets (`SPECFACT_MODULE_PRIVATE_SIGN_KEY`, `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE`).
- **NEW**: Add changed-module release automation that selects only modules with payload changes, applies module-level semver bump, and performs bump/sign/verify in one workflow.
- **MODIFY**: Treat bundled module versions as independent semver from CLI package version; only changed module payloads require module version increments.
- **MODIFY**: Document and codify boundary with `marketplace-02`: this change hardens local/shipped module trust and install safety; online multi-registry ecosystem remains in `marketplace-02`.
- **MODIFY**: Add tests for init/module discovery parity that verify `backlog add` availability does not depend on current working directory.
- **MODIFY**: Strengthen prompt resource detection/copy tests so `specfact init ide` consistently finds bundled prompt resources and installs them to project target locations.

## Capabilities
- **backlog-core** (extended): User-level module availability for `backlog add` and related command surface.
- **init/module-registry** (extended): Stable user-root module lifecycle behavior and bootstrap.
- **ide setup** (extended): Prompt resource detection/copy parity for project prompt targets.


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #298
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/298>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 8809bb30c7849909 -->