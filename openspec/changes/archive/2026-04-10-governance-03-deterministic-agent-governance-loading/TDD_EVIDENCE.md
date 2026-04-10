# TDD Evidence

## Failing-before evidence

- Timestamp: `2026-04-10T22:22:22+02:00`
- Command:

```bash
python3 -m pytest tests/unit/scripts/test_doc_frontmatter/test_agent_rule_frontmatter.py tests/unit/docs/test_agent_rules_governance.py -q
```

- Result: failed as expected before implementation.
- Failure summary:
  - `scripts/check_doc_frontmatter.py` did not expose `AgentRuleFrontmatter`.
  - `docs/agent-rules/INDEX.md` and `docs/agent-rules/05-non-negotiable-checklist.md` did not exist yet.
  - `AGENTS.md` did not yet reference the canonical rule docs.
  - The doc frontmatter validator still accepted `docs/agent-rules/INDEX.md` without required governance fields such as `applies_when`.

## Passing-after evidence

- Timestamp: `2026-04-10T22:39:02+02:00`
- Commands:

```bash
python3 -m pytest tests/unit/scripts/test_doc_frontmatter/test_agent_rule_frontmatter.py tests/unit/docs/test_agent_rules_governance.py -q
python3 -m pytest tests/unit/scripts/test_doc_frontmatter/test_schema.py tests/unit/scripts/test_doc_frontmatter/test_validation.py tests/integration/scripts/test_doc_frontmatter/test_integration.py tests/unit/docs/test_docs_validation_scripts.py -q
python3 -m pytest tests/unit/specfact_cli/test_clean_code_principle_gates.py -q
hatch run format
hatch run yaml-lint
hatch run lint
hatch run contract-test
hatch run smart-test
openspec validate governance-03-deterministic-agent-governance-loading --strict
```

- Result: passing after implementation.
- Notes:
  - `hatch run type-check` still reports the repository's existing warning baseline, so changed-file validation was verified separately with `basedpyright scripts/check_doc_frontmatter.py tests/helpers/doc_frontmatter_types.py tests/unit/scripts/test_doc_frontmatter/test_agent_rule_frontmatter.py tests/unit/docs/test_agent_rules_governance.py`, which passed with `0 errors, 0 warnings, 0 notes`.
  - `hatch run specfact code review run --json --out .specfact/code-review.json` is currently blocked in this worktree because the `nold-ai/specfact-codebase` module that provides the `specfact code review` command is not installed. The command fails immediately with a missing-module message rather than change-related findings.
