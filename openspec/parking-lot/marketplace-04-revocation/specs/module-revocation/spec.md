# module-revocation Specification

## Purpose

Defines per-module revocation records in `registry/modules/revoked.json`, CLI enforcement at install time, and the warning surfaced on invocation of already-installed revoked modules.

## ADDED Requirements

### Requirement: Block installation of revoked module versions

The CLI SHALL enforce module-level revocation at install time, applying the same grace window policy as publisher revocation.

#### Scenario: Module version revoked with security_incident — hard block

- **GIVEN** `registry/modules/revoked.json` contains `name: specfact-jira-sync, version: 1.0.0, reason: security_incident`
- **WHEN** user installs `@mycompany/specfact-jira-sync@1.0.0`
- **THEN** CLI SHALL hard-block: `[ERROR] specfact-jira-sync@1.0.0 has been revoked (security_incident). Installation blocked.`
- **AND** SHALL suggest: `Run: specfact module install @mycompany/specfact-jira-sync (to install latest)`
- **AND** SHALL NOT allow any flag to override

#### Scenario: Module version revoked with api_incompatibility — suggest newer version

- **GIVEN** `name: specfact-jira-sync, version: 0.9.0, reason: api_incompatibility` in revocation index
- **WHEN** user installs or already has `specfact-jira-sync@0.9.0`
- **THEN** CLI SHALL warn: `[WARN] specfact-jira-sync@0.9.0 has a known API incompatibility. Upgrade recommended.`
- **AND** SHALL suggest: `Run: specfact module update specfact-jira-sync`
- **AND** install of 0.9.0 is blocked only after 14-day grace window expiry

### Requirement: Warn on invocation of installed revoked module

The CLI SHALL check revocation status of all loaded modules on `specfact module <command>` invocation.

#### Scenario: Loaded module is revoked (security_incident)

- **GIVEN** `specfact-jira-sync@1.0.0` is installed and subsequently revoked with `security_incident`
- **WHEN** user runs any `specfact` command that loads the module
- **THEN** CLI SHALL display prominently before any command output:

  ```text
  ⚠ WARNING: specfact-jira-sync@1.0.0 has been revoked (security_incident).
    Reason: Remote code execution vulnerability — update or uninstall immediately.
    Run: specfact module update specfact-jira-sync
         specfact module uninstall specfact-jira-sync
  ```

- **AND** SHALL NOT block the command (warn-only for installed modules)

#### Scenario: Loaded module is revoked (policy_violation, within grace window)

- **GIVEN** `specfact-jira-sync@1.0.0` is installed and revoked with `policy_violation`, within 30d grace
- **WHEN** user runs any command loading the module
- **THEN** CLI SHALL display: `[WARN] specfact-jira-sync@1.0.0 has been revoked (policy_violation). Grace window: N days remaining.`
- **AND** SHALL continue command execution

### Requirement: Configurable periodic re-check for installed modules

The CLI SHALL support a configurable periodic revocation re-check for installed modules.

#### Scenario: Periodic re-check (weekly default)

- **GIVEN** `revocation_check_interval: 7d` in `~/.specfact/config.yaml` (default)
- **AND** the last revocation check was more than 7 days ago
- **WHEN** user runs any `specfact` command
- **THEN** CLI SHALL perform a background revocation re-check for all installed modules
- **AND** SHALL surface any newly-revoked module warnings

## Contract Requirements

- `check_module_revocation(module_name: str, version: str, index: ModuleRevocationIndex) -> RevocationStatus` — `@require` module_name and version are non-empty; `@ensure` result.is_revoked is bool; `@beartype`
- `enforce_revocation_policy(status: RevocationStatus, context: RevocationContext) -> RevocationDecision` — `@require` status.reason in KNOWN_REASONS; `@beartype`
