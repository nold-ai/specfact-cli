## Why

An attacker-controlled repository can make an IDE prompt export root, such as
`.github/prompts`, a symlink to a writable location outside the repository.
Prompt cleanup and export currently follow that root, which can delete legacy
directories or write generated prompts outside the requested repository.

## What Changes

- Require every IDE prompt export root to be a real directory path contained
  beneath the resolved target repository before cleanup or export.
- Refuse symlinked or out-of-repository export roots without deleting or
  writing through them.
- Preserve unrelated team-owned directories while retaining normal cleanup of
  legacy SpecFact export directories inside a repository.
- Add focused security regression tests for cleanup and export behavior.

## Capabilities

### Modified Capabilities

- `init-ide-prompt-source-selection`: IDE prompt exports remain confined to the
  selected repository and do not traverse repository-controlled export-root
  symlinks.

## Impact

- Affected code: `src/specfact_cli/utils/ide_setup.py`.
- Affected tests: `tests/unit/utils/test_ide_setup.py`.
- Compatibility: normal in-repository IDE exports and cleanup remain unchanged;
  unsafe symlinked export roots are rejected.
- Documentation: review `README.md`, `docs/`, `docs/index.md`, and navigation;
  no user-facing documentation change is expected because this restores the
  existing repository-bound safety contract.
- Rollback: revert the helper and call-site guard together; doing so would
  reopen the external filesystem deletion/write vulnerability.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **Parent Feature**: [#375](https://github.com/nold-ai/specfact-cli/issues/375)
- **Parent Epic**: [#285](https://github.com/nold-ai/specfact-cli/issues/285)
- **GitHub Issue**: [#720](https://github.com/nold-ai/specfact-cli/issues/720)
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/720
- **Repository**: nold-ai/specfact-cli
- **Blocked By**: none
- **Last Synced Status**: issue open, Todo, assigned, labels and parent verified on 2026-09-06

