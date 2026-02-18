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
- `specfact policy validate` to evaluate configured rules deterministically against policy input artifacts.
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
specfact policy validate --repo . --format both
```

Artifact resolution order when `--snapshot` is omitted:

1. `.specfact/backlog-baseline.json`
2. Latest `.specfact/plans/backlog-*.yaml|yml|json`

You can still override with an explicit path:

```bash
specfact policy validate --repo . --snapshot ./snapshot.json --format both
```

Filter and scope output:

```bash
# only one rule family, max 20 findings
specfact policy validate --repo . --rule scrum.dor --limit 20 --format json

# item-centric grouped output
specfact policy validate --repo . --group-by-item --format both

# in grouped mode, --limit applies to item groups
specfact policy validate --repo . --group-by-item --limit 4 --format json
```

Output formats:

- `json`
- `markdown`
- `both`

When config is missing or invalid, the command prints a docs hint pointing back to this policy format guidance.

### Suggest Policy Fixes

Generate suggestions from validation findings:

```bash
specfact policy suggest --repo .
```

Suggestion shaping options:

```bash
# suggestions for one rule family, limited output
specfact policy suggest --repo . --rule scrum.dod --limit 10

# grouped suggestions by backlog item index
specfact policy suggest --repo . --group-by-item

# grouped mode limits item groups, not per-item fields
specfact policy suggest --repo . --group-by-item --limit 4
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

## Accepted Policy Input Shapes

Policy commands normalize these payload structures:

- `[{...}, {...}]`
- `{ items: [{...}, {...}] }`
- `{ items: { "ID-1": {...}, "ID-2": {...} } }`
- `{ backlog_graph: { items: [...] } }`
- `{ backlog_graph: { items: { "ID-1": {...} } } }`

## Compatibility Mapping for Imported Artifacts

Before evaluating rules, policy input normalization maps common aliases to canonical policy fields:

- `acceptance_criteria` from aliases such as `acceptanceCriteria`, `System.AcceptanceCriteria`, or description section `## Acceptance Criteria`
- `business_value` from aliases such as `businessValue` or `Microsoft.VSTS.Common.BusinessValue`
- `definition_of_done` from aliases such as `definitionOfDone` or description section `## Definition of Done`
