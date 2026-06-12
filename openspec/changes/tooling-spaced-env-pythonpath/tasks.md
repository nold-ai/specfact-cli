# Tasks: tooling-spaced-env-pythonpath

## 1. Spec and failing evidence

- [x] 1.1 Add an OpenSpec delta for whitespace-safe required quality-gate command construction.
- [x] 1.2 Add a failing regression for unquoted Python interpreter command substitution in required shell-based gates.
- [x] 1.3 Reproduce the Mac path-space failure with the current Hatch scripts and record evidence.

## 2. Implementation

- [x] 2.1 Quote the active Python executable command substitution in `hatch run type-check`.
- [x] 2.2 Quote the active Python executable command substitution in `hatch run lint`.
- [x] 2.3 Verify no other executable command-substitution path patterns remain unquoted in active gate scripts.

## 3. Verification

- [x] 3.1 Validate the OpenSpec change with `openspec validate tooling-spaced-env-pythonpath --strict`.
- [x] 3.2 Run the focused regression test.
- [x] 3.3 Run `hatch run type-check` on macOS with the current Hatch environment path containing `Application Support`.
- [x] 3.4 Run or re-run the relevant commit-gate checks and record any unrelated residual blockers.
