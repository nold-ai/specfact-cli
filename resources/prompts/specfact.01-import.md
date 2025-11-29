---
description: Import codebase → plan bundle. CLI extracts routes/schemas/relationships. LLM enriches with context.
---

# SpecFact Import Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Import codebase → plan bundle. CLI extracts (routes, schemas, relationships, contracts). LLM enriches (context, "why", completeness).

## Parameters

**Target/Input**: `--bundle NAME` (required), `--repo PATH`, `--entry-point PATH`, `--enrichment PATH`  
**Output/Results**: `--report PATH`  
**Behavior/Options**: `--shadow-only`, `--enrich-for-speckit`  
**Advanced/Configuration**: `--confidence FLOAT` (0.0-1.0), `--key-format FORMAT` (classname|sequential)

## Workflow

1. **Execute CLI**: `specfact import from-code <bundle> --repo <path> [options]`

   CLI extracts (no AI): routes (FastAPI/Flask/Django), schemas (Pydantic), relationships (imports/deps), contracts (OpenAPI scaffolds), source tracking, bundle metadata.

2. **LLM Enrichment** (if `--enrichment` provided):
   - **Context file**: Read `.specfact/projects/<bundle>/enrichment_context.md` for relationships, contracts, schemas
   - Use CLI output + bundle metadata + enrichment context as context
   - Enrich: business context, "why" reasoning, missing acceptance criteria
   - Validate: contracts vs code, feature/story alignment
   - Complete: constraints, test scenarios, edge cases

3. **Present**: Bundle location, report path, summary (features/stories/contracts/relationships)

## CLI Enforcement

**ALWAYS execute CLI first**. Never modify `.specfact/` directly. Use CLI output as grounding.

## Expected Output

**Success**: Bundle location, report path, summary (features/stories/contracts/relationships)  
**Error**: Missing bundle name or bundle already exists

## Common Patterns

```bash
/specfact.01-import --bundle legacy-api --repo .
/specfact.01-import --bundle legacy-api --repo . --enrichment report.md
/specfact.01-import --bundle auth-module --repo . --entry-point src/auth/
/specfact.01-import --bundle legacy-api --repo . --enrich-for-speckit
```

## Context

{ARGS}
