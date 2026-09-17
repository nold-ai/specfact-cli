## Context

Module discovery intentionally includes project modules. That metadata is useful for diagnostics, but it is not trusted installation input. Both pip's resolver and installer can execute build hooks, so the boundary must be enforced before either subprocess is reached.

## Goals / Non-Goals

**Goals:** verify the selected artifact first, constrain automatic dependencies to index-hosted PEP 508 named requirements, and exclude discovered project metadata from pip subprocess input.

**Non-Goals:** add a direct-URL allowlist, replace pip's resolver, or change module discovery precedence.

## Decisions

1. Parse every automatic-install requirement with `packaging.requirements.Requirement` and reject URLs. Invalid PEP 508 strings thereby reject pip options and local paths.
2. Resolve only the selected marketplace artifact's requirements. Existing discovered modules remain discoverable and available to non-install diagnostics, but their declarations never reach pip during an unrelated install.
3. Verify the extracted artifact before recursive bundle dependency installation or pip resolution. Atomic placement retains its existing verification as defense in depth.

## Rollback

Revert the change as one unit. Partial rollback is unsafe because syntax validation alone does not fix the cross-module trust-boundary violation.
