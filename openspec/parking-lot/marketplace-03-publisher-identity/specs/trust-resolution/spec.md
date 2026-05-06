# trust-resolution Specification

## Purpose

Defines the trust tier resolution order, install-time enforcement, override flags, audit logging, and display of trust tiers in module search and info output.

## ADDED Requirements

### Requirement: Enforce trust tier resolution order at install time

The CLI SHALL resolve effective trust tier and enforce install policy based on `official > verified > community > unregistered`.

#### Scenario: Install official module without prompt

- **GIVEN** a module with effective tier `official`
- **WHEN** user runs `specfact module install @nold-ai/specfact-codebase`
- **THEN** CLI SHALL install without any prompt or warning
- **AND** SHALL log `[INFO] Installing @nold-ai/specfact-codebase (official)`

#### Scenario: Install verified module without prompt

- **GIVEN** a module with effective tier `verified`
- **WHEN** user runs `specfact module install @mycompany/specfact-jira-sync`
- **THEN** CLI SHALL install without any prompt or warning
- **AND** SHALL log `[INFO] Installing @mycompany/specfact-jira-sync (verified)`

#### Scenario: Install community module with warning prompt

- **GIVEN** a module with effective tier `community`
- **WHEN** user runs `specfact module install @devuser/specfact-lint-rules`
- **THEN** CLI SHALL display a `[WARN] @devuser/specfact-lint-rules is community-verified (publisher identity confirmed, content not reviewed by NOLD AI)`
- **AND** SHALL prompt: `Install anyway? [y/N]`
- **AND** SHALL abort on `N` or no input

#### Scenario: Install community module with --trust-community flag

- **GIVEN** a module with effective tier `community`
- **AND** user passes `--trust-community` flag
- **WHEN** user runs `specfact module install @devuser/specfact-lint-rules --trust-community`
- **THEN** CLI SHALL install without prompt
- **AND** SHALL append to `~/.specfact/module-audit.log`: `timestamp, @devuser/specfact-lint-rules, community, installed, --trust-community`

#### Scenario: Block unregistered module

- **GIVEN** a module with effective tier `unregistered` (publisher not in index)
- **WHEN** user runs `specfact module install some/unregistered-module`
- **THEN** CLI SHALL display `[ERROR] some/unregistered-module is not registered in the NOLD AI trust index. Use --trust-unregistered to override.`
- **AND** SHALL exit with non-zero status code

#### Scenario: Install unregistered module with --trust-unregistered flag

- **GIVEN** a module with effective tier `unregistered`
- **AND** user passes `--trust-unregistered` flag
- **WHEN** user runs `specfact module install some/unregistered-module --trust-unregistered`
- **THEN** CLI SHALL install with a prominent warning: `[WARN] Installing unregistered module — NOLD AI has not verified this publisher`
- **AND** SHALL append to `~/.specfact/module-audit.log`: `timestamp, some/unregistered-module, unregistered, installed, --trust-unregistered`

### Requirement: Display trust tier in search output

The CLI SHALL show tier badges in `specfact module search` results.

#### Scenario: Search results include tier badges

- **GIVEN** multiple modules from different tiers
- **WHEN** user runs `specfact module search backlog`
- **THEN** each result line SHALL include a tier badge:
  - `[official]` for NOLD AI official modules
  - `[verified]` for domain-verified publisher modules
  - `[community]` for GitHub-identity-only publisher modules
  - `[unregistered]` for modules not in the trust index

### Requirement: Display trust tier in info output

The CLI SHALL show tier detail in `specfact module info <module>`.

#### Scenario: Module info shows publisher tier detail

- **GIVEN** a module `@mycompany/specfact-jira-sync` with tier `verified`
- **WHEN** user runs `specfact module info @mycompany/specfact-jira-sync`
- **THEN** CLI SHALL display:
  - `Publisher: mycompany (verified ✅)`
  - `Publisher ID: pub_abc123`
  - `Trust: registry endorsed (NOLD AI countersig verified)`

### Requirement: Audit log is append-only and human-readable

The CLI SHALL maintain an append-only audit log of all module install decisions.

#### Scenario: Audit log entry format

- **GIVEN** a module install (any tier)
- **WHEN** install completes or is overridden
- **THEN** CLI SHALL append one line to `~/.specfact/module-audit.log`:
  - Format: `ISO8601_UTC | module_handle | tier | action | flag_used_or_none`
  - Example: `2026-02-27T12:00:00Z | @devuser/specfact-lint-rules | community | installed | --trust-community`

## Contract Requirements

- `resolver.resolve_effective_tier(publisher_tier: str, registry_tier: str) -> str` — `@require` both inputs in allowed tier set; `@ensure` result is minimum of the two tiers (by rank order); `@beartype`
- `resolver.enforce_install_policy(module_handle: str, tier: str, flags: InstallFlags) -> InstallDecision` — `@require` tier in known set; `@ensure` result is one of `{install, prompt, block}`; `@beartype`
- `resolver.append_audit_log(entry: AuditEntry) -> None` — `@require` entry timestamp is UTC; `@beartype`
