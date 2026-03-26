# TDD evidence — docs-12-docs-validation-ci

## Pre-implementation (failing / N/A)

- Command/link validation did not exist; no prior automated test for `check-docs-commands.py` behavior.
- Timestamp: 2026-03-26 (session).

## Post-implementation

- `hatch run pytest tests/unit/docs/test_docs_validation_scripts.py -v` — passing (parser + URL extraction).
- `hatch run pytest tests/unit/docs/ -q` — 29 passed, 1 skipped (opt-in handoff URL test).
- `hatch run check-docs-commands` — exit 0 (92 unique command prefixes checked).
- `hatch run docs-validate` — exit 0 (commands strict; cross-site `--warn-only`).

## Notes

- Live `modules.specfact.io` URLs may 404 until deploys; cross-site link step is warn-only in CI and in `docs-validate` aggregate.
- Set `SPECFACT_RUN_HANDOFF_URL_CHECK=1` to run the handoff map HTTP test locally or in a scheduled job.
