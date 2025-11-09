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

3. **Use uvx** (no installation needed):

   ```bash
   uvx --from specfact-cli specfact --help
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

**Issue**: `No Spec-Kit project found` when running `import from-spec-kit`

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
   specfact import from-spec-kit --repo /path/to/speckit-project
   ```

### Code Analysis Fails

**Issue**: `Analysis failed` or `No features detected`

**Solutions**:

1. **Check repository path**:

   ```bash
   specfact import from-code --repo . --verbose
   ```

2. **Lower confidence threshold**:

   ```bash
   specfact import from-code --repo . --confidence 0.3
   ```

3. **Check file structure**:

   ```bash
   find . -name "*.py" -type f | head -10
   ```

4. **Use CoPilot mode** (if available):

   ```bash
   specfact --mode copilot import from-code --repo . --confidence 0.7
   ```

---

## Sync Issues

### Watch Mode Not Starting

**Issue**: Watch mode exits immediately or doesn't detect changes

**Solutions**:

1. **Check repository path**:

   ```bash
   specfact sync spec-kit --repo . --watch --interval 5 --verbose
   ```

2. **Verify directory exists**:

   ```bash
   ls -la .specify/
   ls -la .specfact/
   ```

3. **Check permissions**:

   ```bash
   ls -la .specfact/plans/
   ```

4. **Try one-time sync first**:

   ```bash
   specfact sync spec-kit --repo . --bidirectional
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
   specfact sync spec-kit --repo .

   # SpecFact → Spec-Kit only (manual)
   # Edit Spec-Kit files manually
   ```

---

## Enforcement Issues

### Enforcement Not Working

**Issue**: Violations not being blocked or warned

**Solutions**:

1. **Check enforcement configuration**:

   ```bash
   cat .specfact/enforcement/config.yaml
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
   specfact import from-code --repo . --confidence 0.7
   ```

3. **Check enforcement rules**:

   ```bash
   cat .specfact/enforcement/config.yaml
   ```

4. **Use minimal mode** (observe only):

   ```bash
   specfact enforce stage --preset minimal
   ```

---

## Plan Comparison Issues

### Plans Not Found

**Issue**: `Plan not found` when running `plan compare`

**Solutions**:

1. **Check plan locations**:

   ```bash
   ls -la .specfact/plans/
   ls -la .specfact/reports/brownfield/
   ```

2. **Use explicit paths**:

   ```bash
   specfact plan compare \
     --manual .specfact/plans/main.bundle.yaml \
     --auto .specfact/reports/brownfield/auto-derived.*.yaml
   ```

3. **Generate auto-derived plan first**:

   ```bash
   specfact import from-code --repo .
   ```

### No Deviations Found (Expected Some)

**Issue**: Comparison shows no deviations but you expect some

**Solutions**:

1. **Check feature key normalization**:

   - Different key formats may normalize to the same key
   - Check `reference/feature-keys.md` for details

2. **Verify plan contents**:

   ```bash
   cat .specfact/plans/main.bundle.yaml | grep -A 5 "features:"
   ```

3. **Use verbose mode**:

   ```bash
   specfact plan compare --repo . --verbose
   ```

---

## IDE Integration Issues

### Slash Commands Not Working

**Issue**: Slash commands not recognized in IDE

**Solutions**:

1. **Reinitialize IDE integration**:

   ```bash
   specfact init --ide cursor --force
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
   specfact init --ide cursor --force
   ```

3. **Check IDE type**:

   ```bash
   specfact init --ide cursor  # For Cursor
   specfact init --ide vscode  # For VS Code
   ```

---

## Mode Detection Issues

### Wrong Mode Detected

**Issue**: CI/CD mode when CoPilot should be detected (or vice versa)

**Solutions**:

1. **Use explicit mode**:

   ```bash
   specfact --mode copilot import from-code --repo .
   ```

2. **Check environment variables**:

   ```bash
   echo $COPILOT_API_URL
   echo $VSCODE_PID
   ```

3. **Set mode explicitly**:

   ```bash
   export SPECFACT_MODE=copilot
   specfact import from-code --repo .
   ```

4. **See [Operational Modes](../reference/modes.md)** for details

---

## Performance Issues

### Slow Analysis

**Issue**: Code analysis takes too long

**Solutions**:

1. **Use CI/CD mode** (faster):

   ```bash
   specfact --mode cicd import from-code --repo .
   ```

2. **Increase confidence threshold** (fewer features):

   ```bash
   specfact import from-code --repo . --confidence 0.8
   ```

3. **Exclude directories**:

   ```bash
   # Use .gitignore or exclude patterns
   specfact import from-code --repo . --exclude "tests/"
   ```

### Watch Mode High CPU

**Issue**: Watch mode uses too much CPU

**Solutions**:

1. **Increase interval**:

   ```bash
   specfact sync spec-kit --repo . --watch --interval 10
   ```

2. **Use one-time sync**:

   ```bash
   specfact sync spec-kit --repo . --bidirectional
   ```

3. **Check file system events**:

   - Too many files being watched
   - Consider excluding directories

---

## Getting Help

If you're still experiencing issues:

1. **Check logs**:

   ```bash
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
