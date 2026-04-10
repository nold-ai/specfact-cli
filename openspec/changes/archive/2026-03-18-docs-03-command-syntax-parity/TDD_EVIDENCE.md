# TDD Evidence: docs-03-command-syntax-parity

## Pre-Implementation Failing Run

**Timestamp**: 2026-03-18

**Command**:

```
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-03-command-syntax-parity
hatch test -- tests/unit/docs/test_release_docs_parity.py -v -k "removed or current"
```

**Result**: 9 FAILED, 3 PASSED

**Failing tests**:

- `test_removed_project_plan_syntax_absent_from_authored_docs` — 'specfact project plan' still present in authored docs
- `test_removed_project_import_from_bridge_syntax_absent_from_authored_docs` — 'project import from-bridge' still present
- `test_removed_backlog_policy_syntax_absent_from_authored_docs` — 'backlog policy' still present
- `test_removed_spec_contract_syntax_absent_from_authored_docs` — 'spec contract' still present
- `test_removed_spec_api_syntax_absent_from_authored_docs` — 'spec api' still present
- `test_removed_spec_sdd_syntax_absent_from_authored_docs` — 'spec sdd' still present
- `test_removed_spec_generate_syntax_absent_from_authored_docs` — 'spec generate <subcommand>' still present
- `test_current_spec_commands_documented_in_commands_reference` — 'spec validate' missing from commands.md (stale bundle mapping table still shows old spec commands)
- `test_current_backlog_subcommands_documented_in_commands_reference` — 'backlog refine' missing from commands reference

## Post-Implementation Passing Run

**Timestamp**: 2026-03-18

**Command**:

```
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/docs-03-command-syntax-parity
hatch test -- tests/unit/docs/test_release_docs_parity.py -v
```

**Result**: 21 PASSED (all)

All new parity tests pass:

- `test_removed_project_plan_syntax_absent_from_authored_docs` ✓
- `test_removed_project_import_from_bridge_syntax_absent_from_authored_docs` ✓
- `test_removed_backlog_policy_syntax_absent_from_authored_docs` ✓
- `test_removed_spec_contract_syntax_absent_from_authored_docs` ✓
- `test_removed_spec_api_syntax_absent_from_authored_docs` ✓
- `test_removed_spec_sdd_syntax_absent_from_authored_docs` ✓
- `test_removed_spec_generate_syntax_absent_from_authored_docs` ✓
- `test_current_code_import_from_bridge_documented` ✓
- `test_current_spec_commands_documented_in_commands_reference` ✓
- `test_current_govern_enforce_sdd_documented` ✓
- `test_current_backlog_subcommands_documented_in_commands_reference` ✓

All 10 pre-existing tests also pass.
