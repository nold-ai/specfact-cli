---
layout: default
title: Team Collaboration Workflow
permalink: /team-collaboration-workflow/
---

# Team Collaboration Workflow

> **Complete guide to using SpecFact CLI for team collaboration with persona-based workflows**

---

## Overview

SpecFact CLI supports team collaboration through persona-based workflows where different roles (Product Owner, Architect, Developer) work on different aspects of the project using Markdown files. This guide explains when and how to use the team collaboration commands.

**Related**: [Agile/Scrum Workflows](agile-scrum-workflows.md) - Complete persona-based collaboration guide

---

## When to Use Team Collaboration Commands

Use these commands when:

- **Multiple team members** need to work on the same project bundle
- **Different roles** (Product Owner, Architect, Developer) need to edit different sections
- **Concurrent editing** needs to be managed safely
- **Version control** integration is needed for team workflows

---

## Core Commands

### `project init-personas`

Initialize persona definitions for a project bundle.

**When to use**: First-time setup for team collaboration.

**Example**:

```bash
specfact project init-personas --bundle my-project
```

**Related**: [Agile/Scrum Workflows - Persona Setup](agile-scrum-workflows.md#persona-based-workflows)

---

### `project export`

Export persona-specific Markdown artifacts for editing.

**When to use**: When a team member needs to edit their role-specific sections.

**Example**:

```bash
# Export Product Owner view
specfact project export --bundle my-project --persona product-owner

# Export Developer view
specfact project export --bundle my-project --persona developer

# Export Architect view
specfact project export --bundle my-project --persona architect
```

**Workflow**: Export → Edit in Markdown → Import back

**Related**: [Agile/Scrum Workflows - Exporting Persona Artifacts](agile-scrum-workflows.md#exporting-persona-artifacts)

---

### `project import`

Import persona edits from Markdown files back into the project bundle.

**When to use**: After editing exported Markdown files.

**Example**:

```bash
# Import Product Owner edits
specfact project import --bundle my-project --persona product-owner --source docs/backlog.md

# Dry-run to validate without applying
specfact project import --bundle my-project --persona product-owner --source docs/backlog.md --dry-run
```

**Workflow**: Export → Edit → Import → Validate

**Related**: [Agile/Scrum Workflows - Importing Persona Edits](agile-scrum-workflows.md#importing-persona-edits)

---

### `project lock` / `project unlock`

Lock sections to prevent concurrent edits.

**When to use**: When multiple team members might edit the same section simultaneously.

**Example**:

```bash
# Lock a section for editing
specfact project lock --bundle my-project --section idea --persona product-owner

# Edit and import
specfact project export --bundle my-project --persona product-owner
# ... edit exported file ...
specfact project import --bundle my-project --persona product-owner --source backlog.md

# Unlock when done
specfact project unlock --bundle my-project --section idea
```

**Workflow**: Lock → Export → Edit → Import → Unlock

**Related**: [Agile/Scrum Workflows - Section Locking](agile-scrum-workflows.md#section-locking)

---

### `project locks`

List all locked sections.

**When to use**: Before starting work to see what's locked.

**Example**:

```bash
specfact project locks --bundle my-project
```

**Related**: [Agile/Scrum Workflows - Checking Locks](agile-scrum-workflows.md#checking-locks)

---

## Complete Workflow Example

### Scenario: Product Owner Updates Backlog

```bash
# 1. Check what's locked
specfact project locks --bundle my-project

# 2. Lock the section you need
specfact project lock --bundle my-project --section idea --persona product-owner

# 3. Export your view
specfact project export --bundle my-project --persona product-owner --output backlog.md

# 4. Edit backlog.md in your preferred editor

# 5. Import changes back
specfact project import --bundle my-project --persona product-owner --source backlog.md

# 6. Unlock the section
specfact project unlock --bundle my-project --section idea
```

---

## Integration with Version Management

Team collaboration integrates with version management:

```bash
# After importing changes, check if version bump is needed
specfact project version check --bundle my-project

# If needed, bump version
specfact project version bump --bundle my-project --type minor
```

**Related**: [Project Version Management](../reference/commands.md#project-version)

---

## Integration with Command Chains

Team collaboration commands are part of the **Plan Promotion & Release Chain**:

1. Export persona views
2. Edit in Markdown
3. Import back
4. Review plan
5. Enforce SDD
6. Promote plan
7. Bump version

**Related**: [Plan Promotion & Release Chain](command-chains.md#5-plan-promotion--release-chain)

---

## See Also

- [Agile/Scrum Workflows](agile-scrum-workflows.md) - Complete persona-based collaboration guide
- [Command Chains Reference](command-chains.md) - Complete workflows
- [Common Tasks Index](common-tasks.md) - Quick reference
- [Project Commands Reference](../reference/commands.md#project---project-bundle-management) - Complete command documentation
