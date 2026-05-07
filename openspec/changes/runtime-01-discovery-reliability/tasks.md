# Tasks: runtime-01-discovery-reliability

## 1. Readiness and spec validation

- [x] 1.1 Confirm issues `#552`, `#553`, and `#554` are correctly scoped to `specfact-cli`, not `specfact-cli-modules`, and record that decision in `TDD_EVIDENCE.md`.
- [x] 1.2 Confirm public GitHub metadata is complete: dedicated user-story issue `#557`, feature parent `#353`, labels, project assignment, issue dependencies, and Todo/not-in-progress status.
- [x] 1.3 Validate the OpenSpec change with `openspec validate runtime-01-discovery-reliability --strict`.

## 2. Failing-first tests

- [x] 2.1 Add tests for clean installed module runtime loading with temp installed `specfact-project` and `specfact-codebase` modules, no sibling module source path, and `specfact code` exposing `import`, `analyze`, `drift`, `validate`, and `repro`.
- [x] 2.2 Add tests proving module load/import failures are classified as installed-unavailable instead of absent.
- [x] 2.3 Add tests for rootless monorepo environment detection with `uv` on `PATH`, package-level `pyproject.toml`/`uv.lock`, and explicit `init ide --env-manager uv`.
- [x] 2.4 Run the targeted tests before production edits and record failing evidence in `TDD_EVIDENCE.md`.

## 3. Runtime discovery fixes

- [x] 3.1 Add a focused helper that prepends enabled discovered module `src/` roots to `sys.path` before lazy-loading installed module command apps.
- [x] 3.2 Preserve existing development behavior but prevent sibling `specfact-cli-modules` source paths from hiding installed-runtime test failures.
- [x] 3.3 Capture lazy loader failures in availability diagnostics so known module commands distinguish absent, disabled, skipped, and load-failed providers.

## 4. Environment manager fixes

- [x] 4.1 Extend environment-manager detection to scan rootless monorepo package directories up to two levels deep.
- [x] 4.2 Add PATH fallback detection for supported tools, preferring `uv`, then `hatch`, `poetry`, and `pip`.
- [x] 4.3 Add `specfact init ide --env-manager <auto|uv|hatch|poetry|pip>` and use the explicit manager when provided.

## 5. Passing evidence and quality gates

- [x] 5.1 Re-run targeted tests and record passing evidence in `TDD_EVIDENCE.md`.
- [x] 5.2 Run required quality gates for touched scope: formatting, type-check, lint, contract-test, smart-test or targeted equivalent, and SpecFact code review JSON.
- [x] 5.3 Add a CI-capable runtime discovery smoke script that exercises module install, upgrade/init-adjacent discovery, rootless monorepo environment-manager detection, and installed `specfact code` command loading against a real demo checkout.
- [x] 5.4 Update task checkboxes and prepare the branch for PR to `dev`.
