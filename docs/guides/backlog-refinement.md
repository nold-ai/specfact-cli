---
layout: default
title: Backlog Refinement Guide
permalink: /guides/backlog-refinement/
---

# Backlog Refinement Guide

> **🆕 NEW FEATURE: AI-Assisted Template-Driven Backlog Refinement**  
> Transform arbitrary DevOps backlog input into structured, template-compliant work items using AI-assisted refinement with template detection and validation.

This guide explains how to use SpecFact CLI's backlog refinement feature to standardize work items from GitHub Issues, Azure DevOps, and other backlog tools into corporate templates (user stories, defects, spikes, enablers).

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
specfact backlog refine github --search "is:open label:feature"

# Filter by labels and state
specfact backlog refine github --labels feature,enhancement --state open

# Filter by sprint and assignee
specfact backlog refine github --sprint "Sprint 1" --assignee dev1

# Filter by framework and persona (Scrum + Product Owner)
specfact backlog refine github --framework scrum --persona product-owner --labels feature

# Refine with specific template
specfact backlog refine github --template user_story_v1 --search "is:open"

# Check Definition of Ready before refinement
specfact backlog refine github --check-dor --labels feature

# Preview refinement without writing (default - safe mode)
specfact backlog refine github --preview --labels feature

# Write refinement to backlog (explicit opt-in required)
specfact backlog refine github --write --labels feature

# Auto-accept high-confidence refinements
specfact backlog refine github --auto-accept-high-confidence --search "is:open"
```

### 2. Refine and Import to OpenSpec Bundle

```bash
# Refine and automatically import to OpenSpec bundle
specfact backlog refine github \
  --bundle my-project \
  --auto-bundle \
  --search "is:open label:enhancement"
```

### 3. Refine Azure DevOps Work Items

```bash
# Refine ADO work items
specfact backlog refine ado --search "State = 'New'"

# Filter by sprint and state
specfact backlog refine ado --sprint "Sprint 1" --state Active

# Filter by iteration path (ADO format)
specfact backlog refine ado --iteration "Project\\Release 1\\Sprint 1"

# Refine with defect template
specfact backlog refine ado --template defect_v1 --search "WorkItemType = 'Bug'"
```

---

## How It Works

### Step 1: Fetch Backlog Items

The command fetches backlog items from the specified adapter (GitHub, ADO, etc.) and converts them to the unified `BacklogItem` domain model.

```bash
specfact backlog refine github --search "is:open"
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
specfact backlog refine github --framework scrum --persona product-owner --search "is:open"

# Force specific template (overrides priority-based resolution)
specfact backlog refine github --template user_story_v1 --search "is:open"
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
specfact backlog refine github --search "is:open"

# The CLI will:
# 1. Display the refinement prompt
# 2. Wait for you to paste refined content from IDE AI copilot
# 3. Validate and score the refinement
# 4. Ask for confirmation before applying
```

### Step 4: Preview and Apply Refinement

Once validated, the refinement can be previewed or applied:

**Preview Mode (Default - Safe)**:

- Shows what will be updated (title, body) vs preserved (assignees, tags, state, priority, etc.)
- Displays original vs refined content diff
- **Does NOT write to remote backlog** (safe by default)

**Write Mode (Explicit Opt-in)**:

- Requires `--write` flag to explicitly opt-in
- Updates `BacklogItem.body_markdown` with refined content
- Sets `refinement_applied = True`
- Records `refinement_timestamp`
- Updates template detection metadata
- **Preserves all other fields** (assignees, tags, state, priority, due_date, story_points, etc.)

**Field Preservation Policy**:

- **Updated**: `title`, `body_markdown`
- **Preserved**: `assignees`, `tags`, `state`, `priority`, `due_date`, `story_points`, and all other metadata

```bash
# Preview mode (default - safe, no writeback)
specfact backlog refine github --preview --search "is:open"

# Write mode (explicit opt-in required)
specfact backlog refine github --write --search "is:open"

# Auto-accept high-confidence refinements (>= 0.85) and write
specfact backlog refine github --auto-accept-high-confidence --write --search "is:open"
```

### Step 4.5: Definition of Ready (DoR) Validation (Optional)

If `--check-dor` flag is set, SpecFact CLI validates backlog items against Definition of Ready rules:

- Loads DoR configuration from `.specfact/dor.yaml` (repo-level)
- Validates required fields (story_points, priority, business_value, acceptance_criteria, dependencies)
- Displays DoR status before refinement
- Warns if items are not ready for sprint planning

```bash
# Check DoR before refinement
specfact backlog refine github --check-dor --labels feature
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
specfact backlog refine github \
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

### `specfact backlog refine`

Refine backlog items using AI-assisted template matching.

```bash
specfact backlog refine <ADAPTER> [OPTIONS]
```

**Arguments**:

- `ADAPTER` - Backlog adapter name (`github`, `ado`, etc.)

**Options**:

- `--search`, `-s` - Search query to filter backlog items
- `--template`, `-t` - Target template ID (default: auto-detect)
- `--auto-accept-high-confidence` - Auto-accept refinements with confidence >= 0.85
- `--bundle`, `-b` - OpenSpec bundle path to import refined items
- `--auto-bundle` - Auto-import refined items to OpenSpec bundle

