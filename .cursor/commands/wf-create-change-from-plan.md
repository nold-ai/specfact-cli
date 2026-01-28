---
name: /wf-change-from-plan
id: wf-change-from-plan
category: Workflow
description: Create OpenSpec change proposal from a plan document with validation, alignment checks, and optional GitHub issue creation.
---

<!-- WORKFLOW:START -->
**Purpose**

Create an OpenSpec change proposal from a plan document (e.g., documentation improvement plan, implementation plan) with comprehensive validation, alignment checks, and automatic GitHub issue creation for public-facing changes.

**When to use:** Converting strategic plans, documentation plans, or implementation plans into actionable OpenSpec change proposals with proper validation and public issue tracking.

**Quick:** `/wf-change-from-plan <plan-path>` or `/wf-change-from-plan` (interactive selection)

**Guardrails**

- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Never proceed with ambiguities or conflicts - always ask for clarification interactively.
- Do not write any code during the proposal stage. Only create design documents (proposal.md, tasks.md, design.md, and spec deltas).
- Always validate alignment against existing plans and implementation reality before proceeding.
- **CRITICAL**: Only create GitHub issues in the target repository specified by the plan. Never create issues in a different repository than the plan's target.
- For public-facing changes, always sanitize content before creating GitHub issues.
- **CRITICAL Git Workflow**: Always add tasks to create a git branch (feature/bugfix/hotfix based on change-id) BEFORE any code modifications, and create a Pull Request to `dev` branch AFTER all tasks are complete. Never work directly on protected branches (main/dev). Branch naming: `<branch-type>/<change-id>`.

**Workflow Steps**

### Step 1: Plan Selection and Discovery

**If plan path provided in user input:**

1. Parse the plan path from user input (if provided, otherwise ask for clarification)
2. Resolve to absolute path within workspace
3. Verify file exists and is readable
4. If not found, search for similar files in workspace and suggest alternatives

**If no plan path provided:**

1. Search for plan documents in workspace:
   - Search `specfact-cli-internal/docs/internal/brownfield-strategy/` for `*.md` files
   - Search `specfact-cli-internal/docs/internal/implementation/` for `*.md` files
   - Search `specfact-cli/docs/` for plan documents (if accessible)
2. Display numbered list of found plans with:
   - File path (relative to workspace root)
   - First heading or title (if available)
   - Last modified date (if available)
3. Prompt user: "Select plan to use (enter number, or provide path):"
4. Parse selection and resolve to absolute path
5. Verify file exists and is readable

**Output:** Absolute path to selected plan document

### Step 2: Plan Review and Alignment Check

**2.1: Read and Parse Plan Document**

1. Read the selected plan file completely
2. Extract key information:
   - Plan title and purpose (from first H1 heading)
   - **Target repository** (critical for Step 6):
     - Look for `**Repository**:` or `Repository:` in plan header/metadata (usually line 4-5)
     - Extract repository identifier from formats like:
       - `` `nold-ai/specfact-cli` `` → `nold-ai/specfact-cli`
       - Handle markdown: `**Repository**:`nold-ai/specfact-cli`(public)` → extract `nold-ai/specfact-cli`
     - If not found in header, check "Files Summary" section for repository prefixes
     - Store as: `{owner: "nold-ai", name: "specfact-cli", full: "nold-ai/specfact-cli"}` (dictionary/object format)
   - Phases/tasks with descriptions
   - Files to create/modify (note repository prefixes)
   - Dependencies and relationships
   - Success metrics
   - Estimated effort
3. Identify referenced targets (files, directories, repositories mentioned in plan)

**2.2: Cross-Reference Check Against Existing Plans**

1. Search for related plans in `specfact-cli-internal/docs/internal/brownfield-strategy/`:
   - Look for plans with similar scope or overlapping targets
   - Check for conflicting approaches or timelines
   - Identify dependencies or prerequisites
2. Search for related plans in `specfact-cli-internal/docs/internal/implementation/`:
   - Check for implementation plans that might conflict
   - Verify alignment with technical architecture
3. Read related plans and extract:
   - Conflicting information
   - Overlapping scope
   - Dependency relationships
   - Timeline conflicts

**2.3: Target Validation**

For each target mentioned in the plan (files, directories, repositories):

1. **File targets:**
   - Check if file exists (for modifications)
   - Verify file is readable/writable
   - Check if file is in expected location
   - Verify file structure matches plan assumptions

2. **Directory targets:**
   - Check if directory exists (for new files)
   - Verify directory structure matches plan assumptions
   - Check for conflicting files

3. **Repository targets:**
   - Verify repository exists in workspace
   - Check repository structure matches plan assumptions
   - Verify access permissions

4. **Code references:**
   - If plan references code files, verify they exist
   - Check if referenced functions/classes exist
   - Verify code structure matches plan assumptions

**2.4: Alignment Analysis**

Analyze the plan for:

1. **Accuracy:**
   - Are file paths correct?
   - Are repository references accurate?
   - Do referenced files/directories exist?
   - Are command examples valid?

2. **Correctness:**
   - Are technical details accurate?
   - Do implementation approaches align with codebase patterns?
   - Are dependencies correctly identified?
   - Are success metrics measurable?

3. **Ambiguities:**
   - Unclear requirements or tasks
   - Vague acceptance criteria
   - Missing context or assumptions
   - Unspecified edge cases

4. **Conflicts:**
   - Conflicting approaches with other plans
   - Overlapping scope with existing work
   - Timeline conflicts
   - Resource conflicts

5. **Consistency:**
   - Alignment with project rules (from `specfact-cli/.cursor/rules/`)
   - Alignment with OpenSpec conventions
   - Alignment with existing implementation patterns

**2.5: Issue Detection and Interactive Resolution**

**If any issues found (inaccuracies, ambiguities, conflicts):**

1. **Categorize issues:**
   - Critical (must resolve before proceeding)
   - Warning (should resolve but can proceed with confirmation)
   - Info (nice to have, non-blocking)

