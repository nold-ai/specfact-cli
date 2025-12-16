# Migration Guide: v0.16.x to v0.19.x

This guide helps you upgrade from SpecFact CLI v0.16.x to v0.19.x.

## Overview

v0.17.0 - v0.19.0 are part of the **0.x stabilization track** leading to v0.20.0 LTS.

### Key Changes

| Version | Changes |
|---------|---------|
| **0.17.0** | Deprecated `implement` command, added bridge commands, version management |
| **0.18.0** | Updated documentation positioning, AI IDE bridge workflow |
| **0.19.0** | Full test coverage for Phase 7, migration guide |

---

## Breaking Changes

### `implement` Command Deprecated

The `implement tasks` command is deprecated in v0.17.0 and will be removed in v1.0.

**Before (v0.16.x):**

```bash
specfact implement tasks .specfact/projects/my-bundle/tasks.yaml
```

**After (v0.17.0+):**

Use the new bridge commands instead:

```bash
# Find gaps in your code
specfact analyze gaps --bundle my-bundle

# Generate AI-ready prompt to fix a gap
specfact generate fix-prompt GAP-001 --bundle my-bundle

# Generate AI-ready prompt to add tests
specfact generate test-prompt src/auth/login.py --bundle my-bundle
```

### `run idea-to-ship` Removed

The `run idea-to-ship` command has been removed in v0.17.0.

**Rationale:** Code generation features are being redesigned for v1.0 with AI-assisted workflows.

---

## New Features

### Bridge Commands (v0.17.0)

New commands that generate AI-ready prompts for your IDE:

```bash
# Generate fix prompt for a gap
specfact generate fix-prompt GAP-001

# Generate test prompt for a file
specfact generate test-prompt src/module.py --type unit
```

### Version Management (v0.17.0)

New commands for managing bundle versions:

```bash
# Check for recommended version bump
specfact project version check --bundle my-bundle

# Bump version (major/minor/patch)
specfact project version bump --bundle my-bundle --type minor

# Set explicit version
specfact project version set --bundle my-bundle --version 2.0.0
```

### CI Version Check (v0.17.0)

GitHub Actions template now includes version check with configurable modes:

- `info` - Informational only
- `warn` (default) - Log warnings, continue CI
- `block` - Fail CI if version bump not followed

---

## Upgrade Steps

### Step 1: Update SpecFact CLI

```bash
pip install -U specfact-cli
# or
uvx specfact-cli@latest --version
```

### Step 2: Verify Version

```bash
specfact --version
# Should show: SpecFact CLI version 0.19.0
```

### Step 3: Update Workflows

If you were using `implement tasks` or `run idea-to-ship`, migrate to bridge commands:

**Old workflow:**

```bash
specfact generate tasks --bundle my-bundle
specfact implement tasks .specfact/projects/my-bundle/tasks.yaml
```

**New workflow:**

```bash
# 1. Analyze for gaps
specfact analyze gaps --bundle my-bundle

# 2. Generate AI prompts for each gap
specfact generate fix-prompt GAP-001

# 3. Copy prompt to AI IDE, get fix, apply

# 4. Validate
specfact enforce sdd --bundle my-bundle
```

### Step 4: Update CI/CD (Optional)

Add version check to your GitHub Actions:

```yaml
- name: Version Check
  run: specfact project version check --bundle ${{ env.BUNDLE_NAME }}
  env:
    SPECFACT_VERSION_CHECK_MODE: warn  # or 'info' or 'block'
```

---

## FAQ

### Q: Why was `implement` deprecated?

**A:** The `implement` command attempted to generate code directly, but this approach doesn't align with the Ultimate Vision for v1.0. In v1.0, AI copilots will consume structured data from SpecFact and generate code, with SpecFact validating the results. The bridge commands provide a transitional workflow.

### Q: Can I still use v0.16.x?

**A:** Yes, v0.16.x will continue to work. However, we recommend upgrading to v0.19.x for the latest fixes and features. v0.20.0 will be the Long-Term Stable (LTS) release.

### Q: When will v1.0 be released?

**A:** See the [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions) for the v1.0 roadmap.

---

## Support

- 💬 **Questions?** [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 **Found a bug?** [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 **Need help?** [hello@noldai.com](mailto:hello@noldai.com)
