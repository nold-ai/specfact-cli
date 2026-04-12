# TDD evidence — profile-04-safe-project-artifact-writes

## Failing-first (targeted)

- **When**: 2026-04-12 (Europe/Berlin)
- **Command**:

```bash
cd ../specfact-cli-worktrees/bugfix/profile-04-safe-project-artifact-writes
hatch run pytest \
  tests/unit/utils/test_project_artifact_write.py \
  tests/unit/utils/test_ide_setup.py \
  tests/unit/scripts/test_verify_safe_project_writes.py \
  tests/unit/modules/init/test_init_ide_prompt_selection.py \
  -q
```

- **Note**: New scenarios (`malformed_json_raises`, `preserves_unrelated_keys`, verify script) were added before the
  safe-merge implementation; prior behavior treated invalid JSON as `{}` and could destroy user settings (issue #487).

## Passing-after (targeted + e2e)

- **When**: 2026-04-12
- **Commands**:

```bash
hatch run pytest tests/unit/utils/test_project_artifact_write.py \
  tests/unit/utils/test_ide_setup.py tests/unit/scripts/test_verify_safe_project_writes.py \
  tests/unit/modules/init/test_init_ide_prompt_selection.py tests/e2e/test_init_command.py -q
hatch run format && hatch run type-check && hatch run lint
hatch run contract-test
hatch run smart-test
```

- **Module signatures**: `hatch run ./scripts/verify-modules-signature.py --require-signature` — pass without bumping
  `src/specfact_cli/modules/init/module-package.yaml` (init UX errors are raised from `ide_setup` so the init module
  payload checksum is unchanged).

## Code review gate

- **Attempted**: `hatch run specfact code review run --json --out .specfact/code-review.json` — blocked in a minimal Hatch env
  because the `code` command group is provided by the `nold-ai/specfact-codebase` module (not installed in this worktree by default).
- **Follow-up before PR**: install the codebase bundle (e.g. `specfact init --profile solo-developer` or `specfact module install nold-ai/specfact-codebase`)
  in the same environment, then re-run the command above and attach `.specfact/code-review.json` to the PR.

## Worktree cleanup (post-merge on developer machine)

- Remove worktree, delete branch, prune — see `tasks.md` section 5 (not executed in this implementation session).
