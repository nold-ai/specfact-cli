# Change: Safe Project Artifact Writes For Init And IDE Setup

## Why

`specfact init` and `specfact init ide` currently mutate user-owned project artifacts such as `.vscode/settings.json` without a first-class safety contract. Issue [#487](https://github.com/nold-ai/specfact-cli/issues/487) showed that a single setup run can destroy unrelated local configuration, forcing manual git restore and hand repair; that failure mode is unacceptable for any tool that writes into customer repositories.

## What Changes

- **NEW**: Introduce a core safe-write policy for project artifacts that classifies targets as create-only, mergeable, append-only, or replace-only-with-explicit-approval.
- **NEW**: Add a structured write planning flow for init/setup commands that records whether an operation will create, merge, skip, back up, or fail before touching an existing user file.
- **NEW**: Require backup and recovery metadata for destructive or lossy local mutations initiated by core setup flows.
- **NEW**: Add conflict handling rules for structured files such as `.vscode/settings.json` so SpecFact-managed keys are merged into existing documents instead of replacing the whole artifact.
- **EXTEND**: `specfact init ide` to preserve non-SpecFact settings, strip only prior SpecFact-managed prompt recommendations when needed, and fail safely on malformed settings files unless the user explicitly chooses a replacement path.
- **EXTEND**: `specfact init` and related bootstrap helpers to route project-file writes through the same safe-write contract instead of ad hoc `write_text` or overwrite behavior.
- **EXTEND**: Documentation for init/setup commands with explicit guarantees about preservation, backup behavior, and how users can preview or force replacements when necessary.

## Capabilities

### New Capabilities

- `project-artifact-write-safety`: Policy, planning, and recovery rules for any core command that creates or mutates user-project artifacts.

### Modified Capabilities

- `init-ide-prompt-source-selection`: `specfact init ide` must reconcile prompt recommendations with existing IDE settings without deleting unrelated user configuration.
- `module-owned-ide-prompts`: Core setup flows that materialize bundle-owned IDE assets must use the safe-write policy when touching user-project files.

## Impact

- Affected code: `src/specfact_cli/utils/ide_setup.py`, `src/specfact_cli/modules/init/src/commands.py`, and any shared core helpers introduced for safe project-file mutations.
- Affected docs: `README.md`, `docs/getting-started/installation.md`, `docs/getting-started/quickstart.md`, and core CLI/init reference pages.
- Integration points: installed bundle prompt exports from `specfact-cli-modules`; paired runtime adoption change required in `nold-ai/specfact-cli-modules` so bundle commands follow the same guarantees.
- Dependencies: linked bug [#487](https://github.com/nold-ai/specfact-cli/issues/487); sync under parent feature [#365](https://github.com/nold-ai/specfact-cli/issues/365) Configuration Profiles.

## Source Tracking

- **GitHub Issue**: #490
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/490>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #365
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/365>
- **Related Bug**: #487
- **Related Bug URL**: <https://github.com/nold-ai/specfact-cli/issues/487>
