## Context

This change creates a systematic misuse/anti-pattern test suite that proves every command group fails safely on bad input. It builds on the scenario schema from cli-val-01 and adds Hypothesis fuzzing for edge cases humans do not anticipate.

## Goals / Non-Goals

**Goals:**

- Create anti-pattern scenarios for all Wave 1 command groups using the cli-val-01 YAML schema
- Implement a test runner that asserts three safety properties per anti-pattern
- Add Hypothesis strategies for 3-5 major command groups
- Surface and document any production code bugs found during anti-pattern testing

**Non-Goals:**

- No production CLI code changes in this change scope (bugs found are tracked separately)
- No acceptance test runner (that is cli-val-04)
- No CI integration (that is cli-val-05)
- No interactive prompt testing (pexpect-based testing is out of scope)

## Decisions

- Anti-pattern scenarios are stored in the same `tests/cli-contracts/` directory as patterns, using `type: anti-pattern` in the YAML
- The three-property assertion (exit code, error message, filesystem) is implemented as a reusable test helper function to avoid duplication
- Hypothesis settings: `max_examples=50`, `deadline=30000ms` per command group — bounded to keep CI runtime predictable
- Traceback detection uses regex matching for `Traceback (most recent call last)` — covers standard Python tracebacks
- Filesystem side-effect detection compares directory snapshots before and after command execution using `tmp_path`

## Risks / Trade-offs

- [Anti-patterns may reveal production bugs] -> Mitigation: track found bugs as separate issues; do not block this change on fixing them
- [Hypothesis may find flaky edge cases] -> Mitigation: use `@settings(suppress_health_check=[HealthCheck.too_slow])` and bounded strategies
- [Coverage of all misuse categories] -> Mitigation: start with the 5 common categories (missing args, invalid flags, bad paths, malformed input, forbidden combos); extend incrementally

## Migration Plan

1. Create anti-pattern YAML scenarios for all Wave 1 command groups
2. Implement three-property assertion helper
3. Create test files that load anti-patterns and run assertions
4. Add Hypothesis strategies for 3-5 major commands
5. Run full suite and document findings

## Open Questions

- Whether Hypothesis-discovered edge cases should be added back to the anti-pattern catalog automatically or manually curated
- Whether to include `--debug` mode testing (which intentionally shows tracebacks) as a separate scenario category
