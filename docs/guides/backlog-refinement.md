---
layout: default
title: Backlog Refinement Guide
permalink: /guides/backlog-refinement/
---

# Backlog Refinement Guide

> **🆕 NEW FEATURE: AI-Assisted Template-Driven Backlog Refinement**  
> Transform arbitrary DevOps backlog input into structured, template-compliant work items using AI-assisted refinement with template detection and validation.

This guide explains how to use SpecFact CLI's backlog refinement feature to standardize work items from GitHub Issues, Azure DevOps, and other backlog tools into corporate templates (user stories, defects, spikes, enablers).

Preferred command path is `specfact backlog ceremony refinement ...`. The legacy `specfact backlog refine ...` path remains supported for compatibility.

**Tutorial**: For an end-to-end walkthrough with your AI IDE (Cursor, VS Code, etc.)—including interactive slash prompt, story quality, underspecification, splitting, and DoR—see **[Tutorial: Backlog Refine with AI IDE](../getting-started/tutorial-backlog-refine-ai-ide.md)**.

## Overview

**Why This Matters**: DevOps teams often create backlog items with informal, unstructured descriptions. Template-driven refinement helps enforce corporate standards while maintaining lossless synchronization with your backlog tools.

SpecFact CLI's backlog refinement feature:

- **Template Detection**: Automatically detects which template (user story, defect, spike, enabler) matches a backlog item
- **AI-Assisted Refinement**: Generates prompts for IDE AI copilots to refine unstructured input into template-compliant format
- **Confidence Scoring**: Validates refined content and provides confidence scores
- **Lossless Preservation**: Preserves original backlog data for round-trip synchronization
- **Arbitrary Input Handling**: Works with any DevOps backlog format (GitHub Issues, ADO work items, etc.)

**Architecture Note**: SpecFact CLI follows a CLI-first architecture:

- SpecFact CLI generates prompts/instructions for IDE AI copilots (Cursor, Claude Code, etc.)
- IDE AI copilots execute those instructions using their native LLM
- IDE AI copilots feed results back to SpecFact CLI
- SpecFact CLI validates and processes the results
- SpecFact CLI does NOT directly invoke LLM APIs (OpenAI, Anthropic, etc.)

---

## Quick Start

### 1. Refine a Single Backlog Item

```bash
# Refine GitHub issues (auto-detect template)
specfact backlog ceremony refinement github --search "is:open label:feature"

# Filter by labels and state
specfact backlog ceremony refinement github --labels feature,enhancement --state open

# Filter by sprint and assignee
specfact backlog ceremony refinement github --sprint "Sprint 1" --assignee dev1

# Filter by framework and persona (Scrum + Product Owner)
specfact backlog ceremony refinement github --framework scrum --persona product-owner --labels feature

# Refine with specific template
specfact backlog ceremony refinement github --template user_story_v1 --search "is:open"

# Check Definition of Ready before refinement
specfact backlog ceremony refinement github --check-dor --labels feature

# Preview refinement without writing (default - safe mode)
specfact backlog ceremony refinement github --preview --labels feature

# Write refinement to backlog (explicit opt-in required)
specfact backlog ceremony refinement github --write --labels feature

# Auto-accept high-confidence refinements
specfact backlog ceremony refinement github --auto-accept-high-confidence --search "is:open"
```

### 2. Refine and Import to OpenSpec Bundle

```bash
# Refine and automatically import to OpenSpec bundle
specfact backlog ceremony refinement github \
  --bundle my-project \
  --auto-bundle \
  --search "is:open label:enhancement"
```

### 3. Refine Azure DevOps Work Items

```bash
# Refine ADO work items
specfact backlog ceremony refinement ado --search "State = 'New'"

# Filter by sprint and state
specfact backlog ceremony refinement ado --sprint "Sprint 1" --state Active

# Filter by iteration path (ADO format)
specfact backlog ceremony refinement ado --iteration "Project\\Release 1\\Sprint 1"

# Refine with defect template
specfact backlog ceremony refinement ado --template defect_v1 --search "WorkItemType = 'Bug'"

# Use custom field mapping for custom ADO process templates
specfact backlog ceremony refinement ado \
  --ado-org my-org \
  --ado-project my-project \
  --custom-field-mapping /path/to/ado_custom.yaml \
  --state Active
```

---

## How It Works

### Step 1: Fetch Backlog Items

The command fetches backlog items from the specified adapter (GitHub, ADO, etc.) and converts them to the unified `BacklogItem` domain model.

```bash
specfact backlog ceremony refinement github --search "is:open"
```

