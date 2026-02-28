---
layout: default
title: Reference Documentation
permalink: /reference/
---

# Reference Documentation

Complete technical reference for SpecFact CLI.

## Available References

- **[Commands](commands.md)** - Complete command reference with all options
- **[Thorough Codebase Validation](thorough-codebase-validation.md)** - Quick check, contract-decorated, sidecar, and dogfooding
- **[Command Syntax Policy](command-syntax-policy.md)** - Source-of-truth argument syntax conventions for docs
- **[Authentication](authentication.md)** - Device code auth flows and token storage
- **[Architecture](architecture.md)** - Technical design, module structure, and internals
- **[Debug Logging](debug-logging.md)** - Where and what is logged when using `--debug`
- **[Operational Modes](modes.md)** - CI/CD vs CoPilot modes
- **[Specmatic API](specmatic.md)** - Specmatic integration API reference (functions, classes, integration points)
- **[Telemetry](telemetry.md)** - Opt-in analytics and privacy guarantees
- **[Feature Keys](feature-keys.md)** - Key normalization and formats
- **[Directory Structure](directory-structure.md)** - Project structure and organization
- **[Schema Versioning](schema-versioning.md)** - Bundle schema versions and backward compatibility (v1.0, v1.1)
- **[Module Security](module-security.md)** - Marketplace/module integrity and publisher metadata
- **[Module Categories](module-categories.md)** - Category grouping model, canonical module assignments, bundles, and first-run profiles
- **[Dependency resolution](dependency-resolution.md)** - How module/pip dependency resolution works and bypass options

## Quick Reference

### Commands

- `specfact import from-bridge --adapter speckit` - Import from external tools via bridge adapter
- `specfact import from-code <bundle-name>` - Reverse-engineer plans from code
- `specfact plan init <bundle-name>` - Initialize new development plan
- `specfact plan compare` - Compare manual vs auto plans
- `specfact enforce stage` - Configure quality gates
- `specfact repro` - Run full validation suite
- `specfact sync bridge --adapter <adapter> --bundle <bundle-name>` - Sync with external tools via bridge adapter
- `specfact spec validate [--bundle <name>]` - Validate OpenAPI/AsyncAPI specifications
- `specfact spec generate-tests [--bundle <name>]` - Generate contract tests from specifications
- `specfact spec mock [--bundle <name>]` - Launch mock server for development
- `specfact init ide --ide <cursor|vscode|copilot|...>` - Initialize IDE integration explicitly
- `specfact module install <name|namespace/name> [--scope user|project] [--source auto|bundled|marketplace] [--repo PATH]` - Install modules with scope and source control (bare names normalize to `specfact/<name>`)
- `specfact module list [--source ...] [--show-origin] [--show-bundled-available]` - List modules with trust/publisher, optional origin details, and optional bundled-not-installed section
- `specfact module show <name>` - Show detailed module metadata and full command tree with short descriptions
- `specfact module search <query>` - Search marketplace and installed modules
- `specfact module uninstall <name|namespace/name>` / `specfact module upgrade [<name>|--all]` - Manage module lifecycle with source-aware behavior

### Modes

- **CI/CD Mode** - Fast, deterministic execution
- **CoPilot Mode** - Enhanced prompts with context injection

### IDE Integration

- `specfact init ide --ide <cursor|vscode|copilot|...>` - Set up slash commands in IDE
- See [IDE Integration Guide](../guides/ide-integration.md) for details

## Technical Details

- **Architecture**: See [Architecture](architecture.md)
- **Module Structure**: See [Architecture - Module Structure](architecture.md#module-structure)
- **Operational Modes**: See [Architecture - Operational Modes](architecture.md#operational-modes)
- **Agent Modes**: See [Architecture - Agent Modes](architecture.md#agent-modes)

## Related Documentation

- [Getting Started](../getting-started/README.md) - Installation and first steps
- [Guides](../guides/README.md) - Usage guides and examples
- [Examples](../examples/README.md) - Real-world examples
