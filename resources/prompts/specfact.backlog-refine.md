---
description: "Refine backlog items using template-driven AI assistance"
---

# SpecFact Backlog Refinement Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Refine backlog items from DevOps tools (GitHub Issues, Azure DevOps, etc.) into structured, template-compliant work items using AI-assisted refinement with template detection and validation.

**When to use:** Standardizing backlog items, enforcing corporate templates (user stories, defects, spikes, enablers), preparing items for sprint planning.

**Quick:** `/specfact.backlog-refine --adapter github --labels feature,enhancement` or `/specfact.backlog-refine --adapter ado --sprint "Sprint 1"`

## Parameters

### Required

- `ADAPTER` - Backlog adapter name (github, ado, etc.)

### Adapter Configuration (Required for GitHub/ADO)

**GitHub Adapter:**

- `--repo-owner OWNER` - GitHub repository owner (required for GitHub adapter)
- `--repo-name NAME` - GitHub repository name (required for GitHub adapter)
- `--github-token TOKEN` - GitHub API token (optional, uses GITHUB_TOKEN env var or gh CLI if not provided)

**Azure DevOps Adapter:**

- `--ado-org ORG` - Azure DevOps organization or collection name (required for ADO adapter, except when collection is in base_url)
- `--ado-project PROJECT` - Azure DevOps project (required for ADO adapter)
- `--ado-team TEAM` - Azure DevOps team name (optional, defaults to project name for iteration lookup)
- `--ado-base-url URL` - Azure DevOps base URL (optional, defaults to `https://dev.azure.com` for cloud)
  - **Cloud**: `https://dev.azure.com` (default)
  - **On-premise**: `https://server` or `https://server/tfs/collection` (if collection included)
- `--ado-token TOKEN` - Azure DevOps PAT (optional, uses AZURE_DEVOPS_TOKEN env var or stored token if not provided)

**ADO Configuration Notes:**

- **Cloud (Azure DevOps Services)**: Always requires `--ado-org` and `--ado-project`. Base URL defaults to `https://dev.azure.com`.
- **On-premise (Azure DevOps Server)**:
  - If base URL includes collection (e.g., `https://server/tfs/DefaultCollection`), `--ado-org` is optional.
  - If base URL doesn't include collection, provide collection name via `--ado-org`.
- **API Endpoints**:
  - WIQL queries use POST to `{base_url}/{org}/{project}/_apis/wit/wiql?api-version=7.1` (project-level)
  - Work items batch GET uses `{base_url}/{org}/_apis/wit/workitems?ids={ids}&api-version=7.1` (organization-level)
  - The `api-version` parameter is **required** for all ADO API calls

### Filters

- `--labels LABELS` or `--tags TAGS` - Filter by labels/tags (comma-separated, e.g., "feature,enhancement")
- `--state STATE` - Filter by state (case-insensitive, e.g., "open", "closed", "Active", "New")
- `--assignee USERNAME` - Filter by assignee (case-insensitive):
  - **GitHub**: Login or @username (e.g., "johndoe" or "@johndoe")
  - **ADO**: displayName, uniqueName, or mail (e.g., "Jane Doe" or `"jane.doe@example.com"`)
- `--iteration PATH` - Filter by iteration path (ADO format: "Project\\Sprint 1", case-insensitive)
- `--sprint SPRINT` - Filter by sprint (case-insensitive):
  - **ADO**: Use full iteration path (e.g., "Project\\Sprint 1") to avoid ambiguity when multiple sprints share the same name
  - If omitted, defaults to current active iteration for the team
  - Ambiguous name-only matches will prompt for explicit iteration path
- `--release RELEASE` - Filter by release identifier (case-insensitive)
- `--limit N` - Maximum number of items to process in this refinement session (caps batch size)
- `--ignore-refined` / `--no-ignore-refined` - When set (default), exclude already-refined items so `--limit` applies to items that need refinement. Use `--no-ignore-refined` to process the first N items in order.
- `--id ISSUE_ID` - Refine only this backlog item (issue or work item ID). Other items are ignored.
- `--persona PERSONA` - Filter templates by persona (product-owner, architect, developer)
- `--framework FRAMEWORK` - Filter templates by framework (agile, scrum, safe, kanban)

### Template Selection

- `--template TEMPLATE_ID` or `-t TEMPLATE_ID` - Target template ID (default: auto-detect)
- `--auto-accept-high-confidence` - Auto-accept refinements with confidence >= 0.85

### Preview and Writeback

