# CLI Usage Enforcement Rules

## Core Principle

**ALWAYS use SpecFact CLI commands. Never create artifacts directly.**

## Rules

1. **Execute CLI First**: Always run CLI commands before any analysis
2. **Use CLI for Writes**: All write operations must go through CLI
3. **Read for Display Only**: Use file reading tools for display/analysis only
4. **Never Modify .specfact/**: Do not create/modify files in `.specfact/` directly
5. **Never Bypass Validation**: CLI ensures schema compliance and metadata

## What Happens If You Don't Follow

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures
- ❌ Works only in Copilot mode, fails in CI/CD

## Available CLI Commands

- `specfact plan init <bundle-name>` - Initialize project bundle
- `specfact import from-code <bundle-name> --repo <path>` - Import from codebase
- `specfact plan review <bundle-name>` - Review plan
- `specfact plan harden <bundle-name>` - Create SDD manifest
- `specfact enforce sdd <bundle-name>` - Validate SDD
- `specfact sync bridge --adapter <adapter> --repo <path>` - Sync with external tools
- See [Command Reference](../../docs/reference/commands.md) for full list