**Note**: Adapter search methods (`adapter.search_issues()`, `adapter.list_work_items()`) are required for fetching. These will be implemented when adapters support them.

### Step 2: Template Detection with Priority-Based Resolution

For each backlog item, SpecFact CLI detects which template best matches using **priority-based resolution**:

- **Priority Order** (most specific to least specific):
  1. `provider+framework+persona` (e.g., GitHub + Scrum + Product Owner)
  2. `provider+framework` (e.g., GitHub + Scrum)
  3. `framework+persona` (e.g., Scrum + Product Owner)
  4. `framework` (e.g., Scrum)
  5. `provider+persona` (e.g., GitHub + Product Owner)
  6. `persona` (e.g., Product Owner)
  7. `provider` (e.g., GitHub)
  8. Default (framework-agnostic, persona-agnostic, provider-agnostic)

- **Detection Scoring**:
  - **Structural Fit** (60% weight): Checks if required section headings are present
  - **Pattern Fit** (40% weight): Matches regex patterns in title and body
  - **Confidence Score**: Calculates weighted confidence (0.0-1.0)
  - **Missing Fields**: Identifies required template fields that are missing

```bash
# Auto-detect template with persona/framework filtering (default)
specfact backlog ceremony refinement github --framework scrum --persona product-owner --search "is:open"

# Force specific template (overrides priority-based resolution)
specfact backlog ceremony refinement github --template user_story_v1 --search "is:open"
```

### Step 3: AI-Assisted Refinement

SpecFact CLI generates a refinement prompt for your IDE AI copilot:

1. **Prompt Generation**: Creates a markdown prompt with:
   - Original backlog item content
   - Target template structure
   - Required sections and fields
   - Examples and guidelines

2. **IDE AI Copilot Execution**: You copy the prompt to your IDE AI copilot (Cursor, Claude Code, etc.), which:
   - Executes the refinement using its native LLM
   - Returns refined content in template-compliant format

3. **Validation**: SpecFact CLI validates the refined content:
   - Checks for required sections
   - Detects TODO markers (reduces confidence)
   - Detects NOTES sections (reduces confidence)
   - Calculates confidence score (0.0-1.0)

```bash
# Interactive refinement (default)
specfact backlog ceremony refinement github --search "is:open"

# The CLI will:
# 1. Display the refinement prompt
# 2. Wait for you to paste refined content from IDE AI copilot
# 3. Validate and score the refinement
# 4. Ask for confirmation before applying
```

### Story scope and specification level

During interactive refinement (e.g. when using the slash prompt in your AI IDE), the team should assess each story’s **specification level** so you can improve quality and respect Definition of Ready:

- **Under-specified**: Missing acceptance criteria, vague scope, unclear “so that” or user value. The AI should list what’s missing (e.g. “No AC”, “Scope could mean X or Y”) so the team can add detail before approving.
- **Over-specified**: Too much implementation detail, too many sub-steps for one story, or solution prescribed instead of outcome. The AI should suggest what to trim or move so the story stays fit for one sprint or one outcome.
- **Fit for scope and intent**: Clear persona, capability, benefit, and testable AC; appropriate size. The AI should state briefly why it’s ready (and, if you use DoR, that DoR is satisfied).

Include this assessment in the **interactive feedback loop**: present story → assess under-/over-/fit → list ambiguities → ask clarification → re-refine until the PO/stakeholder approves. That way the DevOps team gets to know if a story is under-/over-specified or actually fitting for scope and intent before updating the backlog.

### Step 4: Preview and Apply Refinement

Once validated, the refinement can be previewed or applied:

**Preview Mode (Default - Safe)**:

- Shows what will be updated (title, body) vs preserved (assignees, tags, state, priority, etc.)
- **Displays assignee information**: Always shows assignee(s) or "Unassigned" status for each item
- **Displays acceptance criteria**: Always shows acceptance criteria if required by template (even when empty, shows `(empty - required field)` indicator)
- **Displays required fields**: All required fields from the template are always displayed, even when empty, to help copilot identify missing elements
- Displays original vs refined content diff
- **Does NOT write to remote backlog** (safe by default)

**Progress Indicators**:

During initialization (typically 5-10 seconds, longer in corporate environments with security scans/firewalls), the command shows detailed progress:

```bash
⏱️  Started: 2026-01-27 15:34:05
⠋ ✓ Templates initialized   0:00:02
⠋ ✓ Template detector ready 0:00:00
⠋ ✓ AI refiner ready        0:00:00
⠋ ✓ Adapter registry ready  0:00:00
⠋ ✓ Configuration validated 0:00:00
⠸ ✓ Fetched backlog items 0:00:01
```

