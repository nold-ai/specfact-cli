---
name: openspec-workflows
description: Create OpenSpec changes from implementation plans, and validate existing changes before implementation. Use when the user wants to turn a plan document into an OpenSpec change proposal, or validate that a change is safe to implement (breaking changes, dependency analysis).
license: MIT
metadata:
  author: openspec
  version: "1.0"
---

Two workflows for managing OpenSpec changes at the proposal stage.

**Input**: Optionally specify a workflow name (`create` or `validate`) and a target (plan path or change ID). If omitted, ask the user which workflow they need.

## Workflow Selection

Determine which workflow to run:

| User Intent | Workflow | Reference |
|---|---|---|
| Turn a plan into an OpenSpec change | **Create Change from Plan** | `references/create-change-from-plan.md` |
| Validate a change before implementation | **Validate Change** | `references/validate-change.md` |

If the user's intent is unclear, use **AskUserQuestion** to ask which workflow they need.

## Create Change from Plan

Turns an implementation plan document into a fully formed OpenSpec change with proposal, specs, design, and tasks — including GitHub issue creation for public repos.

**When to use**: The user has a plan document (typically in `specfact-cli-internal/docs/internal/implementation/`) and wants to create an OpenSpec change from it.

**Load** `references/create-change-from-plan.md` and follow the full workflow.

**Key steps**:
1. Select and parse the plan document
2. Cross-reference against existing plans and validate targets
3. Resolve any issues interactively
4. Create the OpenSpec change via `opsx:ff` skill
5. Review and improve: enforce TDD-first, add git workflow tasks (branch first, PR last), validate against `openspec/config.yaml`
6. Create GitHub issue (public repos only)

## Validate Change

Performs dry-run simulation to detect breaking changes, analyze dependencies, and verify format compliance before implementation begins.

**When to use**: The user wants to validate that an existing change is safe to implement — check for breaking interface changes, missing dependency updates, and format compliance.

**Load** `references/validate-change.md` and follow the full workflow.

**Key steps**:
1. Select the change (by ID or interactive list)
2. Parse all change artifacts (proposal, tasks, design, spec deltas)
3. Simulate interface changes in a temporary workspace
4. Analyze dependencies and detect breaking changes
5. Present findings and get user decision if breaking changes found
6. Run `openspec validate <change-id> --strict`
7. Create `CHANGE_VALIDATION.md` report

## Guardrails

- Read `openspec/config.yaml` for project context and rules
- Read `CLAUDE.md` for project conventions
- Never modify production code during validation — use temp workspaces
- Never proceed with ambiguities — ask for clarification
- Enforce TDD-first ordering in tasks (per config.yaml)
- Enforce git workflow: branch creation first task, PR creation last task
- Only create GitHub issues in the target repository specified by the plan