- `--preview` / `--no-preview` - Preview mode: show what will be written without updating backlog (default: --preview)
  - **Preview mode shows**: Full item details (title, body, metrics, acceptance_criteria, work_item_type, etc.)
  - **Preview mode skips**: Interactive refinement prompts (use `--write` to enable interactive refinement)
- `--write` - Write mode: explicitly opt-in to update remote backlog (requires --write flag)

### Export/Import for Copilot Processing

- `--export-to-tmp` - Export backlog items to temporary file for copilot processing (default: `/tmp/specfact-backlog-refine-<timestamp>.md`)
- `--import-from-tmp` - Import refined content from temporary file after copilot processing (default: `/tmp/specfact-backlog-refine-<timestamp>-refined.md`)
- `--tmp-file PATH` - Custom temporary file path (overrides default)

**Export/Import Workflow**:

1. Export items: `specfact backlog refine --adapter github --export-to-tmp --repo-owner OWNER --repo-name NAME`
2. Process with copilot: Open exported file, use copilot to refine items, save as `-refined.md`
3. Import refined: `specfact backlog refine --adapter github --import-from-tmp --repo-owner OWNER --repo-name NAME --write`

### Definition of Ready (DoR)

- `--check-dor` - Check Definition of Ready (DoR) rules before refinement (loads from `.specfact/dor.yaml`)

### OpenSpec Integration

- `--bundle BUNDLE` or `-b BUNDLE` - OpenSpec bundle path to import refined items
- `--auto-bundle` - Auto-import refined items to OpenSpec bundle
- `--openspec-comment` - Add OpenSpec change proposal reference as comment (preserves original body)

### Generic Search

- `--search QUERY` or `-s QUERY` - Search query using provider-specific syntax (e.g., GitHub: "is:open label:feature")

## Workflow

### Step 1: Execute CLI Command

Execute the SpecFact CLI command with user-provided arguments:

```bash
specfact backlog refine $ADAPTER \
  [--labels LABELS] [--state STATE] [--assignee USERNAME] \
  [--iteration PATH] [--sprint SPRINT] [--release RELEASE] \
  [--limit N] \
  [--persona PERSONA] [--framework FRAMEWORK] \
  [--template TEMPLATE_ID] [--auto-accept-high-confidence] \
  [--preview] [--write] \
  [--bundle BUNDLE] [--auto-bundle] \
  [--search QUERY]
```

**Capture CLI output**:

- List of backlog items found
- Template detection results for each item
- Refinement prompts for IDE AI copilot
- Validation results
- Preview of what will be written (if --preview)
- Writeback confirmation (if --write)

### Step 2: Process Refinement Prompts (If Items Need Refinement)

**When CLI generates refinement prompts**:

1. **For each item needing refinement**:
   - CLI displays a refinement prompt
   - Copy the prompt and execute it in your IDE AI copilot
   - Get refined content from AI copilot response
   - Paste refined content back to CLI when prompted

2. **CLI validation**:
   - CLI validates refined content against template requirements
   - CLI provides confidence score
   - CLI shows preview of changes (original vs refined)

3. **User confirmation**:
   - Review preview (fields that will be updated vs preserved)
   - Accept or reject refinement
   - If accepted and --write flag set, CLI updates remote backlog

4. **Session control**:
   - Use `:skip` to skip the current item without updating
   - Use `:quit` or `:abort` to cancel the entire session gracefully
   - Session cancellation shows summary and exits without error

### Interactive refinement (Copilot mode)

When refining backlog items in Copilot mode (e.g. after export to tmp or during a refinement session), follow this **per-story loop** so the PO and stakeholders can review and approve before any update:

1. **For each story** (one at a time):
   - **Present** the refined story in a clear, readable format:
     - Use headings for Title, Body, Acceptance Criteria, Metrics.
     - Use tables or panels for structured data so it is easy to scan.
   - **Assess specification level** so the DevOps team knows if the story is ready, under-specified, or over-specified:
     - **Under-specified**: Missing acceptance criteria, vague scope, unclear "so that" or user value. List evidence (e.g. "No AC", "Scope could mean X or Y"). Suggest what to add.
     - **Over-specified**: Too much implementation detail, too many sub-steps for one story, or solution prescribed instead of outcome. List evidence and suggest what to trim or split.
     - **Fit for scope and intent**: Clear persona, capability, benefit, and testable AC; appropriate size. State briefly why it is ready (and, if DoR is in use, that DoR is satisfied).
   - **List ambiguities** or open questions (e.g. unclear scope, missing acceptance criteria, conflicting assumptions).
   - **Ask** the PO and other stakeholders for clarification: "Please review the refined story above. Do you want any changes? Any ambiguities to resolve? Should this story be split?"
   - **If the user provides feedback**: Re-refine the story incorporating the feedback, then repeat from "Present" for this story.
   - **Only when the user explicitly approves** (e.g. "looks good", "approved", "no changes"): Mark this story as done and move to the **next** story.
   - **Do not update** the backlog item (or write to the refined file as final) until the user has approved this story.

