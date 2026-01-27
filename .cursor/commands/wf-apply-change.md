---
name: /wf-apply-change
id: wf-apply-change
category: Workflow
description: Apply an approved OpenSpec change proposal to the codebase, executing openspec-apply workflow.
---

<!-- WORKFLOW:START -->
**Purpose**

Apply an approved OpenSpec change proposal to the codebase. This workflow wraps `/openspec-apply` and guides the AI through implementing the change.

**When to use:** After an OpenSpec change proposal has been validated and approved, when ready to implement the change in the codebase.

**Quick:** `/wf-apply-change <change-id>` or `/wf-apply-change` (interactive selection)

**Guardrails**

- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Refer to `openspec/AGENTS.md` for OpenSpec conventions
- Work through tasks sequentially, keeping edits minimal and focused
- Confirm completion before updating statuses - ensure every task in `tasks.md` is finished

**Workflow Steps**

### Step 1: Change Selection

**If change ID provided in user input:**

1. Parse the change ID from user input (e.g., `add-feature-x`)
2. Resolve to change directory: `openspec/changes/<change-id>/`
3. Verify change directory exists and contains `proposal.md`
4. If not found, search for similar changes and suggest alternatives

**If no change ID provided:**

1. Search for active changes in workspace:
   - Run: `openspec list` to get active changes
   - Display numbered list of changes with:
     - Change ID
     - Status (from proposal.md)
     - Brief description (from proposal.md summary)
     - Last modified date (if available)
2. Prompt user: "Select change to apply (enter number, or provide change-id):"
3. Parse selection and resolve to change directory
4. Verify change directory exists and is readable

**Output:** Change ID, path to change directory

### Step 2: Read Change Artifacts

**2.1: Read Proposal**

1. Read `proposal.md` to understand the change
2. Extract key information:
   - Rationale (from "Why" section)
   - Scope (from "What Changes" section)
   - Affected files/modules (from "Impact" section)
   - Acceptance criteria

**2.2: Read Tasks**

1. Read `tasks.md` to get implementation checklist
2. Extract task list:
   - All tasks with their dependencies
   - Task validation requirements
   - Task execution order

**2.3: Read Design (if exists)**

1. If `design.md` exists:
   - Read `design.md` for architectural decisions
   - Extract design information:
     - Architectural decisions
     - Trade-offs and rationale
     - Integration points
     - Implementation patterns
2. If `design.md` doesn't exist:
   - Skip design reading (not all changes have design docs)

**2.4: Read Spec Deltas**

1. For each spec delta in `specs/<capability>/spec.md`:
   - Read `spec.md`
   - Parse ADDED/MODIFIED/REMOVED sections
2. Extract spec delta information:
   - All ADDED requirements with scenarios
   - All MODIFIED requirements with changes
   - All REMOVED requirements
   - Cross-references to other capabilities

**Output:** Complete change understanding from markdown artifacts

### Step 3: Execute openspec-apply Workflow

Execute the `/openspec-apply` workflow:

1. **Read change artifacts:**
   - Use markdown versions from Step 2
   - Reference proposal, tasks, design, and spec deltas

2. **Work through tasks sequentially:**
   - Follow task order from `tasks.md`
   - Keep edits minimal and focused on requested change
   - Implement requirements as specified

3. **Apply changes:**
   - Implement requirements from spec deltas
   - Follow architectural decisions from design (if available)
   - Handle errors appropriately

4. **Validate implementation:**
   - Verify all requirements are met
   - Run tests and quality checks as specified in tasks

5. **Update task checklist:**
   - Mark each completed task as `- [x]` in `tasks.md`
   - Ensure all tasks reflect reality

**Output:** Implemented change, task checklist updated

### Step 4: Completion and Summary

**4.1: Present Results**

Display summary:

```text
✓ Change applied successfully

Change ID: <change-id>
Location: openspec/changes/<change-id>/

Implementation:
  ✓ All tasks completed
  ✓ All requirements satisfied
  ✓ Code quality checks passed
  ✓ Tests passing

Next Steps:
  1. Review implementation: <files-modified>
  2. Update change status if needed
```

**4.2: Provide Next Actions**

1. **Review implementation:**
   - Suggest reviewing modified files

2. **Update change status:**
   - Inform about updating proposal status if needed
   - Mention syncing with GitHub issue if applicable

**Output:** Completion summary, next action guidance

**Reference**

- OpenSpec apply command: `/openspec-apply`
- OpenSpec list command: `openspec list`
- OpenSpec show command: `openspec show <id> --json --deltas-only`
- OpenSpec conventions: `openspec/AGENTS.md`
- Project rules: `specfact-cli/.cursor/rules/`

**Error Handling**

- **Change not found:** Search and suggest alternatives, ask user to confirm
- **Implementation fails:** Report errors clearly, allow retry, don't proceed until fixed

**Common Patterns**

```bash
# With change ID
/wf-apply-change add-feature-x

# Interactive selection
/wf-apply-change
```

<!-- WORKFLOW:END -->

--- End Command ---
