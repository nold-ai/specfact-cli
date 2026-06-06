## Why

A socket.dev attribution audit revealed two wrong packages and several GPL-licensed dependencies in specfact-cli's dependency tree. **specfact-cli is licensed Apache-2.0. (A)GPL licenses are incompatible with Apache-2.0 and directly block any future enterprise/commercial licensing.** GPL-licensed packages in any distributed extra — not just the base install — constitute a license violation that can prevent enterprise adoption. Two packages are also outright wrong: `syft` (PyPI) is OpenMined's federated ML framework, not the Anchore SBOM tool its comment describes; `bearer` (PyPI) is a SaaS HTTP auth client, not a security scanner. This change removes all wrong packages, eliminates the GPL breach in distributed extras, and establishes a forward-looking policy for enterprise license cleanliness.

## What Changes

License compliance — Phase 1 (this change, blocking):

- **Remove** `pyan3` (GPL-2.0) from `dev` and `enhanced-analysis` extras — GPL is incompatible with Apache-2.0; directly blocks enterprise/commercial licensing. Replace with `pycg>=0.0.7` (MIT).

Wrong packages — removal:

- **Remove** `syft` from `enhanced-analysis` extra — wrong package (OpenMined ML ≠ Anchore SBOM tool).
- **Remove** `bearer` from `dev` and `enhanced-analysis` extras — wrong package (PyPI `bearer` is a SaaS HTTP auth client, not the Bearer security scanner CLI).

Security / maintenance replacements:

- **Add** `bandit>=1.7.0` (MIT) to `dev` extra — correct Python-native static security analysis, replacing the intended-but-wrong `bearer`.
- **Replace** `json5` (runtime, low-adoption) with `commentjson>=0.9.0` (MIT) + stdlib `json.dumps`.

License compliance — Phase 2 (separate change, tracked):

- **Remove** `pylint` (GPL-2.0-or-later) from `dev` and `hatch-test` envs; replace with `ruff --select ALL` in strict mode (already covers the majority of pylint rules, MIT-licensed). Phase 2 because it requires ruff rule alignment work.
- Full `gitpython` → `dulwich` migration (3-file adapter rewrite).

Retained with documented exceptions:

- `pygments` (GPL-2.0-or-later) — transitive dep of `rich` (runtime); cannot remove without removing rich. Accepted under the dynamically-linked library-use interpretation; monitored for future alternatives.
- `semgrep` (LGPL-2.1) — **kept in all environments** as required for code analysis. LGPL (not GPL/AGPL), invoked as a subprocess tool. Not statically linked into specfact-cli's distributed code. Documented exception.

No action needed:

- `mando` — transitive dep via `radon` only; no direct import; drops automatically if radon removes it upstream.

## Capabilities

### New Capabilities

- `call-graph-analysis`: Python call-graph extraction via `pycg` CLI (replaces GPL `pyan3`). Same optional dep gate (`check_cli_tool_available("pycg")`), subprocess invocation in `graph_analyzer.py`, and JSON-based call-graph parsing. Functionally equivalent to the previous DOT-based pipeline; MIT-licensed throughout.
- `dep-license-gate`: Proactive dependency hygiene gate. A `scripts/check_license_compliance.py` script (using `pip-licenses`, MIT) that fails CI if any (A)GPL package appears outside the documented allowlist. A companion `hatch run security-audit` script (using `pip-audit`, MIT, by PyPA) scans for known CVEs. Both are wired into CI and the `docs/agent-rules/` framework to prevent recurrence. An exception allowlist (`scripts/license_allowlist.yaml`) documents each accepted exception with a human-readable reason.

### Modified Capabilities

- `dependency-resolution`: The package set in `dev`, `enhanced-analysis`, and `hatch-test` changes (removals: `syft`, `bearer`, `pyan3`; additions: `bandit`, `pycg`, `pip-licenses`, `pip-audit`; runtime: `json5` → `commentjson`). No public CLI surface changes.

## Impact

### pyproject.toml

