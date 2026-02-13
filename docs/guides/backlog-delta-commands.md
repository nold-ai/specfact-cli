---
layout: default
title: Backlog Delta Commands
permalink: /guides/backlog-delta-commands/
---

# Backlog Delta Commands

`delta` commands are grouped under backlog because they describe backlog graph drift and impact, not source-code diffs.

## Command Group

```bash
specfact backlog delta status --project-id <id> --adapter <github|ado>
specfact backlog delta impact <item-id> --project-id <id> --adapter <github|ado>
specfact backlog delta cost-estimate --project-id <id> --adapter <github|ado>
specfact backlog delta rollback-analysis --project-id <id> --adapter <github|ado>
```

## What Each Command Does

- `status`: compares current graph vs baseline and summarizes added/updated/deleted nodes and edges.
- `impact`: traces downstream effects for a changed item.
- `cost-estimate`: estimates effort from detected delta scope.
- `rollback-analysis`: identifies likely breakage if recent delta is reverted.

## Baseline

`status`, `cost-estimate`, and `rollback-analysis` rely on a backlog baseline graph (default `.specfact/backlog-baseline.json`).

Generate/update baseline with:

```bash
specfact project snapshot --bundle <bundle>
```
