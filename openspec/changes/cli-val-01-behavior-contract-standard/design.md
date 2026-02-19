## Context

This change establishes the foundational artifact format for CLI end-user validation. It defines how command behavior expectations are recorded, validated, and consumed by downstream validation changes (cli-val-03, cli-val-04, cli-val-06). No production CLI code is modified.

## Goals / Non-Goals

**Goals:**

- Define a YAML schema for CLI behavior scenarios that is both human-readable and machine-executable
- Pilot the format on 2-3 command groups to validate usability
- Provide a schema validation tool that integrates with the existing hatch script system
- Keep the format simple enough for AI copilots to generate reliably

**Non-Goals:**

- No test runner implementation (that is cli-val-04)
- No CI integration (that is cli-val-05)
- No changes to production CLI commands
- No snapshot testing infrastructure (that is cli-val-02)

## Decisions

- Store scenario files in `tests/cli-contracts/` to keep them adjacent to existing test tiers
- Use YAML (not JSON or TOML) for scenario files — aligns with existing SpecFact config patterns and is copilot-friendly
- Separate patterns and anti-patterns within the same file using a `type` field rather than separate files — keeps related behavior together
- Use JSON Schema for the schema definition — enables validation with `jsonschema` (already a project dependency)
- Pilot on three command groups: one with many args (e.g., `backlog ceremony`), one with file I/O (e.g., `validate`), one simple (e.g., `--help`/`--version`)

## Schema Design

```yaml
# tests/cli-contracts/schema/cli-scenario.schema.yaml
feature: string           # command group name (e.g., "spec validate")
scenarios:
  - name: string          # human-readable scenario name
    type: pattern | anti-pattern
    argv: [string]        # exact command tokens
    context:              # optional workspace setup
      requires: string    # "empty-repo" | "sample-bundle" | "initialized-project"
      env: {key: value}   # environment variable overrides
      stdin: string       # stdin input (if any)
    expect:
      exit: int           # exact exit code (for patterns)
      exit_nonzero: bool  # true for anti-patterns
      stdout_contains: [string]
      stdout_regex: [string]
      stderr_contains: [string]
      stderr_regex: [string]
      no_traceback: bool  # assert no Python traceback in output
    fs:
      creates: [string]   # files expected to be created
      modifies: [string]  # files expected to be modified
      forbidden: [string] # files that must NOT be created/modified
```

## Risks / Trade-offs

- [Schema rigidity] -> Mitigation: start with a minimal schema and extend per downstream change needs; version the schema
- [YAML complexity for many scenarios] -> Mitigation: one file per command group keeps files manageable; add `$ref` support later if needed
- [Scenario maintenance burden] -> Mitigation: cli-val-06 provides copilot generation; cli-val-05 CI catches stale scenarios

## Migration Plan

1. Define schema and validation tool
2. Create pilot scenario files for 3 command groups
3. Validate all pilots pass schema validation
4. Document format in `docs/` for contributors
5. Downstream changes (cli-val-03/04/06) consume the format

## Open Questions

- Exact command groups for the pilot: recommend `backlog ceremony standup`, `validate`, and root `specfact --help`/`--version`
- Whether to support YAML anchors and aliases for reducing repetition in large scenario files
