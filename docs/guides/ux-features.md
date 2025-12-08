# UX Features Guide

This guide covers the user experience features that make SpecFact CLI intuitive and efficient.

## Progressive Disclosure

SpecFact CLI uses progressive disclosure to show the most important options first, while keeping advanced options accessible when needed.

### Regular Help

By default, `--help` shows only the most commonly used options:

```bash
specfact import from-code --help
```

This displays:
- Required arguments
- Common options (bundle, repo, output)
- Behavior flags (interactive, verbose)

### Advanced Help

To see all options including advanced configuration, use `--help-advanced`:

```bash
specfact import from-code --help-advanced
```

This reveals:
- Advanced configuration options (confidence thresholds, key formats)
- Specialized flags
- Expert-level settings

**Tip**: Advanced options are still functional even when hidden - you can use them directly without `--help-advanced`. The flag only affects what's shown in help text.

## Context Detection

SpecFact CLI automatically detects your project context to provide smart defaults and suggestions.

### Auto-Detection

When you run commands, SpecFact automatically detects:

- **Project Type**: Python, JavaScript, etc.
- **Framework**: FastAPI, Django, Flask, etc.
- **Existing Specs**: OpenAPI/AsyncAPI specifications
- **Plan Bundles**: Existing SpecFact project bundles
- **Configuration**: Specmatic configuration files

### Smart Defaults

Based on detected context, SpecFact provides intelligent defaults:

```bash
# If OpenAPI spec detected, suggests validation
specfact spec validate --bundle <auto-detected>

# If low contract coverage detected, suggests analysis
specfact analyze --bundle <auto-detected>
```

### Explicit Context

You can also explicitly check your project context:

```bash
# Context detection is automatic, but you can verify
specfact import from-code --bundle my-bundle --repo .
# CLI automatically detects Python, FastAPI, existing specs, etc.
```

## Intelligent Suggestions

SpecFact provides context-aware suggestions to guide your workflow.

### Next Steps

After running commands, SpecFact suggests logical next steps:

```bash
$ specfact import from-code --bundle legacy-api
✓ Import complete

💡 Suggested next steps:
  • specfact analyze --bundle legacy-api  # Analyze contract coverage
  • specfact enforce sdd --bundle legacy-api  # Enforce quality gates
  • specfact sync intelligent --bundle legacy-api  # Sync code and specs
```

### Error Fixes

When errors occur, SpecFact suggests specific fixes:

```bash
$ specfact analyze --bundle missing-bundle
✗ Error: Bundle 'missing-bundle' not found

💡 Suggested fixes:
  • specfact plan select  # Select an active plan bundle
  • specfact import from-code --bundle missing-bundle  # Create a new bundle
```

### Improvements

Based on analysis, SpecFact suggests improvements:

```bash
$ specfact analyze --bundle legacy-api
⚠ Low contract coverage detected (30%)

💡 Suggested improvements:
  • specfact analyze --bundle legacy-api  # Identify missing contracts
  • specfact import from-code --bundle legacy-api  # Extract contracts from code
```

## Template-Driven Quality

SpecFact uses templates to ensure high-quality, consistent specifications.

### Feature Specification Templates

When creating features, templates guide you to focus on:

- **WHAT** users need (not HOW to implement)
- **WHY** the feature is valuable
- **Uncertainty markers** for ambiguous requirements: `[NEEDS CLARIFICATION: specific question]`
- **Completeness checklists** to ensure nothing is missed

### Implementation Plan Templates

Implementation plans follow templates that:

- Keep high-level steps readable
- Extract detailed algorithms to separate files
- Enforce test-first thinking (contracts → tests → implementation)
- Include phase gates for architectural principles

### Contract Extraction Templates

Contract extraction uses templates to:

- Extract contracts from legacy code patterns
- Identify validation logic
- Map to formal contracts (icontract, beartype)
- Mark uncertainties for later clarification

## Enhanced Watch Mode

Watch mode has been enhanced with intelligent change detection.

### Hash-Based Detection

Watch mode only processes files that actually changed:

```bash
specfact sync intelligent --bundle my-bundle --watch
```

**Features**:
- SHA256 hash-based change detection
- Only processes files with actual content changes
- Skips unchanged files (even if modified timestamp changed)
- Faster sync operations

### Dependency Tracking

Watch mode tracks file dependencies:

- Identifies dependent files
- Processes dependencies when source files change
- Incremental processing (only changed files and dependencies)

### Cache Optimization

Watch mode uses an optimized cache:

- LZ4 compression (when available) for faster I/O
- Persistent cache across sessions
- Automatic cache management

## Unified Progress Display

All commands use consistent progress indicators.

### Progress Format

Progress displays use a consistent `n/m` format:

```
Loading artifact 3/12: FEATURE-001.yaml
```

This shows:
- Current item number (3)
- Total items (12)
- Current artifact name (FEATURE-001.yaml)
- Elapsed time

### Visibility

Progress is shown for:
- All bundle load/save operations
- Long-running operations (>1 second)
- File processing operations
- Analysis operations

**No "dark" periods** - you always know what's happening.

## Best Practices

### Using Progressive Disclosure

1. **Start with regular help** - Most users only need common options
2. **Use `--help-advanced`** when you need fine-grained control
3. **Advanced options work without help** - You can use them directly

### Leveraging Context Detection

1. **Let SpecFact auto-detect** - It's usually correct
2. **Verify context** - Check suggestions match your project
3. **Use explicit flags** - Override auto-detection when needed

### Following Suggestions

1. **Read suggestions carefully** - They're context-aware
2. **Follow the workflow** - Suggestions guide logical next steps
3. **Use error suggestions** - They provide specific fixes

### Using Templates

1. **Follow template structure** - Ensures quality and consistency
2. **Mark uncertainties** - Use `[NEEDS CLARIFICATION]` markers
3. **Complete checklists** - Templates include completeness checks

---

**Related Documentation**:
- [Command Reference](../reference/commands.md) - Complete command documentation
- [Workflows](workflows.md) - Common daily workflows
- [IDE Integration](ide-integration.md) - Enhanced IDE experience

