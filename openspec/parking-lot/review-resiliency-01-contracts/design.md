# Design: review-resiliency-01-contracts

## Architecture

Follows existing code-review pattern:

```text
specfact review resiliency <paths>
        │
        ▼
[ResiliencyRunner] (bundle-owned, modules repo)
        │
        ▼ emits → ResiliencyFinding[]
        │
[ResiliencyScorer] (core-owned, this change)
        │
        ▼ → ResiliencyReport (shared review-report-model envelope)
        │
        ├── stdout/markdown/json export
        ├── exit code (profile enforcement mode)
        └── evidence append (knowledge-01 schema, optional)
```

## Finding model

```python
class ResiliencyFinding(BaseModel):
    rule_id: str          # RES-RETRY-001, RES-TIMEOUT-003, etc.
    category: Literal[
        "retry-policy", "timeout-budget", "idempotency",
        "backpressure", "circuit-breaker", "graceful-degradation",
        "load-profile", "failure-mode", "capacity-plan",
    ]
    severity: Literal["blocker", "high", "medium", "low", "info"]
    location: CodeLocation
    message: str
    remediation: str | None
    evidence_ref: str | None   # knowledge-01 fingerprint when emitted
```

Rule-id convention: `RES-<CATEGORY>-<NNN>`; numbering reserved per category band. Rules are registered in `src/specfact_cli/reviews/resiliency/rules.py` (core-owned table mapping rule-id → category + severity default).

## Scorer

Deterministic: for a given finding, severity is fixed by rule-id × profile overrides. Scorer aggregates per category and emits a single `resiliency` block into the review-report envelope. Pass/fail verdict follows `policy-02-packs-and-modes`: advisory = always pass; mixed = fail on blocker; hard = fail on high+.

## Shared `ReviewReport` envelope checkpoint (before rollout)

Before enabling default emission of the **`resiliency`** pillar in bundled modules:

1. **Extend and validate** the shared **`ReviewReport`** schema so parsers accept a top-level **`resiliency`** object
   with the fields referenced by this design (finding list, summary, optional evidence refs).
2. **Bump `schema_version`** (or agreed semantic version field on `review-report-model`) with a documented migration
   matrix: additive vs breaking changes.
3. **Add unit and integration schema-validation tests** that load golden JSON fixtures with and without `resiliency`.
4. **Coordinate modules** that produce or consume **`resiliency`** alongside **`policy-02-packs-and-modes`** enforcement
   so JSON contract drift does not break cross-repo consumers.

## CLI contract

```text
specfact review resiliency [PATHS...]
  --report {json,markdown}   default: markdown on tty, json otherwise
  --severity-threshold LEVEL exit code 1 only if finding ≥ threshold
  --evidence / --no-evidence toggle evidence emission (default: auto if knowledge module present)
  --profile NAME             override active profile for this run
```

Exit codes:

- `0` — no findings ≥ enforced severity
- `1` — findings ≥ enforced severity
- `2` — configuration / runner error (no findings produced)

## Non-goals

- Runtime telemetry / APM — resiliency is static review only.
- Load-profile probes (live chaos/load testing) — optional, bundle-owned follow-up.
- Incident-response automation — out of scope.

## Alternatives considered

1. **Fold into code-review**: rejected. Resiliency is a distinct reviewer with its own rule catalogue and scoring band; colocation would muddle severity calibration.
2. **Only rule-ids, no categories**: rejected. Categories drive dashboard grouping and evidence tagging for distillation.

## Risks

- Rule catalogue breadth can explode. Mitigated by registering rules in a versioned table with ownership per category.
- False positives in async-heavy code. Mitigated by severity band tuning + `--severity-threshold` escape hatch.