2. **Present issues to user:**
   - Format: `[CRITICAL/WARNING/INFO] <category>: <description>`
   - Include context (which section, line numbers if available)
   - Suggest resolution options

3. **Interactive resolution:**
   - For each critical issue, prompt: "How should we resolve this? (provide clarification or 'skip' to abort):"
   - For warnings, prompt: "Resolve this warning? (y/n/skip):"
   - Store user responses and update plan understanding

4. **Re-validate after resolution:**
   - Re-run alignment check with updated information
   - If new issues discovered, go back to Step 2.5
   - Continue until all critical issues resolved

**If no issues found:**

- Proceed to Step 3

**Output:** Validated and clarified plan understanding, list of resolved issues

### Step 3: Integrity Re-Check

**3.1: Final Validation**

1. Re-run all checks from Step 2 with updated plan understanding
2. Verify all user clarifications are consistent
3. Check for any new issues introduced by clarifications
4. Verify plan is actionable (all required information present)

**3.2: Misalignment Detection**

**If misalignments still exist:**

1. Present remaining misalignments to user
2. Go back to Step 2.5 (Interactive Resolution)
3. Continue until all misalignments resolved

**If no misalignments:**

- Proceed to Step 4

**Output:** Confirmed plan ready for OpenSpec proposal creation

### Step 4: OpenSpec Change Creation (OPSX)

**4.1: Determine Change Name from Plan**

1. **Extract change name from plan:**
   - Use plan title (first H1 heading) as basis
   - Convert to kebab-case (e.g., "Documentation Improvement Plan" → `documentation-improvement-plan`)
   - Or derive from plan purpose/scope if title is too generic
   - Ensure name is unique (check existing changes with `openspec list`)

2. **Store change name:**
   - Change name in kebab-case format
   - Will be used for `/opsx:ff` command

**4.2: Execute OPSX Fast-Forward Command**

Execute the `/opsx:ff` command to create all artifacts at once:

1. **Call OPSX fast-forward workflow:**

   ```bash
   /opsx:ff <change-name>
   ```

   - Use the plan as the source of requirements
   - Map plan phases/tasks to OpenSpec capabilities
   - The OPSX workflow will:
     - Create change directory: `openspec/changes/<change-name>/`
     - Use `openspec/changes/<change-name>/config.yaml` for project context and rules
     - Generate all required artifacts: proposal.md, specs/, design.md, tasks.md
     - Follow artifact dependencies defined by the schema (spec-driven: proposal → specs → design → tasks)

2. **OPSX workflow will automatically:**
   - Read `openspec/config.yaml` for project context and per-artifact rules
   - Inject context into all artifact creation requests
   - Apply artifact-specific rules (proposal, specs, design, tasks) from config.yaml
   - Create artifacts following the schema's dependency order
   - Use `openspec instructions <artifact-id> --change "<name>" --json` for each artifact

3. **Monitor OPSX execution:**
   - Ensure it follows the OPSX workflow patterns
   - Verify it creates proper OpenSpec structure
   - Check that config.yaml rules are applied (source tracking format, GitHub issue creation policy, etc.)
   - Verify artifacts follow format requirements from config.yaml

4. **Artifact format requirements (from config.yaml):**
   - **proposal.md**: Must include Why, What Changes, Capabilities, Impact sections. Capabilities section is critical - each capability needs a spec file.
   - **specs/<capability>/spec.md**: Use Given/When/Then format for scenarios. Reference existing patterns in openspec/specs/.
   - **design.md**: Document bridge adapter integration, sequence diagrams for multi-repo flows, contract enforcement strategy.
   - **tasks.md**: Break into 2-hour maximum chunks. Include contract decorator tasks, test tasks, quality gate tasks, git workflow tasks (branch creation first, PR creation last).

5. **Note**: After OPSX completes, Step 5 will add git workflow tasks (branch creation and PR creation) and quality standards if not already included.

**4.3: Extract Change ID**

1. Identify the created change ID from OPSX output (or use the change name)
2. Verify change directory exists: `openspec/changes/<change-id>/`
3. Verify artifacts were created: proposal.md, tasks.md, and specs/ directory
4. Store change ID for later steps

**Output:** Change ID, path to change proposal directory

### Step 5: Proposal Review and Improvement

**5.1: Review Against Project Rules and Config**

1. **Read openspec/config.yaml:**
   - Project context (tech stack, constraints, architecture patterns)
   - Per-artifact rules (proposal, specs, design, tasks)
   - Verify artifacts follow config.yaml rules

2. **Read and apply rules from `specfact-cli/.cursor/rules/`:**
   - **spec-fact-cli-rules.mdc**: Problem analysis, centralize logic, testing requirements, contract-first approach
   - **testing-and-build-guide.mdc**: Contract-bound testing, contract-first test commands, coverage requirements
   - **clean-code-principles.mdc**: Code quality standards, refactoring guidelines
   - **python-github-rules.mdc**: Python code standards, GitHub integration patterns
   - **markdown-rules.mdc**: Markdown formatting standards (for documentation changes)

3. **Verify config.yaml rules are applied:**
   - Proposal includes Source Tracking section (if public-facing change)
   - Tasks include GitHub issue creation task (if public-facing change in public repo)
   - Tasks follow 2-hour maximum chunk rule
   - All artifacts reference existing architecture patterns where applicable

**5.2: Update Tasks with Quality Standards and Git Workflow**

**5.2.1: Determine Branch Type from Change ID**

1. **Analyze change ID to determine branch type:**
   - Extract change ID (e.g., `add-command-chains-reference`, `fix-documentation-bug`)
   - Determine branch type based on change ID prefix or content:
     - `add-*`, `create-*`, `implement-*`, `enhance-*` → `feature/`
     - `fix-*`, `correct-*`, `repair-*` → `bugfix/`
     - `update-*`, `modify-*`, `refactor-*` → `feature/` (unless explicitly bugfix)
     - `remove-*`, `delete-*` → `feature/` (unless explicitly bugfix)
     - `hotfix-*`, `urgent-*` → `hotfix/`
     - Default: `feature/` if unclear
   - **If user explicitly requests different branch type:** Use user's preference
   - Format: `<branch-type>/<change-id>` (e.g., `feature/add-command-chains-reference`)

