---
layout: default
title: Troubleshooting
permalink: /troubleshooting/
---

# Troubleshooting

Common issues and solutions for SpecFact CLI.

## Installation Issues

### Command Not Found

**Issue**: `specfact: command not found`

**Solutions**:

1. **Check installation**:

   ```bash
   pip show specfact-cli
   ```

2. **Reinstall**:

   ```bash
   pip install --upgrade specfact-cli
   ```

## Plan Select Command is Slow

**Symptom**: `specfact plan select` takes a long time (5+ seconds) to list plans.

**Cause**: Plan bundles may be missing summary metadata (older schema version 1.0).

**Solution**:

```bash
# Upgrade all plan bundles to latest schema (adds summary metadata)
specfact plan upgrade --all

# Verify upgrade worked
specfact plan select --last 5
```

**Performance Improvement**: After upgrade, `plan select` is 44% faster (3.6s vs 6.5s) and scales better with large plan bundles.

1. **Use uvx** (no installation needed):

   ```bash
   uvx specfact-cli@latest --help
   ```

### Permission Denied

**Issue**: `Permission denied` when running commands

**Solutions**:

1. **Use user install**:

   ```bash
   pip install --user specfact-cli
   ```

2. **Check PATH**:

   ```bash
   echo $PATH
   # Should include ~/.local/bin
   ```

3. **Add to PATH**:

   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

---

## Import Issues

### Spec-Kit Not Detected

**Issue**: `No Spec-Kit project found` when running `import from-bridge --adapter speckit`

**Solutions**:

1. **Check directory structure**:

   ```bash
   ls -la .specify/
   ls -la specs/
   ```

2. **Verify Spec-Kit format**:

   - Should have `.specify/` directory
   - Should have `specs/` directory with feature folders
   - Should have `specs/[###-feature-name]/spec.md` files

3. **Use explicit path**:

   ```bash
   specfact import from-bridge --adapter speckit --repo /path/to/speckit-project
   ```

### Code Analysis Fails (Brownfield) ⭐

**Issue**: `Analysis failed` or `No features detected` when analyzing legacy code

**Solutions**:

1. **Check repository path**:

   ```bash
   specfact import from-code legacy-api --repo . --verbose
   ```

2. **Lower confidence threshold** (for legacy code with less structure):

   ```bash
   specfact import from-code legacy-api --repo . --confidence 0.3
   ```

3. **Check file structure**:

   ```bash
   find . -name "*.py" -type f | head -10
   ```

4. **Use CoPilot mode** (recommended for brownfield - better semantic understanding):

   ```bash
   specfact --mode copilot import from-code legacy-api --repo . --confidence 0.7
   ```

5. **For legacy codebases**, start with minimal confidence and review extracted features:

   ```bash
   specfact import from-code legacy-api --repo . --confidence 0.2
   ```

---

## Sync Issues

### Watch Mode Not Starting

**Issue**: Watch mode exits immediately or doesn't detect changes

**Solutions**:

1. **Check repository path**:

   ```bash
   specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --watch --interval 5 --verbose
   ```

2. **Verify directory exists**:

   ```bash
   ls -la .specify/
   ls -la .specfact/
   ```

3. **Check permissions**:

   ```bash
   ls -la .specfact/projects/
   ```

4. **Try one-time sync first**:

   ```bash
   specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional
   ```

### Bidirectional Sync Conflicts

**Issue**: Conflicts during bidirectional sync

**Solutions**:

1. **Check conflict resolution**:

   - SpecFact takes priority by default
   - Manual resolution may be needed

2. **Review changes**:

   ```bash
   git status
   git diff
   ```

3. **Use one-way sync**:

   ```bash
   # Spec-Kit → SpecFact only
   specfact sync bridge --adapter speckit --bundle <bundle-name> --repo .

   # SpecFact → Spec-Kit only (manual)
   # Edit Spec-Kit files manually
   ```

---

## Enforcement Issues

### Enforcement Not Working

**Issue**: Violations not being blocked or warned

**Solutions**:

1. **Check enforcement configuration** (use CLI commands):

   ```bash
   specfact enforce show-config
   ```

2. **Verify enforcement mode**:

   ```bash
   specfact enforce stage --preset balanced
   ```

3. **Run validation**:

   ```bash
   specfact repro --verbose
   ```

4. **Check severity levels**:

   - HIGH → BLOCK (in balanced/strict mode)
   - MEDIUM → WARN (in balanced/strict mode)
   - LOW → LOG (in all modes)

