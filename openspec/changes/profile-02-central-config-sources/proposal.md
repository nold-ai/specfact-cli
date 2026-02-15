# Change: Central Config Sources — Org Baselines with Local Overlays

## Why




Mid-size and enterprise teams need centralized configuration baselines that individual repos inherit without copy-pasting. Today every repo has its own `.specfact/config.yaml`, leading to configuration drift across hundreds of repos. A read-only central config source that repos pull from — with local overlays and divergence warnings — gives organizations consistent governance while letting individual teams adapt to their specific needs.

## What Changes




- **NEW**: Config source declaration in `.specfact/profile.yaml`:
  ```yaml
  config_sources:
    - git+ssh://github.com/myorg/engineering-standards/.specfact  # Read-only baseline
    - git+https://github.com/myorg/payments-team/.specfact       # BU overlay
  overlay:
    policy_mode: mixed  # Local override (highest priority)
  ```
- **NEW**: `specfact profile pull` — fetch and cache central config sources locally (`.specfact/cache/config-sources/`)
- **NEW**: `specfact profile diff` (extended) — compare local resolved config against central baseline, showing divergence with source annotations
- **NEW**: Config resolution order: profile defaults → central baselines (in order) → local overlay. Central baselines are **read-only** — local changes cannot modify them, only override via overlay.
- **NEW**: Divergence detection and warnings: when local config deviates from central baseline, warn on every `specfact validate` and `specfact init` run
- **NEW**: Staleness detection: warn when cached central config is older than configurable threshold (default 7 days)
- **NEW**: Git-based config sources: support `git+ssh://` and `git+https://` URIs pointing to a repo path containing `.specfact/` config files
- **EXTEND**: Profile module (profile-01) extended with central config resolution and pull commands

## Capabilities
### New Capabilities

- `central-config-sources`: Read-only central configuration baselines with git-based source URIs, local overlay support, divergence detection, staleness warnings, and cached resolution. Organizations define baselines once, repos inherit and optionally override.

### Modified Capabilities

- `profile-config-layering`: Extended with central config source resolution in the layering order (profile defaults → central baselines → local overlay)


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #249
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/249>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: c1cabe4676d20083 -->