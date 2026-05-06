## Context

This change adds snapshot testing infrastructure to freeze CLI output as versioned contracts. It uses syrupy (a pytest snapshot plugin) to capture and compare help text, structured output, and error messages. No production CLI code changes are needed.

## Goals / Non-Goals

**Goals:**

- Add syrupy as a dev/test dependency
- Create snapshot tests for all command `--help` outputs
- Create snapshot tests for key structured outputs and error messages
- Define a snapshot update policy that prevents accidental drift
- Integrate with hatch scripts for developer workflow

**Non-Goals:**

- No CI gating implementation (that is cli-val-05)
- No production CLI code changes
- No changes to command behavior or output format
- No interactive test output (snapshots are for deterministic, non-interactive commands only)

## Decisions

- Use syrupy over inline assert strings — syrupy manages snapshot files automatically, supports multiple serialization formats, and provides clear diffs on failure
- Store snapshots in `tests/snapshots/` — keeps them separate from test code for cleaner diffs
- Normalize dynamic values (timestamps, absolute paths, version strings) before snapshot comparison — prevents false failures across environments
- Create one snapshot test file per command tier: `test_help_snapshots.py`, `test_output_snapshots.py`, `test_error_snapshots.py`
- Add `hatch run snapshot-update` script for explicit snapshot refresh

## Risks / Trade-offs

- [Snapshot maintenance on intentional changes] -> Mitigation: explicit `--snapshot-update` flag + PR review of snapshot diffs
- [Dynamic output causes false failures] -> Mitigation: normalize timestamps, paths, and version strings before comparison
- [Large snapshot files in git] -> Mitigation: text-based snapshots are compressible; help text snapshots are small

## Migration Plan

1. Add syrupy dependency to pyproject.toml dev extras
2. Create snapshot test files with normalization helpers
3. Generate initial snapshots for all existing commands
4. Verify all snapshots pass on clean run
5. Document update workflow in docs/

## Open Questions

- Whether to snapshot Rich-formatted output (with ANSI codes) or plain text — recommend plain text for stability
- Whether error message snapshots should cover all error paths or only the most common ones — recommend starting with 5-10 key error templates
