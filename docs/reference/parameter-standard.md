# Parameter Standard

**Date**: 2025-11-26  
**Status**: Active  
**Purpose**: Standardize parameter names and grouping across all SpecFact CLI commands

---

## 📋 Overview

This document defines the standard parameter names, groupings, and conventions for all SpecFact CLI commands. All commands must follow these standards for consistency and improved user experience.

---

## 🎯 Parameter Naming Conventions

### Standard Parameter Names

| Concept | Standard Name | Deprecated Names | Notes |
|---------|--------------|------------------|-------|
| Repository path | `--repo` | `--base-path` | Use `--repo` for repository root path |
| Output file path | `--out` | `--output` | Use `--out` for output file paths |
| Output format | `--output-format` | `--format` | Use `--output-format` for format specification |
| Interactive mode | `--interactive/--no-interactive` | `--non-interactive` | Use `--interactive/--no-interactive` for mode control |
| Project bundle | `--bundle` | `--name`, `--plan` (when used for bundle name) | Use `--bundle` for project bundle name |
| Plan bundle path | `--plan` | N/A | Use `--plan` for plan bundle file/directory path |
| SDD manifest path | `--sdd` | N/A | Use `--sdd` for SDD manifest file path |

### Deprecation Policy

- **Transition Period**: 3 months from implementation date
- **Deprecation Warnings**: Commands using deprecated names will show warnings
- **Removal**: Deprecated names will be removed after transition period
- **Documentation**: All examples and docs updated immediately

---

## 📊 Parameter Grouping

Parameters must be organized into logical groups in the following order:

### Group 1: Target/Input (Required)

**Purpose**: What to operate on

**Parameters**:

- `--bundle NAME` - Project bundle name (required for modular structure)
- `--repo PATH` - Repository path (default: ".")
- `--plan PATH` - Plan bundle path (default: active plan for bundle)
- `--sdd PATH` - SDD manifest path (default: bundle-specific .specfact/projects/<bundle-name>/sdd.yaml, Phase 8.5, with fallback to legacy .specfact/sdd/<bundle-name>.yaml)
- `--constitution PATH` - Constitution path (default: .specify/memory/constitution.md)

**Help Text Format**:

```python
# Target/Input
--bundle NAME        # Project bundle name (required)
--repo PATH          # Repository path (default: ".")
--plan PATH          # Plan bundle path (default: active plan for bundle)
```

### Group 2: Output/Results

**Purpose**: Where to write results

**Parameters**:

- `--out PATH` - Output file path (default: auto-generated)
- `--report PATH` - Report file path (default: auto-generated)
- `--output-format FMT` - Output format: yaml, json, markdown (default: yaml)

**Help Text Format**:

```python
# Output/Results
--out PATH           # Output file path (default: auto-generated)
--report PATH        # Report file path (default: auto-generated)
--output-format FMT  # Output format: yaml, json, markdown (default: yaml)
```

### Group 3: Behavior/Options

**Purpose**: How to operate

**Parameters**:

- `--interactive/--no-interactive` - Interactive mode (default: auto-detect)
- `--force` - Overwrite existing files
- `--dry-run` - Preview without writing
- `--verbose` - Verbose output
- `--shadow-only` - Observe without enforcing

**Help Text Format**:

```python
# Behavior/Options
--interactive        # Interactive mode (default: auto-detect)
--no-interactive     # Non-interactive mode (for CI/CD)
--force              # Overwrite existing files
--dry-run            # Preview without writing
--verbose            # Verbose output
```

### Group 4: Advanced/Configuration

**Purpose**: Advanced settings and configuration

**Parameters**:

- `--confidence FLOAT` - Confidence threshold: 0.0-1.0 (default: 0.5)
- `--budget SECONDS` - Time budget in seconds (default: 120)
- `--preset PRESET` - Enforcement preset: minimal, balanced, strict (default: balanced)
- `--max-questions INT` - Maximum questions per session (default: 5)

**Help Text Format**:

```python
# Advanced/Configuration
--confidence FLOAT   # Confidence threshold: 0.0-1.0 (default: 0.5)
--budget SECONDS     # Time budget in seconds (default: 120)
--preset PRESET      # Enforcement preset: minimal, balanced, strict (default: balanced)
```

---

## 🔄 Parameter Changes Required

### Phase 1.2: Rename Inconsistent Parameters ✅ **COMPLETED**

The following parameters have been renamed:

1. **`--base-path` → `--repo`** ✅
   - **File**: `src/specfact_cli/commands/generate.py`
   - **Command**: `generate contracts`
   - **Status**: Completed - Parameter renamed and all references updated

2. **`--output` → `--out`** ✅
   - **File**: `src/specfact_cli/commands/constitution.py`
   - **Command**: `constitution bootstrap`
   - **Status**: Completed - Parameter renamed and all references updated

