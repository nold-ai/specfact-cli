# Change Validation: validation-02-full-chain-engine

- **Historical validation snapshot (UTC):** 2026-03-22T22:28:26+00:00
- **Workflow:** /wf-validate-change (proposal-stage dry-run validation)
- **Strict command:** `openspec validate validation-02-full-chain-engine --strict`
- **Result:** PASS

## Scope Summary

- **Primary capability:** `full-chain-validation`
- **Clean-code delta:** add optional `--with-code-quality` side-channel reporting without turning clean-code into a traceability layer
- **Declared dependencies:** governance evidence envelope; policy/profile severity consumers

## Breaking-Change Analysis (Dry-Run)

- The delta preserves the existing Req → Arch → Spec → Code → Tests layer model.
- The optional side-channel adds evidence only and does not change baseline full-chain behavior.

## Dependency and Integration Review

- Validation ownership remains separate from governance envelope ownership.
- No scope expansion was needed beyond the optional review side-channel.

## Validation Outcome

- Required artifacts are present and parseable.
- Strict OpenSpec validation passed.
- Change is ready to consume clean-code review output as a parallel quality dimension.

## Current planning amendment — 2026-09-20

The normative deltas now preserve independent current execution, optional chronology, unassessed coverage and original producer verdicts. This is planning-only; no runtime readiness follows from the historical snapshot above. Strict OpenSpec and scoped Markdown/whitespace checks passed for this amendment. Serialization uses distinct ADDED requirements rather than replacing producer-owned Full Chain Validation or Policy Engine, so archival cannot delete those owners' scenarios or require an absent target requirement. Core retains the envelope contract; modules retains emission and file persistence. The earlier broad dependency observations are historical, not new blockers on R09 or workflow adoption.

The sidecar extension also uses a distinct ADDED requirement, preserving existing spec-code behavior without replacing an absent generic Sidecar Validation header. Strict validation reports no archive incompatibility for these two amended changes.
