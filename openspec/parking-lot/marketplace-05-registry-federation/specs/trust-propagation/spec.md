# trust-propagation Specification

## Purpose

Defines how effective module trust tier is calculated as the minimum of publisher tier and registry tier, and how this propagates to search output badges and install policy.

## MODIFIED Requirements

### Requirement: Effective trust = min(publisher_tier, registry_tier)

The CLI SHALL resolve effective trust tier as the minimum (by rank) of the publisher's tier and the registry's effective tier.

#### Scenario: Verified publisher from verified registry

- **GIVEN** publisher tier = `verified`, registry effective_tier = `verified`
- **WHEN** CLI resolves effective tier
- **THEN** effective_tier = `verified`

#### Scenario: Official publisher from verified registry

- **GIVEN** publisher tier = `official`, registry effective_tier = `verified`
- **WHEN** CLI resolves effective tier
- **THEN** effective_tier = `official` (official publisher outranks registry tier)

#### Scenario: Verified publisher from community registry

- **GIVEN** publisher tier = `verified`, registry effective_tier = `community`
- **WHEN** CLI resolves effective tier
- **THEN** effective_tier = `community` (registry tier caps the effective tier)

#### Scenario: Verified publisher from local-trust registry

- **GIVEN** publisher tier = `verified`, registry effective_tier = `local`
- **WHEN** CLI resolves effective tier
- **THEN** effective_tier = `local`
- **AND** module is shown as `[local]` in search output regardless of publisher tier

#### Scenario: Any publisher from unregistered registry

- **GIVEN** registry_tier = `unregistered` (registry added without any cert or trust-local flag)
- **WHEN** CLI resolves effective tier
- **THEN** effective_tier = `unregistered`
- **AND** install is blocked unless `--trust-unregistered`

### Requirement: Trust tier badges in search output reflect effective tier

Search output SHALL display the effective tier (min of publisher_tier and registry_tier), not the raw publisher tier.

#### Scenario: Search output shows effective tier badge

- **GIVEN** a module from a `verified` publisher served by a `community` registry
- **WHEN** user runs `specfact module search <term>`
- **THEN** the module entry SHALL show `[community]` (effective tier, not publisher tier)
- **AND** the raw publisher tier SHALL be visible in `specfact module info` but not in search list view

#### Scenario: Local-trust module badge in search

- **GIVEN** a module from a `--trust-local` registry
- **WHEN** user runs `specfact module search <term>`
- **THEN** the module entry SHALL show `[local]` badge
- **AND** SHALL NOT show `[verified]` or `[community]` even if the publisher record is verified

### Requirement: Install policy uses effective tier (not publisher tier)

The install gate SHALL use effective_tier (publisher ∩ registry) for all policy decisions, not the raw publisher tier.

#### Scenario: Community-effective module requires prompt even if publisher is verified

- **GIVEN** effective_tier = `community` (verified publisher + community registry)
- **WHEN** user installs the module without `--trust-community`
- **THEN** CLI SHALL apply community install policy (warn + prompt)
- **AND** SHALL display: `[WARN] Registry for this module is community-certified. Publisher is verified, but registry is not. Install anyway? [y/N]`

## Contract Requirements

- `resolve_effective_tier(publisher_tier: str, registry_tier: str) -> str` — extended to include `local` in tier rank order; `@ensure` result in {"official", "verified", "community", "local", "unregistered"}; `@beartype`
- Tier rank order (for min resolution): `official(4) > verified(3) > community(2) > local(1) > unregistered(0)`
