# Change Validation: Planning Correction

## Status

`PLANNED — IMPLEMENTATION EVIDENCE NOT YET AVAILABLE`

This branch changes OpenSpec planning artifacts only. It deliberately does not claim that the corrected R07 behavior is implemented or verified.

## Validated planning boundaries

- R07 owns current-run exact-selector planning, execution, JUnit reconciliation, publication, and independent review handoff.
- R08 owns bounded historical red-to-green replay.
- Static inference of complete Python/pytest execution inputs is out of scope.
- The modules report must separate current execution from historical chronology before core implementation begins.

## Blockers before implementation can pass

1. The paired modules planning change must be implemented and released as a signed immutable fixture.
2. Corrected failing tests must be recorded before production changes.
3. Core must consume the signed module report without restoring legacy-ledger or static dependency-closure behavior.
4. Full PR scope and all mandatory tools must resolve; unresolved evidence is not pass.

Historical green reports and the existing TDD ledger predate this correction and are not evidence that the corrected contract is satisfied.

