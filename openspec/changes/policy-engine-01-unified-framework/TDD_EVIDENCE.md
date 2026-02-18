# TDD Evidence: policy-engine-01-unified-framework

## Pre-implementation failing run

- Timestamp (UTC): 2026-02-17T22:03:01Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -v
```

- Result: **FAILED** (3 failed)
- Failure summary:
  - `policy validate` command not yet available (`exit_code=2` instead of expected behavior).
  - `policy suggest` command not yet available (`exit_code=2`).
  - All new scenario tests failed prior to implementation as required by strict TDD order.

## Post-implementation passing run

- Timestamp (UTC): 2026-02-17T22:10:06Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -v
```

- Result: **PASSED** (3 passed)
- Notes:
  - `hatch run format`, `hatch run type-check`, and `hatch run contract-test` were run after implementation.
  - `contract-test` reported cached status with no modified-file contract deltas in this run.

## Scope extension (templates + docs hints) failing run

- Timestamp (UTC): 2026-02-17T23:46:01Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -v
```

- Result: **FAILED** (3 failed)
- Failure summary:
  - Missing docs hint in `policy validate` missing-config output.
  - `policy init` command unavailable in non-interactive mode.
  - `policy init` command unavailable in interactive mode.

## Scope extension (templates + docs hints) passing run

- Timestamp (UTC): 2026-02-17T23:47:19Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -v
```

- Result: **PASSED** (6 passed)
- Notes:
  - Added built-in template loading from `resources/templates/policies/`.
  - Added validate output docs hint for missing/invalid `.specfact/policy.yaml`.

## Scope extension (artifact auto-discovery + format normalization) failing run

- Timestamp (UTC): 2026-02-18T00:04:31Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -q
```

- Result: **FAILED** (3 failed, 5 passed)
- Failure summary:
  - `policy validate` still required explicit `--snapshot` and did not auto-discover `.specfact` artifacts.
  - `policy suggest` still required explicit `--snapshot`.
  - Loader did not yet consume baseline/plan shapes for this workflow extension.

## Scope extension (artifact auto-discovery + format normalization) passing run

- Timestamp (UTC): 2026-02-18T00:06:52Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -q
```

- Result: **PASSED** (8 passed)
- Notes:
  - Added automatic artifact discovery order: `.specfact/backlog-baseline.json`, then latest `.specfact/plans/backlog-*`.
  - Added payload normalization for `items` list, `items` dict, and `backlog_graph.items`.

## Scope extension (compatibility mapping) failing run

- Timestamp (UTC): 2026-02-18T00:15:45Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -q
```

- Result: **FAILED** (1 failed, 8 passed)
- Failure summary:
  - Imported baseline artifact with provider/raw aliases and description sections did not yet satisfy canonical policy fields (`acceptance_criteria`, `business_value`, `definition_of_done`) before evaluation.

## Scope extension (compatibility mapping) passing run

- Timestamp (UTC): 2026-02-18T00:18:24Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -q
```

- Result: **PASSED** (9 passed)
- Notes:
  - Added compatibility mapping for common raw-data aliases.
  - Added markdown section extraction for `Acceptance Criteria` and `Definition of Done`.

## Scope extension (filter/limit/group output) failing run

- Timestamp (UTC): 2026-02-18T00:23:57Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -q
```

- Result: **FAILED** (3 failed, 9 passed)
- Failure summary:
  - New CLI options `--rule`, `--limit`, and `--group-by-item` were not yet recognized by `policy validate|suggest`.

## Scope extension (filter/limit/group output) passing run

- Timestamp (UTC): 2026-02-18T00:25:46Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -q
```

- Result: **PASSED** (12 passed)
- Notes:
  - Added filtering (`--rule`) and truncation (`--limit`) to validate/suggest.
  - Added grouped output (`--group-by-item`) for validate/suggest.

## Scope extension (grouped-limit semantics) failing observation

- Timestamp (UTC): 2026-02-18T00:21:20Z
- Command:

```bash
hatch run specfact policy suggest --group-by-item --limit 4
```

- Result: **FAILED (behavioral)** (limit applied to sub-item suggestions, not item groups)
- Failure summary:
  - Output returned 2 item groups with `suggestion_count` totaling 4, showing `--limit` was truncating suggestion entries instead of limiting grouped item count.

## Scope extension (grouped-limit semantics) passing run

- Timestamp (UTC): 2026-02-18T00:23:53Z
- Command:

```bash
hatch run pytest tests/integration/commands/test_policy_engine_commands.py -q
```

- Result: **PASSED** (14 passed)
- Notes:
  - Added grouped-limit regression tests for both `policy validate` and `policy suggest`.
  - Updated grouped-mode `--limit` semantics to cap backlog item groups and keep full per-item findings/suggestions.
