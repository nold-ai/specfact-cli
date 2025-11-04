---
description: Compare manual and auto-derived plans to detect deviations and inconsistencies.
---
# SpecFact Compare Plan Command

## User Input

```text
$ARGUMENTS
```

## Action Required

**If arguments provided**: Execute `specfact plan compare` immediately with provided arguments.

**If arguments missing**: Ask user interactively for:

1. **Manual plan path**: "Which manual plan to compare? (default: .specfact/plans/main.bundle.yaml)"
2. **Auto plan path**: "Which auto-derived plan to compare? (default: latest in .specfact/reports/brownfield/)"
3. **Output format**: "Output format? (1) Markdown, (2) JSON, (3) YAML (default: markdown)"
4. **Output file**: "Save report to file? (optional, default: auto-generated with timestamp)"

**Only execute after** getting necessary information from user.

## Command

```bash
specfact plan compare [--manual PATH] [--auto PATH] [--format {markdown|json|yaml}] [--out PATH]
```

## Quick Reference

**Arguments:**

- `--manual PATH` - Manual plan bundle path (default: `.specfact/plans/main.bundle.yaml`) - **ASK USER if default not found**
- `--auto PATH` - Auto-derived plan bundle path (default: latest in `.specfact/reports/brownfield/`) - **ASK USER if default not found**
- `--format {markdown|json|yaml}` - Output format (default: `markdown`) - **ASK USER if not specified**
- `--out PATH` - Output file path (optional, default: auto-generated in `.specfact/reports/comparison/`)

**What it does:**

1. Loads and validates both plan bundles (manual and auto-derived)
2. Compares features and stories between plans
3. Detects deviations (missing features, mismatches, etc.)
4. Assigns severity (HIGH, MEDIUM, LOW) to each deviation
5. Generates structured comparison report (Markdown, JSON, or YAML)
6. Displays summary in console with deviation counts and severity breakdown
7. Optionally applies enforcement rules (if `.specfact/enforcement.yaml` exists)

## Interactive Flow

**Step 1**: Check if `--manual` is specified.

- **If missing**: Check if default path (`.specfact/plans/main.bundle.yaml`) exists
  - **If exists**: Use default path
  - **If not exists**: Ask user: "Manual plan not found at default location. Enter path to manual plan bundle, or create one with `specfact plan init --interactive`?"
- **If provided**: Use specified path

**Step 2**: Check if `--auto` is specified.

- **If missing**: Try to find latest auto-derived plan in `.specfact/plans/`
  - **If found**: Ask user: "Use latest auto-derived plan: [PATH]? (y/n, or enter different path)"
  - **If not found**: Ask user: "No auto-derived plans found. Enter path to auto-derived plan bundle, or generate one with `specfact import from-code --repo . --name my-project`?"
- **If provided**: Use specified path

**Step 3**: Check if `--format` is specified.

- **If missing**: Ask user: "Output format? (1) Markdown, (2) JSON, (3) YAML (default: markdown)"
- **If provided**: Use specified format

**Step 4**: Check if `--out` is specified.

- **If missing**: Ask user: "Save report to file? (y/n, default: auto-generated in .specfact/reports/comparison/)"
  - **If yes**: Generate default path with timestamp and format extension
  - **If no**: Skip file output (display in console only)
- **If provided**: Use specified path

**Step 5**: Confirm execution.

- Show summary: "Will compare [MANUAL_PATH] vs [AUTO_PATH] and save report as [OUT_PATH] in [FORMAT] format. Continue? (y/n)"
- **If yes**: Execute command
- **If no**: Cancel or ask for changes

**Step 6**: Execute command with confirmed arguments.

## Expected Output

**Console output (with deviations):**

```bash
SpecFact CLI - Plan Comparator

Manual Plan: .specfact/plans/main.bundle.yaml
Auto Plan: .specfact/reports/brownfield/auto-derived-2025-11-02T12-00-00.bundle.yaml
Total Deviations: 15

Comparison Results

Manual Plan: .specfact/plans/main.bundle.yaml
Auto Plan: .specfact/reports/brownfield/auto-derived-2025-11-02T12-00-00.bundle.yaml
Total Deviations: 15

Deviation Summary:
  🔴 HIGH: 3
  🟡 MEDIUM: 8
  🔵 LOW: 4

Deviations by Type and Severity
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Severity  ┃ Type              ┃ Description                        ┃ Location       ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ 🔴 HIGH   │ Missing Feature   │ FEATURE-005 exists in auto but not │ features[4]    │
│           │                   │ in manual                           │                │
│ 🔴 HIGH   │ Critical Mismatch │ STORY-003 acceptance criteria differ│ features[0].   │
│           │                   │ significantly                       │ stories[2]     │
└───────────┴───────────────────┴────────────────────────────────────┴───────────────┘

✓ Report written to: .specfact/reports/comparison/deviations-2025-11-02T12-00-00.md
```

**Console output (no deviations):**

```bash
No deviations found! Plans are identical.
```

**Console output (enforcement blocked):**

```bash
Enforcement Rules
Using enforcement config: .specfact/enforcement.yaml

🚫 [HIGH] missing_feature: BLOCK
❌ Enforcement BLOCKED: 1 deviation(s) violate quality gates
Fix the blocking deviations or adjust enforcement config
```

## Execution Steps

### 3. Validate Plan Bundles

Load and validate both plan bundles:

- **Schema validation**: Use Pydantic models to validate structure
- **Required fields**: Check all required fields are present
- **Data types**: Validate data types match schema
- **Report errors**: If validation fails, report error and exit