### False Positives

**Issue**: Valid code being flagged as violations

**Solutions**:

1. **Review violation details**:

   ```bash
   specfact repro --verbose
   ```

2. **Adjust confidence threshold**:

   ```bash
   specfact import from-code legacy-api --repo . --confidence 0.7
   ```

3. **Check enforcement rules** (use CLI commands):

   ```bash
   specfact enforce show-config
   ```

4. **Use minimal mode** (observe only):

   ```bash
   specfact enforce stage --preset minimal
   ```

---

## Constitution Issues

### Constitution Missing or Minimal

**Issue**: `Constitution required` or `Constitution is minimal` when running `sync bridge --adapter speckit`

**Solutions**:

1. **Auto-generate bootstrap constitution** (recommended for brownfield):

   ```bash
   specfact sdd constitution bootstrap --repo .
   ```

   This analyzes your repository (README.md, pyproject.toml, .cursor/rules/, docs/rules/) and generates a bootstrap constitution.

2. **Enrich existing minimal constitution**:

   ```bash
   specfact sdd constitution enrich --repo .
   ```

   This fills placeholders in an existing constitution with repository context.

3. **Validate constitution completeness**:

   ```bash
   specfact sdd constitution validate
   ```

   This checks if the constitution is complete and ready for use.

4. **Manual creation** (for greenfield):

   - Run `/speckit.constitution` command in your AI assistant
   - Fill in the constitution template manually

**When to use each option**:

- **Bootstrap** (brownfield): Use when you want to extract principles from existing codebase
- **Enrich** (existing constitution): Use when you have a minimal constitution with placeholders
- **Manual** (greenfield): Use when starting a new project and want full control

### Constitution Validation Fails

**Issue**: `specfact sdd constitution validate` reports issues

**Solutions**:

1. **Check for placeholders**:

   ```bash
   grep -r "\[.*\]" .specify/memory/constitution.md
   ```

2. **Run enrichment**:

   ```bash
   specfact sdd constitution enrich --repo .
   ```

3. **Review validation output**:

   ```bash
   specfact sdd constitution validate --constitution .specify/memory/constitution.md
   ```

   The output will list specific issues (missing sections, placeholders, etc.).

4. **Fix issues manually** or re-run bootstrap:

   ```bash
   specfact sdd constitution bootstrap --repo . --overwrite
   ```

---

## Plan Comparison Issues

### Plans Not Found

**Issue**: `Plan not found` when running `plan compare`

**Solutions**:

1. **Check plan locations**:

   ```bash
   ls -la .specfact/projects/
   ls -la .specfact/projects/<bundle-name>/reports/brownfield/
   ```

2. **Use explicit paths** (bundle directory paths):

   ```bash
   specfact plan compare \
     --manual .specfact/projects/manual-plan \
     --auto .specfact/projects/auto-derived
   ```

3. **Generate auto-derived plan first**:

   ```bash
   specfact import from-code legacy-api --repo .
   ```

### No Deviations Found (Expected Some)

**Issue**: Comparison shows no deviations but you expect some

**Solutions**:

1. **Check feature key normalization**:

   - Different key formats may normalize to the same key
   - Check `reference/feature-keys.md` for details

2. **Verify plan contents** (use CLI commands):

   ```bash
   specfact plan review <bundle-name>
   ```

3. **Use verbose mode**:

   ```bash
   specfact plan compare --bundle legacy-api --verbose
   ```

---

## IDE Integration Issues

### Slash Commands Not Working

**Issue**: Slash commands not recognized in IDE

**Solutions**:

1. **Reinitialize IDE integration**:

```bash
   specfact init ide --ide cursor --force
```

2. **Check command files**:

   ```bash
   ls -la .cursor/commands/specfact-*.md
   ```

3. **Restart IDE**: Some IDEs require restart to discover new commands

4. **Check IDE settings**:

   - VS Code: Check `.vscode/settings.json`
   - Cursor: Check `.cursor/settings.json`

### Command Files Not Created

**Issue**: Command files not created after `specfact init`

**Solutions**:

1. **Check permissions**:

   ```bash
   ls -la .cursor/commands/
   ```

2. **Use force flag**:

```bash
   specfact init ide --ide cursor --force
```

3. **Check IDE type**:

```bash
   specfact init ide --ide cursor  # For Cursor
   specfact init ide --ide vscode  # For VS Code
```

---

## Mode Detection Issues

### Wrong Mode Detected

**Issue**: CI/CD mode when CoPilot should be detected (or vice versa)

