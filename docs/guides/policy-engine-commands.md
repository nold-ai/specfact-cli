---
layout: default
title: Policy Engine Commands
permalink: /guides/policy-engine-commands/
---

# Policy Engine Commands


> Modules docs handoff: this page remains in the core docs set as release-line overview content.
> Canonical bundle-specific deep guidance now lives in the canonical modules docs site, currently
> published at `https://modules.specfact.io/`.

> **Note**: `backlog policy` commands were removed. The equivalent workflows are now under `backlog verify-readiness`, `backlog refine`, and `backlog ceremony`.

Use SpecFact policy commands to validate readiness, refine backlog items, and run agile ceremonies.

## Overview

The policy engine currently supports:

- `specfact backlog verify-readiness` to evaluate configured rules deterministically against policy input artifacts.
- `specfact backlog refine` to generate confidence-scored, patch-ready recommendations (no automatic writes).
- `specfact backlog ceremony` to run agile ceremonies (standup, refinement, etc.).

## Commands

### Verify Readiness

Check that backlog items meet Definition of Ready / Definition of Done criteria:

```bash
specfact backlog verify-readiness --repo . --format both
```

Artifact resolution order when `--snapshot` is omitted:

1. `.specfact/backlog-baseline.json`
2. Latest `.specfact/plans/backlog-*.yaml|yml|json`

You can still override with an explicit path:

```bash
specfact backlog verify-readiness --repo . --snapshot ./snapshot.json --format both
```

Filter and scope output:

```bash
# only one rule family, max 20 findings
specfact backlog verify-readiness --repo . --rule scrum.dor --limit 20 --format json

# item-centric grouped output
specfact backlog verify-readiness --repo . --group-by-item --format both

# in grouped mode, --limit applies to item groups
specfact backlog verify-readiness --repo . --group-by-item --limit 4 --format json
```

Output formats:

- `json`
- `markdown`
- `both`

When config is missing or invalid, the command prints a docs hint pointing back to this policy format guidance.

### Refine Backlog Items

Generate suggestions from readiness findings:

```bash
specfact backlog refine --repo .
```

Suggestion shaping options:

```bash
# suggestions for one rule family, limited output
specfact backlog refine --repo . --rule scrum.dod --limit 10

# grouped suggestions by backlog item index
specfact backlog refine --repo . --group-by-item

# grouped mode limits item groups, not per-item fields
specfact backlog refine --repo . --group-by-item --limit 4
```

Suggestions include confidence scores and patch-ready structure, but no file is modified automatically.

### Run Agile Ceremonies

Run standup or refinement ceremonies:

```bash
specfact backlog ceremony standup
specfact backlog ceremony refinement
```

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