This provides clear feedback during the initialization phase, especially important in corporate environments where network latency and security scans can cause delays.

**Complete Preview Output Example**:

```
Preview Mode: Full Item Details
Title: Fix the error
URL: https://dev.azure.com/dominikusnold/69b5d0c2-2400-470d-b937-b5205503a679/_apis/wit/workItems/185
State: new
Provider: ado
Assignee: Unassigned

Story Metrics:
  - Priority: 2 (1=highest)
  - Work Item Type: User Story

Acceptance Criteria:
╭───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ <div><ul><li>quality of this story needs to comply with devops scrum standards. </li> </ul> </div>                        │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Body:
╭───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ <div>This story is here to be refined. </div>                                                                             │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Target Template: Azure DevOps Work Item (ID: ado_work_item_v1)
Template Description: Work item template optimized for Azure DevOps with area path and iteration path support
```

**Note**: If a required field (like Acceptance Criteria) is empty but required by the template, it will show:

```
Acceptance Criteria:
╭───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ (empty - required field)                                                                                                 │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

This helps copilot identify missing elements that need to be added during refinement.

**Write Mode (Explicit Opt-in)**:

- Requires `--write` flag to explicitly opt-in
- Updates `BacklogItem.body_markdown` with refined content
- Sets `refinement_applied = True`
- Records `refinement_timestamp`
- Updates template detection metadata
- **Preserves all other fields** (assignees, tags, state, priority, due_date, story_points, etc.)
- Parses structured refinement output into canonical fields before writeback:
  - accepts markdown-heading sections and label-style sections (for example `Description:`, `Acceptance Criteria:`, `Story Points:`)
  - maps ADO description/acceptance criteria/metrics to separate provider fields
  - avoids writing prompt label blocks verbatim into ADO description

**Field Preservation Policy**:

- **Updated**: `title`, `body_markdown`
- **Preserved**: `assignees`, `tags`, `state`, `priority`, `due_date`, `story_points`, and all other metadata

```bash
# Preview mode (default - safe, no writeback)
specfact backlog ceremony refinement github --preview --search "is:open"

# Write mode (explicit opt-in required)
specfact backlog ceremony refinement github --write --search "is:open"

# Auto-accept high-confidence refinements (>= 0.85) and write
specfact backlog ceremony refinement github --auto-accept-high-confidence --write --search "is:open"
```

### Step 4.5: Definition of Ready (DoR) Validation (Optional)

If `--check-dor` flag is set, SpecFact CLI validates backlog items against Definition of Ready rules:

- Loads DoR configuration from `.specfact/dor.yaml` (repo-level)
- Validates required fields (story_points, priority, business_value, acceptance_criteria, dependencies)
- Displays DoR status before refinement
- Warns if items are not ready for sprint planning

```bash
# Check DoR before refinement
specfact backlog ceremony refinement github --check-dor --labels feature
```

**DoR Configuration** (`.specfact/dor.yaml`):

```yaml
rules:
  story_points: true
  priority: true
  business_value: true
  acceptance_criteria: true
  dependencies: false  # Optional
```

### Step 5: OpenSpec Integration (Optional)

Refined items can be imported into OpenSpec bundles:

```bash
# Import to OpenSpec bundle
specfact backlog ceremony refinement github \
  --bundle my-project \
  --auto-bundle \
  --search "is:open"
```

This creates OpenSpec change proposals with:

- Refined content in template-compliant format
- Source tracking metadata (template_id, refinement_confidence, etc.)
- Link to original backlog item

---

## Pre-built Templates

SpecFact CLI includes four pre-built templates:

### User Story Template (`user_story_v1`)

Standard user story format with:

- **As a** (user persona)
- **I want** (capability)
- **So that** (benefit)
- **Acceptance Criteria** (testable conditions)

**Example**:

```markdown
## As a
Customer

## I want
To reset my password via email

## So that
I can regain access to my account when I forget my password

## Acceptance Criteria
- User can request password reset from login page
- System sends reset email with secure token
- User can set new password using token
- Token expires after 24 hours
```

### Defect Template (`defect_v1`)

Bug report format with:

- **Summary** (brief description)
- **Steps to Reproduce** (reproduction steps)
- **Expected Behavior** (what should happen)
- **Actual Behavior** (what actually happens)
- **Environment** (OS, browser, version, etc.)

**Example**:

```markdown
## Summary
Login button does not respond on mobile Safari

## Steps to Reproduce
1. Open app on iPhone Safari
2. Enter credentials
3. Tap "Login" button

## Expected Behavior
User is redirected to dashboard

## Actual Behavior
Button does not respond, no action occurs

