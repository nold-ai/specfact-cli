# Tasks: tester-cli-reliability

## 1. Readiness and source tracking

- [x] 1.1 Confirm tester bugs `#585`-`#593` are mapped to core/modules ownership and record the decision in `TDD_EVIDENCE.md`.
- [x] 1.2 Confirm GitHub tracking issue `#594` and paired modules issue `nold-ai/specfact-cli-modules#306` exist with source links and labels.
- [x] 1.3 Validate the OpenSpec change with `openspec validate tester-cli-reliability --strict`.

## 2. Spec-first and failing evidence

- [x] 2.1 Add spec deltas for CLI error guidance, generated command overview, tool probing, command runtime validation, docs reference validation, and CI runtime matrix.
- [x] 2.2 Add failing tests for unknown commands, missing subcommands, missing required parameters, generated command overview freshness, docs/template stale-command detection, uv-run upgrade detection, and active tool probing.
- [x] 2.3 Run the targeted tests before production edits and record failing evidence in `TDD_EVIDENCE.md`.

## 3. CLI guidance and command inventory

- [x] 3.1 Implement shared error rendering for unknown commands, missing subcommands, and missing required parameters.
- [x] 3.2 Add deterministic command overview generation for core command groups.
- [x] 3.3 Commit generated `llms.txt`, Markdown, and JSON command overview artifacts and link them from `README.md`.

## 4. Docs, prompts, and code guidance validation

- [x] 4.1 Add generated-artifact freshness as a docs validation gate.
- [x] 4.2 Scan Markdown, `.github/prompts`, Jinja2/templates, and Python guidance strings for stale command paths and option ordering.
- [x] 4.3 Repair core docs and guidance that still mention obsolete flat shims or invalid `code import` ordering.
- [x] 4.4 Add grouped `SKILL.md` export support for skill-based AI IDEs while keeping slash-command prompt exports for command-based IDEs.

## 5. Runtime environment and CI simulation

- [x] 5.1 Fix upgrade install-method detection so effective `uv run` context wins over stale/global pipx inventory.
- [x] 5.2 Add active tool probing for uv/hatch/pip/pipx contexts.
- [x] 5.3 Extend runtime smoke/CI to execute representative commands through hatch, pip editable, pipx, uv run, and uvx paths.
- [x] 5.4 Fix pipx upgrade success handling so stale/broken `specfact` launchers are detected and repaired with `pipx reinstall specfact-cli`.

## 6. Passing evidence and quality gates

- [x] 6.1 Re-run targeted tests and record passing evidence in `TDD_EVIDENCE.md`.
- [ ] 6.2 Run required quality gates for touched scope: format, type-check, lint, YAML lint, contract-test, smart-test or targeted equivalent.
- [ ] 6.3 Run SpecFact code review and resolve findings or document explicit exceptions.
