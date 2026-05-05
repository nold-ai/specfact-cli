## Context

This change extends the existing test-prompt generation workflow to support CLI behavior scenarios. It creates prompt templates that AI copilots use to generate scenario YAML, anti-pattern catalogs, and acceptance tests for new or modified CLI commands.

## Goals / Non-Goals

**Goals:**

- Create a prompt template in `resources/prompts/` for CLI scenario generation
- Extend `specfact generate test-prompt` to detect CLI commands and offer the template
- Document the convention that CLI command changes require scenario files
- Make scenario authoring a natural part of the copilot-assisted development workflow

**Non-Goals:**

- No new CLI commands or production code beyond prompt template and workflow extension
- No automatic enforcement (that is cli-val-05)
- No schema changes (the template generates cli-val-01-compliant YAML)

## Decisions

- Prompt template is a Jinja2 template in `resources/prompts/` — consistent with existing prompt templates
- Template takes command metadata (name, args, options, types) as input and generates three outputs: scenario YAML, anti-pattern list, and Markdown acceptance test
- The `generate test-prompt` workflow auto-detects CLI commands by scanning for `@app.command()` and `typer.Typer()` patterns
- Convention enforcement is documentation-only in this change; CI enforcement comes from cli-val-05

## Risks / Trade-offs

- [Copilot output quality varies] -> Mitigation: template provides structured examples; schema validation (cli-val-01) catches malformed output
- [Convention may not be followed without enforcement] -> Mitigation: cli-val-05 CI gates enforce scenario presence
- [Template maintenance as schema evolves] -> Mitigation: template references the schema directly; schema version field enables compatibility checking

## Migration Plan

1. Create prompt template with example inputs and outputs
2. Extend generate test-prompt workflow to detect CLI commands
3. Document the convention and workflow in docs/
4. Test with 2-3 example commands to validate template quality

## Open Questions

- Whether the prompt template should generate scenario files directly to disk or output to stdout for copilot review
- Whether to include a `specfact generate cli-scenarios` subcommand or rely solely on the existing `generate test-prompt` workflow
