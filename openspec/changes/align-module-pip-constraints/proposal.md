# Align module dependency resolution with installation constraints

## Why

The pip-editable launcher resolves a newer Typer through pip-compile, then fails installation because the invoking workflow pins the reviewed version through `PIP_CONSTRAINT`. The same caller policy must apply to both phases.

## What changes

- Pass pip's constraint file arguments into pip-compile when the caller asks pip to apply those constraints.
- Preserve dependency conflict errors, module signature and cutoff checks, and the existing installer.
- Verify the repair using the immutable runtime fixture and the normal six-launcher workflow.

## Dependencies

Core #797 supplies the audit base. Core #798 is a blocker for modules #513 and PR #524.

<!-- source_repo: nold-ai/specfact-cli -->
- GitHub Issue: #798
- Parent: #375
