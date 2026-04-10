---
layout: default
title: Command Syntax Policy
permalink: /reference/command-syntax-policy/
description: Source-of-truth policy for documenting SpecFact CLI command argument syntax.
---

# Command Syntax Policy

This policy defines how command examples must be documented so docs stay consistent with actual CLI behavior.

## Core Rule

Always document commands exactly as implemented by `specfact <command> --help` in the current release.

- Do not assume all commands use the same bundle argument style.
- Do not convert positional bundle arguments to `--bundle` unless the command explicitly supports it.

## Bundle Argument Conventions

- Positional bundle argument:
  - `specfact code import [BUNDLE]`
  - `specfact project snapshot --bundle <bundle-name>`
  - `specfact project devops-flow --stage <plan|develop|review|release|monitor>`
- `--bundle` option:
  - Supported by many spec and govern commands (for example `spec validate`, `spec generate-tests`, `govern enforce sdd`)
  - Not universally supported across all commands

## IDE Init Syntax

- Preferred explicit form: `specfact init ide --ide <cursor|vscode|copilot|...>`
- `specfact init` is valid for auto-detection/bootstrap, but docs should be explicit when IDE-specific behavior is intended.

## Docs Author Checklist

Before merging command docs updates:

1. Verify syntax with `hatch run specfact <command> --help`.
2. Verify at least one real invocation for changed commands.
3. Keep examples aligned with current argument model (positional vs option).
4. Prefer one canonical example style per command in each page.

## Quick Verification Commands

```bash
hatch run specfact code import --help
hatch run specfact project snapshot --help
hatch run specfact project devops-flow --help
hatch run specfact govern enforce --help
hatch run specfact spec validate --help
```
