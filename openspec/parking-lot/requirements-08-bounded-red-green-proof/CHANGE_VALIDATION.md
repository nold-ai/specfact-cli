# Change Validation

## Status

`PARKED / SUPERSEDED — DO NOT IMPLEMENT OR ARCHIVE`

Core issue #675 and paired modules issue #414 are closed as `not planned`.
Seal-bound risk/test intent and bounded implementation checkpoints in core
issues #682/#684 and modules #431/#434 replace the historical B/R/H/D replay
design.
No core or modules behavior implements this change.

## Parking evidence

- The complete change folder moved from `openspec/changes/` to
  `openspec/parking-lot/`; no file was moved under `openspec/changes/archive/`.
- `openspec/CHANGE_ORDER.md` classifies R08 as parked and superseded.
- `openspec/parking-lot/README.md` records the explicit un-park trigger.
- The sibling internal wiki records both public source paths as parked and its
  strict health check passes.
- Rollback is recoverable: move the unchanged folder back to
  `openspec/changes/` and revalidate it against current architecture. Do not use
  `openspec archive` unless the behavior is first implemented and verified.

## Local gate limitation

The 2026-08-29 core pre-commit deletion guard recognizes only complete native
archive moves. It rejects this complete parking-lot move as “not a complete
native archive move,” even though archiving is explicitly prohibited because it
would merge unimplemented delta specifications. The preflight planning subset
passed the full staged pre-commit pipeline separately, including Requirements
evidence; the parking commit therefore records this narrow, deterministic gate
exception rather than weakening the guard or widening a planning PR into a
tooling behavior change.

## Supersession record

- Core issue #675: closed `not planned` on 2026-08-29.
- Modules issue #414: closed `not planned` on 2026-08-29.
- Replacement planning: core #682/#684 and modules #431/#434.
- Historical proposal/design/spec/tasks are retained for traceability only.
