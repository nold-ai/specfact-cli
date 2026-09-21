# Design: Reviewed compatible dependency consolidation

## Context and decision

Keep this change as one maintenance proposal and one future implementation scope. Reuse `uv`, the scheduled compatibility lane, `scripts/refresh_reproducible_delivery.py`, the repository vulnerability gate, dependency-trust policy, and required Socket checks. Discovery remains advisory; release validation uses committed frozen inputs.

The inventory distinguishes baseline versions, unrestricted resolver suggestions, policy-bounded candidates, and latest registry releases. A candidate is never described as safe merely because resolution or a vulnerability query succeeded. Security results are scoped to their timestamp, graph, package version, artifact, service, and coverage.

## Discovery and candidate selection

1. Refresh source PR state, advisory state, and current dev identity. Preserve current declaration, primary lock/export, isolated requirements input/lock, tool-floor, and exception hashes.
2. Enumerate runtime, build backend, every extra, every Hatch environment, isolated Code Review requirements, and all transitive records, including marker-specific versions. Reconcile setup.py runtime declarations and module manifests if implicated; do not mutate external module sources.
3. Resolve latest packages in a disposable directory. Never alter the working proposal's authoritative lock. Exact pins receive a separate registry check. Include removed and new transitives in the diff.
4. Constrain the candidate graph to existing supported major lines; defer migrations even where loose declarations permit them. Keep provenance-sensitive pycparser at 2.22 until fresh review. Treat zero-major updates as potentially breaking and inspect upstream notes.
5. Enumerate every intervening stable release between baseline and candidate. Record release-note review and primary sources for compatibility, deprecations, Python requirements, licensing, and security changes. Enumeration is not review; pending reviews remain explicit blockers to promotion.

### Metadata-only boundary

Do not install, import, or execute a new candidate to discover whether it is trustworthy. Query registry/advisory metadata and inspect archives as data first. Source-only packages may require reading static metadata from a hash-verified archive; never run unreviewed setup/build hooks. The initial assessment supplies statically inspected metadata for unchanged commentjson 0.9.0 and lark-parser 0.7.8 in the disposable resolver only. No metadata override enters delivery inputs.

The permanent refresh uses the normal reviewed resolver after screening. Its graph must match the approved package/artifact inventory; any new transitive, version, marker branch, or artifact reopens screening. An unresolved source-metadata or registry failure produces `unverified`, not an implicit approval or a resolver fallback.

## Security acceptance

Audit the baseline and candidate primary graphs and the isolated Code Review graphs separately. Use the existing fail-closed gate plus explicit package/version advisory queries to cover marker branches not selected by the host. Retain CVE/GHSA/OSV IDs, affected and fixed ranges, transitive paths, primary references, withdrawal state, timestamps, and coverage gaps. Reconcile conflicts against upstream notices before deciding.

Independently check Socket and available upstream/package-registry malicious-release reports. Read check output and graph identity: a green status whose payload says skipped or no dependency changes cannot approve an artifact. Review suspicious ownership/provenance changes, unexpected executable payloads, obfuscation, newly introduced dependencies, and exact distribution identities. Hashes establish identity, not absence of malware.

Confirmed malicious or explicitly denied releases are rejected without exceptions. Unresolved malware signals, unavailable scans, or missing artifact evidence defer adoption. CVE exceptions retain existing exact package/version/advisory, mitigation, and expiry requirements and cannot replace an available compatible fix. Do not broaden deny rules, remove floors, or renew exceptions solely to make a candidate pass.

Security approval precedes candidate installation. Compatibility approval follows tests. Before merge, rerun audits on the final committed graph; before release, refresh when package identities or advisory information change. A changed graph invalidates the earlier approval for the changed packages and their affected paths.

## Frozen inputs and compatibility

Update both Hatchling pins and the existing build-backend regression expectation together. Regenerate `uv.lock` and its hash-protected all-extras CI export through existing tooling; refresh the isolated Code Review lock with its exact-input hash separately. Keep setup.py, optional extras, and Hatch/test declarations aligned when changing their corresponding requirements. Retain established runtime minima unless a demonstrated security or compatibility need justifies raising them.

Exercise latest and lowest-direct graphs in separate disposable environments on Python 3.11, 3.12, and 3.13; invoke pytest through the environment actually synchronized by uv. Keep these investigations separate from frozen release evidence. Verify minimal runtime and each relevant extra, built-wheel metadata and installation, pip/pipx/uv paths, contract tooling, scanner/tool pairs, and module discovery. Any new behavior fix follows spec -> tests -> failing evidence -> code -> passing evidence.

For docs, evaluate JSON 2.x within the existing Jekyll graph, retain Jekyll 4.4.1 or a separately approved compatible successor, and disallow the PR #727 downgrade. Audit and build the Ruby graph if changed. No broad npm/action/tool-runtime upgrade is implied; verify existing pinned delivery tools still work.

## Evidence, failure handling, and rollout

`DEPENDENCY_AUDIT.md` is the human summary; `dependency-inventory.json` carries complete package-level metadata, source identities, declarations, paths, dispositions, and coverage. They are dated planning snapshots, not reusable allowlists. Planned Requirements inspection mappings describe future acceptance without claiming tests executed.

Main failure modes are (1) resolver success despite runtime breakage, mitigated by supported-Python/profile tests; (2) vulnerability-negative but malicious artifacts, mitigated by independent malware/provenance review before execution; and (3) declaration/lock/policy drift, mitigated by coherent regeneration and exact identity checks. Registry outages and missing scans retain a blocked/unverified disposition.

The proposal is independently mergeable and unstarted. Implementation selects the next valid patch version, validates signed-module/core compatibility against that resulting version, and ships through normal dev-to-main promotion. Revalidate affected proof if the release identity changes. Preserve existing failures separately; do not waive gates or alter unrelated work to obtain green checks. Close superseded bot PRs only once their replacement has merged. Archive through the OpenSpec CLI after the implementation is complete.
