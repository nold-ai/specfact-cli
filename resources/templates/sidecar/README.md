# Sidecar Validation Templates

Purpose: Run validation tools against a target repository without modifying its source.

This template set is intended for Phase B validation and can be copied into a
separate sidecar workspace. Use `.specfact/projects/<bundle>/contracts/` as the
source of truth for API contracts (specmatic/OpenAPI).

## Quick Start

1. Copy this folder into a sidecar workspace, or run:

```bash
./sidecar-init.sh /path/to/sidecar /path/to/target/repo bundle-name
```

1. Export environment variables (or use the `.env` file created by `sidecar-init.sh`):

```bash
export REPO_PATH=/path/to/target/repo
export BUNDLE_NAME=bundle-name
export SEMGREP_CONFIG=/path/to/semgrep.yml   # optional
export REPO_PYTHONPATH="/path/to/target/repo/src:/path/to/target/repo"
export SIDECAR_SOURCE_DIRS="/path/to/target/repo/src"  # optional (defaults to src/)
export PYTHON_CMD=python3  # optional (auto-detects venv if .venv/ or venv/ exists)
export DJANGO_SETTINGS_MODULE=project.settings  # optional (auto-detected for Django projects)
export SPECMATIC_CMD=/path/to/specmatic  # optional (CLI binary, or: "npx --yes specmatic")
export SPECMATIC_JAR=/path/to/specmatic.jar  # optional (java -jar fallback)
export SPECMATIC_CONFIG=/path/to/specmatic.yaml  # optional config file
export SPECMATIC_TEST_BASE_URL=http://localhost:5000  # optional target
export SPECMATIC_HOST=localhost  # optional target host
export SPECMATIC_PORT=5000  # optional target port
export SPECMATIC_TIMEOUT=30  # optional request timeout (seconds)
export SPECMATIC_AUTO_STUB=1  # optional (default: 1) run stub when no target configured
export SPECMATIC_STUB_HOST=127.0.0.1  # optional stub host
export SPECMATIC_STUB_PORT=19000  # optional stub port
export SPECMATIC_STUB_WAIT=15  # optional stub startup wait (seconds)
export SIDECAR_APP_CMD="python -m your_app"  # optional app command to run
export SIDECAR_APP_HOST=127.0.0.1  # optional app host
export SIDECAR_APP_PORT=5000  # optional app port
export SIDECAR_APP_WAIT=15  # optional app startup wait (seconds)
export BINDINGS_PATH=/path/to/bindings.yaml  # optional bindings map
export FEATURES_DIR=/path/to/features  # optional features dir (FEATURE-*.yaml)
export CROSSHAIR_VERBOSE=1  # optional CrossHair debug output
export CROSSHAIR_REPORT_ALL=1  # optional report all postconditions
export CROSSHAIR_REPORT_VERBOSE=1  # optional report stack traces
export CROSSHAIR_MAX_UNINTERESTING_ITERATIONS=50  # optional iteration budget
export CROSSHAIR_PER_PATH_TIMEOUT=2  # optional per-path timeout
export CROSSHAIR_PER_CONDITION_TIMEOUT=10  # optional per-condition timeout
export CROSSHAIR_ANALYSIS_KIND=icontract  # optional kinds (comma-separated)
export CROSSHAIR_EXTRA_PLUGIN=/path/to/plugin.py  # optional extra plugins
export RUN_BASEDPYRIGHT=0  # optional toggle per tool (default: 0)
export TIMEOUT_BASEDPYRIGHT=30  # optional per-tool timeout
export GENERATE_HARNESS=1  # optional (default: 1)
export HARNESS_PATH=harness_contracts.py  # optional
export INPUTS_PATH=inputs.json  # optional
export SIDECAR_REPORTS_DIR=/path/to/repo/.specfact/projects/bundle/reports/sidecar  # optional
```

1. Run the sidecar script:

```bash
./run_sidecar.sh
```

## Refreshing the Sidecar Workspace

If you update templates (for example `adapters.py`, `run_sidecar.sh`, or the
harness generator), re-initialize the sidecar workspace so the new templates
are copied over:

```bash
./sidecar-init.sh /path/to/sidecar /path/to/target/repo bundle-name
```

Notes:

- This overwrites existing template files in the sidecar workspace.
- Preserve local changes (for example `bindings.yaml` or `.env`) before
  re-running if you have custom edits.
- Re-run `./run_sidecar.sh` with `GENERATE_HARNESS=1` if you want a fresh
  `harness_contracts.py` and `inputs.json` after template updates.

## Notes

- CrossHair requires contracts (icontract/PEP316/deal) or registered contracts.
  Use `harness_contracts.py` or `crosshair_plugin.py` to attach contracts
  externally without touching production code.

