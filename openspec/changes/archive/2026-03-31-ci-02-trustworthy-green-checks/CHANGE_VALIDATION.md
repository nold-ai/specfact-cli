# Change Validation: ci-02-trustworthy-green-checks

- **Validated on (UTC+02:00):** 2026-03-30T01:41:57+02:00
- **Workflow:** /wf-validate-change (proposal-stage dry-run validation)
- **Strict command:** `openspec validate ci-02-trustworthy-green-checks --strict`
- **Result:** PASS

## Scope Summary

- **Primary capability:** `trustworthy-green-checks`
- **Focus:** make required CI/review/hook signals explicitly blocking, preserve advisory signals as advisory, and close release-PR and workflow-validation blind spots
- **Declared dependencies:** `ci-01-pr-orchestrator-log-artifacts`; `code-review-08-review-run-integration`

## Breaking-Change Analysis (Dry-Run)

- No production CLI or runtime API change is proposed.
- The expected behavior change is governance-only: some currently green-but-advisory checks may become blocking once implemented.
- Release PRs may run more validation than they do today if parity cannot be proven safely.

## Dependency and Integration Review

- The change stays within CI/review/hook ownership and does not reassign docs-review ownership.
- CodeRabbit remains advisory; the proposal standardizes branch-target coverage rather than turning review findings into a hard merge gate by itself.
- The change is compatible with existing docs-review and SpecFact validation workflows.

## Validation Outcome

- Required artifacts are present and parseable.
- Strict OpenSpec validation passed.
- The change is appropriately scoped as a proposal-stage CI/review hardening effort.
