# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

All notable changes to this project will be documented in this file.

**Important:** Changes need to be documented below this block as this is the header section. Each section should be separated by a horizontal rule.

---

## [Unreleased]

### In Progress

- CLI command implementation (import, analyze, plan, compare, enforce, repro)
- Contract-first validation with icontract and beartype
- Pydantic models for plan bundles and protocols
- Semgrep async anti-pattern rules
- CrossHair contract exploration

---

## 0.1.0 - 2025-01-29 (Initial Release)

### Added (0.1.0)

- **Project Structure**
  - Initialized SpecFact CLI repository structure
  - Created `src/specfact_cli/` for CLI implementation
  - Created `src/common/` for shared utilities (logger_setup, platform_base)
  - Set up `tests/` directory with unit, integration, and e2e structure

- **Documentation**
  - Comprehensive README.md with CLI usage examples
  - AGENTS.md with repository guidelines and development patterns
  - CONTRIBUTING.md with contribution workflow
  - LICENSE.md with Sustainable Use License
  - USAGE-FAQ.md with licensing and usage questions
  - CODE_OF_CONDUCT.md for community guidelines
  - SECURITY.md for security policy

- **Configuration**
  - pyproject.toml with contract-first testing support
  - setup.py for package distribution
  - pyrightconfig.json for strict type checking with basedpyright
  - .yamllint for YAML validation
  - .prettierrc.json for consistent formatting
  - .gitignore with appropriate exclusions (including docs/internal/)

- **Cursor AI Rules**
  - `.cursor/rules/spec-fact-cli-rules.mdc` - SpecFact CLI development guidelines
  - `.cursor/rules/python-github-rules.mdc` - Python development standards
  - `.cursor/rules/testing-and-build-guide.mdc` - Testing procedures
  - `.cursor/rules/clean-code-principles.mdc` - Code quality enforcement
  - `.cursor/rules/estimation-bias-prevention.mdc` - Realistic time estimation
  - `.cursor/rules/session_startup_instructions.mdc` - Session startup checklist
  - `.cursor/rules/oss-strategy-rules.mdc` - OSS strategy and evidence requirements
  - `.cursor/rules/markdown-rules.mdc` - Markdown linting standards

- **GitHub Workflows**
  - PR Orchestrator workflow with contract-first CI/CD
  - Contract validation and exploration jobs
  - Type checking with basedpyright
  - Linting with ruff and pylint
  - CLI command validation
  - Package validation (pip/uvx distribution)
  - Container build and push to GHCR

- **Testing Infrastructure**
  - Contract-first testing approach with icontract
  - Runtime type checking with beartype
  - Contract exploration with CrossHair
  - Property-based testing with Hypothesis
  - Scenario tests for CLI workflows

### Changed (0.1.0)

### Security (0.1.0)

- Applied Sustainable Use License for proper commercial protection
- Protected internal documentation via .gitignore (docs/internal/)
- Removed all internal email addresses and project references
- Ensured no sensitive information in public repository

### Infrastructure (0.1.0)

- PyPI package name: specfact-cli
- CLI command: specfact
- Container registry: ghcr.io/nold-ai/specfact-cli
- Python support: 3.11, 3.12, 3.13
- Distribution methods: pip, uvx, container

---

## Project History

**2025-01-29**: Initial repository creation and setup for SpecFact CLI public release

- Forked from specfact internal project
- Cleaned up for open-source distribution
- Aligned with CLI-First Strategy (OSS-first approach)
- Prepared for public release on GitHub

---

**Note**: This is a new project. For the history of the internal coding-factory project that preceded this CLI tool, see the coding-factory repository (private).

---

Copyright © 2025 Nold AI (Owner: Dominikus Nold)