- `enhanced-analysis` extra: remove `syft`, `bearer`, `pyan3`; add `pycg`.
- `dev` extra: remove `bearer`, `pyan3`; add `bandit`, `pycg`.
- `hatch-test` env deps: remove `bearer`, `pyan3`; add `pycg`.
- Runtime deps: replace `json5` with `commentjson`.
- Add inline comment on `gitpython` pin: CVE history + Phase 2 dulwich plan.
- Add inline comments on `pylint` (Phase 2 target), `pygments` (accepted exception), `semgrep` (LGPL accepted exception, required for code analysis).

### src/specfact\_cli/utils/optional\_deps.py

- Remove `syft` and `bearer` availability checks.
- Add `bandit` CLI availability check.
- Rename `pyan3` → `pycg` in availability check and all docstrings/messages.

### src/specfact\_cli/analyzers/graph\_analyzer.py

- `extract_call_graph`: replace `subprocess.run(["pyan3", ..., "--dot", ...])` with `subprocess.run(["pycg", ..., "--output", tmp_json])`.
- Replace `_parse_dot_file` with `_parse_pycg_json` (reads PyCG simple JSON: `{caller: [callee, ...]}` adjacency list).
- Update docstrings and user-facing messages.

### src/specfact\_cli/utils/project\_artifact\_write.py

- Replace `import json5` with `import commentjson` + `import json`.
- `json5.loads(raw_text)` → `commentjson.loads(raw_text)` (line 106).
- `json5.dumps(payload, indent=4, quote_keys=True, trailing_commas=False)` → `json.dumps(payload, indent=4)` (lines 83, 252).

### CI / policy / license artifacts

- `.github/workflows/pr-orchestrator.yml`: add `license-check` / `security-audit` gates and ensure
  dependency-policy inputs trigger them.
- `.github/workflows/publish-modules.yml`: auto-publish bundled modules after module-signing on
  `dev` / `main`.
- `scripts/check_license_compliance.py`, `scripts/security_audit_gate.py`,
  `scripts/license_allowlist.yaml`, `scripts/module_pip_dependencies_licenses.yaml`: enforce
  fail-closed dependency hygiene for env and bundled manifests.
- `docs/agent-rules/55-dependency-hygiene.md`: codify the package/license policy used by this
  change.

### Tests

- Exercise `graph_analyzer.py` with mocked `pycg` subprocess (argv includes `--package` / `--output`) and JSON parse coverage for `_parse_pycg_json`.
- Validate `project_artifact_write.py` JSONC reads via `commentjson` and writes via stdlib `json` (merge paths, trailing commas, recovery).
- Align `optional_deps.py` tests with `check_enhanced_analysis_dependencies()` keys (`pycg`, `bandit`, `graphviz`) and removed tools (`pyan3`, wrong PyPI `syft` / `bearer`).

**No public CLI surface changes.** All commands behave identically. Call-graph feature remains an optional enhancement gated by `pycg` availability.

## Cross-Repository Coordination

This change also requires lockstep follow-up in the sibling `nold-ai/specfact-cli-modules`
repository before merge:

- Replace remaining `pyan3` consumers with `pycg` in
  `packages/specfact-project/src/specfact_project/analyzers/graph_analyzer.py`,
  `packages/specfact-project/src/specfact_project/analyzers/code_analyzer.py`, and
  `packages/specfact-project/src/specfact_project/import_cmd/commands.py`.
- Align `json5` references with the `commentjson` / stdlib `json` migration where module code still
  mirrors core `project_artifact_write` behavior.
- Update any module-repo dependency metadata, docs, and accepted-license notes so `pycg`, `bandit`,
  `commentjson`, and the same manifest/license policy are reflected consistently.

Track that coordination with an explicit sibling-repo PR or issue link before closing this change.

## Source Tracking

- **GitHub Issue**: #508
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/508>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open (implementation in PR #507)
- **GitHub Pull Request**: #507
- **Pull Request URL**: <https://github.com/nold-ai/specfact-cli/pull/507>
