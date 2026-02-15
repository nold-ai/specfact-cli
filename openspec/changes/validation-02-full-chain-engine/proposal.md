# Change: Full-Chain Validation Engine

## Why




Validation today operates only at the spec-code level (`specfact validate` checks spec deltas and contract enforcement). There is no way to validate the entire chain from business requirements through architecture to code and tests. This means a project can pass all technical validations while building entirely the wrong thing. A `--full-chain` validation mode that checks every layer transition — Req → Arch → Spec → Code → Tests — and reports gaps, orphans, and coverage metrics, unlocks the core value proposition: end-to-end traceability with actionable evidence.

## Module Package Structure

```
modules/validate/
  # Extends existing validate module — no new module directory
  src/validate/
    engine/
      full_chain.py            # Full-chain validation orchestrator
      layer_transitions.py     # Per-transition validation rules (req→arch, arch→spec, etc.)
      coverage_calculator.py   # Compute coverage percentages per layer
      evidence_writer.py       # Write machine-readable evidence JSON
    models/
      chain_report.py          # FullChainReport, LayerTransitionResult, CoverageMetrics
```

## Module Package Structure

```
modules/validate/
  # Extends existing validate module — no new module directory
  src/validate/
    engine/
      full_chain.py            # Full-chain validation orchestrator
      layer_transitions.py     # Per-transition validation rules (req→arch, arch→spec, etc.)
      coverage_calculator.py   # Compute coverage percentages per layer
      evidence_writer.py       # Write machine-readable evidence JSON
    models/
      chain_report.py          # FullChainReport, LayerTransitionResult, CoverageMetrics
```

## What Changes




- **EXTEND**: `specfact validate` extended with `--full-chain` flag that runs validation across all layer transitions:
  - Req → Arch: Every business rule mapped to component; every architectural constraint has ADR
  - Arch → Spec: Every component has OpenAPI/AsyncAPI spec
  - Spec → Code: Existing spec-delta validation (unchanged)
  - Code → Tests: Contract coverage, test existence checks
  - Orphan detection: Specs with no requirement, code with no spec
- **NEW**: Full-chain validation orchestrator in `modules/validate/src/validate/engine/full_chain.py` — runs all layer transition checks, aggregates results, computes coverage metrics
- **NEW**: Layer transition rules with profile-dependent severity: solo gets advisory-only, enterprise gets hard-fail with evidence
- **NEW**: Machine-readable evidence output (JSON) for CI gates:
  ```json
  {
    "schema_version": "1.0",
    "timestamp": "...",
    "profile": "enterprise",
    "layers": {
      "req_to_arch": { "pass": 12, "fail": 2, "advisory": 1 },
      "arch_to_spec": { "pass": 8, "fail": 0, "advisory": 3 },
      "spec_to_code": { "pass": 47, "fail": 0 },
      "orphans": { "specs_without_req": ["GET /legacy/endpoint"] }
    },
    "policy_mode": "hard",
    "overall": "PASS_WITH_ADVISORY"
  }
  ```
- **NEW**: `--evidence-dir .specfact/evidence/` flag for persisting validation evidence artifacts
- **EXTEND**: Policy engine integration — layer transition severities configurable via policy-engine-01 policy rules

## Capabilities
### New Capabilities

- `full-chain-validation`: End-to-end validation across all traceability layers (Req → Arch → Spec → Code → Tests) with profile-dependent severity, orphan detection, coverage metrics, and machine-readable evidence output for CI gates.

### Modified Capabilities

- `sidecar-validation`: Extended with `--full-chain` flag; existing spec-delta validation preserved as-is when flag is omitted


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #241
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/241>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: a3883e07d01faefe -->