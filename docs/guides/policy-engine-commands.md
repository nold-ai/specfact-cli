---
layout: default
title: Policy Engine Commands
permalink: /guides/policy-engine-commands/
---

# Policy Engine Commands

Use SpecFact policy commands to scaffold, validate, and improve policy configuration for common frameworks.

## Overview

The policy engine currently supports:

- `specfact policy init` to scaffold `.specfact/policy.yaml` from a built-in template.
- `specfact policy validate` to evaluate configured rules deterministically against a snapshot.
- `specfact policy suggest` to generate confidence-scored, patch-ready recommendations (no automatic writes).

## Commands

### Initialize Policy Config

Create a starter policy configuration file:

```bash
specfact policy init --repo . --template scrum
```

Supported templates:

- `scrum`
- `kanban`
- `safe`
- `mixed`

Interactive mode (template prompt):

```bash
specfact policy init --repo .
```

The command writes `.specfact/policy.yaml`. Use `--force` to overwrite an existing file.

### Validate Policies

Run policy checks with deterministic output:

```bash
specfact policy validate --repo . --snapshot ./snapshot.json --format both
```

Output formats:

- `json`
- `markdown`
- `both`

When config is missing or invalid, the command prints a docs hint pointing back to this policy format guidance.

### Suggest Policy Fixes

Generate suggestions from validation findings:

```bash
specfact policy suggest --repo . --snapshot ./snapshot.json
```

Suggestions include confidence scores and patch-ready structure, but no file is modified automatically.

## Policy File Location and Format

Expected location:

- `.specfact/policy.yaml`

Minimal structure:

```yaml
scrum:
  dor_required_fields: [acceptance_criteria]
  dod_required_fields: [definition_of_done]
kanban:
  columns:
    In Progress:
      exit_required_fields: [qa_status]
safe:
  pi_readiness_required_fields: [risk_owner]
```

## Template Assets

Built-in templates are shipped from:

- `resources/templates/policies/`

These templates are intended as a starting point and should be adjusted to team/project policy needs.
