# Reference Documentation

Complete technical reference for SpecFact CLI.

## Available References

- **[Commands](commands.md)** - Complete command reference with all options
- **[Architecture](architecture.md)** - Technical design, module structure, and internals
- **[Operational Modes](modes.md)** - CI/CD vs CoPilot modes
- **[Telemetry](telemetry.md)** - Opt-in analytics and privacy guarantees
- **[Feature Keys](feature-keys.md)** - Key normalization and formats
- **[Directory Structure](directory-structure.md)** - Project structure and organization

## Quick Reference

### Commands

- `specfact import from-bridge --adapter speckit` - Import from external tools via bridge adapter
- `specfact import from-code <bundle-name>` - Reverse-engineer plans from code
- `specfact plan init <bundle-name>` - Initialize new development plan
- `specfact plan compare` - Compare manual vs auto plans
- `specfact enforce stage` - Configure quality gates
- `specfact repro` - Run full validation suite
- `specfact sync bridge --adapter <adapter> --bundle <bundle-name>` - Sync with external tools via bridge adapter
- `specfact init` - Initialize IDE integration

### Modes

- **CI/CD Mode** - Fast, deterministic execution
- **CoPilot Mode** - Enhanced prompts with context injection

### IDE Integration

- `specfact init` - Set up slash commands in IDE
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
