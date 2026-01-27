# Change: Fix Code Scanning Vulnerabilities

## Why

GitHub Code Scanning identified 13 security vulnerabilities in the public `specfact-cli` repository that need to be mitigated to improve code security and follow best practices. These findings include 1 critical ReDoS vulnerability, 5 URL sanitization issues, and 7 missing workflow permissions that violate security best practices.

## What Changes

- **MODIFY**: Fix ReDoS vulnerability in `src/specfact_cli/backlog/mappers/github_mapper.py` by replacing regex-based section removal with line-by-line processing to avoid exponential backtracking
- **MODIFY**: Fix incomplete URL sanitization in `src/specfact_cli/adapters/github.py` by replacing substring matching with proper URL parsing using `urllib.parse.urlparse()`
- **MODIFY**: Fix incomplete URL sanitization in `src/specfact_cli/sync/bridge_sync.py` (3 instances) by replacing substring matching with proper URL parsing
- **MODIFY**: Fix incomplete URL sanitization in `src/specfact_cli/adapters/ado.py` by replacing substring matching with proper URL parsing
- **MODIFY**: Add explicit `permissions: contents: read` blocks to 7 GitHub Actions jobs in `.github/workflows/pr-orchestrator.yml` to follow least-privilege security model

## Impact

- Affected specs: None (code quality improvements, no spec changes)
- Affected code: 
  - `src/specfact_cli/backlog/mappers/github_mapper.py`
  - `src/specfact_cli/adapters/github.py`
  - `src/specfact_cli/sync/bridge_sync.py`
  - `src/specfact_cli/adapters/ado.py`
  - `.github/workflows/pr-orchestrator.yml`
- Integration points: No breaking changes, all fixes maintain backward compatibility

## Source Tracking

- **GitHub Issue**: #147
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/147>
- **Repository**: nold-ai/specfact-cli
- **Source**: GitHub Code Scanning (13 open findings)
- **Last Synced Status**: proposed