**Solutions**:

1. **Use explicit mode**:

   ```bash
   specfact --mode copilot import from-code my-project --repo .
   ```

2. **Check environment variables**:

   ```bash
   echo $COPILOT_API_URL
   echo $VSCODE_PID
   ```

3. **Set mode explicitly**:

   ```bash
   export SPECFACT_MODE=copilot
   specfact import from-code legacy-api --repo .
   ```

4. **See [Operational Modes](../reference/modes.md)** for details

---

## Performance Issues

### Slow Analysis

**Issue**: Code analysis takes too long

**Solutions**:

1. **Use CI/CD mode** (faster):

   ```bash
   specfact --mode cicd import from-code my-project --repo .
   ```

2. **Increase confidence threshold** (fewer features):

   ```bash
   specfact import from-code legacy-api --repo . --confidence 0.8
   ```

3. **Exclude directories**:

   ```bash
   # Use .gitignore or exclude patterns
   specfact import from-code legacy-api --repo . --exclude "tests/"
   ```

### Watch Mode High CPU

**Issue**: Watch mode uses too much CPU

**Solutions**:

1. **Increase interval**:

   ```bash
   specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --watch --interval 10
   ```

2. **Use one-time sync**:

   ```bash
   specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional
   ```

3. **Check file system events**:

   - Too many files being watched
   - Consider excluding directories

---

## Terminal Output Issues

SpecFact CLI **automatically detects terminal capabilities** and adjusts output formatting for optimal user experience across different environments. No manual configuration required - the CLI adapts to your terminal environment.

### How Terminal Auto-Detection Works

The CLI automatically detects terminal capabilities in this order:

1. **Test Mode Detection**:
   - `TEST_MODE=true` or `PYTEST_CURRENT_TEST` → **MINIMAL** mode

2. **CI/CD Detection**:
   - `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `CIRCLECI`, `TRAVIS`, `JENKINS_URL`, `BUILDKITE` → **BASIC** mode

3. **Color Support Detection**:
   - `NO_COLOR` → Disables colors (respects [NO_COLOR standard](https://no-color.org/))
   - `FORCE_COLOR=1` → Forces colors
   - `TERM` and `COLORTERM` environment variables → Additional hints

4. **Terminal Type Detection**:
   - TTY detection (`sys.stdout.isatty()`) → Interactive vs non-interactive
   - Interactive TTY with animations → **GRAPHICAL** mode
   - Non-interactive → **BASIC** mode

5. **Default Fallback**:
   - If uncertain → **BASIC** mode (safe, readable output)

### Terminal Modes

The CLI supports three terminal modes (auto-selected based on detection):

- **GRAPHICAL** - Full Rich features (colors, animations, progress bars) for interactive terminals
- **BASIC** - Plain text, no animations, simple progress updates for CI/CD and embedded terminals
- **MINIMAL** - Minimal output for test mode

### Environment Variables (Optional Overrides)

You can override auto-detection using standard environment variables:

- **`NO_COLOR`** - Disables all colors (respects [NO_COLOR standard](https://no-color.org/))
- **`FORCE_COLOR=1`** - Forces color output even in non-interactive terminals
- **`CI=true`** - Explicitly enables basic mode (no animations, plain text)
- **`TEST_MODE=true`** - Enables minimal mode for testing

### Examples

```bash
# Auto-detection (default behavior)
specfact import from-code my-bundle
# → Automatically detects terminal and uses appropriate mode

# Manual override: Disable colors
NO_COLOR=1 specfact import from-code my-bundle

# Manual override: Force colors in CI/CD
FORCE_COLOR=1 specfact sync bridge

