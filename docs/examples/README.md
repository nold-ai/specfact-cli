# Examples

Real-world examples of using SpecFact CLI.

## Available Examples

- **[Integration Showcases](integration-showcases/)** ⭐ **START HERE** - Real bugs fixed via VS Code, Cursor, GitHub Actions integrations
  - **CLI-First**: Works offline, no account required, integrates with any IDE
  - Start with the [Integration Showcases README](integration-showcases/README.md) for an overview
  - Read the [main showcase document](integration-showcases/integration-showcases.md) for real examples
- **[Brownfield Examples](./)** ⭐ **NEW** - Complete hard-SDD workflow demonstrations
  - **[Django Modernization](brownfield-django-modernization.md)** - Legacy Django app → contract-enforced modern codebase
  - **[Flask API](brownfield-flask-api.md)** - Legacy Flask API → contract-enforced modern service
  - **[Data Pipeline](brownfield-data-pipeline.md)** - Legacy ETL pipeline → contract-enforced data processing
  - All examples now include: `plan harden`, `enforce sdd`, `plan review`, and `plan promote` with SDD validation
- **[Quick Examples](quick-examples.md)** - Quick code snippets for common tasks, including SDD workflow
- **[Dogfooding SpecFact CLI](dogfooding-specfact-cli.md)** - We ran SpecFact CLI on itself (< 10 seconds!)

## Quick Start

### See It In Action

**For Brownfield Modernization** (Recommended):

Read the complete brownfield examples to see the hard-SDD workflow:

**[Django Modernization Example](brownfield-django-modernization.md)**

This example shows the complete workflow:

1. ⚡ **Extract specs** from legacy code → 23 features, 112 stories in **8 seconds**
2. 📋 **Create SDD manifest** → Hard spec with WHY/WHAT/HOW, coverage thresholds
3. ✅ **Validate SDD** → Hash match, coverage threshold validation
4. 📊 **Review plan** → SDD validation integrated, ambiguity resolution
5. 🚀 **Promote plan** → SDD required for "review" or higher stages
6. 🔒 **Add contracts** → Runtime enforcement prevents regressions
7. 🔍 **Re-validate SDD** → Ensure coverage thresholds maintained

**For Quick Testing**:

**[Dogfooding SpecFact CLI](dogfooding-specfact-cli.md)**

This example shows:

- ⚡ Analyzed 19 Python files → Discovered **19 features** and **49 stories** in **3 seconds**
- 🚫 Set enforcement to "balanced" → **Blocked 2 HIGH violations** (as configured)
- 📊 Compared manual vs auto-derived plans → Found **24 deviations** in **5 seconds**

**Total time**: < 10 seconds | **Total value**: Found real naming inconsistencies and undocumented features

## Related Documentation

- [Use Cases](../guides/use-cases.md) - More real-world scenarios
- [Getting Started](../getting-started/README.md) - Installation and setup
- [Command Reference](../reference/commands.md) - All available commands
