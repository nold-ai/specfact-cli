---
layout: default
title: Tutorial - Backlog Quickstart Demo (GitHub + ADO)
description: Short end-to-end demo for backlog init-config, map-fields, daily, and refine on GitHub and Azure DevOps.
permalink: /getting-started/tutorial-backlog-quickstart-demo/
---

# Tutorial: Backlog Quickstart Demo (GitHub + ADO)

This is a short, copy/paste-friendly demo for new users covering:

1. `specfact backlog init-config`
2. `specfact backlog map-fields`
3. `specfact backlog daily`
4. `specfact backlog refine` (GitHub + ADO)

It also includes a minimal create/check loop using `specfact backlog add`.

Preferred ceremony aliases:

- `specfact backlog ceremony standup` (same behavior as `backlog daily`)
- `specfact backlog ceremony refinement` (same behavior as `backlog refine`)

## Targets Used in This Demo

- **GitHub**: `nold-ai/specfact-demo-repo`
- **Azure DevOps**: `dominikusnold/Specfact CLI`

## Prerequisites

- SpecFact CLI installed
- Auth configured:

```bash
specfact backlog auth github
specfact backlog auth azure-devops
specfact backlog auth status
```

Expected status should show both providers as valid.

## 1) Initialize Backlog Config

```bash
specfact backlog init-config --force
```

This creates `.specfact/backlog-config.yaml`.

## 2) Map Fields (ADO)

Run field mapping for your ADO project. This command is interactive by design.

```bash
specfact backlog map-fields \
  --provider ado \
  --ado-org dominikusnold \
  --ado-project "Specfact CLI" \
  --ado-framework scrum
```

Notes:

- Select the process style intentionally (`--ado-framework scrum|agile|safe|kanban|default`).
- Mapping is written to `.specfact/templates/backlog/field_mappings/ado_custom.yaml`.
- Provider context is updated in `.specfact/backlog.yaml`.

Optional reset:

```bash
specfact backlog map-fields \
  --provider ado \
  --ado-org dominikusnold \
  --ado-project "Specfact CLI" \
  --ado-framework scrum \
  --reset
```

## 3) Daily Standup View (Check Backlog Read)

GitHub:

```bash
specfact backlog daily github \
  --repo-owner nold-ai \
  --repo-name specfact-demo-repo \
  --state open \
  --limit 5
```

Disable default state/assignee filters explicitly (for exact ID checks):

```bash
specfact backlog daily github \
  --repo-owner nold-ai \
  --repo-name specfact-demo-repo \
  --id 28 \
  --state any \
  --assignee any
```

ADO:

```bash
specfact backlog daily ado \
  --ado-org dominikusnold \
  --ado-project "Specfact CLI" \
  --limit 5
```

## 4) Refine Workflow (Preview + Tmp Export/Import)

GitHub export:

```bash
specfact backlog refine github \
  --repo-owner nold-ai \
  --repo-name specfact-demo-repo \
  --limit 3 \
  --export-to-tmp
```

ADO export:

```bash
specfact backlog refine ado \
  --ado-org dominikusnold \
  --ado-project "Specfact CLI" \
  --limit 3 \
  --export-to-tmp
```

After refining in your AI IDE, import and write back:

```bash
# GitHub
specfact backlog refine github \
  --repo-owner nold-ai \
  --repo-name specfact-demo-repo \
  --import-from-tmp \
  --write

# ADO
specfact backlog refine ado \
  --ado-org dominikusnold \
  --ado-project "Specfact CLI" \
  --import-from-tmp \
  --write
```

### Required Tmp File Contract (Important)

For `--import-from-tmp`, each item block must keep:

- `## Item N: <title>`
- `**ID**: <original-id>` (mandatory, unchanged)
- `**URL**`, `**State**`, `**Provider**`
- `**Body**:` fenced with ```markdown

Minimal scaffold:

````markdown
## Item 1: Example title

**ID**: 123
**URL**: https://example
**State**: Active
**Provider**: ado

**Body**:
```markdown
## As a
...
```
````

Do not rename labels and do not remove details during refinement.

## 5) Minimal Create + Check Loop

Create test issue/work item:

```bash
# GitHub create
specfact backlog add \
  --adapter github \
  --project-id nold-ai/specfact-demo-repo \
  --type story \
  --title "SpecFact demo smoke test $(date +%Y-%m-%d-%H%M)" \
  --body "Demo item created by quickstart." \
  --acceptance-criteria "Demo item exists and is retrievable" \
  --non-interactive

# ADO create
specfact backlog add \
  --adapter ado \
  --project-id "dominikusnold/Specfact CLI" \
  --type story \
  --title "SpecFact demo smoke test $(date +%Y-%m-%d-%H%M)" \
  --body "Demo item created by quickstart." \
  --acceptance-criteria "Demo item exists and is retrievable" \
  --non-interactive
```

Then verify retrieval by ID using `daily` or `refine --id <id>`.

## Quick Troubleshooting

- DNS/network errors (`api.github.com`, `dev.azure.com`): verify outbound network access.
- Auth errors: re-run `specfact backlog auth status`.
- ADO mapping issues: re-run `backlog map-fields` and confirm `--ado-framework` is correct.
- Refine import mismatch: check `**ID**` was preserved exactly.

## ADO Hardening Profile (Corporate Networks)

For unstable corporate VPN/proxy/firewall paths, use this reliability profile.

### Runtime behavior now hardened in CLI

- ADO `daily`/`refine` read paths now retry transient transport failures (`ConnectionError`, reset/disconnect, timeout).
- Retry policy also covers retryable HTTP statuses (`429`, `500`, `502`, `503`, `504`) with backoff.
- Hardened paths include:
  - WIQL query execution
  - Work-item batch fetch
  - Iteration/team lookup
  - Work-item comments fetch

### Operational command recommendations

Use explicit provider context and bounded scope to reduce query fragility:

```bash
# Daily: explicit scope
specfact backlog daily ado \
  --ado-org dominikusnold \
  --ado-project "Specfact CLI" \
  --state New \
  --limit 20

# Refine: small batches first, then scale
specfact backlog refine ado \
  --ado-org dominikusnold \
  --ado-project "Specfact CLI" \
  --state New \
  --limit 5 \
  --export-to-tmp
```

If current iteration auto-detection is unreliable in your environment, pass explicit filters (`--state`, `--sprint`, `--iteration`) rather than relying on defaults.

### Create flow reliability notes

- `backlog add` uses safe no-replay behavior for create operations to avoid accidental duplicate work-item creation on ambiguous transport failures.
- If create returns an ambiguous transport error, check ADO for the title before retrying manually.
