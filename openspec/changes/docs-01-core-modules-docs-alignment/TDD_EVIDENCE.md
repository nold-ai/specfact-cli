# TDD Evidence: docs-01-core-modules-docs-alignment

## Pre-implementation failing run

- Timestamp: 2026-03-05
- Command:

```bash
/bin/bash -lc 'HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/docs/test_release_docs_parity.py -q'
```

- Result: failed (`3 failed, 4 passed`)
- Failure summary:
  - `docs/getting-started/module-bootstrap-checklist.md` still used stale `backlog-core` install/uninstall examples.
  - `docs/guides/publishing-modules.md` still described the old tag-driven publish flow instead of the decoupled `specfact-cli-modules` branch workflow.
  - `docs/reference/module-contracts.md` still described the pre-migration ownership boundary and module location.

## Post-implementation passing run

- Timestamp: 2026-03-05
- Command:

```bash
/bin/bash -lc 'HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/docs/test_release_docs_parity.py -q'
```

- Result: passed (`7 passed`)

## Pre-implementation failing run: markdown auto-fix hook regression

- Timestamp: 2026-03-05
- Command:

```bash
/bin/bash -lc 'HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/scripts/test_pre_commit_smart_checks_docs.py -q'
```

- Result: failed (`2 failed`)
- Failure summary:
  - `scripts/pre-commit-smart-checks.sh` did not run a markdown auto-fix stage before `markdownlint`.
  - The hook did not re-stage Markdown files after auto-fix changes.

## Post-implementation passing run: markdown auto-fix hook regression

- Timestamp: 2026-03-05
- Command:

```bash
/bin/bash -lc 'HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/scripts/test_pre_commit_smart_checks_docs.py -q'
```

- Result: passed (`2 passed`)