2. **Store branch information:**
   - Branch type: `feature`, `bugfix`, `hotfix`, etc.
   - Branch name: `<branch-type>/<change-id>`
   - Target branch: `dev` (default, unless user specifies otherwise)

**5.2.2: Add Git Branch Creation Task (FIRST TASK)**

**Add as the FIRST task in `tasks.md` (before any code modifications):**

1. **Create git branch task:**
   - Task: "Create git branch `<branch-type>/<change-id>` from `dev` branch"
   - **CRITICAL**: This must be the FIRST task - no code modifications before branch creation
   - **If GitHub issue exists**: Use `gh issue develop` to automatically link branch to issue
   - **If no GitHub issue**: Use standard `git checkout -b` command
   - Steps:

     - [ ] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
     - [ ] 1.1.2 Create branch with Development link to issue (if exists): `gh issue develop <issue-number> --repo <target-owner>/<target-name> --name <branch-type>/<change-id> --checkout`
     - [ ] 1.1.3 Or create branch without issue link: `git checkout -b <branch-type>/<change-id>` (if no issue)
     - [ ] 1.1.4 Verify branch was created: `git branch --show-current`

   - **Validation**: Verify branch exists and is checked out. If issue exists, verify Development link appears on issue page.
   - **Rationale**: Prevents accidental commits to protected branches (main/dev) and ensures proper branch isolation. Using `gh issue develop` automatically creates Development link between branch and issue.

**5.2.3: Update Existing Tasks with Quality Standards**

For each task in `tasks.md` (after branch creation task), ensure it includes:

1. **Testing requirements:**
   - Unit tests for new/modified code
   - Contract tests for new contracts
   - Integration tests for new features
   - E2E tests for user-facing changes

2. **Code quality checks:**
   - Linting: `hatch run format`
   - Type checking: `hatch run type-check`
   - Contract validation: `hatch run contract-test`
   - Test coverage: `hatch run smart-test`

3. **Validation steps:**
   - OpenSpec validation: `openspec validate <change-id> --strict`
   - Build verification
   - Documentation checks

4. **Dependencies:**
   - Required tools/commands
   - Prerequisite changes
   - External dependencies

**5.2.4: Add Pull Request Creation Task (LAST TASK)**

**Add as the LAST task in `tasks.md` (after all implementation tasks are complete):**