## Environment
- OS: iOS 17.0
- Browser: Safari 17.0
- Device: iPhone 14 Pro
```

### Spike Template (`spike_v1`)

Research spike format with:

- **Research Question** (what needs to be investigated)
- **Research Approach** (how to investigate)
- **Findings** (what was discovered)
- **Recommendation** (what to do next)

### Enabler Template (`enabler_v1`)

Enabler work format with:

- **Enabler Description** (what capability is being enabled)
- **Dependencies** (what this enables)
- **Implementation Approach** (how to implement)
- **Success Criteria** (how to measure success)

---

## Command Reference

### `specfact backlog ceremony refinement`

Refine backlog items using AI-assisted template matching.

```bash
specfact backlog ceremony refinement <ADAPTER> [OPTIONS]
```

**Arguments**:

- `ADAPTER` - Backlog adapter name (`github`, `ado`, etc.)

**Options**:

- `--search`, `-s` - Search query to filter backlog items
- `--state any` / `--assignee any` - Explicitly disable state/assignee filtering when needed (for example ID-specific runs).
- `--template`, `-t` - Target template ID (default: auto-detect)
- `--ignore-refined` / `--no-ignore-refined` - When using `--limit N`, apply limit to items that need refinement (default: ignore already-refined items so you see N items that actually need work)
- `--id` - Refine only the backlog item with the given issue or work item ID
- `--auto-accept-high-confidence` - Auto-accept refinements with confidence >= 0.85
- `--bundle`, `-b` - OpenSpec bundle path to import refined items
- `--auto-bundle` - Auto-import refined items to OpenSpec bundle

**Examples**:

```bash
# Refine GitHub issues (auto-detect template)
specfact backlog ceremony refinement github --search "is:open label:feature"

# Filter by labels and state
specfact backlog ceremony refinement github --labels feature,enhancement --state open

# Filter by sprint and assignee
specfact backlog ceremony refinement github --sprint "Sprint 1" --assignee dev1

# Filter by framework and persona (Scrum + Product Owner)
specfact backlog ceremony refinement github --framework scrum --persona product-owner --labels feature

# Refine with specific template
specfact backlog ceremony refinement github --template user_story_v1 --search "is:open"

# Check Definition of Ready before refinement
specfact backlog ceremony refinement github --check-dor --labels feature

# Preview refinement without writing (default - safe mode)
specfact backlog ceremony refinement github --preview --labels feature

# Write refinement to backlog (explicit opt-in required)
specfact backlog ceremony refinement github --write --labels feature

# Auto-accept high-confidence refinements
specfact backlog ceremony refinement github --auto-accept-high-confidence --search "is:open"

# Refine and import to OpenSpec bundle
specfact backlog ceremony refinement github \
  --bundle my-project \
  --auto-bundle \
  --search "is:open label:enhancement"

# Refine ADO work items with sprint filter
specfact backlog ceremony refinement ado --sprint "Sprint 1" --state Active

# Refine ADO work items with custom field mapping
specfact backlog ceremony refinement ado \
  --ado-org my-org \
  --ado-project my-project \
  --custom-field-mapping .specfact/templates/backlog/field_mappings/ado_custom.yaml \
  --state Active

# Refine ADO work items with iteration path
specfact backlog ceremony refinement ado --iteration "Project\\Release 1\\Sprint 1"
```

### 4. Export Full Comment Context for Copilot

`specfact backlog ceremony refinement --export-to-tmp` now includes issue/work item comments (when adapter supports comments, including ADO) so refinement context is complete by default.

```bash
# Export with full comment history (default, no truncation)
specfact backlog ceremony refinement ado \
  --ado-org my-org \
  --ado-project my-project \
  --state Active \
  --export-to-tmp

# Optional: preview only first N comments in terminal output
specfact backlog ceremony refinement ado \
  --ado-org my-org \
  --ado-project my-project \
  --state Active \
  --preview \
  --first-comments 3

# Optional: preview only last N comments in terminal output
specfact backlog ceremony refinement ado \
  --ado-org my-org \
  --ado-project my-project \
  --state Active \
  --preview \
  --last-comments 4
```

Preview defaults to the last 2 comments per item to keep CLI output readable.  
`--first-comments N` and `--last-comments N` are mutually exclusive and affect preview density and write-mode prompt comment context.  
In `--write` workflows, prompts include full comment history by default unless a first/last comment window is provided.  
`--export-to-tmp` always writes full comment history.
The export file now includes a `## Copilot Instructions` block and per-item template guidance, and Copilot should follow those embedded instructions when refining.  
For export-driven refinement, treat the embedded file instructions as the canonical format contract.  
For `--import-from-tmp`, ensure the refined artifact excludes the instruction header and retains only `## Item N:` sections with refined fields.

