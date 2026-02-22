# TDD Evidence: backlog-core-02-interactive-issue-creation

## Failing-before Implementation

- Timestamp: 2026-02-20 23:06:46 +0100
- Command:

```bash
hatch test --cover -v modules/backlog-core/tests/unit/test_backlog_protocol.py modules/backlog-core/tests/unit/test_adapter_create_issue.py modules/backlog-core/tests/unit/test_add_command.py
```

- Result: **FAILED** (expected at this stage)
- Failure summary:
  - `GitHubAdapter` missing `create_issue(...)`
  - `AdoAdapter` missing `create_issue(...)`
  - `specfact backlog add` command not registered/implemented yet (`SystemExit(2)` in command tests)

## Passing-after Implementation

- Timestamp: 2026-02-20 23:11:39 +0100
- Command:

```bash
hatch test -v modules/backlog-core/tests/unit/test_backlog_protocol.py modules/backlog-core/tests/unit/test_adapter_create_issue.py modules/backlog-core/tests/unit/test_add_command.py
```

- Result: **PASSED** (11 passed)

## Regression Fix Round: Sprint Persistence and Canonical GitHub Created ID

### Failing-before Implementation

- Timestamp: 2026-02-22 23:16:44 +0100
- Command:

```bash
hatch test -v modules/backlog-core/tests/unit/test_adapter_create_issue.py
```

- Result: **FAILED** (expected at this stage)
- Failure summary:
  - GitHub `create_issue` returned internal DB id in `id` instead of canonical issue number (`id != key`).
  - ADO `create_issue` did not map payload `sprint` to `/fields/System.IterationPath`.

### Passing-after Implementation

- Timestamp: 2026-02-22 23:17:07 +0100
- Command:

```bash
hatch test -v modules/backlog-core/tests/unit/test_adapter_create_issue.py
```

- Result: **PASSED** (5 passed)