2. **Formatting**:
   - Use clear headings, bullet lists, and optional tables/panels so refinement sessions are easy to follow and enjoyable.
   - Keep each story’s block self-contained so stakeholders can focus on one item at a time.

3. **Rule**: The backlog item (or exported block) must only be updated/finalized **after** the user has approved the refined content for that story. Then proceed to the next story with the same process.

### Step 3: Present Results

Display refinement results:

- Number of items refined
- Number of items skipped
- Template matches found
- Confidence scores
- Preview status (if --preview)
- Writeback status (if --write)

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules**:

- Execute CLI first - never modify backlog items directly
- Use refinement prompts generated by CLI
- Validate refined content through CLI
- Use --preview flag by default for safety
- Use --write flag only when ready to update backlog

## Field Preservation Policy

**Fields that will be UPDATED**:

- `title`: Updated if changed during refinement
- `body_markdown`: Updated with refined content
- `acceptance_criteria`: Updated if extracted/refined (provider-specific mapping)
- `story_points`: Updated if extracted/refined (provider-specific mapping)
- `business_value`: Updated if extracted/refined (provider-specific mapping)
- `priority`: Updated if extracted/refined (provider-specific mapping)
- `value_points`: Updated if calculated (SAFe: business_value / story_points)
- `work_item_type`: Updated if extracted/refined (provider-specific mapping)

**Fields that will be PRESERVED** (not modified):

- `assignees`: Preserved
- `tags`: Preserved
- `state`: Preserved (original state maintained)
- `sprint`: Preserved (if present)
- `release`: Preserved (if present)
- `iteration`: Preserved (if present)
- `area`: Preserved (if present)
- `source_state`: Preserved for cross-adapter state mapping (stored in bundle entries)
- All other metadata: Preserved in provider_fields

**Provider-Specific Field Mapping**:

- **GitHub**: Fields are extracted from markdown body (headings, labels, etc.) and mapped to canonical fields
- **ADO**: Fields are extracted from separate ADO fields (System.Description, System.AcceptanceCriteria, Microsoft.VSTS.Common.StoryPoints, etc.) and mapped to canonical fields
- **Custom Mapping**: ADO supports custom field mapping via `.specfact/templates/backlog/field_mappings/ado_custom.yaml` or `SPECFACT_ADO_CUSTOM_MAPPING` environment variable

**Cross-Adapter State Preservation**:

- When items are imported into bundles, the original `source_state` (e.g., "open", "closed", "New", "Active") is stored in `source_metadata["source_state"]`
- During cross-adapter export (e.g., GitHub → ADO), the `source_state` is used to determine the correct target state
- Generic state mapping ensures state is correctly translated between any adapter pair using OpenSpec as intermediate format
- This ensures closed GitHub issues sync to ADO as "Closed", and open GitHub issues sync to ADO as "New"

**OpenSpec Comment Integration**:

- When `--openspec-comment` is used, a structured comment is added to the backlog item
- The comment includes: Change ID, template used, confidence score, refinement timestamp
- Original body is preserved; comment provides OpenSpec reference for cross-sync

**Cross-Adapter State Mapping**:

- When refining items that will be synced across adapters (e.g., GitHub ↔ ADO), state is preserved using generic mapping
- Generic state mapping uses OpenSpec as intermediate format:
  - Source adapter state → OpenSpec status → Target adapter state
  - Example: GitHub "open" → OpenSpec "proposed" → ADO "New"
  - Example: GitHub "closed" → OpenSpec "applied" → ADO "Closed"
- State preservation: Original `source_state` is stored in bundle entries and used during cross-adapter export
- Bidirectional mapping: Works in both directions (GitHub → ADO and ADO → GitHub)
- State mapping is automatic during `sync bridge` operations when `source_state` and `source_type` are present

## Architecture Note

SpecFact CLI follows a CLI-first architecture:

- SpecFact CLI generates prompts/instructions for IDE AI copilots
- IDE AI copilots execute those instructions using their native LLM
- IDE AI copilots feed results back to SpecFact CLI
- SpecFact CLI validates and processes the results
- SpecFact CLI does NOT directly invoke LLM APIs

## Expected Output

### Success (Preview Mode)

```text
✓ Refinement completed (Preview Mode)

Found 5 backlog items
Limited to 3 items (found 5 total)
Refined: 3
Skipped: 0

Preview mode: Refinement will NOT be written to backlog
Use --write flag to explicitly opt-in to writeback
```