1. **Create Pull Request task:**
   - Task: "Create Pull Request from `<branch-type>/<change-id>` to `dev` branch"
   - **CRITICAL**: This must be the LAST task - only after all implementation tasks are complete
   - **Prerequisites**: All previous tasks completed, all tests passing, all validations passing
   - **CRITICAL**: Only create PR if target repository is public-facing (specfact-cli, platform-frontend). Skip for internal repos (specfact-cli-internal).
   - **Tasks** (using hierarchical format):
     - [ ] N.1 Prepare changes for commit
       - [ ] N.1.1 Ensure all changes are committed: `git add .`
       - [ ] N.1.2 Commit with conventional message: `git commit -m "<type>: <brief description>"` (use "feat:", "fix:", "docs:", etc. based on change type)
       - [ ] N.1.3 Push to remote: `git push origin <branch-type>/<change-id>`

     - [ ] N.2 Create PR body from template
       - [ ] N.2.1 Create PR body file in `/tmp` to avoid escaping issues: `PR_BODY_FILE="/tmp/pr-body-<change-id>.md"`
       - [ ] N.2.2 Execute Python script to read template, fill in values, and write to temp file:
         - Set environment variables: `CHANGE_ID="<change-id>" ISSUE_NUMBER="<issue-number>" TARGET_REPO="<target-owner>/<target-name>" SUMMARY="<brief summary>" BRANCH_TYPE="<branch-type>" PR_TEMPLATE_PATH="<absolute-path-to-PR-template>" PR_BODY_FILE="$PR_BODY_FILE"`
         - Run Python script (see Python script below) with these environment variables
         - The script will use full repository path format for issue references (e.g., `nold-ai/specfact-cli#78`) to ensure proper Development linking
       - [ ] N.2.3 Verify PR body file was created: `cat "$PR_BODY_FILE"` (should contain issue reference in format `<target-repo>#<issue-number>`)

     - [ ] N.3 Create Pull Request using gh CLI
       - [ ] N.3.1 Create PR without project flag first: `gh pr create --repo <target-owner>/<target-name> --base dev --head <branch-type>/<change-id> --title "<type>: <brief description>" --body-file "$PR_BODY_FILE"`
       - [ ] N.3.2 Verify PR was created and capture PR number and URL from output
       - [ ] N.3.3 Extract PR number from output (format: "Created pull request #<number>" or extract from URL)
       - [ ] N.3.4 Link PR to project (if target is specfact-cli): `gh project item-add 1 --owner nold-ai --url "https://github.com/nold-ai/specfact-cli/pull/<PR_NUMBER>"` (if this fails, project linking requires project scope: `gh auth refresh -s project`)
       - [ ] N.3.5 Verify/ensure branch and PR are linked to issue (Development section):
         - [ ] N.3.5.1 Verify branch is linked: Branch was created using `gh issue develop <ISSUE_NUMBER>` (Step 1.1.2), which automatically links the branch to the issue
         - [ ] N.3.5.2 Verify PR is linked: PR body contains `Fixes <target-repo>#<ISSUE_NUMBER>` (or `Closes <target-repo>#<ISSUE_NUMBER>`), which should automatically link the PR to the issue
         - [ ] N.3.5.3 **If automatic linking didn't work**: Manually link from the issue's Development section:
           - Open issue page: `https://github.com/<target-owner>/<target-name>/issues/<ISSUE_NUMBER>`
           - In the right sidebar, find the "Development" section
           - Click "Development" and search for the PR (or branch if PR doesn't exist yet)
           - Select the PR/branch to link it to the issue
         - [ ] N.3.5.4 Verify Development link: Check issue page "Development" section - both branch and PR should appear if properly linked
       - [ ] N.3.6 Update project status for issue to "In Progress" (if target is specfact-cli and issue exists):
         - [ ] N.3.6.1 Get issue item ID: `ISSUE_ITEM_ID=$(gh api graphql -f query='{organization(login: "nold-ai") {projectV2(number: 1) {items(first: 20) {nodes {id content {... on Issue {number}}}}}}}' | jq -r '.data.organization.projectV2.items.nodes[] | select(.content.number == <ISSUE_NUMBER>) | .id')`
         - [ ] N.3.6.2 Update status: `gh project item-edit --id "$ISSUE_ITEM_ID" --field-id PVTSSF_lADODWwjB84BKws4zg6iOak --project-id PVT_kwDODWwjB84BKws4 --single-select-option-id 47fc9ee4` (Status field ID: `PVTSSF_lADODWwjB84BKws4zg6iOak`, "In Progress" option ID: `47fc9ee4`, Project ID: `PVT_kwDODWwjB84BKws4`)
       - [ ] N.3.7 Update project status for PR to "In Progress" (if target is specfact-cli):
         - [ ] N.3.7.1 Get PR item ID: `PR_ITEM_ID=$(gh api graphql -f query='{organization(login: "nold-ai") {projectV2(number: 1) {items(first: 20) {nodes {id content {... on PullRequest {number}}}}}}}' | jq -r '.data.organization.projectV2.items.nodes[] | select(.content.number == <PR_NUMBER>) | .id')`
         - [ ] N.3.7.2 Update status: `gh project item-edit --id "$PR_ITEM_ID" --field-id PVTSSF_lADODWwjB84BKws4zg6iOak --project-id PVT_kwDODWwjB84BKws4 --single-select-option-id 47fc9ee4` (Status field ID: `PVTSSF_lADODWwjB84BKws4zg6iOak`, "In Progress" option ID: `47fc9ee4`, Project ID: `PVT_kwDODWwjB84BKws4`)
       - [ ] N.3.8 Verify Development link: PR and branch automatically linked to issue (if issue exists - check issue page "Development" section)
       - [ ] N.3.9 Verify project link: PR appears in project board (<https://github.com/orgs/nold-ai/projects/1>) (if target is specfact-cli)
       - [ ] N.3.10 Cleanup PR body file: `rm /tmp/pr-body-<change-id>.md`

     **Python script for PR body generation** (use in N.2.2):

     ```python
     import os
     import re
     
     change_id = os.environ.get("CHANGE_ID", "<change-id>")
     issue_number = os.environ.get("ISSUE_NUMBER", "")  # Empty string if no issue
     target_repo = os.environ.get("TARGET_REPO", "")  # Format: "nold-ai/specfact-cli" or "nold-ai/platform-frontend"
     summary = os.environ.get("SUMMARY", "<brief summary from proposal>")
     branch_type = os.environ.get("BRANCH_TYPE", "<branch-type>")
     template_path = os.environ.get("PR_TEMPLATE_PATH", "")  # Absolute path to target repo's PR template
     output_file = os.environ.get("PR_BODY_FILE", "/tmp/pr-body-<change-id>.md")
     
     # Read PR template if available
     if template_path and os.path.exists(template_path):
       with open(template_path, 'r', encoding='utf-8') as f:
         pr_body = f.read()
     else:
       # Fallback template structure matching specfact-cli template
       pr_body = """# Description
     
     Please include a summary of the change and which issue is fixed. Include relevant motivation and context.
     
     **Fixes** #(issue)
     
     **New Features** #(issue)
     
     **Contract References**: List any contracts (`@icontract` decorators) that this change affects or implements.
     """
     
     # Fill in issue references using full repository path format (e.g., "nold-ai/specfact-cli#78")
     # This format ensures proper Development linking between PR, branch, and issue
     # Note: "Fixes <repo>#X" creates Development link between PR, branch, and issue
     if issue_number and issue_number.strip() and target_repo:
       # Use full repository path format for Development link: "nold-ai/specfact-cli#78"
       issue_ref = f"{target_repo}#{issue_number}"
       # Always use "Fixes" for Development link, regardless of branch type
       # This ensures the branch and PR show up in the issue's Development section
       pr_body = re.sub(r'\*\*Fixes\*\* #\(issue\)', f'**Fixes** {issue_ref}', pr_body)
       pr_body = re.sub(r'\*\*New Features\*\* #\(issue\)', '**New Features** (none)', pr_body)
     elif issue_number and issue_number.strip():
       # Fallback to simple format if target_repo not provided
       pr_body = re.sub(r'\*\*Fixes\*\* #\(issue\)', f'**Fixes** #{issue_number}', pr_body)
       pr_body = re.sub(r'\*\*New Features\*\* #\(issue\)', '**New Features** (none)', pr_body)
     else:
       pr_body = re.sub(r'\*\*Fixes\*\* #\(issue\)', '**Fixes** (none)', pr_body)
       pr_body = re.sub(r'\*\*New Features\*\* #\(issue\)', '**New Features** (none)', pr_body)
     
     # Add OpenSpec reference and summary
     description_addition = f"\n\nImplements OpenSpec change proposal: `{change_id}`\n\n{summary}\n"
     pr_body = re.sub(r'(# Description\n)', r'\1' + description_addition, pr_body, count=1)
     
     # Write to temp file
     with open(output_file, 'w', encoding='utf-8') as f:
       f.write(pr_body)
     
     print(f"PR body written to {output_file}")
     ```

     **Note**: When generating tasks, replace placeholders with actual values:
     - `<target-owner>/<target-name>` → e.g., `nold-ai/specfact-cli` (for TARGET_REPO)
     - `<change-id>` → actual change ID
     - `<issue-number>` → actual issue number (or empty string if no issue)
     - `<absolute-path-to-PR-template>` → absolute path to `.github/pull_request_template.md` in target repository
     - The Python script should be executed with all environment variables set: `CHANGE_ID="..." ISSUE_NUMBER="..." TARGET_REPO="..." SUMMARY="..." BRANCH_TYPE="..." PR_TEMPLATE_PATH="..." PR_BODY_FILE="$PR_BODY_FILE" python3 << 'PYEOF' ... PYEOF`
     - **CRITICAL**: The `TARGET_REPO` variable ensures issue references use full repository path format (e.g., `nold-ai/specfact-cli#78`) for proper Development linking

   - **Validation**:
     - Verify PR was created and is visible on GitHub
     - If issue exists, verify Development link is present on the issue page (shows linked PR and branch)
     - Verify PR body follows the template structure
   - **Rationale**: Ensures all work is properly reviewed before merging to protected `dev` branch, and properly links PR/branch to issue for tracking
   - **Note**:
     - GitHub automatically creates Development links when PR body contains `Fixes <repo>#<issue-number>` or `Closes <repo>#<issue-number>` (full repository path format)
     - Use full repository path format: `Fixes nold-ai/specfact-cli#78` (not just `Fixes #78`)
     - The Python script automatically uses `TARGET_REPO` to generate the correct format
     - The Development link appears on the issue's "Development" section, showing both the PR and the branch
   - **Target branch**: Always use `dev` as the base branch (default, unless user specifies otherwise)
   - **Template usage**: Always use the repository's PR template (`.github/pull_request_template.md`) if available, with proper content escaping

2. **PR Title Format:**
   - Use conventional commit format: `<type>: <description>`
   - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, etc.
   - Match branch type: `feature/` → `feat:`, `bugfix/` → `fix:`, etc.

3. **PR Body Template Requirements:**
   - **MUST** use the repository's PR template (`.github/pull_request_template.md`) if available
   - **MUST** properly escape special characters (backticks, asterisks, underscores, brackets) in user-provided content
   - **MUST** fill in the template sections:
     - Description: Include OpenSpec change ID and summary
     - Fixes/New Features: Include issue number if GitHub issue was created
     - Contract References: List any contracts affected (if applicable)
     - Type of Change: Mark appropriate checkboxes based on change type
   - **Development Link**:
     - **Automatic linking**:
       - Branch: `gh issue develop <issue-number>` (Step 1.1.2) automatically links the branch to the issue
       - PR: PR body containing `Fixes <repo>#<issue-number>` or `Closes <repo>#<issue-number>` should automatically link the PR to the issue
       - The Python script automatically uses `TARGET_REPO` environment variable to generate the correct format (e.g., `Fixes nold-ai/specfact-cli#78`)
     - **Manual linking (if automatic doesn't work)**:
       - Navigate to the issue page on GitHub (e.g., `https://github.com/<target-owner>/<target-name>/issues/<issue-number>`)
       - In the right sidebar, find the "Development" section
       - Click "Development" and search for the PR (or branch if PR doesn't exist yet)
       - Select the PR/branch to link it to the issue
     - **Important**: You link the PR/branch TO the issue from the issue's Development section, not the other way around
     - **CRITICAL**: Use full repository path format (`nold-ai/specfact-cli#78`) instead of short format (`#78`) to ensure proper Development linking
   - **Project Linking**: If target is `specfact-cli`, create PR first, then link to project separately using `gh project item-add 1 --owner nold-ai --url <PR_URL>` (more reliable than `--project` flag which requires project scope)

**5.3: Update Proposal with Quality Gates and Git Workflow**

Update `proposal.md` to include:

1. **Quality standards section:**
   - Testing requirements
   - Code quality requirements
   - Validation requirements

2. **Git workflow requirements:**
   - Branch creation: Work must be done in feature/bugfix/hotfix branch (not on main/dev)
   - Branch protection: `main` and `dev` branches are protected - no direct commits
   - Pull Request: All changes must be merged via PR to `dev` branch
   - Branch naming: `<branch-type>/<change-id>` format

3. **Acceptance criteria:**
   - Git branch created before any code modifications
   - All tests pass
   - Contracts validated
   - Documentation updated
   - No linting errors
   - Pull Request created and ready for review

**5.4: Validate with OpenSpec**

1. **Format validation (before OpenSpec validation):**
   - Verify `proposal.md` format:
     - Title starts with `# Change:` (not `#` or `# Change:` without space)
     - Has `## Why` section
     - Has `## What Changes` section with bullet list
     - Has `## Impact` section
   - Verify `tasks.md` format:
     - Uses hierarchical numbered format: `## 1.`, `## 2.`, etc.
     - Tasks use format: `- [ ] 1.1 [Description]`
     - Sub-tasks use format: `- [ ] 1.1.1 [Description]` (indented)
   - If format issues found, fix them before proceeding

2. **Check change status:**

   ```bash
   openspec status --change "<change-id>" --json
   ```

   - Verify all required artifacts are complete (status: "done")
   - Check artifact dependencies are satisfied

3. **Run OpenSpec validation:**

   ```bash
   openspec validate <change-id> --strict
   ```

   - **If validation fails:**
     - Read validation errors
     - Fix issues in proposal.md, tasks.md, design.md (if exists), or spec deltas
     - Re-run validation
     - Continue until validation passes

4. **If validation passes:**
   - Proceed to Step 5.5 (Markdown Linting)

**Output:** Validated and improved change proposal, passing OpenSpec validation and format checks

**5.5: Markdown Linting and Formatting**

1. **Identify markdown files in change directory:**
   - Find all `.md` files in `openspec/changes/<change-id>/`
   - Include: `proposal.md`, `tasks.md`, `design.md` (if exists), and all files in `specs/` subdirectories

2. **Run markdownlint with auto-fix:**

   ```bash
   # Get repository root (where .markdownlint.json config is located)
   REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
   CHANGE_DIR="$REPO_ROOT/openspec/changes/<change-id>"
   
   # Change to the change directory
   cd "$CHANGE_DIR"
   
   # Find all markdown files
   MARKDOWN_FILES=$(find . -name "*.md" -type f)
   
   if [ -z "$MARKDOWN_FILES" ]; then
     echo "⚠ No markdown files found in change directory"
     cd "$REPO_ROOT"
     exit 0
   fi
   
   # Run markdownlint with auto-fix if available
   # Use config from repository root if it exists
   CONFIG_FILE="$REPO_ROOT/.markdownlint.json"
   if command -v markdownlint >/dev/null 2>&1; then
     if [ -f "$CONFIG_FILE" ]; then
       # Use repository's markdownlint config
       markdownlint --config "$CONFIG_FILE" --fix $MARKDOWN_FILES 2>&1 || {
         # If --fix fails, run without fix to show errors
         echo "⚠ Some issues couldn't be auto-fixed. Remaining errors:"
         markdownlint --config "$CONFIG_FILE" $MARKDOWN_FILES 2>&1 || {
           echo "❌ Markdown linting errors found. Please fix manually:"
           markdownlint --config "$CONFIG_FILE" $MARKDOWN_FILES
           cd "$REPO_ROOT"
           exit 1
         }
       }
     else
       # Run without config file
       markdownlint --fix $MARKDOWN_FILES 2>&1 || {
         echo "⚠ Some issues couldn't be auto-fixed. Remaining errors:"
         markdownlint $MARKDOWN_FILES 2>&1 || {
           echo "❌ Markdown linting errors found. Please fix manually:"
           markdownlint $MARKDOWN_FILES
           cd "$REPO_ROOT"
           exit 1
         }
       }
     fi
     echo "✓ Markdown linting passed (auto-fixed where possible)"
   else
     echo "⚠ markdownlint not found. Install with: npm install -g markdownlint-cli"
     echo "⚠ Skipping markdown linting. Please run manually before proceeding."
   fi
   
   # Return to original directory
   cd "$REPO_ROOT"
   ```

3. **Verify linting passed:**
   - If markdownlint reports errors that couldn't be auto-fixed:
     - Display the errors clearly
     - Fix issues manually in the affected files
     - Re-run markdownlint until all issues are resolved
   - If markdownlint passes or is not available:
     - Proceed to Step 6

4. **Common markdown linting issues to fix:**
   - MD009: Trailing spaces (remove trailing whitespace)
   - MD012: Multiple consecutive blank lines (reduce to single blank line)
   - MD031: Fenced code blocks not surrounded by blank lines (add blank lines)
   - MD032: Lists not surrounded by blank lines (add blank lines)
   - MD036: Emphasis used instead of heading (use proper heading syntax)
   - MD047: File doesn't end with single newline (add final newline)

**Output:** All markdown files in change directory pass linting checks

### Step 6: GitHub Issue Creation (Target Repository Only)

**6.1: Determine Target Repository and Issue Creation**

1. **Extract target repository from plan:**
   - Check plan document header/metadata for target repository:
     - Look for `**Repository**:` or `Repository:` followed by repository identifier (e.g., `` `nold-ai/specfact-cli` `` or `nold-ai/specfact-cli`)
     - Handle markdown formatting: `**Repository**:`nold-ai/specfact-cli`(public)` → extract `nold-ai/specfact-cli`
     - Look for `**Repository**:` or `Repository:` in plan metadata section (usually near top)
   - Check plan sections for repository references:
     - Look in "Files Summary" section for repository prefixes (e.g., `specfact-cli/docs/...` → `specfact-cli`)
     - Look in "Files to Create/Modify" sections for repository paths
   - If plan explicitly states repository, use that as target
   - **Common formats to detect:**
     - `` `**Repository**: `nold-ai/specfact-cli` (public)` ``
     - `Repository: nold-ai/specfact-cli`
     - `Target Repository: specfact-cli`
     - File paths like `specfact-cli/docs/...` or `platform-frontend/sites/...`

2. **Determine if GitHub issue should be created:**
   - **Extract repository name from full identifier:**
     - If repository identifier is `nold-ai/specfact-cli` → name is `specfact-cli`
     - If repository identifier is `nold-ai/platform-frontend` → name is `platform-frontend`
     - If repository identifier is `nold-ai/specfact-cli-internal` → name is `specfact-cli-internal`
   - **If target repository name is `specfact-cli` (public repo):**
     - Create GitHub issue in `nold-ai/specfact-cli`
     - Proceed to Step 6.2 (Sanitize Content)
   - **If target repository name is `platform-frontend` (public repo):**
     - Create GitHub issue in `nold-ai/platform-frontend` (if repository supports issues)
     - Proceed to Step 6.2 (Sanitize Content)
   - **If target repository name is `specfact-cli-internal` (internal repo):**
     - Skip GitHub issue creation (internal repository)
     - Skip to Step 8 (Completion)
     - Inform user: "Change targets internal repository (specfact-cli-internal). GitHub issue creation skipped."
   - **If target repository not specified or unclear:**
     - Ask user: "Which repository does this change target? (specfact-cli/platform-frontend/specfact-cli-internal/other):"
     - Based on response:
       - If `specfact-cli` or `platform-frontend` → proceed to Step 6.2
       - If `specfact-cli-internal` or `other` → skip GitHub issue creation, proceed to Step 8

3. **Store target repository information:**
   - Repository owner (e.g., `nold-ai`)
   - Repository name (e.g., `specfact-cli`, `platform-frontend`)
   - Repository identifier: `<owner>/<name>` (e.g., `nold-ai/specfact-cli`)

**Output:** Target repository identifier, decision to create issue or skip

**6.2: Sanitize Proposal Content**

**If creating GitHub issue (target is specfact-cli or platform-frontend):**

1. **Read proposal content:**
   - Read `openspec/changes/<change-id>/proposal.md`
   - Extract: rationale (Why), description (What Changes)

2. **Sanitize for public consumption:**
   - **Remove:**
     - Competitive analysis sections
     - Market positioning statements
     - Internal strategy details
     - Implementation file paths (generalize)
     - Effort estimates and timelines
     - Internal decision-making rationale
   - **Preserve:**
     - User-facing value propositions
     - High-level feature descriptions
     - Acceptance criteria (user-facing)
     - External documentation links
     - Public API changes

3. **Create sanitized content:**
   - Format according to GitHub issue template: `specfact-cli/.github/ISSUE_TEMPLATE/change_proposal.md`
   - Follow config.yaml rules for GitHub issue format:
     - Title: `[Change] <Brief Description>`
     - Labels: `enhancement` and `change-proposal`
     - Body structure:
       - `## Why` (sanitized rationale from proposal)
       - `## What Changes` (sanitized description from proposal)
       - `## Acceptance Criteria` (from proposal, user-facing only)
     - Footer: `*OpenSpec Change Proposal:`<change-id>`*`

4. **User review:**
   - Display sanitized content
   - Prompt: "Approve sanitized content for public issue? (y/n/edit):"
   - If `edit`: Allow user to modify, then re-approve
   - If `n`: Skip GitHub issue creation, inform user

**Output:** Sanitized issue content ready for GitHub

### Step 7: Create GitHub Issue via gh CLI

**7.1: Prepare Issue Content**

1. **Create temporary file:**
   - Write sanitized content to `/tmp/github-issue-<change-id>.md`
   - Format according to template structure

2. **Extract issue title:**
   - Use proposal title or first line of "What Changes"
   - Format: `[Change] <Brief Description>`

3. **Determine target repository:**
   - Use target repository from Step 6.1 (stored repository identifier)
   - Format: `<owner>/<name>` (e.g., `nold-ai/specfact-cli` or `nold-ai/platform-frontend`)

**7.2: Create Issue via gh CLI**

1. **Verify gh CLI availability:**
   - Run: `gh --version`
   - If not available, error: "GitHub CLI (gh) not found. Install it or create issue manually."

2. **Create issue in target repository:**

   **For target repository `nold-ai/specfact-cli` (with project linking):**

   ```bash
   # Create issue first (without project flag - more reliable)
   # Follow config.yaml format: title `[Change] <Brief Description>`, labels `enhancement` and `change-proposal`
   ISSUE_OUTPUT=$(gh issue create \
     --repo nold-ai/specfact-cli \
     --title "[Change] <title>" \
     --body-file /tmp/github-issue-<change-id>.md \
     --label "enhancement" \
     --label "change-proposal" 2>&1)
   
   # Extract issue number from output
   # Handle both formats: "https://github.com/.../issues/123" and "Created issue #123"
   ISSUE_NUMBER=$(echo "$ISSUE_OUTPUT" | grep -oP 'issues/\K[0-9]+' || echo "$ISSUE_OUTPUT" | grep -oP '#\K[0-9]+' || echo "$ISSUE_OUTPUT" | grep -oP 'issue #\K[0-9]+')
   ISSUE_URL="https://github.com/nold-ai/specfact-cli/issues/$ISSUE_NUMBER"
   echo "✓ Issue #$ISSUE_NUMBER created: $ISSUE_URL"
   
   # Link issue to project separately (more reliable than --project flag)
   # Note: This requires project scope: gh auth refresh -s project
   gh project item-add 1 \
     --owner nold-ai \
     --url "$ISSUE_URL" 2>&1 || {
     echo "⚠ Failed to link issue to project automatically."
     echo "⚠ This requires project scope. Run interactively: gh auth refresh -s project"
     echo "⚠ Then retry: gh project item-add 1 --owner nold-ai --url $ISSUE_URL"
     echo "⚠ Or link via web interface: $ISSUE_URL"
   }
   ```

   **For other target repositories (no project linking):**

   ```bash
   # Create issue without project linking
   # Follow config.yaml format: title `[Change] <Brief Description>`, labels `enhancement` and `change-proposal`
   ISSUE_OUTPUT=$(gh issue create \
     --repo <target-owner>/<target-name> \
     --title "[Change] <title>" \
     --body-file /tmp/github-issue-<change-id>.md \
     --label "enhancement" \
     --label "change-proposal" 2>&1)
   
   # Extract issue number from output
   ISSUE_NUMBER=$(echo "$ISSUE_OUTPUT" | grep -oP 'issues/\K[0-9]+' || echo "$ISSUE_OUTPUT" | grep -oP '#\K[0-9]+')
   ISSUE_URL="https://github.com/<target-owner>/<target-name>/issues/$ISSUE_NUMBER"
   ```

3. **Capture issue number:**
   - Parse output: `Created issue #<number>` or extract from URL
   - Store issue number and URL
   - Display: `✓ Issue #<number> created: <url>`

**7.3: Project Linking (Fallback for specfact-cli)**

**If target repository is `nold-ai/specfact-cli`:**

1. **Verify if issue is already linked to project:**

   ```bash
   # Check if issue is linked to project (requires project scope)
   PROJECT_LINKED=$(gh issue view "$ISSUE_NUMBER" --repo nold-ai/specfact-cli --json projectCards --jq '.projectCards | length' 2>/dev/null || echo "0")
   ```

2. **If not linked, attempt to link via `gh project item-add`:**

   ```bash
   if [ "$PROJECT_LINKED" -eq "0" ]; then
     echo "Attempting to link issue #$ISSUE_NUMBER to project..."
     # Try to add issue to project using project number
     gh project item-add 1 \
       --owner nold-ai \
       --url "$ISSUE_URL" 2>&1 || {
     echo "⚠ Failed to link issue to project automatically."
     echo "⚠ This requires project scope. Run interactively: gh auth refresh -s project"
     echo "⚠ Then retry: gh project item-add 1 --owner nold-ai --url $ISSUE_URL"
     echo "⚠ Or link via web interface: $ISSUE_URL"
     }
   else
     echo "✓ Issue #$ISSUE_NUMBER already linked to project"
   fi
   ```

3. **Verify project link:**

   ```bash
   # Re-check project link status
   PROJECT_LINKED=$(gh issue view "$ISSUE_NUMBER" --repo nold-ai/specfact-cli --json projectCards --jq '.projectCards | length' 2>/dev/null || echo "0")
   if [ "$PROJECT_LINKED" -gt "0" ]; then
     echo "✓ Issue #$ISSUE_NUMBER successfully linked to project: https://github.com/orgs/nold-ai/projects/1"
   else
     echo "⚠ Issue #$ISSUE_NUMBER not linked to project. Manual linking may be required."
   fi
   ```

**If target repository is NOT specfact-cli:**

- Project linking is skipped (project is specific to specfact-cli)
- Inform user: "Issue created in <target-repo>. Project linking skipped (project is specfact-cli-specific)."

**7.4: Update OpenSpec Source Tracking**

1. **Read proposal.md:**
   - Read `openspec/changes/<change-id>/proposal.md`

2. **Add source tracking section:**
   - If section doesn't exist, add: `## Source Tracking`
   - Add entry with target repository:

     ```markdown
     ## Source Tracking

     - **GitHub Issue**: #<issue-number>
     - **Issue URL**: <https://github.com/<target-owner>/<target-name>/issues/<issue-number>>
     - **Repository**: <target-owner>/<target-name>
     - **Last Synced Status**: proposed
     ```

   **Example for specfact-cli:**

   ```markdown
   ## Source Tracking

   - **GitHub Issue**: #123
   - **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/123>
   - **Repository**: nold-ai/specfact-cli
   - **Last Synced Status**: proposed
   ```

   **Example for platform-frontend:**

   ```markdown
   ## Source Tracking

   - **GitHub Issue**: #456
   - **Issue URL**: <https://github.com/nold-ai/platform-frontend/issues/456>
   - **Repository**: nold-ai/platform-frontend
   - **Last Synced Status**: proposed
   ```

3. **Save proposal.md:**
   - Write updated content back to file

**7.5: Cleanup**

1. Remove temporary file: `/tmp/github-issue-<change-id>.md`

**Output:** GitHub issue created in target repository, linked to project (if specfact-cli), source tracking updated

### Step 8: Completion and Summary

**8.1: Present Results**

Display summary:

```text
✓ Change proposal created successfully

Change ID: <change-id>
Location: openspec/changes/<change-id>/

Validation:
  ✓ OpenSpec validation passed
  ✓ Markdown linting passed (auto-fixed where possible)
  ✓ Project rules applied
  ✓ Quality standards integrated
  ✓ Git workflow tasks added (branch creation + PR creation)

GitHub Issue (if target repository supports issues):
  ✓ Issue #<number> created in <target-repo>: <url>
  ✓ Linked to project (specfact-cli only): <https://github.com/orgs/nold-ai/projects/1>
    (If linking failed, run: gh auth refresh -s read:project,write:project and retry)
  ✓ Source tracking updated in proposal.md

Next Steps:
  1. Review proposal: openspec/changes/<change-id>/proposal.md
  2. Review tasks: openspec/changes/<change-id>/tasks.md
  3. Verify git workflow tasks are included:
     - First task: Create branch `<branch-type>/<change-id>`
     - Last task: Create PR to `dev` branch
  4. Apply change when ready: /opsx:apply <change-id> (or /openspec-apply <change-id> for legacy)
```

**8.2: Provide Next Actions**

1. **Review proposal:**
   - Suggest reviewing proposal.md, tasks.md, design.md (if exists)
   - Suggest reviewing spec deltas

2. **Apply change:**
   - Inform about `/openspec-apply` command
   - Remind about approval workflow

3. **Update GitHub issue:**
   - Inform about updating issue as work progresses
   - Mention `/specfact.sync-backlog` for syncing updates

**Output:** Completion summary, next action guidance

**Reference**

- OPSX commands: `/opsx:new`, `/opsx:ff`, `/opsx:continue`, `/opsx:apply`, `/opsx:verify`, `/opsx:archive`
- OpenSpec config: `openspec/config.yaml` (project context and per-artifact rules)
- Legacy commands: `/openspec-proposal` (use `/opsx:ff` instead), `/openspec-apply` (use `/opsx:apply` instead)
- Sync backlog command: `/specfact.sync-backlog`
- Project rules: `specfact-cli/.cursor/rules/`
- GitHub issue template: `specfact-cli/.github/ISSUE_TEMPLATE/change_proposal.md`
- GitHub project: <https://github.com/orgs/nold-ai/projects/1>

**Error Handling**

- **Plan not found:** Search and suggest alternatives, ask user to confirm
- **Validation failures:** Present errors clearly, allow interactive resolution
- **OpenSpec validation fails:** Fix issues and re-validate, don't proceed until passing
- **GitHub CLI not available:** Inform user, provide manual creation instructions
- **Issue creation fails:** Log error, allow retry, don't fail entire workflow
- **Project linking fails:** Log warning, continue (non-critical)

**Common Patterns**

```bash
# With plan path
/wf-change-from-plan docs/plans/documentation-improvement-plan.md

# Interactive selection
/wf-change-from-plan

# Change targeting specfact-cli (will create GitHub issue in specfact-cli)
/wf-change-from-plan docs/plans/documentation-improvement-plan.md

# Change targeting platform-frontend (will create GitHub issue in platform-frontend)
/wf-change-from-plan docs/plans/platform-frontend-messaging-plan.md

# Change targeting specfact-cli-internal (no GitHub issue - internal repo)
/wf-change-from-plan docs/internal/implementation/internal-plan.md
```

<!-- WORKFLOW:END -->
