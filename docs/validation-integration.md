# Validation Integration with Change Proposals

This document describes how SpecFact validation integrates with OpenSpec change proposals to validate against proposed specifications.

## Overview

The validation integration enables SpecFact to:

1. **Load active change proposals** from OpenSpec repositories
2. **Merge current Spec-Kit specs** with proposed OpenSpec changes
3. **Validate against merged specs** (current + proposed)
4. **Update validation status** in change proposals
5. **Report validation results** to backlog tools (GitHub Issues)

This allows teams to validate code against proposed changes before they are applied, ensuring that implementations align with planned specifications.

## How It Works

### 1. Change Proposal Loading

When `specfact validate` is executed in a repository with OpenSpec:

1. The system detects the OpenSpec repository (checks for `openspec/` directory or `bridge_config.external_base_path`)
2. Loads active change proposals (status: `"proposed"` or `"in-progress"`)
3. Extracts associated spec deltas from change proposals
4. If OpenSpec is not found, validation falls back to Spec-Kit only

**Example:**

```python
from specfact_cli.validators.change_proposal_integration import load_active_change_proposals

# Load active proposals
active_tracking = load_active_change_proposals(repo_path, bridge_config)

if active_tracking:
    # Process active proposals
    for change_name, proposal in active_tracking.proposals.items():
        print(f"Active proposal: {change_name} - {proposal.status}")
```

### 2. Spec Merging

Current Spec-Kit specs are merged with proposed OpenSpec changes:

- **ADDED requirements**: Included in validation set
- **MODIFIED requirements**: Replace existing with proposed version
- **REMOVED requirements**: Excluded from validation set

**Example:**

```python
from specfact_cli.validators.change_proposal_integration import merge_specs_with_change_proposals

# Current specs from Spec-Kit
current_specs = {
    "feature-1": {"key": "feature-1", "title": "Feature 1"},
}

# Merge with proposed changes
merged_specs = merge_specs_with_change_proposals(current_specs, active_tracking)

# merged_specs now includes:
# - feature-1 (current)
# - feature-2 (ADDED from proposal)
# - feature-3 (MODIFIED from proposal)
# - feature-4 (REMOVED, excluded)
```

**Conflict Detection:**

If the same requirement is modified in multiple active proposals, a `ValueError` is raised with details about the conflict:

```python
try:
    merged_specs = merge_specs_with_change_proposals(current_specs, active_tracking)
except ValueError as e:
    print(f"Spec merging conflict: {e}")
    # Handle conflict (e.g., prompt user to resolve)
```

### 3. Validation Status Updates

After validation completes, the system updates validation status in change proposals:

- `validation_status`: `"passed"`, `"failed"`, or `"pending"`
- `validation_results`: Detailed validation output (contracts validated, deviations, etc.)

**Example:**

```python
from specfact_cli.validators.change_proposal_integration import update_validation_status

# Validation results
validation_results = {
    "feature-1": {
        "success": True,
        "contracts_validated": 5,
        "deviations": [],
    },
    "feature-2": {
        "success": False,
        "error": "Contract violation detected",
    },
}

# Update validation status
update_validation_status(active_tracking, validation_results, repo_path, bridge_config)

# Status is saved back to OpenSpec automatically
```

### 4. Validation Result Reporting

Validation results are reported to backlog tools (GitHub Issues) if configured:

- Adds comment to GitHub issue with validation status
- Updates issue labels based on validation status (`validation-failed` for failures)
- Handles missing GitHub adapter gracefully (skips reporting)

**Example:**

```python
from specfact_cli.validators.change_proposal_integration import report_validation_results_to_backlog

# Report results to GitHub
report_validation_results_to_backlog(active_tracking, validation_results, bridge_config)

# GitHub issue will have:
# - Comment with validation results
# - Updated labels (validation-failed if any failures)
```

## Cross-Repository Support

The validation integration supports cross-repository scenarios using `bridge_config.external_base_path`:

```yaml
# bridge_config.yaml
adapter: github
external_base_path: ../openspec-repo  # External OpenSpec repository
```

When `external_base_path` is set:

- OpenSpec repository is loaded from the external path
- All path operations respect the external base path
- Change proposals are loaded from the external repository

## Usage Examples

### Basic Validation with Change Proposals

```bash
# In repository with OpenSpec
specfact validate sidecar run my-bundle /path/to/repo

# System automatically:
# 1. Detects OpenSpec repository
# 2. Loads active change proposals
# 3. Merges specs (current + proposed)
# 4. Validates against merged specs
# 5. Updates validation status
# 6. Reports results to GitHub (if configured)
```

### Validation with External OpenSpec Repository

```bash
# With bridge_config.yaml specifying external_base_path
specfact validate sidecar run my-bundle /path/to/repo --bridge-config bridge_config.yaml

# System loads OpenSpec from external repository
```

### Programmatic Usage

```python
from pathlib import Path
from specfact_cli.validators.change_proposal_integration import (
    load_active_change_proposals,
    merge_specs_with_change_proposals,
    update_validation_status,
    report_validation_results_to_backlog,
)

repo_path = Path("/path/to/repo")

# Load active proposals
active_tracking = load_active_change_proposals(repo_path)

if active_tracking:
    # Merge specs
    current_specs = load_current_specs()  # Your function
    merged_specs = merge_specs_with_change_proposals(current_specs, active_tracking)
    
    # Validate
    validation_results = run_validation(merged_specs)  # Your function
    
    # Update status
    update_validation_status(active_tracking, validation_results, repo_path)
    
    # Report to backlog
    report_validation_results_to_backlog(active_tracking, validation_results)
```

## Error Handling

The validation integration handles errors gracefully:

- **Missing OpenSpec**: Falls back to Spec-Kit only validation
- **Missing proposals**: Continues with current specs only
- **Spec conflicts**: Raises `ValueError` with conflict details
- **Validation failures**: Marks proposals as `"failed"` and stores error details
- **GitHub reporting failures**: Logs but doesn't fail (non-critical)

## Integration Points

The validation integration integrates with:

- **OpenSpec adapter**: Loads change proposals and spec deltas
- **Spec-Kit adapter**: Loads current specifications
- **SpecFact validation**: Validates against merged specs
- **Backlog adapters**: Reports results (GitHub and ADO available, future: Jira, Linear)

## Future Enhancements

Future backlog adapters (Jira, Linear) will follow the same reporting pattern. Azure DevOps (ADO) is now available and follows this pattern.

- Tool-agnostic status mapping
- Tool-agnostic metadata extraction
- Reusable conflict resolution
- Consistent reporting interface

See `docs/adapters/backlog-adapter-patterns.md` for details on implementing future backlog adapters.