3. **`--format` → `--output-format`** ✅
   - **Files**:
     - `src/specfact_cli/commands/plan.py` (plan compare command)
     - `src/specfact_cli/commands/enforce.py` (enforce sdd command)
   - **Status**: Completed - Parameters renamed and all references updated

4. **`--non-interactive` → `--no-interactive`** ✅
   - **Files**:
     - `src/specfact_cli/cli.py` (global flag)
     - `src/specfact_cli/commands/plan.py` (multiple commands)
     - `src/specfact_cli/commands/enforce.py` (enforce sdd command)
     - `src/specfact_cli/commands/generate.py` (generate contracts command)
   - **Status**: Completed - Global flag and all command flags updated, interaction logic fixed

### Phase 1.3: Verify `--bundle` Parameter ✅ **COMPLETED**

**Commands with `--bundle` Parameter**:

| Command | Parameter Type | Status | Notes |
|---------|---------------|--------|-------|
| `plan init` | Required Argument | ✅ | `bundle: str = typer.Argument(...)` |
| `plan review` | Required Argument | ✅ | `bundle: str = typer.Argument(...)` |
| `plan promote` | Required Argument | ✅ | `bundle: str = typer.Argument(...)` |
| `plan harden` | Required Argument | ✅ | `bundle: str = typer.Argument(...)` |
| `enforce sdd` | Required Argument | ✅ | `bundle: str = typer.Argument(...)` |
| `import from-code` | Required Argument | ✅ | `bundle: str = typer.Argument(...)` |
| `plan add-feature` | Optional Option | ✅ | `bundle: str \| None = typer.Option(...)` with validation |
| `plan add-story` | Optional Option | ✅ | `bundle: str \| None = typer.Option(...)` with validation |
| `plan update-idea` | Optional Option | ✅ | `bundle: str \| None = typer.Option(...)` with validation |
| `plan update-feature` | Optional Option | ✅ | `bundle: str \| None = typer.Option(...)` with validation |
| `plan update-story` | Optional Option | ✅ | `bundle: str \| None = typer.Option(...)` with validation |
| `plan compare` | Optional Option | ✅ | `bundle: str \| None = typer.Option(...)` - Added for consistency |
| `generate contracts` | Optional Option | ✅ | `bundle: str \| None = typer.Option(...)` - Added, prioritizes bundle over plan/sdd |
| `sync bridge` | Optional Option | ✅ | `bundle: str \| None = typer.Option(...)` - Auto-detects if not provided |

**Validation Improvements**:

- ✅ Enhanced `_find_bundle_dir()` function with better error messages
- ✅ Lists available bundles when bundle not found
- ✅ Suggests similar bundle names
- ✅ Provides clear creation instructions
- ✅ All commands with optional `--bundle` have fallback logic to find default bundle
- ✅ Help text updated to indicate when `--bundle` is required vs optional

---

## ✅ Validation Checklist

Before marking a command as compliant:

- [ ] All parameters use standard names (no deprecated names)
- [ ] Parameters grouped in correct order (Target → Output → Behavior → Advanced)
- [ ] Help text shows parameter groups with comments
- [ ] Defaults shown explicitly in help text
- [ ] Deprecation warnings added for old names (if applicable)
- [ ] Tests updated to use new parameter names
- [ ] Documentation updated with new parameter names

---

## 📝 Examples

### Before (Inconsistent)

```python
@app.command("contracts")
def generate_contracts(
    base_path: Path | None = typer.Option(None, "--base-path", help="Base directory"),
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Non-interactive mode"),
) -> None:
    ...
```

### After (Standardized)

```python
@app.command("contracts")
def generate_contracts(
    # Target/Input
    repo: Path | None = typer.Option(None, "--repo", help="Repository path (default: current directory)"),
    
    # Behavior/Options
    no_interactive: bool = typer.Option(False, "--no-interactive", help="Non-interactive mode (for CI/CD automation)"),
) -> None:
    ...
```

---

## 🔗 Related Documentation

- **[CLI Reorganization Implementation Plan](../../specfact-cli-internal/docs/internal/implementation/CLI_REORGANIZATION_IMPLEMENTATION_PLAN.md)** - Full reorganization plan
- **[Command Reference](./commands.md)** - Complete command reference
- **[Project Bundle Refactoring Plan](../../specfact-cli-internal/docs/internal/implementation/PROJECT_BUNDLE_REFACTORING_PLAN.md)** - Bundle parameter requirements

---

**Rulesets Applied**:

- Clean Code Principles (consistent naming, logical grouping)
- Estimation Bias Prevention (evidence-based standards)
- Markdown Rules (proper formatting, comprehensive structure)

**AI Model**: Claude Sonnet 4.5 (claude-sonnet-4-20250514)
