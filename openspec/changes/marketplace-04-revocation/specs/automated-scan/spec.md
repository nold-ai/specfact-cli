# automated-scan Specification

## Purpose

Defines the CI AST-based scan of published module bundles for high-risk patterns. Runs as part of `scripts/publish-module.py` and as a standalone GitHub Actions workflow.

## ADDED Requirements

### Requirement: Block publication on obfuscated code detection

The scan system SHALL detect and block publication of bundles containing obfuscated code patterns using stdlib `ast` analysis.

#### Scenario: Obfuscated code detected

- **GIVEN** a bundle contains `exec(base64.b64decode(...))` or single-char variable names at module level (≥ 80% of top-level assignments)
- **WHEN** `scripts/publish-module.py` is run
- **THEN** SHALL abort publication with `[ERROR] Obfuscated code pattern detected in <file>. Publication blocked.`
- **AND** SHALL create a GitHub issue in `nold-ai/specfact-cli-internal` with file path and line

### Requirement: Block publication on shell=True + external URL pattern

The scan system SHALL detect and block `subprocess.run(shell=True)` combined with external URLs in the same file.

#### Scenario: subprocess with shell=True and external URL

- **GIVEN** a bundle file contains `subprocess.run(..., shell=True)` or `subprocess.Popen(..., shell=True)` AND the same file contains a string literal matching an HTTP/HTTPS URL
- **WHEN** `scripts/publish-module.py` is run
- **THEN** SHALL abort publication with `[ERROR] Suspicious subprocess(shell=True) + URL pattern in <file>. Manual review required.`
- **AND** SHALL create a security issue in `nold-ai/specfact-cli-internal`

### Requirement: Warn on network calls at module import scope

The scan system SHALL warn (not hard-block) on network API calls that appear at module top level rather than inside functions.

#### Scenario: Network call at top-level (not inside a function)

- **GIVEN** a bundle file contains `socket.connect()`, `urllib.request.urlopen()`, or `requests.get()` at module top level (not inside `def`, `class`, `if __name__`, etc.)
- **WHEN** `scripts/publish-module.py` is run
- **THEN** SHALL warn: `[WARN] Network call at module import scope in <file>:<line>. Review before publication.`
- **AND** SHALL NOT hard-block (warn only — e.g. health check on import is legitimate in some contexts)
- **AND** SHALL require explicit `--allow-import-network` flag to proceed

### Requirement: Block on eval/exec applied to remote strings

The scan system SHALL detect and block `eval()` or `exec()` applied to variables assigned from network responses.

#### Scenario: eval or exec on remote string

- **GIVEN** a bundle file contains `eval(<variable>)` or `exec(<variable>)` where `<variable>` is assigned from a network response (urllib, requests, socket read)
- **WHEN** `scripts/publish-module.py` is run
- **THEN** SHALL abort publication with `[ERROR] eval/exec on remote data in <file>. Publication blocked.`

### Requirement: CI scan runs as GitHub Actions workflow

The AST scan SHALL run automatically in CI on every bundle-modifying PR.

#### Scenario: Scan on PR to specfact-cli-modules

- **GIVEN** `.github/workflows/scan-bundles.yml` is configured
- **WHEN** a PR is opened against `specfact-cli-modules` that modifies any `*.py` file in a bundle
- **THEN** GitHub Actions SHALL run the AST scan
- **AND** SHALL fail the PR check if any hard-block pattern is detected
- **AND** SHALL annotate the PR with file path and line for each finding

## Contract Requirements

- `scan_bundle(bundle_path: Path) -> ScanReport` — `@require` bundle_path is an existing directory; `@ensure` result.findings is a list; `@beartype`
- `ScanReport.has_blocking_findings() -> bool` — `@ensure` result is True iff any finding has `severity == "block"`; `@beartype`
