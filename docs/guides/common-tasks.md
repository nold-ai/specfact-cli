---
layout: default
title: Common Tasks Quick Reference
permalink: /common-tasks/
---

# Common Tasks Quick Reference

> **Quick answers to "How do I X?" questions**

---

## Overview

This guide maps common user goals to recommended SpecFact CLI commands or command chains. Each entry includes a task description, recommended approach, link to detailed guide, and a quick example.

**Not sure which task matches your goal?** Use the [Command Chains Decision Tree](command-chains.md#when-to-use-which-chain) to find the right workflow.

---

## Getting Started

### I want to analyze my legacy code

**Recommended**: [Brownfield Modernization Chain](command-chains.md#1-brownfield-modernization-chain)

**Command**: `import from-code`

**Quick Example**:

```bash
specfact import from-code legacy-api --repo .
```

**Detailed Guide**: [Brownfield Engineer Guide](brownfield-engineer.md)

---

### I want to plan a new feature from scratch

**Recommended**: [Greenfield Planning Chain](command-chains.md#2-greenfield-planning-chain)

**Command**: `plan init` → `plan add-feature` → `plan add-story`

**Quick Example**:

```bash
specfact plan init new-feature --interactive
specfact plan add-feature --bundle new-feature --name "User Authentication"
specfact plan add-story --bundle new-feature --feature <feature-id> --story "As a user, I want to log in"
```

**Detailed Guide**: [Agile/Scrum Workflows](agile-scrum-workflows.md)

---

### I want to sync with Spec-Kit or OpenSpec

**Recommended**: [External Tool Integration Chain](command-chains.md#3-external-tool-integration-chain)

**Command**: `import from-bridge` → `sync bridge`

**Quick Example**:

```bash
specfact import from-bridge --repo . --adapter speckit --write
specfact sync bridge --adapter speckit --bundle <bundle-name> --bidirectional --watch
```

**Detailed Guide**: [Spec-Kit Journey](speckit-journey.md) | [OpenSpec Journey](openspec-journey.md)

---

## Brownfield Modernization

### I want to extract specifications from existing code

**Recommended**: `import from-code`

**Quick Example**:

```bash
specfact import from-code legacy-api --repo ./legacy-app
```

**Detailed Guide**: [Brownfield Engineer Guide](brownfield-engineer.md#step-1-understand-what-you-have)

---

### I want to review and update extracted features

**Recommended**: `plan review` → `plan update-feature`

**Quick Example**:

```bash
specfact plan review legacy-api
specfact plan update-feature --bundle legacy-api --feature <feature-id>
```

**Detailed Guide**: [Brownfield Engineer Guide](brownfield-engineer.md#step-2-refine-your-plan)

---

### I want to detect code-spec drift

**Recommended**: [Code-to-Plan Comparison Chain](command-chains.md#6-code-to-plan-comparison-chain)

**Command**: `plan compare` → `drift detect`

**Quick Example**:

```bash
specfact import from-code current-state --repo .
specfact plan compare --bundle <plan-bundle> --code-vs-plan
specfact drift detect --bundle <bundle-name>
```

**Detailed Guide**: [Drift Detection](../reference/commands.md#drift-detect)

---

### I want to add contracts to existing code

**Recommended**: [AI-Assisted Code Enhancement Chain](command-chains.md#7-ai-assisted-code-enhancement-chain-emerging)

**Command**: `generate contracts-prompt` → [AI IDE] → `contracts-apply`

**Quick Example**:

```bash
specfact generate contracts-prompt --bundle <bundle-name> --feature <feature-id>
# Then use AI IDE slash command: /specfact-cli/contracts-apply <prompt-file>
specfact contract coverage --bundle <bundle-name>
```

**Detailed Guide**: [AI IDE Workflow](ai-ide-workflow.md)

---

## API Development

### I want to validate API contracts

**Recommended**: [API Contract Development Chain](command-chains.md#4-api-contract-development-chain)

**Command**: `spec validate` → `spec backward-compat`

**Quick Example**:

```bash
specfact spec validate --spec openapi.yaml
specfact spec backward-compat --spec openapi.yaml --previous-spec openapi-v1.yaml
```

**Detailed Guide**: [Specmatic Integration](specmatic-integration.md)

---

### I want to validate an external codebase without modifying source

**Recommended**: [Sidecar Validation Chain](command-chains.md#5-sidecar-validation-chain)

**Command**: `validate sidecar init` → `validate sidecar run`

**Quick Example**:

```bash
# Initialize sidecar workspace
specfact validate sidecar init legacy-api /path/to/django-project

# Run validation workflow
specfact validate sidecar run legacy-api /path/to/django-project
```

**What it does**:

- Detects framework (Django, FastAPI, DRF, Flask, pure Python)
- Automatically installs dependencies in isolated venv (`.specfact/venv/`)
- Extracts routes and schemas from framework patterns (all HTTP methods captured for Flask)
- Populates OpenAPI contracts automatically (with expected status codes and response structure validation)
- Generates CrossHair harness for symbolic execution (using venv Python)
- Runs CrossHair and Specmatic validation

**Detailed Guide**: [Sidecar Validation Guide](sidecar-validation.md)

---

### I want to generate tests from API specifications

**Recommended**: `spec generate-tests`

**Quick Example**:

```bash
specfact spec generate-tests --spec openapi.yaml --output tests/
pytest tests/
```

**Detailed Guide**: [Contract Testing Workflow](contract-testing-workflow.md)

---

### I want to create a mock server for API development

**Recommended**: `spec mock`

**Quick Example**:

```bash
specfact spec mock --spec openapi.yaml --port 8080
```

**Detailed Guide**: [Specmatic Integration](specmatic-integration.md)

---

## Team Collaboration

### I want to set up team collaboration

**Recommended**: [Team Collaboration Workflow](team-collaboration-workflow.md)

**Command**: `project export` → `project import` → `project lock/unlock`

**Quick Example**:

```bash
specfact project init-personas --bundle <bundle-name>
specfact project export --bundle <bundle-name> --persona product-owner
# Edit exported Markdown files
specfact project import --bundle <bundle-name> --persona product-owner --source exported-plan.md
```

**Detailed Guide**: [Agile/Scrum Workflows](agile-scrum-workflows.md)

---

### I want to export persona-specific views

**Recommended**: `project export`

**Quick Example**:

```bash
specfact project export --bundle <bundle-name> --persona product-owner
specfact project export --bundle <bundle-name> --persona architect
specfact project export --bundle <bundle-name> --persona developer
```

**Detailed Guide**: [Agile/Scrum Workflows](agile-scrum-workflows.md#persona-based-workflows)

---

### I want to manage project versions

**Recommended**: `project version check` → `project version bump`

**Quick Example**:

```bash
specfact project version check --bundle <bundle-name>
specfact project version bump --bundle <bundle-name> --type minor
```

**Detailed Guide**: [Project Version Management](../reference/commands.md#project-version)

---

## Plan Management

### I want to promote a plan through stages

**Recommended**: [Plan Promotion & Release Chain](command-chains.md#5-plan-promotion--release-chain)

**Command**: `plan review` → `enforce sdd` → `plan promote`

**Quick Example**:

```bash
specfact plan review <bundle-name>
specfact enforce sdd --bundle <bundle-name>
specfact plan promote --bundle <bundle-name> --stage approved
```

**Detailed Guide**: [Agile/Scrum Workflows](agile-scrum-workflows.md)

---

### I want to compare two plans

**Recommended**: `plan compare`

**Quick Example**:

```bash
specfact plan compare --bundle plan-v1 plan-v2
```

**Detailed Guide**: [Plan Comparison](../reference/commands.md#plan-compare)

---

## Validation & Enforcement

### I want to validate everything

**Recommended**: `repro`

**Quick Example**:

```bash
specfact repro --verbose
```

**Detailed Guide**: [Validation Workflow](brownfield-engineer.md#step-3-validate-everything)

---

### I want to enforce SDD compliance

**Recommended**: `enforce sdd`

**Quick Example**:

```bash
specfact enforce sdd --bundle <bundle-name>
```

**Detailed Guide**: [SDD Enforcement](../reference/commands.md#enforce-sdd)

---

### I want to find gaps in my code

**Recommended**: [Gap Discovery & Fixing Chain](command-chains.md#9-gap-discovery--fixing-chain-emerging)

**Command**: `repro --verbose` → `generate fix-prompt`

**Quick Example**:

```bash
specfact repro --verbose
specfact generate fix-prompt --bundle <bundle-name> --gap <gap-id>
# Then use AI IDE to apply fixes
```

**Detailed Guide**: [AI IDE Workflow](ai-ide-workflow.md)

---

## AI IDE Integration

### I want to set up AI IDE slash commands

**Recommended**: `init --ide cursor`

**Quick Example**:

```bash
specfact init ide --ide cursor
```

**Detailed Guide**: [AI IDE Workflow](ai-ide-workflow.md) | [IDE Integration](ide-integration.md)

---

### I want to generate tests using AI

**Recommended**: [Test Generation from Specifications Chain](command-chains.md#8-test-generation-from-specifications-chain-emerging)

**Command**: `generate test-prompt` → [AI IDE] → `spec generate-tests`

**Quick Example**:

```bash
specfact generate test-prompt --bundle <bundle-name> --feature <feature-id>
# Then use AI IDE slash command: /specfact-cli/test-generate <prompt-file>
specfact spec generate-tests --spec <spec-file> --output tests/
```

**Detailed Guide**: [AI IDE Workflow](ai-ide-workflow.md)

---

## DevOps Integration 🆕 **NEW FEATURE**

### I want to integrate SpecFact into my agile DevOps workflows

**Recommended**: [DevOps Adapter Integration](devops-adapter-integration.md) - Bidirectional backlog sync

**Command**: `sync bridge --adapter github --bidirectional`

**Quick Example**:

```bash
# Export OpenSpec change proposals to GitHub Issues
specfact sync bridge --adapter github --bidirectional \
  --repo-owner your-org --repo-name your-repo

# Import GitHub Issues as change proposals (automatic with --bidirectional)
# Track code changes automatically
specfact sync bridge --adapter github --track-code-changes \
  --repo-owner your-org --repo-name your-repo
```

**Detailed Guide**: [DevOps Adapter Integration](devops-adapter-integration.md)

---

### I want to standardize backlog items using templates

**Recommended**: [Backlog Refinement Guide](backlog-refinement.md) 🆕 **NEW FEATURE** - AI-assisted template-driven refinement

**Command**: `backlog refine`

**Quick Example**:

```bash
# Refine GitHub issues with auto-detection
specfact backlog refine github --search "is:open label:feature"

# Filter by sprint and assignee
specfact backlog refine github --sprint "Sprint 1" --assignee dev1

# Filter by framework and persona (Scrum + Product Owner)
specfact backlog refine github --framework scrum --persona product-owner --labels feature

# Check Definition of Ready before refinement
specfact backlog refine github --check-dor --labels feature

# Preview refinement without writing (default - safe mode)
specfact backlog refine github --preview --labels feature

# Write refinement to backlog (explicit opt-in)
specfact backlog refine github --write --labels feature
```

**Detailed Guide**: [Backlog Refinement Guide](backlog-refinement.md)

---

### I want to refine backlog items in a specific sprint

**Recommended**: `backlog refine` with sprint filtering

**Command**: `backlog refine --sprint <sprint-name>`

**Quick Example**:

```bash
# Refine items in current sprint
specfact backlog refine github --sprint "Sprint 1" --state open

# Refine ADO work items in specific iteration
specfact backlog refine ado --iteration "Project\\Sprint 1" --state Active
```

**Detailed Guide**: [Backlog Refinement Guide](backlog-refinement.md#quick-start)

---

### I want to use persona-specific templates for backlog refinement

**Recommended**: `backlog refine` with persona/framework filtering

**Command**: `backlog refine --persona <persona> --framework <framework>`

**Quick Example**:

```bash
# Use Product Owner templates with Scrum framework
specfact backlog refine github --persona product-owner --framework scrum --labels feature

# Use Developer templates with Agile framework
specfact backlog refine github --persona developer --framework agile --labels task
```

**Detailed Guide**: [Backlog Refinement Guide](backlog-refinement.md#template-system)

---

### I want to check if backlog items are ready for sprint planning

**Recommended**: `backlog refine` with DoR validation

**Command**: `backlog refine --check-dor`

**Quick Example**:

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

**Detailed Guide**: [Backlog Refinement Guide](backlog-refinement.md#definition-of-ready-dor)

---

### I want to sync change proposals to GitHub Issues

**Recommended**: DevOps bridge adapter with bidirectional sync 🆕

**Command**: `sync bridge --adapter github --bidirectional` (or `--mode export-only` for export-only)

**Quick Example**:

```bash
# Bidirectional sync (export AND import)
specfact sync bridge --adapter github --bidirectional \
  --repo-owner your-org --repo-name your-repo

# Export-only (one-way: OpenSpec → GitHub)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org --repo-name your-repo

# Update existing issue (when proposal already linked to issue)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org --repo-name your-repo \
  --change-ids your-change-id \
  --update-existing
```

**Detailed Guide**: [DevOps Adapter Integration](devops-adapter-integration.md)

---

### I want to update an existing GitHub issue with my change proposal

**Recommended**: Use `--update-existing` flag with `--change-ids` to update a specific linked issue

**Command**: `sync bridge --adapter github --mode export-only --update-existing --change-ids <change-id>`

**Prerequisites**:

- Change proposal must have `source_tracking` metadata linking it to the GitHub issue
- The issue number should be in the proposal's `proposal.md` file under "Source Tracking" section

**Quick Example**:

```bash
# Update issue #105 for change proposal 'implement-adapter-enhancement-recommendations'
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai \
  --repo-name specfact-cli \
  --change-ids implement-adapter-enhancement-recommendations \
  --update-existing \
  --repo /path/to/openspec-repo
```

**What Gets Updated**:

- Issue body with latest proposal content (if content changed)
- Issue title (if proposal title changed)
- Status labels (OpenSpec status ↔ GitHub labels)
- OpenSpec metadata footer in issue body

**Note**: The adapter uses content hash detection - if proposal hasn't changed, issue won't be updated (prevents unnecessary API calls).

**Detailed Guide**: [DevOps Adapter Integration - Update Existing Issues](devops-adapter-integration.md#update-existing-issues)

---

### I want to track changes in GitHub Projects

**Recommended**: DevOps bridge adapter with project linking

**Quick Example**:

```bash
specfact sync bridge --adapter github --mode export-only --project "SpecFact CLI Development Board"
```

**Detailed Guide**: [DevOps Adapter Integration](devops-adapter-integration.md)

---

## Migration & Troubleshooting

### I want to migrate from an older version

**Recommended**: Check migration guides

**Quick Example**:

```bash
# Check current version
specfact --version

# Review migration guide for your version
# See: guides/migration-*.md
```

**Detailed Guide**: [Migration Guide](migration-guide.md) | [Troubleshooting](troubleshooting.md)

---

### I want to troubleshoot an issue

**Recommended**: [Troubleshooting Guide](troubleshooting.md)

**Quick Example**:

```bash
# Run validation with verbose output
specfact repro --verbose

# Check plan for issues
specfact plan review <bundle-name>
```

**Detailed Guide**: [Troubleshooting](troubleshooting.md)

---

## See Also

- [Command Chains Reference](command-chains.md) - Complete workflows with decision trees
- [Command Reference](../reference/commands.md) - Complete command documentation
- [Brownfield Engineer Guide](brownfield-engineer.md) - Legacy modernization guide
- [Agile/Scrum Workflows](agile-scrum-workflows.md) - Team collaboration patterns