### 4. Compare Plans

Perform comprehensive comparison:

#### 4.1 Feature Comparison

For each feature in both plans:

- **Feature matching**: Match features by key (exact match) or title (fuzzy match)
- **Feature deviations**:
  - **Missing in manual**: Features in auto plan but not in manual
  - **Missing in auto**: Features in manual plan but not in auto
  - **Title mismatch**: Same key but different titles
  - **Outcomes mismatch**: Different expected outcomes
  - **Acceptance criteria mismatch**: Different acceptance criteria
  - **Confidence mismatch**: Significant confidence difference (> 0.3)

#### 4.2 Story Comparison

For each story in matched features:

- **Story matching**: Match stories by key (exact match) or title (fuzzy match)
- **Story deviations**:
  - **Missing in manual**: Stories in auto plan but not in manual
  - **Missing in auto**: Stories in manual plan but not in auto
  - **Title mismatch**: Same key but different titles
  - **Acceptance criteria mismatch**: Different acceptance criteria
  - **Confidence mismatch**: Significant confidence difference (> 0.3)

#### 4.3 Structure Comparison

- **Feature count**: Compare total feature counts
- **Story count**: Compare total story counts per feature
- **Coverage gaps**: Identify areas with no coverage in either plan

### 5. Assign Severity

Classify each deviation by severity:

- **HIGH**:
  - Missing features/stories in manual plan (potential oversight)
  - Critical acceptance criteria mismatch
  - Confidence difference > 0.5
  - Structural inconsistencies (orphaned stories, duplicate keys)

- **MEDIUM**:
  - Title mismatches (possible naming inconsistencies)
  - Acceptance criteria differences (non-critical)
  - Confidence difference 0.3-0.5
  - Outcome mismatches

- **LOW**:
  - Minor title variations
  - Confidence difference < 0.3
  - Cosmetic differences (formatting, whitespace)
  - Missing optional fields

### 6. Generate Comparison Report

Create structured report based on format:

#### Markdown Format

```markdown
# Plan Comparison Report

**Manual Plan**: `/path/to/manual.bundle.yaml`
**Auto Plan**: `/path/to/auto.bundle.yaml`
**Timestamp**: `2025-11-02T12:00:00Z`
**Total Deviations**: `15`

## Summary

- 🔴 **HIGH**: 3
- 🟡 **MEDIUM**: 8
- 🔵 **LOW**: 4

## Deviations

### HIGH Severity

| ID | Type | Description | Location |
|----|------|-------------|----------|
| H1 | Missing Feature | FEATURE-005 exists in auto but not in manual | features[4] |
| H2 | Critical Mismatch | STORY-003 acceptance criteria differ significantly | features[0].stories[2] |

### MEDIUM Severity

...

### LOW Severity

...
```

#### JSON Format

```json
{
  "manual_plan": "/path/to/manual.bundle.yaml",
  "auto_plan": "/path/to/auto.bundle.yaml",
  "timestamp": "2025-11-02T12:00:00Z",
  "total_deviations": 15,
  "severity_counts": {
    "HIGH": 3,
    "MEDIUM": 8,
    "LOW": 4
  },
  "deviations": [
    {
      "id": "H1",
      "severity": "HIGH",
      "type": "missing_feature",
      "description": "FEATURE-005 exists in auto but not in manual",
      "location": "features[4]"
    }
  ]
}
```

#### YAML Format

Same structure as JSON, in YAML format.

### 7. Output Results

- **Console output**: Display summary with deviation counts and severity breakdown
- **Table view**: Show detailed deviation table in console with deviations grouped by severity
- **Comparison report**: Write to specified output path (if `--out` provided)

### 8. Apply Enforcement Rules (Optional)

If enforcement config exists (`.specfact/enforcement.yaml`):

- **Load config**: Parse enforcement configuration
- **Check blocking**: Identify deviations that should block (based on severity)
- **Report blocking**: If blocking deviations found, report error and exit with code 1
- **Report passing**: If no blocking deviations, report success

**Note**: Finding deviations is a successful comparison result. Exit code 0 indicates successful execution (even if deviations were found). Use the report file, stdout, or enforcement config to determine if deviations are critical.

## Output Format

### Deviation Structure

Each deviation includes:

- **ID**: Unique identifier (e.g., "H1", "M5", "L2")
- **Severity**: HIGH, MEDIUM, or LOW
- **Type**: Deviation type (e.g., "missing_feature", "title_mismatch")
- **Description**: Human-readable description
- **Location**: Path to deviation in plan structure (e.g., "features[0].stories[2]")

### Report Structure

- **Header**: Manual plan path, auto plan path, timestamp
- **Summary**: Total deviations, severity counts
- **Deviations by Severity**: Grouped deviations with details
- **Coverage Gaps**: Features/stories missing in either plan
- **Recommendations**: Suggestions for resolving deviations

## Guidelines

### Feature Matching

- **Exact match**: Same feature key (preferred)
- **Fuzzy match**: Similar feature titles (fallback, lower confidence)
- **No match**: Treat as missing feature

### Story Matching

- **Exact match**: Same story key within same feature (preferred)
- **Fuzzy match**: Similar story titles within same feature (fallback)
- **No match**: Treat as missing story

### Severity Assignment

- Use consistent criteria for severity classification
- Consider business impact when assigning severity
- Err on side of higher severity for missing features/stories

### Error Handling

- **Missing files**: Report error with helpful suggestions
- **Invalid format**: Report error and exit
- **Validation failures**: Report validation errors and exit
- **Permission errors**: Report error and exit gracefully

## Context

{ARGS}
