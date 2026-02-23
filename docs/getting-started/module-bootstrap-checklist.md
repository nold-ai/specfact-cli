---
layout: default
title: Module Bootstrap Checklist
permalink: /getting-started/module-bootstrap-checklist/
description: Quick checklist to verify bundled modules are installed and discoverable in user/project scope.
---

# Module Bootstrap Checklist

Use this checklist right after installing or upgrading SpecFact CLI to ensure bundled modules are installed and discoverable.
Use plain `specfact ...` commands below (not `hatch run specfact ...`) so the steps work for pipx, pip, uv tool installs, and packaged environments.

## 1. Initialize Bundled Modules

### User scope (default)

```bash
specfact module init
```

This seeds bundled modules into `~/.specfact/modules`.

### Project scope (optional)

```bash
specfact module init --scope project --repo .
```

This seeds bundled modules into `<repo>/.specfact/modules`.

Use project scope when modules should apply only to a specific codebase/customer repository.

## 2. Verify Installed Modules

```bash
specfact module list
```

If bundled modules are still available but not installed, you'll see a hint to run:

```bash
specfact module list --show-bundled-available
```

## 3. Inspect Bundled But Not Installed Modules

```bash
specfact module list --show-bundled-available
```

This prints a separate bundled table plus install guidance.

## 4. Install Specific Modules Only (Optional)

Install from bundled sources only:

```bash
specfact module install backlog-core --source bundled
```

Install from marketplace only:

```bash
specfact module install specfact/backlog --source marketplace
```

Install with automatic source resolution (`bundled` first, then marketplace):

```bash
specfact module install backlog
```

## 5. Scope-Safe Uninstall

```bash
specfact module uninstall backlog-core --scope user
# or
specfact module uninstall backlog-core --scope project --repo .
```

If the same module exists in both user and project scope, SpecFact requires explicit `--scope` to prevent accidental removal.

## 6. Startup Freshness Guidance

SpecFact performs bundled module freshness checks:

- on first run after a CLI version change
- otherwise at most once per 24 hours

When modules are missing/outdated, startup output suggests exact refresh commands for project and/or user scope.
