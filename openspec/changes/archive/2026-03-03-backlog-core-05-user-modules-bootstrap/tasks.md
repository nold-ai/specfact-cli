# Tasks: backlog-core-05-user-modules-bootstrap

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for behavior changes.

1. Update spec deltas first.
2. Add tests mapped to scenarios.
3. Run tests and capture failing results in `TDD_EVIDENCE.md`.
4. Implement production code.
5. Re-run tests and quality checks; capture passing evidence in `TDD_EVIDENCE.md`.

## 1. Branch and scope

- [x] 1.1 Work on `bugfix/backlog-core-05-user-modules-bootstrap` (or active equivalent) before implementation changes.
- [x] 1.2 Confirm scope is limited to user-root module bootstrap/discovery and prompt resource sync verification.

## 2. Specs first

- [x] 2.1 Finalize `specs/user-module-root/spec.md` scenarios for `<user-home>/.specfact/modules` discovery + bootstrap behavior.
- [x] 2.2 Finalize `specs/prompt-resource-sync/spec.md` scenarios for prompt resource detection and IDE target installation parity.

## 3. Tests first (must fail before implementation)

- [x] 3.1 Add/extend tests for module discovery and installer roots (`tests/unit/registry/test_module_discovery.py`, `tests/unit/registry/test_module_installer.py`, and/or `tests/unit/specfact_cli/registry/test_module_packages.py`).
- [x] 3.2 Add/extend module command tests proving shipped module availability after `specfact module init` bootstrap.
- [x] 3.3 Add/extend IDE setup tests for prompt resource detection/copy behavior (`tests/unit/utils/test_ide_setup.py`).
- [x] 3.5 Add/extend tests ensuring workspace `./modules` is ignored and workspace `.specfact/modules` is discovered.
- [x] 3.6 Add/extend module-init tests for target scope switch: default user scope, project scope at CWD, and project scope with explicit repo.
- [x] 3.7 Add/extend discovery tests proving project `.specfact/modules` precedence over user modules in repo context.
- [x] 3.8 Add/extend startup-check tests for module freshness cadence (version-changed and daily) and guidance output for project/user scope updates.
- [x] 3.9 Add/extend module list tests for bundled-not-installed view and install hints.
- [x] 3.10 Add/extend install/uninstall tests for explicit scope handling and multi-scope uninstall ambiguity safeguards.
- [x] 3.11 Add/extend install tests proving bundled module resolution via `specfact module install`.
- [x] 3.12 Add/extend tests for explicit install source selection and bundled-availability hint in `module list` default output.
- [x] 3.13 Add tests for denylist enforcement on `module install` and `module init` bootstrap paths.
- [x] 3.14 Add tests for one-time trust prompt/flag behavior for non-official publishers in interactive and non-interactive modes.
- [x] 3.15 Add tests for bundled signature/checksum verification during install/bootstrap (pass and fail paths).
- [x] 3.16 Add tests for changed-module release automation (changed-only selection, auto version bump, unchanged-module skip).
- [x] 3.4 Run targeted tests and record failing results in `TDD_EVIDENCE.md`.

## 4. Implementation

- [x] 4.1 Introduce canonical user module root constant/path (`<user-home>/.specfact/modules`) and integrate it into module discovery/installer flows.
- [x] 4.2 Add `specfact module init` bootstrap that syncs bundled/workspace modules into user module root without destructive overwrite.
- [x] 4.3 Update user-facing hints/messages to reference `<user-home>/.specfact/modules` as primary per-user module location.
- [x] 4.4 Ensure prompt resource resolution path remains deterministic for installed runtime and project-target template copy flows.
- [x] 4.5 Remove automatic workspace `./modules` discovery and switch workspace-local root to `<repo>/.specfact/modules`.
- [x] 4.6 Add `specfact module init` target-scope switch (`user` default, optional `project`) and optional repo target for project scope.
- [x] 4.7 Implement project-over-user module precedence in discovery ordering.
- [x] 4.8 Implement startup module freshness checker integrated with existing startup check cadence metadata.
- [x] 4.9 Add `specfact module list` bundled-availability switch and separate table for bundled-not-installed modules.
- [x] 4.10 Implement scoped `module install`/`module uninstall` roots with explicit `--scope` and optional `--repo` handling.
- [x] 4.11 Implement uninstall ambiguity protection when module exists in both project and user roots.
- [x] 4.12 Implement bundled-source resolution path in `module install` before marketplace fallback.
- [x] 4.13 Add explicit `module install --source` control (`auto|bundled|marketplace`) and improve `module list` discoverability hint.
- [x] 4.14 Implement denylist loader/checker applied to install/bootstrap flows for all sources.
- [x] 4.15 Implement persisted trust decisions and trust prompt/flag flow for non-official publishers.
- [x] 4.16 Enforce signature/checksum verification for shipped/bundled module install/bootstrap paths.
- [x] 4.17 Add release signing script/workflow integration for bundled modules (private key via CI secret; no key material in repo).
- [x] 4.18 Add encrypted-key passphrase handling in signing scripts (`--passphrase`, `--passphrase-stdin`, env var) and update CI signing secrets wiring.
- [x] 4.19 Implement changed-module automation in signing tooling (select changed manifests by git base, optional semver bump, re-sign).
- [x] 4.20 Ensure module version enforcement is payload-change based and remains decoupled from CLI package version.

## 5. Validation and docs

- [x] 5.1 Re-run targeted tests and record passing results in `TDD_EVIDENCE.md`.
- [x] 5.2 Run touched-scope quality gates (`hatch run format`, `hatch run type-check`, targeted pytest).
- [x] 5.3 Update docs/command references for user module root, workspace `.specfact/modules`, and init behavior where needed.
- [x] 5.5 Update command docs for module-init scope switch and per-project target behavior under `.specfact/modules`.
- [x] 5.6 Update startup-check docs to include module freshness guidance cadence and command hints.
- [x] 5.7 Update command docs for module-list bundled-availability option and output semantics.
- [x] 5.8 Update command docs for scoped install/uninstall behavior and bundled install resolution.
- [x] 5.9 Align marketplace guide with user/project scope roots and legacy root compatibility note.
- [x] 5.10 Document denylist/trust prompt/signature verification behavior and automation flags for CI.
- [x] 5.11 Document scope boundary with `marketplace-02` (online registry ecosystem vs local/shipped trust hardening).
- [x] 5.12 Document module release workflow for changed-only bump/sign/verify and module-level semver strategy.
- [x] 5.4 Run `openspec validate backlog-core-05-user-modules-bootstrap --strict` and update `CHANGE_VALIDATION.md`.

## 6. Delivery

- [x] 6.1 Update `openspec/CHANGE_ORDER.md` status and placement.
- [x] 6.2 Prepare PR notes with verification across different working directories/machines.
