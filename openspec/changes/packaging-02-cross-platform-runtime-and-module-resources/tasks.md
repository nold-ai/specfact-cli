## 1. Spec And Scope Alignment

- [x] 1.1 Finalize spec deltas for runtime portability and module-owned IDE prompt resources.
- [x] 1.2 Confirm the prompt ownership boundary against `init-ide-prompt-source-selection` so this change provides the discovery foundation without duplicating prompt-selection UX work.
- [x] 1.3 Integrate with `specfact-cli-modules/packaging-01-bundle-resource-payloads` for bundle-packaged prompts and other module-owned resource payloads.

## 2. Test-First Coverage

- [x] 2.1 Add failing tests for help/startup rendering on non-UTF-8 terminal encodings with ASCII-safe fallback behavior.
- [x] 2.2 Add failing tests for actionable runtime/interpreter compatibility errors during backlog automation or similar programmatic invocation.
- [x] 2.3 Add failing tests for module-owned prompt discovery and `specfact init ide` export behavior from installed module resource directories.
- [x] 2.4 Add failing tests for module-owned non-prompt resource lookup, starting with backlog field mapping templates.
- [x] 2.5 Record failing test evidence in `TDD_EVIDENCE.md`.

## 3. Runtime And Resource Implementation

- [x] 3.1 Implement terminal encoding detection and Unicode/icon fallback in the shared runtime/terminal configuration path.
- [x] 3.2 Replace brittle path-injection behavior with installation-scoped runtime/module resolution and explicit compatibility diagnostics.
- [x] 3.3 Refactor `specfact init ide` to build a prompt catalog from installed module resource locations rather than `specfact_cli/resources/prompts`.
- [x] 3.4 Refactor core init/install resource copying to resolve module-owned templates, starting with backlog field mapping templates, from installed bundle packages.
- [x] 3.5 Remove or relocate bundle-owned prompt/resources from core packaging so ownership matches installed modules.

## 4. Validation And Documentation

- [x] 4.1 Re-run the new tests and record passing evidence in `TDD_EVIDENCE.md`.
- [x] 4.2 Update docs and README guidance for cross-platform terminal behavior, supported automation invocation, and module-owned prompt resources.
- [x] 4.3 Run `openspec validate packaging-02-cross-platform-runtime-and-module-resources --strict`.
