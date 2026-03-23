# Change: Profile & Config Layering System

## Why




SpecFact treats every user the same — a solo developer and an enterprise architecture board get identical defaults, enforcement levels, and module activation. This blocks adoption at both ends: solos drown in ceremony they don't need, enterprises can't enforce baselines across hundreds of repos. A profile-driven initialization that deterministically selects modules, templates, policies, and enforcement modes makes SpecFact scale from single-developer projects to regulated enterprise environments without configuration sprawl.

## Module Package Structure

```
modules/profile/
  module-package.yaml          # name: profile; commands: profile init, profile show, profile diff
  src/profile/
    __init__.py
    main.py                    # typer.Typer app — profile command group
    engine/
      resolver.py              # Config layering: profile defaults → org baseline → repo overlay → dev local
      divergence.py            # Detect and warn when local deviates from org baseline
    models/
      profile_config.py        # ProfileConfig Pydantic model (tier, modules, policy_mode, fields)
    profiles/
      solo.yaml                # Minimal modules, advisory mode, 3 required fields
      startup.yaml             # Team modules (+ sync, ceremonies), advisory → mixed
      mid_size.yaml            # Org modules (+ policy, architecture), mixed mode
      enterprise.yaml          # Full modules (+ marketplace, audit), hard mode
    commands/
      init_profile.py          # specfact init --profile solo|startup|mid-size|enterprise
      show_profile.py          # specfact profile show (resolved config with source annotations)
      diff_profile.py          # specfact profile diff (local vs org baseline divergence)
```

**`module-package.yaml` declares:**
- `name: profile`
- `version: 0.1.0`
- `commands: [profile init, profile show, profile diff]`
- `dependencies: []` (no module deps; foundational)
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## Module Package Structure

```
modules/profile/
  module-package.yaml          # name: profile; commands: profile init, profile show, profile diff
  src/profile/
    __init__.py
    main.py                    # typer.Typer app — profile command group
    engine/
      resolver.py              # Config layering: profile defaults → org baseline → repo overlay → dev local
      divergence.py            # Detect and warn when local deviates from org baseline
    models/
      profile_config.py        # ProfileConfig Pydantic model (tier, modules, policy_mode, fields)
    profiles/
      solo.yaml                # Minimal modules, advisory mode, 3 required fields
      startup.yaml             # Team modules (+ sync, ceremonies), advisory → mixed
      mid_size.yaml            # Org modules (+ policy, architecture), mixed mode
      enterprise.yaml          # Full modules (+ marketplace, audit), hard mode
    commands/
      init_profile.py          # specfact init --profile solo|startup|mid-size|enterprise
      show_profile.py          # specfact profile show (resolved config with source annotations)
      diff_profile.py          # specfact profile diff (local vs org baseline divergence)
```

**`module-package.yaml` declares:**
- `name: profile`
- `version: 0.1.0`
- `commands: [profile init, profile show, profile diff]`
- `dependencies: []` (no module deps; foundational)
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## What Changes




- **NEW**: Profile module in `modules/profile/` with config layering engine: profile defaults → org baseline (read-only) → repo overlay → developer local. Highest priority last.
- **NEW**: Four built-in profiles shipped as YAML (`solo.yaml`, `startup.yaml`, `mid_size.yaml`, `enterprise.yaml`) defining: enabled modules, policy enforcement mode, required requirements fields, config sources, and enforcement location.
- **EXTEND**: Tier profiles also define the default clean-code pack mode inherited by `specfact/clean-code-principles`: `solo -> advisory`, `startup -> advisory then mixed`, `mid_size -> mixed`, `enterprise -> hard`.
- **NEW**: Config file `.specfact/profile.yaml` (or extend existing `.specfact/config.yaml`) storing selected profile, config source URIs, and local overlays.
- **NEW**: `specfact init --profile <tier>` generates profile-appropriate config and activates tier-relevant modules.
- **NEW**: `specfact profile show` displays the fully resolved config with annotations showing which layer each value came from.
- **NEW**: `specfact profile diff` detects and warns when local config deviates from the org baseline.
- **EXTEND**: `specfact init` extended with `--profile` flag; existing init behavior preserved as implicit `solo` profile when no flag is passed.

### Profile Behavior Matrix

| Capability | Solo | Startup | Mid-size | Enterprise |
|---|---|---|---|---|
| Modules enabled | minimal (backlog, validate, requirements-light) | team (+ sync, ceremonies) | org (+ policy, architecture) | full (+ marketplace, audit) |
| Policy mode | advisory | advisory → mixed | mixed | hard (with exceptions) |
| Requirements fields | As_a/I_want/So_that only | + Business_outcome, Business_rules | Org-defined schema | Regulated + domain overlays |
| Config sources | local only | local + optional org | org baseline + local overlay | org baseline (read-only) + BU overlays |
| Enforcement location | local warnings only | local + CI advisory | CI mixed (some hard) | CI hard-fail + evidence |

## Capabilities
### New Capabilities

- `profile-config-layering`: Profile-driven config resolution with deterministic layering (profile defaults → org baseline → repo overlay → dev local), divergence detection, and tier-aware module/policy activation.
- `profile-config-layering`: Extended so clean-code enforcement defaults are derived from the selected tier instead of a parallel clean-code profile concept.

### Modified Capabilities

- `init-module-state`: Extended with `--profile` flag for tier-aware initialization; default behavior preserved as implicit `solo` profile.


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #237
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/237>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: d7dfe1519fa64668 -->