**Examples**:

```bash
# Refine GitHub issues (auto-detect template)
specfact backlog refine github --search "is:open label:feature"

# Filter by labels and state
specfact backlog refine github --labels feature,enhancement --state open

# Filter by sprint and assignee
specfact backlog refine github --sprint "Sprint 1" --assignee dev1

# Filter by framework and persona (Scrum + Product Owner)
specfact backlog refine github --framework scrum --persona product-owner --labels feature

# Refine with specific template
specfact backlog refine github --template user_story_v1 --search "is:open"

# Check Definition of Ready before refinement
specfact backlog refine github --check-dor --labels feature

# Preview refinement without writing (default - safe mode)
specfact backlog refine github --preview --labels feature

# Write refinement to backlog (explicit opt-in required)
specfact backlog refine github --write --labels feature

# Auto-accept high-confidence refinements
specfact backlog refine github --auto-accept-high-confidence --search "is:open"

# Refine and import to OpenSpec bundle
specfact backlog refine github \
  --bundle my-project \
  --auto-bundle \
  --search "is:open label:enhancement"

# Refine ADO work items with sprint filter
specfact backlog refine ado --sprint "Sprint 1" --state Active

# Refine ADO work items with iteration path
specfact backlog refine ado --iteration "Project\\Release 1\\Sprint 1"
```

---

## Workflow Integration

### Command Chaining: Refine → Sync

The most common workflow is to refine backlog items and then sync them to external tools. This command chaining workflow is fully supported and tested:

**Workflow**: `backlog refine` → `sync bridge`

1. **Refine Backlog Items**: Use `specfact backlog refine` to standardize backlog items with templates
2. **Sync to External Tools**: Use `specfact sync bridge` to sync refined items back to backlog tools (GitHub, ADO, etc.)

```bash
# Complete command chaining workflow
# 1. Refine GitHub issues (with writeback)
specfact backlog refine github \
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
specfact backlog refine github \
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

### With DevOps Adapter Integration

Backlog refinement works seamlessly with the [DevOps Adapter Integration](../guides/devops-adapter-integration.md):

1. **Import Backlog Items**: Use `specfact sync bridge` to import backlog items as OpenSpec proposals
2. **Refine Items**: Use `specfact backlog refine` to standardize imported items
3. **Export Refined Items**: Use `specfact sync bridge` to export refined proposals back to backlog tools

```bash
# Complete workflow
# 1. Import GitHub issues as OpenSpec proposals
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner my-org --repo-name my-repo \
  --backlog-ids 123,456

# 2. Refine imported items
specfact backlog refine github --bundle my-project --auto-bundle \
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
specfact backlog refine github --search "is:open label:feature"

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
specfact backlog refine github --framework scrum --persona product-owner --labels feature

# Force specific template (overrides priority-based resolution)
specfact backlog refine github --template custom_template_v1
```

---

## Best Practices

### 1. Start with Auto-Detection

Let SpecFact CLI detect templates automatically before forcing specific templates:

```bash
# Good: Auto-detect first
specfact backlog refine github --search "is:open"

# Then use specific template if needed
specfact backlog refine github --template user_story_v1 --search "is:open"
```

### 2. Review Low-Confidence Refinements

Refinements with confidence < 0.85 may need manual review:

```bash
# Review low-confidence refinements manually
specfact backlog refine github --search "is:open"
# CLI will prompt for confirmation on low-confidence refinements
```

### 3. Use Auto-Accept for High-Confidence

For high-confidence refinements (>= 0.85), use auto-accept:

```bash
# Auto-accept high-confidence refinements
specfact backlog refine github --auto-accept-high-confidence --search "is:open"
```

### 4. Integrate with OpenSpec Bundles

Import refined items to OpenSpec bundles for full workflow integration:

```bash
# Refine and import to bundle
specfact backlog refine github \
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
specfact backlog refine github --sprint "Sprint 1" --state open

# Refine items assigned to specific developer
specfact backlog refine github --assignee dev1 --labels bug

# Refine items for specific release
specfact backlog refine ado --release "Release 1.0" --state Active

# Use persona/framework filtering for role-specific templates
specfact backlog refine github --persona product-owner --framework scrum --labels feature
```

### 7. Check Definition of Ready (DoR)

Use DoR validation to ensure items are ready for sprint planning:

```bash
# Check DoR before refinement
specfact backlog refine github --check-dor --labels feature

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
specfact backlog refine github --template user_story_v1 --search "is:open"
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
specfact backlog refine github --bundle my-project --auto-bundle
```

---

## Related Documentation

- **[DevOps Adapter Integration](../guides/devops-adapter-integration.md)** - Complete guide for GitHub Issues and Azure DevOps integration
- **[Command Reference](../reference/commands.md)** - Complete command documentation
- **[Agile/Scrum Workflows](../guides/agile-scrum-workflows.md)** - Persona-based collaboration for teams
- **[IDE Integration](../guides/ide-integration.md)** - Set up slash commands in your IDE

---

**Happy refining!** 🚀
