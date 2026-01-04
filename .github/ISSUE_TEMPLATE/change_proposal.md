---
name: Change Proposal
about: Create a change proposal issue (typically synced from OpenSpec change proposals via `/specfact.sync-backlog`)
title: "[Change] <Brief Description>"
labels: enhancement, change-proposal
assignees: ''

---

<!-- 
This template matches the format used by `/specfact.sync-backlog` when creating GitHub issues from OpenSpec change proposals.
When synced automatically, only the "Why" and "What Changes" sections are populated from the proposal.md file.
Additional sections (Acceptance Criteria, Dependencies, etc.) can be added manually for tracking.
-->

## Why

<!-- Rationale and business value for this change -->
<!-- This section is populated from the `rationale` field in OpenSpec proposal.md -->
<!-- Explain why this change is needed and what problem it solves -->

<!-- Example: -->
<!-- This change addresses the need for unified command chain documentation. Currently, users must navigate 3-5 separate documents to understand a single workflow, which creates friction and reduces adoption. -->

## What Changes

<!-- Description of what will change -->
<!-- This section is populated from the `description` or `what_changes` field in OpenSpec proposal.md -->
<!-- Include high-level implementation approach, affected areas, and key decisions -->

<!-- Example: -->
<!-- This change will create a unified `docs/guides/command-chains.md` reference documenting all 9 command chains (6 mature + 3 emerging) with: -->
<!-- - Overview section explaining what command chains are -->
<!-- - One section per chain with goal, command sequence, decision points, expected outcomes -->
<!-- - Visual flow diagrams (mermaid) for each chain -->
<!-- - "When to use" decision tree -->
<!-- - Cross-references to detailed guides -->

## Acceptance Criteria

<!-- Define what "done" looks like -->
<!-- Use checkboxes for tracking -->

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

<!-- Example: -->
<!-- - [ ] All 9 command chains documented in unified reference -->
<!-- - [ ] Each chain includes: goal, command sequence, decision points, expected outcomes, links to detailed guides -->
<!-- - [ ] Visual flow diagrams (mermaid) created for each chain -->
<!-- - [ ] "When to use" decision tree added -->
<!-- - [ ] Cross-references added from docs/README.md and docs/reference/commands.md -->

## Dependencies

<!-- List any dependencies on other changes, features, or external factors -->

<!-- Example: -->
<!-- - Depends on: #123 (Command reorganization) -->
<!-- - Blocks: #456 (Common tasks index) -->

## Related Issues/PRs

<!-- Link to related issues or pull requests -->

<!-- Example: -->
<!-- - Related to: #789 -->
<!-- - Supersedes: #012 -->

## Additional Context

<!-- Add any other context, examples, or implementation notes -->
<!-- This section is not auto-populated from OpenSpec proposals - add manually as needed -->

<!-- 
Note: When this issue is created via `/specfact.sync-backlog`, the following happens automatically:
- "Why" section populated from proposal.md rationale
- "What Changes" section populated from proposal.md description/what_changes
- OpenSpec change ID added to footer
- Issue number and URL stored in proposal.md source_tracking section
- Labels set based on proposal status
-->

---
*OpenSpec Change Proposal: `change-id-here`*

<!-- 
The footer above is automatically added by `/specfact.sync-backlog`.
Replace `change-id-here` with the actual change ID (e.g., `add-command-chains-reference`).
For manually created issues, you can omit this footer or add it manually.
-->