### Success (Cancelled Session)

```text
Session cancelled by user

Found 5 backlog items
Refined: 1
Skipped: 1
```

### Success (Write Mode)

```text
✓ Refinement completed and written to backlog

Found 5 backlog items
Refined: 3
Skipped: 2

Items updated in remote backlog:
  - #123: User Story Template Applied
  - #124: Defect Template Applied
  - #125: Spike Template Applied
```

## Common Patterns

```bash
# Refine GitHub issues with feature label (requires repo-owner and repo-name)
/specfact.backlog-refine --adapter github --repo-owner nold-ai --repo-name specfact-cli --labels feature

# Refine ADO work items (Azure DevOps Services - cloud) with full iteration path
/specfact.backlog-refine --adapter ado --ado-org my-org --ado-project my-project --sprint "MyProject\\Sprint 1"

# Refine ADO work items using current active iteration (sprint omitted)
/specfact.backlog-refine --adapter ado --ado-org my-org --ado-project my-project --ado-team "My Team" --state Active

# Refine ADO work items (Azure DevOps Server - on-premise, collection in base_url)
/specfact.backlog-refine --adapter ado --ado-base-url "https://devops.company.com/tfs/DefaultCollection" --ado-project my-project --state Active

# Refine ADO work items (Azure DevOps Server - on-premise, collection provided)
/specfact.backlog-refine --adapter ado --ado-base-url "https://devops.company.com" --ado-org "DefaultCollection" --ado-project my-project --state Active

# Refine with batch limit (process max 10 items)
/specfact.backlog-refine --adapter github --repo-owner nold-ai --repo-name specfact-cli --limit 10 --labels feature

# Refine with case-insensitive filters
/specfact.backlog-refine --adapter ado --ado-org my-org --ado-project my-project --state "new" --assignee "jane doe"

# Refine with Scrum framework and Product Owner persona
/specfact.backlog-refine --adapter github --repo-owner nold-ai --repo-name specfact-cli --framework scrum --persona product-owner

# Preview refinement without writing
/specfact.backlog-refine --adapter github --repo-owner nold-ai --repo-name specfact-cli --preview

# Write refinement to backlog with OpenSpec comment (explicit opt-in)
/specfact.backlog-refine --adapter github --repo-owner nold-ai --repo-name specfact-cli --write --openspec-comment

# Check Definition of Ready before refinement
/specfact.backlog-refine --adapter github --repo-owner nold-ai --repo-name specfact-cli --check-dor --labels feature

# Refine and import to OpenSpec bundle
/specfact.backlog-refine --adapter github --repo-owner nold-ai --repo-name specfact-cli --bundle my-project --auto-bundle --state open

# Cross-adapter sync workflow: Refine GitHub → Sync to ADO (with state preservation)
/specfact.backlog-refine --adapter github --repo-owner nold-ai --repo-name specfact-cli --write --labels feature
# Then sync to ADO (state will be automatically mapped: open → New, closed → Closed)
# specfact sync bridge --adapter ado --ado-org my-org --ado-project my-project --mode bidirectional

# Cross-adapter sync workflow: Refine ADO → Sync to GitHub (with state preservation)
/specfact.backlog-refine --adapter ado --ado-org my-org --ado-project my-project --write --state Active
# Then sync to GitHub (state will be automatically mapped: New → open, Closed → closed)
# specfact sync bridge --adapter github --repo-owner my-org --repo-name my-repo --mode bidirectional
```

## Troubleshooting

### ADO API Errors

**Error: "No HTTP resource was found that matches the request URI"**

- **Cause**: Missing `api-version` parameter or incorrect URL format
- **Solution**: Ensure `api-version=7.1` is included in all ADO API URLs. Check base URL format for on-premise installations.

**Error: "The requested resource does not support http method 'GET'"**

- **Cause**: Attempting to use GET on WIQL endpoint (which requires POST)
- **Solution**: WIQL queries must use POST method with JSON body containing the query. This is handled automatically by SpecFact CLI.

**Error: Organization removed from request string**

- **Cause**: Incorrect base URL format (may already include organization/collection)
- **Solution**: For on-premise, check if base URL already includes collection. If yes, omit `--ado-org` or adjust base URL accordingly.

**Error: "Azure DevOps API token required"**

- **Cause**: Missing authentication token
- **Solution**: Provide token via `--ado-token`, `AZURE_DEVOPS_TOKEN` environment variable, or use `specfact auth azure-devops` for device code flow.

## Context

{ARGS}
