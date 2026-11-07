## Why

The owner authorized focused native Semgrep migration preparation on 5 November 2026. The selected Python Semgrep package requires MCP and OpenTelemetry versions whose original risk windows expired. Native Semgrep retains the tested constant-propagation finding without starting the Python CLI.

## What Changes

Migrate existing scanner callers to the unmodified upstream `osemgrep scan --experimental` executable. Remove the Python Semgrep dependency only from inputs whose migrated tool installation can supply the reviewed native executable. Preserve logical Semgrep findings, rule bytes, result consumers, timeouts and fail-closed delivery gates. Existing CI must capture JSON stdout because native `--output` does not create the requested file.

## Capabilities

### New Capabilities

- `native-semgrep-cli`: native executable discovery and scanning without the Python CLI dependency.

## Impact

Paired core and official code-review module preparation. No signature, module adoption, CI dispatch, exception renewal, protected authority, release or merge is granted. Original M69 and consumed proof/signing runs remain immutable. Official module main 209b4ed8 is not adopted because its sealed toolchain retains vulnerable dependencies. Parser 3.11 remains provisional pending fresh supply-chain classification and compatibility. User-facing installation guidance and existing scan commands must be updated before finalization. Rollback during preparation is the isolated branch; no public PR head changes occur.

## Approved project callers

On 6 November 2026 the owner explicitly included the two reachable project scanner owners, their existing manifest and required tests. They retain command lists, copied environment mappings and existing JSON result consumers. No shared launcher, new public API or additional runtime/admission behavior is introduced. Original project version/signatures remain unfinalized until the existing legitimate CI workflow can produce them.

## Existing provider and license boundary

Retain the existing isolated Pylint and npm BasedPyright providers while removing conflicting pip declarations from code-review. Preserve both logical tools and their existing runners. Populate the existing canonical companion Python license map from exact package metadata. Keep native binary attribution and future CI coverage as separate delivery checks. No new provider, exception, framework or installation API is introduced.

## Approved Codebase repro owner

On 6 November 2026 the owner explicitly included the existing Codebase repro validator, direct certifi manifest declaration and one focused test file. Preserve this scanner's managed prefix, optional status, timeout, autofix behavior and logical Semgrep findings. Correct the migrated core missing-tool report at its existing executable boundary. The existing environment probe retains its public signature and logical tool names. Native probing supplies native argv and child-local CA/private-library inputs; it does not alias Python Semgrep. Other module owners remain outside this preparation scope.

## Native Hatch CA ownership

Use immutable, byte-exact selected certifi data and its notice for existing native Hatch commands. A bounded data-only preflight checks the default before direct native execution. Existing explicit SSL_CERT_FILE values stay authoritative, and other commands retain their environment. Exact-path Git attributes prevent byte conversion. This adds no launcher, helper alias, private environment marker, plugin, writable CA cache or new runtime API. Windows native execution and complete bootstrap remain delivery checks.