Use `--first-issues N` or `--last-issues N` to process only a first/last slice of filtered issues in a refine run (mutually exclusive).  
Issue windowing is based on numeric issue/work-item IDs: lower IDs are treated as older (`--first-issues`), higher IDs as newer (`--last-issues`).

### 5. Shared Backlog Filter Parity (Refine + Daily)

`specfact backlog ceremony refinement` and `specfact backlog ceremony standup` now share the same global backlog scoping semantics for common workflows:

- `--search`, `--release`, `--id` for consistent item selection
- `--first-issues N` / `--last-issues N` for deterministic oldest/newest issue windows (numeric ID ordering)
- comment-window options where applicable:
  - **Refine**: `--first-comments N` / `--last-comments N` affect preview and write-prompt context
  - **Daily export/summarize**: `--first-comments N` / `--last-comments N` scope `--comments` output
  - **Daily interactive**: latest comment by default; explicit comment-window flags override that default

For day-to-day team flow, this means you can switch between `backlog ceremony standup` and
`backlog ceremony refinement` without changing filter mental models.

---

## Workflow Integration

### Command Chaining: Refine → Sync

The most common workflow is to refine backlog items and then sync them to external tools. This command chaining workflow is fully supported and tested:

**Workflow**: `backlog ceremony refinement` → `sync bridge`

1. **Refine Backlog Items**: Use `specfact backlog ceremony refinement` to standardize backlog items with templates
2. **Sync to External Tools**: Use `specfact sync bridge` to sync refined items back to backlog tools (GitHub, ADO, etc.)

```bash
# Complete command chaining workflow
# 1. Refine GitHub issues (with writeback)
specfact backlog ceremony refinement github \
  --repo-owner my-org --repo-name my-repo \
  --write \
  --labels feature \
  --state open

# 2. Sync refined items to external tool (same or different adapter)
specfact sync bridge --adapter github \
  --repo-owner my-org --repo-name my-repo \
  --backlog-ids 123,456 \
  --mode export-only

# Cross-adapter sync: Refine from GitHub → Sync to ADO
specfact backlog ceremony refinement github \
  --repo-owner my-org --repo-name my-repo \
  --write \
  --labels feature

specfact sync bridge --adapter ado \
  --ado-org my-org --ado-project my-project \
  --backlog-ids 123,456 \
  --mode export-only
```

**Key Benefits**:

- **Lossless Preservation**: Original backlog data is preserved during refinement
- **Cross-Adapter Support**: Refine from one provider (GitHub) and sync to another (ADO)
- **OpenSpec Integration**: Refined items can include OpenSpec comments without replacing the body
- **Field Preservation**: Only `title` and `body_markdown` are updated; all other fields (assignees, tags, state, priority, etc.) are preserved
- **Generic State Mapping**: Automatic state preservation during cross-adapter sync using OpenSpec as intermediate format

### Cross-Adapter State Mapping

When syncing backlog items between different adapters (e.g., GitHub ↔ ADO), SpecFact CLI uses a **generic state mapping mechanism** that preserves the original state across adapters.

**How It Works**:

1. **State Preservation During Import**: When backlog items are imported into a bundle, the original `source_state` (e.g., "open", "closed", "New", "Active") is stored in `source_metadata["source_state"]` within the bundle entry.

