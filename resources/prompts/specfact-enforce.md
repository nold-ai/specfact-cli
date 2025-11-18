---
description: "Configure quality gates and enforcement modes for contract validation"
---

# SpecFact Enforce Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact enforce stage` before any analysis - execute the CLI command before any other operations
2. **NEVER write code**: Do not implement enforcement configuration logic - the CLI handles this
3. **NEVER create YAML/JSON directly**: All enforcement configuration must be CLI-generated
4. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata - use it, don't bypass its validation
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate or recreate it - use the CLI output as the source of truth
6. **NEVER manipulate internal code**: Do NOT use Python code to directly modify EnforcementConfig objects or any internal data structures. The CLI is THE interface - use it exclusively.
7. **No internal knowledge required**: You should NOT need to know about internal implementation details (EnforcementConfig model, EnforcementPreset enum, etc.). All operations must be performed via CLI commands.
8. **NEVER read artifacts directly**: Do NOT read enforcement configuration files directly to extract information unless for display purposes. Use CLI commands to get configuration information.

### What Happens If You Don't Follow This

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures
- ❌ Works only in Copilot mode, fails in CI/CD
- ❌ Breaks when CLI internals change
- ❌ Requires knowledge of internal code structure

## ⏸️ Wait States: User Input Required

**When user input is required, you MUST wait for the user's response.**

### Wait State Rules

1. **Never assume**: If input is missing, ask and wait
2. **Never continue**: Do not proceed until user responds
3. **Be explicit**: Clearly state what information you need
4. **Provide options**: Give examples or default suggestions

## Goal

Configure quality gates and enforcement modes for contract validation. This command sets the enforcement preset that determines how contract violations are handled (minimal, balanced, strict).

## Operating Constraints

**STRICTLY READ-WRITE**: This command modifies enforcement configuration. All updates must be performed by the specfact CLI.

**Command**: `specfact enforce stage`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag.

## What This Command Does

The `specfact enforce stage` command:

1. **Validates** the preset value (minimal, balanced, strict)
2. **Creates** enforcement configuration from preset
3. **Displays** configuration summary as a table
4. **Saves** configuration to `.specfact/config/enforcement.yaml`
5. **Reports** configuration path and status

## Execution Steps

### 1. Parse Arguments and Validate Input

**Parse user input** to extract:

- Preset (optional, default: `balanced`)
  - Valid values: `minimal`, `balanced`, `strict`

**WAIT STATE**: If user wants to set enforcement but hasn't specified preset, ask:

```text
"Which enforcement preset would you like to use?
- minimal: Log violations, never block
- balanced: Block HIGH severity, warn MEDIUM (default)
- strict: Block all MEDIUM+ violations

Enter preset (minimal/balanced/strict):
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

### 2. Execute Enforce Stage Command

**Execute CLI command**:

```bash
# Use default (balanced)
specfact enforce stage

# Specify preset
specfact enforce stage --preset minimal
specfact enforce stage --preset balanced
specfact enforce stage --preset strict
```

**Capture from CLI**:

- Preset validation (must be minimal, balanced, or strict)
- Configuration created from preset
- Configuration summary table displayed
- Configuration saved to `.specfact/config/enforcement.yaml`

### 3. Handle Errors

**Common errors**:

- **Unknown preset**: CLI will report error and list valid presets
- **Invalid preset format**: CLI will validate and report error

### 4. Report Completion

**After successful execution**:

```markdown
✓ Enforcement mode set successfully!

**Preset**: balanced
**Configuration**: `.specfact/config/enforcement.yaml`

**Enforcement Summary**:

| Severity | Action |
|----------|--------|
| HIGH     | Block  |
| MEDIUM   | Warn   |
| LOW      | Log    |

**Next Steps**:
- Run validation: `/specfact-cli/specfact-repro`
- Review configuration: Check `.specfact/config/enforcement.yaml`
```

## Guidelines

### Enforcement Presets

**minimal**:

- Log all violations
- Never block execution
- Best for: Development, exploration, learning

**balanced** (default):

- Block HIGH severity violations
- Warn on MEDIUM severity violations
- Log LOW severity violations
- Best for: Most production use cases

**strict**:

- Block all MEDIUM+ severity violations
- Log LOW severity violations
- Best for: Critical systems, compliance requirements

### Configuration Location

- Configuration is saved to: `.specfact/config/enforcement.yaml`
- This file is automatically created/updated by the CLI
- Configuration persists across sessions

### Best Practices

- Start with `balanced` preset for most use cases
- Use `minimal` during development to avoid blocking
- Use `strict` for production deployments or compliance
- Review configuration file to understand exact behavior

## Context

{ARGS}

--- End Command ---
