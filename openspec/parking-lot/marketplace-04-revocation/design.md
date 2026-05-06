# Design: Publisher and Module Revocation Infrastructure

## Context

After marketplace-03 introduces publisher attestation, the first external publisher could theoretically be onboarded. However, without revocation infrastructure, a key compromise or policy violation has no response mechanism. This change closes that gap.

**Current State:**

- No revocation mechanism exists in any form
- Revoked publishers/modules cannot be prevented from installing
- No automated scan of bundle contents on publication

**Constraints:**

- Revocation check must be fast: single HTTP fetch + signature verify, cached (1h TTL for revocation vs 7d for publisher index)
- Grace window logic must be centralized in `trust/revocation.py` — no per-module special cases
- Hard blocks (security_incident, expiry after window) must not be bypassable by user-facing flags
- AST scan must run as part of `scripts/publish-module.py` invocation — no separate opt-in

## Goals / Non-Goals

**Goals:**

- Publisher revocation: signed `publishers/revoked.json` fetched and enforced by CLI
- Module revocation: per-module revocation records enforced at install and on invocation
- Grace window enforcement by reason type (immediate / 30d / 14d / 7d)
- CI AST scan on bundle publication
- Policy document for users and publishers

**Non-Goals:**

- Automatic module uninstall on revocation (warn-only for installed modules; user controls uninstall)
- Real-time revocation push/webhooks (polling cache is sufficient for Phase 1)
- OCSP-style stapling (over-engineered for current scale)

## Architecture

### Revocation Checker (`src/specfact_cli/trust/revocation.py`)

```python
# Key public API
def check_publisher_revocation(publisher_id: str, revoked: PublisherRevocationIndex) -> RevocationStatus
def check_module_revocation(module_name: str, version: str, revoked: ModuleRevocationIndex) -> RevocationStatus
def enforce_revocation_policy(status: RevocationStatus, flags: RevocationFlags) -> RevocationDecision
def fetch_revocation_indexes(trust_index_url: str, cache_dir: Path) -> tuple[PublisherRevocationIndex, ModuleRevocationIndex]
```

### Grace Window Policy

Centralized constant mapping in `revocation.py`:

```python
GRACE_WINDOWS: dict[str, GraceWindowPolicy] = {
    "security_incident": GraceWindowPolicy(grace_days=0, install_action="hard_block", existing_action="warn"),
    "policy_violation": GraceWindowPolicy(grace_days=30, install_action="warn", existing_action="warn", post_expiry="hard_block"),
    "publisher_request": GraceWindowPolicy(grace_days=7, install_action="warn", existing_action="warn_soft"),
    "api_incompatibility": GraceWindowPolicy(grace_days=14, install_action="warn_suggest_newer", existing_action="warn_suggest_newer"),
}
```

### Install Flow with Revocation

```text
specfact module install @mycompany/specfact-jira-sync
  │
  ├─ [marketplace-03] trust/publisher_registry: resolve publisher
  ├─ trust/revocation: fetch revocation indexes (1h cache)
  ├─ check_publisher_revocation(publisher_id)
  │   ├─ NOT revoked → continue
  │   └─ REVOKED: reason=security_incident → hard_block (no override)
  │              reason=policy_violation, in window → warn + prompt
  │              reason=policy_violation, past window → hard_block
  ├─ check_module_revocation(name, version)
  │   └─ similar grace window enforcement
  └─ proceed with trust tier resolution (marketplace-03)
```

### Invocation Warning for Installed Revoked Modules

On any `specfact module <command>` invocation, the module_registry checks the revocation index for all loaded modules and surfaces warnings:

```text
⚠ WARNING: specfact-jira-sync@1.0.0 has been revoked (security_incident).
  Reason: Remote code execution vulnerability — update or uninstall immediately.
  Run: specfact module update specfact-jira-sync
       specfact module uninstall specfact-jira-sync
```

This check is non-blocking (warn-only) for installed modules to prevent breaking existing workflows.

### CI AST Scan (`.github/workflows/scan-bundles.yml`)

Triggered by: `push` events to `specfact-cli-modules` (or as pre-publication step in `publish-module.py`).

Checks (all via stdlib `ast` module — no external dependencies):

1. Obfuscated/minified code: detect single-character variable names at module level or `exec(base64.b64decode(...))` patterns
2. `subprocess.run(..., shell=True)` combined with external URL strings
3. Network calls on import: `socket`, `urllib`, `requests` calls at module top level (not inside functions)
4. Known-bad patterns: `eval(`, `exec(` applied to remote strings

Failed scans create a GitHub issue in `nold-ai/specfact-cli-internal` (internal) and block the publication PR.

## Decisions

### Decision 1: Revocation Cache TTL

**Choice**: 1 hour TTL (vs 7 days for publisher index)

**Rationale:**

- Revocation is time-sensitive (especially security_incident: 0-day grace)
- 1h allows near-real-time propagation via CDN with short TTL
- Offline: serve stale with warning (same pattern as publisher index)

### Decision 2: Hard Block Bypassability

**Choice**: `security_incident` revocations are NEVER bypassable by user flags.

**Rationale:**

- A security incident with 0-day grace means immediate hard block is the point — no flag override defeats this
- Other reason codes respect `--force` for emergency internal use (internal flag, not user-facing)

### Decision 3: AST Scan Scope

**Choice**: Stdlib `ast` only, no external analysis tools.

**Rationale:**

- Offline-first: no network call during scan
- No additional CI dependencies
- Covers the highest-risk patterns (remote code exec, obfuscation) adequately for Phase 1
