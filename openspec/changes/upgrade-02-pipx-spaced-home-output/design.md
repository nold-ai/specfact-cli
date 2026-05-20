## Context

`specfact upgrade` currently runs the selected installer directly. For pipx installs, the child process writes its own warning block to the terminal when `PIPX_HOME` contains spaces, even if `pipx upgrade specfact-cli` succeeds. Because that output is interleaved with SpecFact's success path, users see a warning for a completed upgrade.

## Decision

Capture upgrade subprocess stdout and stderr in `_execute_upgrade_command`, then replay filtered output according to the command result:

- On return code `0`, remove only the known pipx spaced-home warning block from pipx upgrade output before replaying any remaining child output.
- On non-zero return code, replay stdout and stderr unfiltered before printing the SpecFact failure summary.
- On timeout, replay any partial stdout and stderr captured by `TimeoutExpired` before printing the existing SpecFact-owned timeout message.
- On `OSError`, keep the existing SpecFact-owned error message.

The filter is intentionally narrow. It matches the current pipx warning lines that start with `Found a space in the pipx home path`, `To see your PIPX_HOME dir`, and `Most likely fix on macOS`, plus their wrapped continuation lines. It does not suppress unrelated warnings.

## Real-World Validation

Add a subprocess-backed validation case that creates a temporary fake `pipx` executable under a directory with spaces, runs `specfact upgrade --yes` against that executable, and emits the warning block from #570 plus a successful upgrade line. The validation proves the CLI handles the same class of macOS path output without depending on a real pipx installation or network access.

## Risks

- Over-filtering could hide actionable pipx output. Mitigation: filter only the exact known warning block and preserve all output on failure.
- Capturing child output changes streaming behavior. Mitigation: this only affects short upgrade command output, and remaining output is replayed after the process exits.
