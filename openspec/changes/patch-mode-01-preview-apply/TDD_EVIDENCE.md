# TDD Evidence: patch-mode-01-preview-apply

## Post-implementation passing run

- **Command**: `hatch test -- tests/unit/specfact_cli/modules/test_patch_mode.py -v`
- **Timestamp**: 2026-02-18
- **Result**: 11 passed in ~3s
- **Summary**: All spec-derived scenarios pass (generate diff, apply local with preflight, apply --write with confirmation, idempotency).

## Scenarios covered

1. **Generate patch**: `generate_unified_diff` returns string; CLI not invoked for generate (backlog refine --patch is future integration).
2. **Apply locally**: `specfact patch apply <file>` applies locally with preflight; `--dry-run` preflight only.
3. **Write upstream**: `specfact patch apply --write` without `--yes` skips; with `--yes` succeeds and marks idempotent.
4. **Idempotency**: `check_idempotent` / `mark_applied` with state dir.

## Note

Tests were written from spec scenarios; implementation was added to satisfy them. Failing run was not captured (implementation done in same session).
