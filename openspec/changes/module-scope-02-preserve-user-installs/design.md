## Overview

Preserve the existing deterministic discovery order while correcting the meaning of a shadowed user module. A project copy is effective only for the current repository; the user copy is neither stale nor invalid by default and remains the effective installation elsewhere.

## Decisions

- Keep all discovery roots, precedence, deduplication, and shadowed-entry reporting unchanged.
- Keep the discovery signal user-visible, but describe it as workspace-local precedence and explicitly state that no action is required.
- Replace the doctor recovery command with explanatory shadowing guidance. `module list --show-origin` remains the diagnostic path for inspecting exact sources.
- Do not weaken or remove explicit `specfact module uninstall --scope user`; this defect concerns automatic/routine advice, not intentional lifecycle commands.
- Test both message producers directly so future wording changes cannot reintroduce the destructive recommendation.

## Risks

- Users with a genuinely unwanted duplicate no longer receive a one-line delete command. Mitigation: diagnostics still show both origins and explicit uninstall remains available in lifecycle documentation.
- Warning language could become noisy despite being safe. Mitigation: existing once-per-process deduplication remains unchanged.
- Only one repository could merge, temporarily leaving inconsistent guidance. Mitigation: paired issues and PRs are cross-linked and independently safe to merge.

## Rollback

Revert the diagnostic text and tests. No persisted module state or installation files are changed by this patch.