- **Dual CrossHair Analysis**: The sidecar runs CrossHair in two modes:
  1. **Source code analysis**: Analyzes source directories directly to catch existing decorators
     (beartype, icontract, PEP316, deal) already present in the codebase (e.g., SpecFact CLI dogfooding).
  2. **Harness analysis**: Analyzes generated harness files to catch contracts added externally
     for code without decorators (e.g., DjangoGoat, Flask, Requests).
  
  Both analyses are necessary for complete coverage:
  - **Case A**: Code with existing decorators → CrossHair analyzes source directly
  - **Case B**: Code without decorators → CrossHair analyzes harness with externally-added contracts
- Specmatic contracts are expected in:
  `<REPO_PATH>/.specfact/projects/<BUNDLE_NAME>/contracts/`
- If you only have the Python `specmatic` package installed, note it does not
  expose a CLI or module runner. Provide a CLI path (`SPECMATIC_CMD`), use `npx`,
  or supply a jar (`SPECMATIC_JAR`) to execute Specmatic in the sidecar.
- For contract tests that hit a running service, set `SPECMATIC_TEST_BASE_URL`
  (or `SPECMATIC_HOST`/`SPECMATIC_PORT`) so Specmatic knows where to send requests.
- If you don't have a target service, the sidecar can auto-start a Specmatic
  stub (`SPECMATIC_AUTO_STUB=1`) or launch a real service with `SIDECAR_APP_CMD`.
- All reports/logs should be written to SpecFact bundle reports, not into the
  target repo.

## CrossHair Defaults (Suggested)

These defaults provide stable results for most repositories; tune them if your
codebase is large or has heavy initialization.

```bash
export CROSSHAIR_ANALYSIS_KIND=icontract
export CROSSHAIR_PER_PATH_TIMEOUT=2
export CROSSHAIR_PER_CONDITION_TIMEOUT=10
export CROSSHAIR_MAX_UNINTERESTING_ITERATIONS=50
export CROSSHAIR_REPORT_ALL=1
export CROSSHAIR_REPORT_VERBOSE=0
```

## Tool Toggles & Timeouts

The sidecar runner supports basic toggles (set to `0` to skip):

- `RUN_SEMGREP`, `RUN_BASEDPYRIGHT`, `RUN_SPECMATIC`, `RUN_CROSSHAIR`
- `GENERATE_HARNESS` (generate `harness_contracts.py` and `inputs.json` from OpenAPI)

And per-tool timeouts in seconds:

- `TIMEOUT_SEMGREP`, `TIMEOUT_BASEDPYRIGHT`, `TIMEOUT_SPECMATIC`, `TIMEOUT_CROSSHAIR`

## Harness Generation

The harness is auto-generated from OpenAPI contracts in:
`<REPO_PATH>/.specfact/projects/<BUNDLE_NAME>/contracts/`

Generated outputs (in the sidecar workspace):

- `harness_contracts.py` (CrossHair harness)
- `inputs.json` (deterministic example requests/responses)
- `bindings.yaml` (optional mapping to real code)

Bindings let you attach harness functions to real code without editing the repo.
If `bindings.yaml` is present, the harness will call the bound function instead
of returning a fixed example.

Binding schema (minimal):

```yaml
bindings:
  - operation_id: create_item
    target: your_package.factory:ItemFactory
    method: create
    factory:
      args: ["$request.item_type"]
    call_style: kwargs
```

Optional keys:

- `adapter`: name of a function in `adapters.py` to handle complex setup.
- `factory.target`: alternate factory callable (module:func) to create instance.
- `factory.args` / `factory.kwargs`: supports `$request.<key>` or `$env.<VAR>` values.

Available adapters (see `adapters.py` for config fields):

- `call_method_with_factory`: construct instance then call method.
- `call_constructor_then_method`: construct instance via `init` and call method.
- `call_classmethod`: call a classmethod/staticmethod on a class target.
- `call_with_context_manager`: create resource in `with` block then call method.
- `call_async`: call async function and run the coroutine.
- `call_with_setup_teardown`: run setup/teardown around a target call.
- `call_with_request_transform`: rename/drop/set/coerce request fields before call.
- `call_generator`: consume a generator/iterator and return list/last/count.
- `call_from_registry`: resolve a callable from a registry/entrypoint map.
- `call_with_overrides`: temporarily override module attributes during a call.
- `call_with_contextvars`: set context variables for the call duration.
- `call_with_session`: create a session/transaction around the call.
- `call_with_callbacks`: inject callbacks into the request payload.

Logs are written to:

- `<REPO_PATH>/.specfact/projects/<BUNDLE_NAME>/reports/sidecar/`
