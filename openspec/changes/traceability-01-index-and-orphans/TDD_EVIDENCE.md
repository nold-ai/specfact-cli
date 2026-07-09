# TDD Evidence: traceability-01-index-and-orphans

- Failing-before: `hatch run pytest tests/unit/traceability/test_evidence_traceability.py -q` — 2026-07-09 Europe/Berlin; failed during collection because `specfact_cli.traceability` did not exist.
- Passing-after: `hatch run pytest tests/unit/traceability/test_evidence_traceability.py -q` — 2026-07-09 Europe/Berlin; 3 passed.
- Failing-before generic-index expansion: `hatch run pytest tests/unit/traceability/test_artifact_index.py -q` — 2026-07-09 Europe/Berlin; failed during collection because the generic index contracts did not exist.
- Passing-after generic-index expansion: `hatch run pytest tests/unit/traceability -q` — 2026-07-09 Europe/Berlin; 7 passed after aligning the compatibility assertion to the generic finding taxonomy.
