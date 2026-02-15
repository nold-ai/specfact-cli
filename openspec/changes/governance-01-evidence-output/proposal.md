# Change: Evidence & Audit Output for CI/CD Pipelines

## Why




Enterprise environments require machine-readable evidence that policies were enforced, traceability exists, and exceptions are tracked. Current validation output is human-readable (Markdown/terminal) but not suitable for CI gates, audit systems, or compliance dashboards. A standardized evidence JSON output format — covering policy results, traceability coverage, exception status, and timestamps — makes SpecFact validation results consumable by any CI/CD pipeline, audit tool, or governance platform.

## What Changes




- **NEW**: Evidence writer producing standardized JSON artifacts:
  ```json
  {
    "schema_version": "1.0",
    "run_id": "uuid",
    "timestamp": "ISO-8601",
    "profile": "enterprise",
    "policy_mode": "hard",
    "validation_results": {
      "full_chain": { "pass": 67, "fail": 2, "advisory": 5 },
      "layers": { ... },
      "orphans": { ... }
    },
    "coverage": {
      "req_to_arch": "92%",
      "arch_to_spec": "100%",
      "spec_to_code": "100%",
      "code_to_test": "87%"
    },
    "exceptions": [
      { "id": "EXC-001", "policy": "...", "expires": "2026-12-31", "status": "active" }
    ],
    "overall_verdict": "PASS_WITH_ADVISORY",
    "ci_exit_code": 0
  }
  ```
- **NEW**: `--evidence-dir .specfact/evidence/` flag on `specfact validate --full-chain` to persist evidence artifacts per run
- **NEW**: `--ci-mode` flag that sets exit codes based on profile enforcement mode: advisory=always 0, mixed=1 for hard-fail rules only, hard=1 for any failure
- **NEW**: Evidence artifact naming: `{timestamp}_{run_id}_evidence.json` for audit trail
- **NEW**: Evidence summary on terminal: human-readable table alongside JSON output
- **EXTEND**: Full-chain validation (validation-02) extended to produce evidence artifacts
- **EXTEND**: Policy engine results formatted as evidence-compatible structures
- **NEW**: Ownership authority — this change is authoritative for evidence JSON envelope/schema; sibling governance changes may add fields only through this envelope contract.

## Capabilities
### New Capabilities

- `governance-evidence-output`: Machine-readable JSON evidence artifacts for CI/CD gates and audit systems, with per-run persistence, CI exit code modes, coverage percentages, exception status, and profile-aware verdicts.

### Modified Capabilities

- `full-chain-validation`: Extended with evidence artifact generation via `--evidence-dir` and `--ci-mode` flags
- `policy-engine`: Results formatted as evidence-compatible structures with run_id and timestamps


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #247
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/247>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 9649f1326a1cc34c -->