---
layout: default
title: Project DevOps Flow
permalink: /guides/project-devops-flow/
---

# Project DevOps Flow

Use `specfact project devops-flow` to run an integrated lifecycle against a linked backlog provider.

## Prerequisite

Link the bundle once:

```bash
specfact project link-backlog --bundle <bundle> --adapter <github|ado> --project-id <provider-project-id>
```

## Stage Actions

```bash
specfact project devops-flow --bundle <bundle> --stage plan --action generate-roadmap
specfact project devops-flow --bundle <bundle> --stage develop --action sync
specfact project devops-flow --bundle <bundle> --stage review --action validate-pr
specfact project devops-flow --bundle <bundle> --stage release --action verify
specfact project devops-flow --bundle <bundle> --stage monitor --action health-check
```

Supported pairs are fixed and validated by CLI:

- `plan/generate-roadmap`
- `develop/sync`
- `review/validate-pr`
- `release/verify`
- `monitor/health-check`

## Related Project Commands

```bash
specfact project health-check --bundle <bundle>
specfact project snapshot --bundle <bundle>
specfact project regenerate --bundle <bundle> [--strict] [--verbose]
specfact project export-roadmap --bundle <bundle>
```

`project regenerate` behavior:

- default: summary-only mismatch output, non-failing
- `--verbose`: prints detailed mismatch lines
- `--strict`: exits non-zero when mismatches are detected