# Manual override: Explicit CI/CD mode
CI=true specfact import from-code my-bundle
```

### No Progress Visible in Embedded Terminals

**Issue**: No progress indicators visible when running commands in Cursor, VS Code, or other embedded terminals.

**Cause**: Embedded terminals are non-interactive and may not support Rich animations.

**Solution**: The CLI automatically detects embedded terminals and switches to basic mode with plain text progress updates. If you still don't see progress:

1. **Verify auto-detection is working**:

   ```bash
   # Check terminal mode (should show BASIC in embedded terminals)
   python -c "from specfact_cli.runtime import get_terminal_mode; print(get_terminal_mode())"
   ```

2. **Check environment variables**:

   ```bash
   # Ensure NO_COLOR is not set (unless you want plain text)
   unset NO_COLOR
   ```

3. **Verify terminal supports stdout**:
   - Embedded terminals should support stdout (not stderr-only)
   - Progress updates are throttled - wait a few seconds for updates

4. **Manual override** (if needed):

   ```bash
   # Force basic mode
   CI=true specfact import from-code my-bundle
   ```

### Colors Not Working in CI/CD

**Issue**: No colors in CI/CD pipeline output.

**Cause**: CI/CD environments are automatically detected and use basic mode (no colors) for better log readability.

**Solution**: This is expected behavior. CI/CD logs are more readable without colors. To force colors:

```bash
FORCE_COLOR=1 specfact import from-code my-bundle
```

---

## Azure DevOps Issues

### Azure DevOps Token Required

**Issue**: "Azure DevOps token required" error when running `specfact backlog refine ado` or `specfact backlog map-fields`.

**Solutions**:

1. **Use stored token** (recommended):

   ```bash
   specfact backlog auth azure-devops
   # Or use PAT token for longer expiration:
   specfact backlog auth azure-devops --pat your_pat_token
   ```

2. **Use explicit token**:

   ```bash
   specfact backlog refine ado --ado-org myorg --ado-project myproject --ado-token your_token
   ```

3. **Set environment variable**:

   ```bash
   export AZURE_DEVOPS_TOKEN=your_token
   specfact backlog refine ado --ado-org myorg --ado-project myproject
   ```

**Token Resolution Priority**:

The command automatically uses tokens in this order:

1. Explicit `--ado-token` parameter
2. `AZURE_DEVOPS_TOKEN` environment variable
3. Stored token via `specfact backlog auth azure-devops`
4. Expired stored token (shows warning with options)

### OAuth Token Expired

**Issue**: "Stored OAuth token expired" warning when using ADO commands.

**Cause**: OAuth tokens expire after approximately 1 hour.

**Solutions**:

1. **Use PAT token** (recommended for automation, up to 1 year expiration):

   ```bash
   specfact backlog auth azure-devops --pat your_pat_token
   ```

2. **Re-authenticate**:

   ```bash
   specfact backlog auth azure-devops
   ```

3. **Use explicit token**:

   ```bash
   specfact backlog refine ado --ado-org myorg --ado-project myproject --ado-token your_token
   ```

### Fields Not Extracted from ADO Work Items

**Issue**: Fields like acceptance criteria or assignee are not being extracted from ADO work items.

**Solutions**:

1. **Check field names**: ADO field names are case-sensitive and must match exactly:
   - Use `specfact backlog map-fields` to discover exact field names in your project
   - Common fields: `Microsoft.VSTS.Common.AcceptanceCriteria` (preferred) or `System.AcceptanceCriteria`

2. **Verify custom mapping**: Check if custom mapping file exists and is correct:

   ```bash
   cat .specfact/templates/backlog/field_mappings/ado_custom.yaml
   ```

3. **Reset to defaults**: If mappings are corrupted:

   ```bash
   specfact backlog map-fields --ado-org myorg --ado-project myproject --reset
   ```

4. **Check multiple alternatives**: SpecFact CLI supports multiple field names for the same canonical field. Both `System.AcceptanceCriteria` and `Microsoft.VSTS.Common.AcceptanceCriteria` are checked automatically.

### Interactive Mapping Command Fails

**Issue**: `specfact backlog map-fields` fails with connection or permission errors.

**Solutions**:

1. **Check token permissions**: Ensure your PAT has "Work Items (Read)" permission
2. **Verify organization/project names**: Check for typos in `--ado-org` and `--ado-project`
3. **Test API connection**:

   ```bash
   curl -u ":{token}" "https://dev.azure.com/{org}/{project}/_apis/wit/fields?api-version=7.1"
   ```

4. **Use explicit token**: Override with `--ado-token` if stored token has issues
5. **Check base URL**: For on-premise Azure DevOps Server, use `--ado-base-url`

### Custom Mapping Not Applied

**Issue**: Custom field mapping file exists but is not being used.

**Solutions**:

1. **Check file location**: Must be at `.specfact/templates/backlog/field_mappings/ado_custom.yaml`
2. **Verify YAML syntax**: Use a YAML validator to check syntax
3. **Check file permissions**: Ensure the file is readable
4. **Validate schema**: Ensure the file matches `FieldMappingConfig` schema
5. **Automatic detection**: Custom mappings are automatically detected - no restart needed. If not working, check file path and syntax.

### Backlog refine or work item PATCH fails (400/422)

**Issue**: `specfact backlog refine ado ... --write` or work item update fails with HTTP 400/422 (e.g. "400 Client Error: Bad Request") or an ADO message like "TF51535: Cannot find field System.AcceptanceCriteria."

**Cause**: The Azure DevOps project may use a custom process template where field names or paths differ from defaults (e.g. no `System.AcceptanceCriteria`). The JSON Patch sent by the CLI targets a field that does not exist or is not writable in that project.

**Solutions**:

1. **Read the console message** – The CLI prints the ADO error text and a hint, e.g. "Check custom field mapping; see ado_custom.yaml or documentation." If a field is named (e.g. "Field 'System.AcceptanceCriteria' not found"), that is the one to fix in mapping or template.

2. **Run with `--debug` and inspect the log** – This gives you the exact ADO response and the patch paths that were sent:
   - Run: `specfact --debug backlog refine ado --ado-org <org> --ado-project <project> ...` (or the failing command).
   - Open `~/.specfact/logs/specfact-debug.log` and search for `"operation": "ado_patch"` and `"status": "failed"`.
   - In that line, `extra.response_body` is a redacted snippet of the ADO error payload; `extra.patch_paths` lists the JSON Patch paths (e.g. `["/fields/System.AcceptanceCriteria", ...]`). Use these to see which field path failed.

3. **Fix field mapping** – If the error is about a missing or wrong field:
   - Ensure `.specfact/templates/backlog/field_mappings/ado_custom.yaml` exists and maps your canonical fields to the field names/paths that exist in your ADO project.
   - Use `specfact backlog map-fields --ado-org <org> --ado-project <project>` to discover available fields in the project.
   - See [Custom Field Mapping](custom-field-mapping.md) and [Debug Logging – Examining ADO API Errors](../reference/debug-logging.md#examining-ado-api-errors).

4. **Check project process template** – Custom ADO process templates can rename or remove fields. Align your mapping with the actual work item type and process in the project.

---

## CI and GitHub Actions

### Downloading test and repro logs from CI

When a PR or push runs the **PR Orchestrator** workflow, test and repro output are uploaded as workflow artifacts so you can debug failures without re-running the full suite locally.

1. **Where to find artifacts**

   - Open the workflow run: **Actions** → select the **PR Orchestrator** run (e.g. from your PR or branch).
   - Scroll to the **Artifacts** section at the bottom of the run.

2. **Artifact names and contents**

   | Artifact             | Job              | Contents                                                                 |
   |----------------------|------------------|---------------------------------------------------------------------------|
   | `test-logs`          | Tests (Python 3.12) | Full test run and coverage logs from `hatch run smart-test-full` (`logs/tests/`). |
   | `coverage-reports`   | Tests (Python 3.12) | Coverage XML for quality gates (when unit tests ran).                     |
   | `compat-py311-logs`  | Compatibility (Python 3.11) | Pytest and coverage XML output from the compat job.                  |
   | `type-check-logs`    | Type Checking (basedpyright) | Full basedpyright type-check output.                              |
   | `lint-logs`          | Linting (ruff, pylint) | Full lint run output.                                                   |
   | `quality-gates-logs`| Quality Gates (Advisory) | Coverage percentage and advisory message.                          |
   | `repro-logs`         | Contract-First CI | Full stdout/stderr of `specfact repro` (`logs/repro/`).                   |
   | `repro-reports`      | Contract-First CI | Repro report YAMLs from `.specfact/reports/enforcement/`.                |

3. **How to use them**

   - Download the artifact (e.g. `test-logs` or `repro-logs`) from the run page.
   - Unzip and open the log or report files to see the full output that led to the failure.
   - Use this instead of copying snippets from the step log, so you get complete error context before fixing and pushing again.

---

## Getting Help

If you're still experiencing issues:

1. **Check logs**:

   - **Debug log file** (when using `--debug`): Debug output and structured operation metadata are written to `~/.specfact/logs/specfact-debug.log`. See [Debug Logging](../reference/debug-logging.md) for what is logged and how to use it.
   - **Verbose repro** (ad-hoc capture):

   ```bash
   specfact --debug <command> <args>   # Writes to ~/.specfact/logs/specfact-debug.log
   specfact repro --verbose 2>&1 | tee debug.log
   ```

2. **Search documentation**:

   - [Command Reference](../reference/commands.md)
   - [Use Cases](use-cases.md)
   - [Workflows](workflows.md)

3. **Community support**:

   - 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
   - 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)

4. **Direct support**:

   - 📧 [hello@noldai.com](mailto:hello@noldai.com)

**Happy building!** 🚀
