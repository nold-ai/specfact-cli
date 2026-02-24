# Design: backlog-core-05-user-modules-bootstrap

## Problem

Installed runtime behavior currently depends on discovery of repository-local `modules/` folders in some execution contexts. This causes command-surface drift (for example missing `backlog add`) across machines and working directories.

## Goals

- Establish `<user-home>/.specfact/modules` as canonical per-user module artifact root.
- Ensure `specfact module init` can bootstrap shipped modules into that root.
- Restrict workspace-local discovery to `<repo>/.specfact/modules` only.
- Add explicit `specfact module init` target scope control (`user` default, optional `project`).
- Add startup module freshness guidance with daily/version-triggered cadence.
- Add optional bundled availability visibility in `specfact module list`.
- Extend `specfact module install` to resolve bundled sources in addition to marketplace.
- Add explicit install/uninstall target scope handling (`user`/`project`) with ambiguity safeguards.
- Add local trust hardening for shipped/bundled modules: signature verification, denylist enforcement, and one-time trust prompts for non-official publishers.
- Keep prompt/resource installation behavior deterministic for project IDE targets.

## Non-goals

- Replace the `specfact module` command group lifecycle UX in this change.
- Remove legacy discovery roots immediately (deprecation can follow later).
- Implement full online marketplace ecosystem controls (multi-registry, dependency resolver, publishing automation) already tracked in `marketplace-02`.

## Approach

1. Discovery / installer alignment
- Add canonical user root constant shared by discovery + installer logic.
- Make installer default to user root.
- Keep legacy `marketplace-modules`/`custom-modules` roots discoverable as compatibility paths.
- Remove automatic `./modules` discovery and only include workspace root `<cwd>/.specfact/modules`.
- Ensure project scope is discovered before user scope to give repository-local intent precedence.

2. Module init bootstrap
- Add `specfact module init` sync that copies shipped module packages into user root when absent or outdated.
- Copy safely (create/update module directories) and avoid destructive deletion of unrelated user modules.
- Keep bootstrap explicit under the `module` command group and leave top-level `init` behavior unchanged.
- Add a scope switch so users can seed project-specific modules into `<repo>/.specfact/modules`.
- For project scope, default repo to CWD and allow explicit repo override.

3. Startup freshness checks
- Extend startup check pipeline with module freshness inspection.
- Reuse current cadence policy style:
  - run on CLI version change;
  - otherwise run at most once per 24h.
- Compare bundled module manifests against target scopes:
  - project: `<repo>/.specfact/modules`
  - user: `<user-home>/.specfact/modules`
- Print scope-specific guidance commands when stale/missing modules are detected.

4. Module list bundled availability
- Add a `module list` switch that computes bundled modules available from package/workspace bundle sources.
- Diff bundled module names against active discovered modules.
- Render bundled-not-installed modules as a separate section/table with install hints for user and project scope init commands.

5. Scoped install/uninstall consistency
- `module install` accepts explicit scope (`user` default, `project` optional with repo path).
- Install resolution checks bundled sources first for exact module name, then marketplace fallback.
- `module uninstall` accepts explicit scope; when module exists in both scopes and no scope is set, command errors and requires explicit selection.
- Uninstall operation removes only the selected scope artifact.

6. Local trust and signature hardening
- Add denylist file support (for example under user config) checked before any install/bootstrap copy operation.
- Add one-time trust acknowledgments for non-official publishers (persisted in user config); non-interactive mode must require explicit trust flag.
- Verify shipped/bundled module integrity/signature metadata before install/bootstrap; fail closed on verification errors unless explicit override is provided for developer workflows.
- Treat publisher string (`nold-ai`) as informational only; authenticity is derived from signature verification.

7. Release-time signing of bundled modules
- Add a repository-local signing step that generates signatures/checksums for bundled modules during release orchestration.
- Private signing key remains externalized (CI secret or secure signing service); never committed in repository.
- Signing outputs are committed as module metadata/signature artifacts consumed by runtime verifier.

3. Resource parity
- Keep prompt resources sourced from packaged `resources/prompts` in installed runtime.
- Validate that prompt copy to repo-local IDE targets works independently of CWD and module root.

## Risks

- Path precedence collisions when the same module exists in multiple roots.
- Migration confusion for users with legacy `./modules` layouts.
- Confusion about whether module init writes globally or per project.
- Startup noise if cadence is not throttled.
- Key management mistakes could weaken trust guarantees.
- Overly strict trust prompts could block CI/non-interactive usage.

## Mitigations

- Keep source priority deterministic and explicit in tests.
- Emit user-facing hints that `<user-home>/.specfact/modules` is primary while legacy paths remain supported.
- Document the workspace-local root as `.specfact/modules` in directory-structure reference.
- Document module init scope switch semantics and target paths in command docs.
- Keep startup warnings concise and only shown when stale modules are detected.
- Support explicit non-interactive trust flags for automation while keeping secure defaults.
- Keep private key outside repository and restrict signing access to release workflows.