2. **Generic State Mapping**: During cross-adapter export, the system uses OpenSpec as an intermediate format:
   - **Step 1**: Source adapter state → OpenSpec status (using source adapter's mapping)
   - **Step 2**: OpenSpec status → Target adapter state (using target adapter's mapping)

3. **Bidirectional Support**: The mapping works in both directions:
   - **GitHub → ADO**: GitHub "open" → OpenSpec "proposed" → ADO "New"
   - **GitHub → ADO**: GitHub "closed" → OpenSpec "applied" → ADO "Closed"
   - **ADO → GitHub**: ADO "New" → OpenSpec "proposed" → GitHub "open"
   - **ADO → GitHub**: ADO "Closed" → OpenSpec "applied" → GitHub "closed"

**Example: Cross-Adapter Sync with State Preservation**:

```bash
# 1. Import closed GitHub issues into bundle (state "closed" is preserved)
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner nold-ai --repo-name specfact-cli \
  --backlog-ids 110,122

# 2. Export to ADO (state is automatically mapped: closed → Closed)
specfact sync bridge --adapter ado --mode export-only \
  --ado-org dominikusnold --ado-project "SpecFact CLI" \
  --bundle cross-sync-test --change-ids add-ado-backlog-adapter,add-template-driven-backlog-refinement

# Result: ADO work items are created with "Closed" state (matching GitHub "closed")
```

**State Mapping Guarantees**:

- **Open Issues**: GitHub "open" ↔ ADO "New" (both represent active work)
- **Closed Issues**: GitHub "closed" ↔ ADO "Closed" (both represent completed work)
- **Active Work**: ADO "Active" → GitHub "open" (active work remains open)
- **Resolved Work**: ADO "Resolved" → GitHub "closed" (resolved work is closed)

**Implementation Details**:

- The generic mapping is implemented in `BacklogAdapterMixin.map_backlog_state_between_adapters()`
- Each adapter provides bidirectional mappings:
  - `map_backlog_status_to_openspec()`: Adapter state → OpenSpec status
  - `map_openspec_status_to_backlog()`: OpenSpec status → Adapter state
- The mapping is automatic when `source_state` and `source_type` are present in bundle entries
- No manual state mapping is required - the system handles it automatically

### With DevOps Adapter Integration

Backlog refinement works seamlessly with the [DevOps Adapter Integration](../guides/devops-adapter-integration.md):

1. **Import Backlog Items**: Use `specfact sync bridge` to import backlog items as OpenSpec proposals
2. **Refine Items**: Use `specfact backlog ceremony refinement` to standardize imported items
3. **Export Refined Items**: Use `specfact sync bridge` to export refined proposals back to backlog tools

```bash
# Complete workflow
# 1. Import GitHub issues as OpenSpec proposals
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner my-org --repo-name my-repo \
  --backlog-ids 123,456

# 2. Refine imported items
specfact backlog ceremony refinement github --bundle my-project --auto-bundle \
  --search "is:open"

# 3. Export refined proposals back to GitHub
specfact sync bridge --adapter github --mode export-only \
  --bundle my-project --change-ids <refined-change-id>
```

### With IDE AI Copilots

The refinement workflow is designed for IDE AI copilots:

1. **Generate Prompt**: SpecFact CLI generates a refinement prompt
2. **Copy to IDE**: Copy the prompt to your IDE AI copilot (Cursor, Claude Code, etc.)
3. **Execute Refinement**: IDE AI copilot executes the refinement using its native LLM
4. **Paste Result**: Paste the refined content back into SpecFact CLI
5. **Validate**: SpecFact CLI validates and scores the refinement

**Example with Cursor**:

```bash
# 1. Run refinement command
specfact backlog ceremony refinement github --search "is:open label:feature"

# 2. CLI displays prompt:
# "Refine the following backlog item into a user story template..."
# [Copy prompt]

# 3. In Cursor IDE:
# /refine [paste prompt]

# 4. Cursor returns refined content:
# "## As a\nCustomer\n\n## I want\n..."

# 5. Paste refined content back into CLI
# CLI validates and applies refinement
```

---

## Field Mapping and Customization

### Custom Field Mappings for Azure DevOps

If your Azure DevOps organization uses custom process templates with non-standard field names, you can create custom field mappings to map your ADO fields to canonical field names.

**Quick Example**:

```bash
# Use custom field mapping file
specfact backlog ceremony refinement ado \
  --ado-org my-org \
  --ado-project my-project \
  --custom-field-mapping .specfact/templates/backlog/field_mappings/ado_custom.yaml \
  --state Active
```

**Custom Mapping File Format**:

Create a YAML file at `.specfact/templates/backlog/field_mappings/ado_custom.yaml`:

```yaml
framework: scrum

field_mappings:
  System.Description: description
  Custom.StoryPoints: story_points
  Custom.BusinessValue: business_value
  Custom.Priority: priority

work_item_type_mappings:
  Product Backlog Item: User Story
  Requirement: User Story
```

**See Also**: [Custom Field Mapping Guide](./custom-field-mapping.md) for complete documentation on field mapping templates, framework-specific examples, and best practices.

## Template Customization

### Creating Custom Templates

Templates are YAML files with the following structure:

```yaml
template_id: custom_template_v1
name: Custom Template
scope: corporate  # or "team"
description: Custom template for specific use case

# Persona, framework, and provider filtering (optional)
personas: ["product-owner", "developer"]  # Empty = all personas
framework: "scrum"  # None = framework-agnostic
provider: "github"  # None = provider-agnostic

required_sections:
  - "## Section 1"
  - "## Section 2"

optional_sections:
  - "## Notes"
  - "## References"

body_patterns:
  section_pattern: "section.*pattern"

title_patterns:
  - "^Feature:"
```

Save custom templates to your project directory:

- **Default templates**: `.specfact/templates/backlog/defaults/`
- **Framework-specific**: `.specfact/templates/backlog/frameworks/<framework>/` (e.g., `scrum/`, `safe/`)
- **Persona-specific**: `.specfact/templates/backlog/personas/<persona>/` (e.g., `product-owner/`, `developer/`)
- **Provider-specific**: `.specfact/templates/backlog/providers/<provider>/` (e.g., `github/`, `ado/`)

**Built-in templates** (included with SpecFact CLI):

- Location: `resources/templates/backlog/` (in the SpecFact CLI package)
- Same subdirectory structure: `defaults/`, `frameworks/`, `personas/`, `providers/`

### Loading Custom Templates

Templates are automatically loaded in priority order (custom templates override built-in):

1. **Project templates** (`.specfact/templates/backlog/`) - Highest priority, overrides built-in
2. **Built-in templates** (`resources/templates/backlog/`) - Included with package
3. **Legacy location** (`src/specfact_cli/templates/`) - Fallback for backward compatibility

Within each location, templates are loaded from:

- `defaults/` subdirectory
- `frameworks/<framework>/` subdirectories
- `personas/<persona>/` subdirectories
- `providers/<provider>/` subdirectories

**Template Resolution**:

When using `--persona`, `--framework`, or provider-specific filtering, SpecFact CLI automatically resolves templates using priority-based matching:

```bash
# Automatically resolves to most specific template match
specfact backlog ceremony refinement github --framework scrum --persona product-owner --labels feature

# Force specific template (overrides priority-based resolution)
specfact backlog ceremony refinement github --template custom_template_v1
```

---

## Best Practices

### 1. Start with Auto-Detection

Let SpecFact CLI detect templates automatically before forcing specific templates:

```bash
# Good: Auto-detect first
specfact backlog ceremony refinement github --search "is:open"

# Then use specific template if needed
specfact backlog ceremony refinement github --template user_story_v1 --search "is:open"
```

### 2. Review Low-Confidence Refinements

Refinements with confidence < 0.85 may need manual review:

```bash
# Review low-confidence refinements manually
specfact backlog ceremony refinement github --search "is:open"
# CLI will prompt for confirmation on low-confidence refinements
```

### 3. Use Auto-Accept for High-Confidence

For high-confidence refinements (>= 0.85), use auto-accept:

```bash
# Auto-accept high-confidence refinements
specfact backlog ceremony refinement github --auto-accept-high-confidence --search "is:open"
```

### 4. Integrate with OpenSpec Bundles

Import refined items to OpenSpec bundles for full workflow integration:

```bash
# Refine and import to bundle
specfact backlog ceremony refinement github \
  --bundle my-project \
  --auto-bundle \
  --search "is:open"
```

### 5. Preserve Original Data

SpecFact CLI preserves original backlog data in `provider_fields` for lossless round-trip:

- Original title and body
- Provider-specific metadata
- Labels, assignees, milestones
- Custom fields
- Sprint and release information (extracted from milestones/iteration paths)

### 6. Use Filtering for Agile Workflows

Leverage filtering options for common agile/scrum workflows:

```bash
# Refine items in current sprint
specfact backlog ceremony refinement github --sprint "Sprint 1" --state open

# Refine items assigned to specific developer
specfact backlog ceremony refinement github --assignee dev1 --labels bug

# Refine items for specific release
specfact backlog ceremony refinement ado --release "Release 1.0" --state Active

# Use persona/framework filtering for role-specific templates
specfact backlog ceremony refinement github --persona product-owner --framework scrum --labels feature
```

### 7. Check Definition of Ready (DoR)

Use DoR validation to ensure items are ready for sprint planning:

```bash
# Check DoR before refinement
specfact backlog ceremony refinement github --check-dor --labels feature

# DoR configuration in .specfact/dor.yaml
rules:
  story_points: true
  priority: true
  business_value: true
  acceptance_criteria: true
```

---

## Troubleshooting

### Template Not Detected

If template detection fails:

1. **Check Template Structure**: Ensure backlog item has required section headings
2. **Check Patterns**: Verify title/body matches template patterns
3. **Force Template**: Use `--template` to force specific template

```bash
# Force template if auto-detection fails
specfact backlog ceremony refinement github --template user_story_v1 --search "is:open"
```

### Low Confidence Scores

Low confidence scores (< 0.6) indicate:

- Missing required sections
- TODO markers in refined content
- NOTES sections indicating uncertainty
- Insufficient content

**Solutions**:

- Review original backlog item for completeness
- Manually edit refined content before applying
- Use `--template` to force template structure

### Adapter Search Not Available

If adapter search methods are not available:

```bash
# CLI will show warning:
# "Note: GitHub issue fetching requires adapter.search_issues() implementation"
```

**Workaround**: Use `specfact sync bridge` to import backlog items first, then refine:

```bash
# 1. Import backlog items
specfact sync bridge --adapter github --mode bidirectional \
  --backlog-ids 123,456

# 2. Refine imported items from bundle
specfact backlog ceremony refinement github --bundle my-project --auto-bundle
```

### Azure DevOps Adapter Configuration

The Azure DevOps (ADO) adapter supports both **Azure DevOps Services (cloud)** and **Azure DevOps Server (on-premise)**. Configuration differs based on your environment.

#### Azure DevOps Services (Cloud)

For cloud-based Azure DevOps, use the standard format:

```bash
# Basic configuration
specfact backlog ceremony refinement ado \
  --ado-org "my-org" \
  --ado-project "my-project" \
  --state Active

# With custom base URL (defaults to https://dev.azure.com)
specfact backlog ceremony refinement ado \
  --ado-org "my-org" \
  --ado-project "my-project" \
  --ado-base-url "https://dev.azure.com" \
  --state Active
```

**URL Format**: `https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version=7.1`

#### Azure DevOps Server (On-Premise)

For on-premise Azure DevOps Server, the URL format depends on whether the collection is included in the base URL:

**Option 1: Collection in Base URL**

If your base URL already includes the collection:

```bash
# Collection already in base_url
specfact backlog ceremony refinement ado \
  --ado-base-url "https://devops.company.com/tfs/DefaultCollection" \
  --ado-project "my-project" \
  --state Active
```

**URL Format**: `https://server/tfs/collection/{project}/_apis/wit/wiql?api-version=7.1`

**Option 2: Collection Provided Separately**

If your base URL doesn't include the collection:

```bash
# Collection provided as org parameter
specfact backlog ceremony refinement ado \
  --ado-base-url "https://devops.company.com" \
  --ado-org "DefaultCollection" \
  --ado-project "my-project" \
  --state Active
```

**URL Format**: `https://server/{collection}/{project}/_apis/wit/wiql?api-version=7.1`

#### ADO API Endpoint Requirements

**WIQL Query Endpoint** (POST):

- **URL**: `{base_url}/{org}/{project}/_apis/wit/wiql?api-version=7.1`
- **Method**: POST
- **Body**: `{"query": "SELECT [System.Id] FROM WorkItems WHERE ..."}`
- **Headers**: `Content-Type: application/json`, `Accept: application/json`
- **Note**: The `api-version` parameter is **required** for all ADO API calls

**Work Items Batch GET Endpoint**:

- **URL**: `{base_url}/{org}/_apis/wit/workitems?ids={ids}&api-version=7.1`
- **Method**: GET
- **Note**: This endpoint is at the **organization level** (not project level) for fetching work item details by IDs

#### Common ADO API Errors

**Error: "No HTTP resource was found that matches the request URI"**

- **Cause**: Missing `api-version` parameter or incorrect URL format
- **Solution**: Ensure `api-version=7.1` is included in all ADO API URLs

**Error: "The requested resource does not support http method 'GET'"**

- **Cause**: Attempting to use GET on WIQL endpoint (which requires POST)
- **Solution**: WIQL queries must use POST method with JSON body

**Error: Organization removed from request string**

- **Cause**: Incorrect base URL format (may already include organization/collection)
- **Solution**: Check if base URL already includes collection, adjust `--ado-org` parameter accordingly

#### Authentication

ADO adapter supports multiple authentication methods:

```bash
# Method 1: Environment variable
export AZURE_DEVOPS_TOKEN="your-pat-token"
specfact backlog ceremony refinement ado --ado-org "my-org" --ado-project "my-project"

# Method 2: CLI parameter
specfact backlog ceremony refinement ado \
  --ado-org "my-org" \
  --ado-project "my-project" \
  --ado-token "your-pat-token"

# Method 3: Stored token (via device code flow)
specfact backlog auth azure-devops  # Interactive device code flow
specfact backlog ceremony refinement ado --ado-org "my-org" --ado-project "my-project"
```

---

## Related Documentation

- **[DevOps Adapter Integration](../guides/devops-adapter-integration.md)** - Complete guide for GitHub Issues and Azure DevOps integration
- **[Command Reference](../reference/commands.md)** - Complete command documentation
- **[Agile/Scrum Workflows](../guides/agile-scrum-workflows.md)** - Persona-based collaboration for teams
- **[IDE Integration](../guides/ide-integration.md)** - Set up slash commands in your IDE

---

**Happy refining!** 🚀
