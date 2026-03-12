# Prompt Templates and Slash Commands Reference

This directory contains documentation and tools for validating slash command prompts, as well as a reference for all available slash commands.

---

## Slash Commands Reference

SpecFact CLI provides slash commands that work with AI-assisted IDEs (Cursor, VS Code + Copilot, Claude Code, etc.). These commands enable a seamless workflow: **SpecFact finds gaps → AI IDE fixes them → SpecFact validates**.

### Quick Start

1. **Initialize IDE integration**:

   ```bash
   specfact init ide --ide cursor
   ```

2. **Use slash commands in your IDE**:

   ```bash
   /specfact.01-import legacy-api --repo .
   /specfact.03-review legacy-api
   /specfact.05-enforce legacy-api
   ```

**Related**: [AI IDE Workflow Guide](../guides/ai-ide-workflow.md) - Complete workflow guide

---

### Core Workflow Commands

#### `/specfact.01-import`

**Purpose**: Import from codebase (brownfield modernization)

**Equivalent CLI**: `specfact code import`

**Example**:

```bash
/specfact.01-import legacy-api --repo .
```

**Workflow**: [Brownfield Modernization Chain](../guides/command-chains.md#1-brownfield-modernization-chain)

---

#### `/specfact.02-plan`

**Purpose**: Plan management (init, add-feature, add-story, update-idea, update-feature, update-story)

**Equivalent CLI**: `specfact project plan init/add-feature/add-story/update-idea/update-feature/update-story`

**Example**:

```bash
/specfact.02-plan init legacy-api
/specfact.02-plan add-feature --bundle legacy-api --key FEATURE-001 --title "User Auth"
```

**Workflow**: [Greenfield Planning Chain](../guides/command-chains.md#2-greenfield-planning-chain)

---

#### `/specfact.03-review`

**Purpose**: Review plan and promote

**Equivalent CLI**: `specfact project plan review`

**Example**:

```bash
/specfact.03-review legacy-api
```

**Workflow**: [Brownfield Modernization Chain](../guides/command-chains.md#1-brownfield-modernization-chain), [Greenfield Planning Chain](../guides/command-chains.md#2-greenfield-planning-chain)

---

#### `/specfact.04-sdd`

**Purpose**: Create SDD manifest

**Equivalent CLI**: `specfact govern enforce sdd`

**Example**:

```bash
/specfact.04-sdd legacy-api
```

**Workflow**: [Brownfield Modernization Chain](../guides/command-chains.md#1-brownfield-modernization-chain)

---

#### `/specfact.05-enforce`

**Purpose**: SDD enforcement

**Equivalent CLI**: `specfact govern enforce sdd`

**Example**:

```bash
/specfact.05-enforce legacy-api
```

**Workflow**: [Brownfield Modernization Chain](../guides/command-chains.md#1-brownfield-modernization-chain), [Plan Promotion & Release Chain](../guides/command-chains.md#5-plan-promotion--release-chain)

---

#### `/specfact.06-sync`

**Purpose**: Sync operations

**Equivalent CLI**: `specfact project sync bridge`

**Example**:

```bash
/specfact.06-sync --adapter speckit --repo . --bidirectional
```

**Workflow**: [External Tool Integration Chain](../guides/command-chains.md#3-external-tool-integration-chain)

---

#### `/specfact.07-contracts`

**Purpose**: Contract management (analyze, generate prompts, apply contracts sequentially)

**Equivalent CLI**: `specfact spec generate contracts-prompt`

**Example**:

```bash
/specfact.07-contracts legacy-api --apply all-contracts
```

**Workflow**: [AI-Assisted Code Enhancement Chain](../guides/command-chains.md#7-ai-assisted-code-enhancement-chain-emerging)

---

### Advanced Commands

#### `/specfact.compare`

**Purpose**: Compare plans

**Equivalent CLI**: `specfact project plan compare`

**Example**:

```bash
/specfact.compare --bundle legacy-api
```

**Workflow**: [Code-to-Plan Comparison Chain](../guides/command-chains.md#6-code-to-plan-comparison-chain)

---

#### `/specfact.validate`

**Purpose**: Validation suite

**Equivalent CLI**: `specfact code repro`

**Example**:

```bash
/specfact.validate --repo .
```

**Workflow**: [Brownfield Modernization Chain](../guides/command-chains.md#1-brownfield-modernization-chain), [Gap Discovery & Fixing Chain](../guides/command-chains.md#9-gap-discovery--fixing-chain-emerging)

---

## Prompt Validation System

This directory contains documentation and tools for validating slash command prompts to ensure they are correct, aligned with CLI commands, and provide good UX.

## Quick Start

### Run Automated Validation

```bash
# Validate all prompts
hatch run validate-prompts

# Or directly
python tools/validate_prompts.py
```

### Run Tests

```bash
# Run prompt validation tests
hatch test tests/unit/prompts/test_prompt_validation.py -v
```

## What Gets Validated

The automated validator checks:

1. **Structure**: Required sections present (CLI Enforcement, Wait States, Goal, Operating Constraints)
2. **CLI Alignment**: CLI commands match actual CLI, enforcement rules present
3. **Wait States**: Wait state rules and markers present
4. **Dual-Stack Workflow**: Three-phase workflow for applicable commands
5. **Consistency**: Consistent formatting and structure across prompts

## Validation Results

All 8 prompts currently pass validation:

- ✅ `specfact.01-import` (20 checks) - Import from codebase
- ✅ `specfact.02-plan` (15 checks) - Plan management (init, add-feature, add-story, update-idea, update-feature, update-story)
- ✅ `specfact.03-review` (15 checks) - Review plan and promote
- ✅ `specfact.04-sdd` (15 checks) - Create SDD manifest
- ✅ `specfact.05-enforce` (15 checks) - SDD enforcement
- ✅ `specfact.06-sync` (15 checks) - Sync operations
- ✅ `specfact.compare` (15 checks) - Compare plans
- ✅ `specfact.validate` (15 checks) - Validation suite

## Manual Review

See [PROMPT_VALIDATION_CHECKLIST.md](./PROMPT_VALIDATION_CHECKLIST.md) for:

- Detailed manual review checklist
- Testing scenarios with Copilot
- Common issues and fixes
- Continuous improvement process

## Files

- **`tools/validate_prompts.py`**: Automated validation tool
- **`tests/unit/prompts/test_prompt_validation.py`**: Unit tests for validator
- **`PROMPT_VALIDATION_CHECKLIST.md`**: Manual review checklist
- **`resources/prompts/`**: Prompt template files

## Integration

The validation tool is integrated into the development workflow:

- **Pre-commit**: Run `hatch run validate-prompts` before committing prompt changes
- **CI/CD**: Add validation step to CI pipeline
- **Development**: Run validation after updating any prompt

## Next Steps

1. **Test with Copilot**: Use the manual checklist to test each prompt in real scenarios
2. **Document Issues**: Document any issues found during testing
3. **Improve Prompts**: Update prompts based on testing feedback
4. **Expand Validation**: Add more checks as patterns emerge

---

**Last Updated**: 2025-12-02 (v0.11.4 - Active Plan Fallback, SDD Hash Stability)  
**Version**: 1.1
