# Proposal: tooling-spaced-env-pythonpath

## Why

On 2026-06-09, local Mac validation reproduced a commit-gate failure reported by `danieldekay`: `hatch run type-check` and `hatch run lint` split the active Python interpreter path when the environment manager stores virtual environments under a directory with spaces, such as macOS `Application Support`.

The same failure class can affect any shell-based gate script that interpolates an environment-manager-provided executable path without quoting it. Env managers such as Hatch, uv, virtualenv, pipx, and system Python launchers may all produce paths that contain whitespace or other shell-significant characters. Required quality gates must treat those paths as opaque arguments.

## What Changes

- Require shell-based quality-gate scripts to quote interpreter path command substitutions passed to tool flags such as `--pythonpath`.
- Keep list-argument subprocess calls as the preferred safe form when commands are assembled in Python.
- Add regression coverage for the Hatch `type-check` and `lint` scripts so future edits cannot reintroduce unquoted Python executable interpolation.

## Capabilities

### Modified Capabilities

- `trustworthy-green-checks`

## Impact

- Affected code/config: Hatch default environment scripts in `pyproject.toml`.
- Affected tests: packaging/config regression coverage for required local quality gates.
- Affected users: macOS and any setup where Hatch, uv, virtualenv, pipx, or another environment manager creates interpreter paths containing spaces.
