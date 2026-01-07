---
layout: default
title: Import Command Features
permalink: /guides/import-features/
---

# Import Command Features

This guide covers advanced features and optimizations in the `import from-code` command.

## Overview

The `import from-code` command has been optimized for large codebases and includes several features to improve reliability, performance, and user experience:

- **Progress Reporting**: Real-time progress bars for long-running operations
- **Feature Validation**: Automatic validation of existing features when resuming imports
- **Early Save Checkpoint**: Features saved immediately after analysis to prevent data loss
- **Performance Optimizations**: Pre-computed caches for 5-15x faster processing
- **Re-validation Flag**: Force re-analysis of features even if files haven't changed

---

## Progress Reporting

The import command now provides detailed progress reporting for all major operations:

### Feature Analysis Progress

During the initial codebase analysis, you'll see:

```
🔍 Analyzing codebase...
✓ Found 3156 features
✓ Detected themes: API, Async, Database, ORM, Testing
✓ Total stories: 5604
```

### Source File Linking Progress

When linking source files to features, a progress bar shows:

```
Linking 3156 features to source files...
[████████████████████] 100% (3156/3156 features)
```

This is especially useful for large codebases where linking can take several minutes.

### Contract Extraction Progress

During OpenAPI contract extraction, progress is shown for each feature being processed.

---

## Feature Validation

When you restart an import on an existing bundle, the command automatically validates existing features:

### Automatic Validation

```bash
# First import
specfact import from-code my-project --repo .

# Later, restart import (validates existing features automatically)
specfact import from-code my-project --repo .
```

### Validation Results

The command reports validation results:

```
🔍 Validating existing features...
✓ All 3156 features validated successfully (source files exist)
```

Or if issues are found:

```
⚠ Feature validation found issues: 3100/3156 valid, 45 orphaned, 11 invalid
  Orphaned features (all source files missing):
    - FEATURE-1234 (3 missing files)
    - FEATURE-5678 (2 missing files)
    ...
  Invalid features (some files missing or structure issues):
    - FEATURE-9012 (1 missing file)
    ...
  Tip: Use --revalidate-features to re-analyze features and fix issues
```

### What Gets Validated

- **Source file existence**: Checks that all referenced implementation and test files still exist
- **Feature structure**: Validates that features have required fields (key, title, stories)
- **Orphaned features**: Detects features whose source files have been deleted
- **Invalid features**: Identifies features with missing files or structural issues

---

## Early Save Checkpoint

Features are saved immediately after the initial codebase analysis, before expensive operations like source tracking and contract extraction.

### Benefits

- **Resume capability**: If the import is interrupted, you can restart without losing the initial analysis
- **Data safety**: Features are persisted early, reducing risk of data loss
- **Faster recovery**: No need to re-run the full codebase scan if interrupted

### Example

```bash
# Start import
specfact import from-code my-project --repo .

# Output shows:
# ✓ Found 3156 features
# 💾 Saving features (checkpoint)...
# ✓ Features saved (can resume if interrupted)

# If you press Ctrl+C during source linking, you can restart:
specfact import from-code my-project --repo .
# The command will detect existing features and resume from checkpoint
```

---

## Performance Optimizations

The import command has been optimized for large codebases (3000+ features):

### Pre-computed Caches

- **AST Parsing**: All files are parsed once before parallel processing
- **File Hashes**: All file hashes are computed once and cached
- **Function Mappings**: Function names are extracted once per file

### Performance Improvements

- **Before**: ~34 features/minute (515/3156 in 15 minutes)
- **After**: 200-500+ features/minute (5-15x faster)
- **Large codebases**: 3000+ features processed in 6-15 minutes (down from 90+ minutes)

### How It Works

1. **Pre-computation phase**: Single pass through all files to build caches
2. **Parallel processing**: Uses cached results (no file I/O or AST parsing)
3. **Thread-safe**: Read-only caches during parallel execution

---

## Re-validation Flag

Use `--revalidate-features` to force re-analysis even if source files haven't changed.

### When to Use

- **Analysis improvements**: When the analysis logic has been improved
- **Confidence changes**: When you want to re-evaluate features with a different confidence threshold
- **File changes outside repo**: When files were moved or renamed outside the repository
- **Validation issues**: When validation reports orphaned or invalid features

### Example

```bash
# Re-analyze all features even if files unchanged
specfact import from-code my-project --repo . --revalidate-features

# Output shows:
# ⚠ --revalidate-features enabled: Will re-analyze features even if files unchanged
```

### What Happens

- Forces full codebase analysis regardless of incremental change detection
- Re-computes all feature mappings and source tracking
- Updates feature confidence scores based on current analysis logic
- Regenerates all contracts and relationships

---

## Best Practices

### Large Codebases

For codebases with 1000+ features:

1. **Use partial analysis**: Start with `--entry-point` to analyze one module at a time
2. **Monitor progress**: Watch the progress bars to estimate completion time
3. **Use checkpoints**: Let the early save checkpoint work for you - don't worry about interruptions
4. **Re-validate periodically**: Use `--revalidate-features` after major code changes

### Resuming Interrupted Imports

1. **Don't delete the bundle**: The checkpoint is stored in the bundle directory
2. **Run the same command**: Just re-run the import command - it will detect existing features
3. **Check validation**: Review validation results to see if any features need attention
4. **Use re-validation if needed**: If validation shows issues, use `--revalidate-features`

### Performance Tips

1. **Exclude tests if not needed**: Use `--exclude-tests` for faster processing (if test analysis isn't critical)
2. **Use entry points**: For monorepos, analyze one project at a time with `--entry-point`
3. **Adjust confidence**: Lower confidence (0.3-0.5) for faster analysis, higher (0.7-0.9) for more accurate results

---

## Troubleshooting

### Slow Linking

If source file linking is slow:

- **Check file count**: Large numbers of files (10,000+) will take longer
- **Monitor progress**: The progress bar shows current status
- **Use entry points**: Limit scope with `--entry-point` for faster processing

### Validation Issues

If validation reports many orphaned features:

- **Check file paths**: Ensure source files haven't been moved
- **Use re-validation**: Run with `--revalidate-features` to fix mappings
- **Review feature keys**: Some features may need manual adjustment

### Interrupted Imports

If import is interrupted:

- **Don't delete bundle**: The checkpoint is in `.specfact/projects/<bundle-name>/`
- **Restart command**: Run the same import command - it will resume
- **Check progress**: Validation will show what was completed

---

## Related Documentation

- [Command Reference](../reference/commands.md#import-from-code) - Complete command documentation
- [Quick Examples](../examples/quick-examples.md) - Quick command examples
- [Brownfield Engineer Guide](brownfield-engineer.md) - Complete brownfield workflow
- [Common Tasks](common-tasks.md) - Common import scenarios

---

**Happy importing!** 🚀
