# grace-window-policy Specification

## Purpose

Defines the by-reason grace window policy governing CLI behaviour during and after revocation grace windows. Centralised in `trust/revocation.py` — no per-module special cases.

## ADDED Requirements

### Requirement: Grace window policy is centralized and by-reason

The CLI SHALL apply grace windows based only on revocation reason code. No per-publisher or per-module override is permitted in the CLI (NOLD AI may adjust reason in the signed record, which is the override mechanism).

#### Scenario: security_incident — immediate hard block

- **GIVEN** a revocation entry with `reason: security_incident`
- **WHEN** CLI checks revocation at any point (install or invocation)
- **THEN** `grace_days = 0`: hard block on install, warn-only on existing invocation
- **AND** No flag combination can override the install block

#### Scenario: policy_violation — 30-day warn window, then hard block

- **GIVEN** a revocation entry with `reason: policy_violation`
- **WHEN** `now - revoked_at <= 30 days`
- **THEN** install shows warning + prompt; invocation shows warning
- **WHEN** `now - revoked_at > 30 days`
- **THEN** install is hard-blocked; invocation shows escalated warning

#### Scenario: publisher_request — 7-day soft warn, then soft block

- **GIVEN** a revocation entry with `reason: publisher_request`
- **WHEN** `now - revoked_at <= 7 days`
- **THEN** install shows warning + prompt; invocation shows informational notice
- **WHEN** `now - revoked_at > 7 days`
- **THEN** install shows warning + prompt (soft block — still installable with confirmation)

#### Scenario: api_incompatibility — 14-day suggest-newer window

- **GIVEN** a revocation entry with `reason: api_incompatibility`
- **WHEN** `now - revoked_at <= 14 days`
- **THEN** install shows: `[WARN] <module>@<version> has a known API incompatibility. Upgrade recommended.` + suggest newer version
- **AND** install is NOT blocked during the 14-day window
- **WHEN** `now - revoked_at > 14 days`
- **THEN** install is soft-blocked (warn + prompt)

### Requirement: Unknown reason code falls back to most restrictive policy

The CLI SHALL apply the most restrictive policy (security_incident equivalent) when an unrecognised revocation reason code is encountered.

#### Scenario: Unknown reason code

- **GIVEN** a revocation entry with an unrecognised `reason` value
- **WHEN** CLI processes the entry
- **THEN** CLI SHALL apply `security_incident` policy (most restrictive)
- **AND** SHALL log `[WARN] Unknown revocation reason '<reason>'; applying most restrictive policy`

## Contract Requirements

- `GRACE_WINDOWS: dict[str, GraceWindowPolicy]` — module-level constant, not overridable at runtime
- `compute_grace_status(revoked_at: datetime, reason: str) -> GraceStatus` — `@require` revoked_at is UTC-aware; `@ensure` result.action in VALID_ACTIONS; `@beartype`
