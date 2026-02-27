---
layout: default
title: Custom registries
permalink: /guides/custom-registries/
description: Add, list, and manage custom module registries with trust levels and priority.
---

# Custom registries

SpecFact can use multiple module registries: the official registry plus private or third-party registries. You control which registries are used, their priority, and how much to trust them.

## Adding registries

```bash
# Add by URL (id derived from URL if not given)
specfact module add-registry https://company.example.com/specfact/registry/index.json

# With explicit id, priority, and trust
specfact module add-registry https://company.example.com/specfact/registry/index.json \
  --id company-registry \
  --priority 10 \
  --trust always
```

- **URL**: Must point to a JSON index that follows the same schema as the official registry (e.g. `modules` array with `id`, `latest_version`, `description`, etc.).
- **--id**: Optional. Default is derived from the URL or `custom`. Use a short, stable id for `remove-registry` and for the **Registry** column in search results.
- **--priority**: Optional. Lower number = higher priority. Default is next available (after existing priorities). Official registry is always first.
- **--trust**: `always` (use without prompting), `prompt` (ask once per registry), or `never` (do not use). Default is `prompt`.

Config is stored in `~/.specfact/config/registries.yaml`.

## Listing and removing

```bash
# List all configured registries (official + custom)
specfact module list-registries

# Remove a custom registry by id
specfact module remove-registry company-registry
```

The official registry cannot be removed; only custom entries are modified.

## Trust levels

| Trust    | Behavior |
|----------|----------|
| `always` | Use this registry without prompting. Prefer for internal/private registries. |
| `prompt` | Ask the user once whether to trust this registry (e.g. first install/search from it). |
| `never`  | Do not use this registry. Use to disable without removing the config. |

Choose `always` for fully controlled internal registries; use `prompt` for unknown or third-party registries.

## Priority

When multiple registries are configured, they are queried in order: official first, then custom registries by ascending priority number. Search and install use this order; the first matching module id wins. Use priority to prefer an internal registry over the official one for overlapping names (e.g. `specfact/backlog` from your mirror).

## Search across registries

`specfact module search <query>` queries all configured registries and local modules. Results include a **Registry** column when more than one registry is configured, so you can see which registry each module came from.

## Enterprise use

- **Private index**: Host a JSON index (and tarballs) on an internal server or artifact store. Add it with `add-registry` and `--trust always`.
- **Air-gapped / proxy**: Serve a mirror of the official index (and artifacts) behind your proxy; point `add-registry` at the mirror URL.
- **Multiple teams**: Use different registry ids and priorities so team-specific registries are tried in the right order.

## Security considerations

- Only add registries from trusted sources; index and tarballs can be tampered with if the server is compromised.
- Use HTTPS for registry URLs.
- Integrity checks (checksum/signature) still apply to downloaded modules; custom registries do not bypass verification.

## See also

- [Module marketplace](module-marketplace.md) – Discovery and security model.
- [Installing modules](installing-modules.md) – Install, list, search, and upgrade.
- [Publishing modules](publishing-modules.md) – Package and publish modules to a registry.
