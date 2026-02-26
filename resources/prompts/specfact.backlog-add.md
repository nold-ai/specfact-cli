---
description: "Create backlog items with guided interactive flow and hierarchy checks"
---

# SpecFact Backlog Add Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Create a new backlog item in GitHub or Azure DevOps using the `specfact backlog add` workflow. The command supports interactive prompts, parent hierarchy validation, DoR checks, and provider-specific fields.

**When to use:** Adding new work items (epic/feature/story/task/bug) with consistent quality and parent-child structure.

**Quick:** `/specfact.backlog-add --adapter github --project-id owner/repo --type story --title "..."`

## Parameters

### Required

- `--adapter ADAPTER` - Backlog adapter (`github`, `ado`)
- `--project-id PROJECT` - Project context
  - GitHub: `owner/repo`
  - ADO: `org/project`

### Common options

- `--type TYPE` - Backlog item type (provider/template specific)
- `--title TITLE` - Item title
- `--body BODY` - Item body/description
- `--parent PARENT_ID` - Optional parent issue/work item id
- `--non-interactive` - Disable prompt flow and require explicit inputs
- `--check-dor` - Run Definition of Ready checks before create
- `--template TEMPLATE` - Optional backlog template override
- `--custom-config PATH` - Optional mapping/config override file

### Adapter-specific options

- GitHub:
  - `--repo-owner OWNER`
  - `--repo-name NAME`
  - `--github-token TOKEN` (or `GITHUB_TOKEN`)
- Azure DevOps:
  - `--ado-org ORG`
  - `--ado-project PROJECT`
  - `--ado-token TOKEN` (or `AZURE_DEVOPS_TOKEN`)
  - `--ado-base-url URL` (optional)

## Workflow

### Step 1: Execute command

Run the CLI command with user arguments:

```bash
specfact backlog add [OPTIONS]
```

### Step 2: Interactive completion (if inputs are missing)

- Prompt for missing required fields.
- Prompt for optional quality fields (acceptance criteria, points, priority) when supported.
- Validate parent selection and allowed hierarchy before create.

### Step 3: Confirm and create

- Show planned create payload summary.
- Execute provider create operation.
- Return created item id/key/url.

## CLI Enforcement

- Always execute `specfact backlog add` for creation.
- Do not create provider issues/work items directly outside CLI unless user explicitly requests a manual path.

## Input Contract

- This command does not use `--export-to-tmp`/`--import-from-tmp` artifacts.
- Provide values through CLI options or interactive prompts; do not fabricate external tmp-file schemas.
- Do not ask Copilot to output `## Item N:` sections, `**ID**` labels, or markdown tmp files for this command.

## Context

{ARGS}
