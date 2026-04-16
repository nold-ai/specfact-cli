## 1. Spec-Driven Test Scaffolding (write tests first, expect failure)

- [x] 1.1 Write failing unit tests for `graph_analyzer.extract_call_graph` using mocked `pycg` subprocess (JSON output format, non-zero exit, binary missing)
- [x] 1.2 Write failing unit tests for `graph_analyzer._parse_pycg_json` verifying dict structure from pycg JSON output
- [x] 1.3 Write failing unit tests for `optional_deps.check_optional_analysis_deps` asserting `"pycg"` key present and `"pyan3"`, `"syft"`, `"bearer"` absent
- [x] 1.4 Write failing unit tests for `project_artifact_write` JSONC read path (commentjson strips `//` comments and trailing commas)
- [x] 1.5 Write failing unit tests for `project_artifact_write` JSON write path (stdlib json.dumps produces equivalent output to previous json5.dumps)
- [x] 1.6 Write failing unit tests for `scripts/check_license_compliance.py` covering: clean pass, GPL violation detected, allowlist exception accepted, unknown license as warning
- [x] 1.7 Record pre-implementation failing test run output in `openspec/changes/dep-security-cleanup/TDD_EVIDENCE.md`

## 2. pyproject.toml — Dependency Changes

- [x] 2.1 Remove `syft` from `enhanced-analysis` extra; add inline comment explaining removal
- [x] 2.2 Remove `bearer` from `dev` and `enhanced-analysis` extras; add inline comment explaining removal
- [x] 2.3 Remove `pyan3` from `dev` and `enhanced-analysis` extras and `hatch-test` env; add inline comment: "GPL-2.0 — replaced by pycg (MIT)"
- [x] 2.4 Add `pycg>=0.0.7` to `dev` and `enhanced-analysis` extras and `hatch-test` env
- [x] 2.5 Add `bandit>=1.7.0` to `dev` extra
- [x] 2.6 Add `pip-licenses>=4.0.0` to `dev` extra
- [x] 2.7 Add `pip-audit>=2.0.0` to `dev` extra
- [x] 2.8 Replace `json5` with `commentjson>=0.9.0` in runtime `dependencies` list
- [x] 2.9 Add inline comment on `gitpython` pin: "CVE history (CVE-2022-24439, CVE-2023-41040, CVE-2023-40590). Phase 2: replace with dulwich."
- [x] 2.10 Add inline comments on retained GPL/LGPL packages (`pylint`: Phase 2 removal target; `pygments`: transitive via rich, accepted; `semgrep`: LGPL, required for code analysis)
- [x] 2.11 Add `bandit-scan`, `license-check`, and `security-audit` hatch scripts under `[tool.hatch.envs.default.scripts]`

## 3. optional_deps.py — Availability Check Updates

- [x] 3.1 Remove `results["syft"] = check_cli_tool_available("syft")` line (keep the `syft` key commented out with note that Anchore binary is detected separately if on `$PATH`)
- [x] 3.2 Remove `results["bearer"] = check_cli_tool_available("bearer")` line
- [x] 3.3 Add `results["bandit"] = check_cli_tool_available("bandit")` line
- [x] 3.4 Rename `results["pyan3"]` → `results["pycg"]` and update the CLI tool name in `check_cli_tool_available("pyan3")` → `check_cli_tool_available("pycg")`
- [x] 3.5 Update the module docstring and `check_optional_analysis_deps` docstring to reflect new tool names; remove references to `pyan3`, `syft`, `bearer`
- [x] 3.6 Update the install hint at the bottom of the docstring: `pip install pycg bandit graphviz`

## 4. graph_analyzer.py — pyan3 → pycg Migration

- [x] 4.1 In `extract_call_graph`: rename the guard from `check_cli_tool_available("pyan3")` → `check_cli_tool_available("pycg")`
- [x] 4.2 Replace `subprocess.run(["pyan3", str(file_path), "--dot", "--no-defines", "--uses", "--defines"], stdout=dot_file, ...)` with `subprocess.run(["pycg", str(file_path), "--output", str(json_path)], ...)`
- [x] 4.3 Change temp file suffix from `.dot` to `.json`; update variable names accordingly (`dot_file` → `json_file`, `dot_path` → `json_path`)
- [x] 4.4 Replace `self._parse_dot_file(dot_path)` call with `self._parse_pycg_json(json_path)`
- [x] 4.5 Add new method `_parse_pycg_json(self, json_path: Path) -> dict[str, list[str]]` that reads the JSON file and returns the call graph dict; decorate with `@beartype` and `@require`/`@ensure`
- [x] 4.6 Remove old `_parse_dot_file` method (or mark deprecated if referenced elsewhere — check with grep)
- [x] 4.7 Update all user-facing messages and docstrings that mention `pyan3` to say `pycg`

## 5. project_artifact_write.py — json5 → commentjson + stdlib json

- [x] 5.1 Replace `import json5` with `import commentjson` and `import json` (if not already imported)
- [x] 5.2 Line 106: replace `json5.loads(raw_text)` with `commentjson.loads(raw_text)`
- [x] 5.3 Line 83: replace `json5.dumps(payload, indent=4, quote_keys=True, trailing_commas=False)` with `json.dumps(payload, indent=4)`
- [x] 5.4 Line 252: replace `json5.dumps(loaded, indent=4, quote_keys=True, trailing_commas=False)` with `json.dumps(loaded, indent=4)`
- [x] 5.5 Verify `@beartype` and `@icontract` decorators on public functions in this module are unchanged

## 6. License Compliance Gate — scripts/

- [x] 6.1 Create `scripts/license_allowlist.yaml` with initial entries: `pylint` (GPL-2.0-or-later, Phase 2 removal), `pygments` (GPL-2.0-or-later, transitive via rich), `semgrep` (LGPL-2.1, required for code analysis)
- [x] 6.2 Create `scripts/check_license_compliance.py` implementing: load allowlist, run `pip-licenses --format=json`, iterate packages, fail on (A)GPL not in allowlist, warn on UNKNOWN, print exception entries with reason
- [x] 6.3 Ensure `check_license_compliance.py` exits 0 on clean pass, exits 1 on violation
- [x] 6.4 Add `license-check = "python scripts/check_license_compliance.py"` to `[tool.hatch.envs.default.scripts]`
- [x] 6.5 Add `security-audit = "pip-audit --desc --strict"` to `[tool.hatch.envs.default.scripts]`
- [x] 6.6 Add `bandit-scan = "bandit -r src/ -ll"` to `[tool.hatch.envs.default.scripts]`

## 7. CI Integration

- [x] 7.1 Add `license-check` step to the relevant GitHub Actions workflow (runs on `pyproject.toml` changes and all PRs)
- [x] 7.2 Add `security-audit` step to CI workflow (runs on all PRs)
- [x] 7.3 Verify both steps fail the workflow with non-zero exit on violations

## 8. Agent-Rules Documentation

- [x] 8.1 Create `docs/agent-rules/55-dependency-hygiene.md` with sections: (A)GPL prohibition, allowlist process, approved license list (MIT/Apache-2.0/BSD/PSF), required gate scripts, Phase 2 tracking
- [x] 8.2 Add entry to `docs/agent-rules/INDEX.md` pointing to the new file
- [x] 8.3 Add `applies_when` signal to `55-dependency-hygiene.md` so agents load it on dependency-related tasks

## 9. Docs Review and Update

- [x] 9.1 Search `docs/` and `README.md` for references to `pyan3`, `json5`, `bearer`, `syft`; update install instructions and any tool references
- [x] 9.2 Check if any getting-started or contributing guide references the old tool names; update accordingly
- [x] 9.3 Add a note in `SECURITY.md` (or create if absent) about the `gitpython` CVE history and the Phase 2 dulwich plan

## 10. TDD Completion and Code Review

- [x] 10.1 Run full test suite (`hatch test --cover -v`) — all tests must pass — **verified 2026-04-16** via `hatch test -q` (2548 passed, 9 skipped); use `hatch test --cover -v` before merge if coverage gate required
- [x] 10.2 Run `hatch run license-check` — exit 0 on 2026-04-16 after fixing the `piplicenses` module invocation and documenting the dev-only `yamllint` exception
- [x] 10.3 Run `hatch run security-audit` — review output; resolve any high-severity findings — **2026-04-16**: wrapper exit 0; pip GHSA reported as WARNING (CVSS 0.0 in JSON)
- [x] 10.4 Run `hatch run bandit-scan` — review output; document or fix any findings — **2026-04-16**: scan run; Bandit reports existing issue counts (non-zero exit); baseline documented in `TDD_EVIDENCE.md`
- [x] 10.5 Run `hatch run format` and `hatch run type-check` — must pass clean — **2026-04-16**
- [ ] 10.6 Run `specfact code review run --json --out .specfact/code-review.json`; resolve all findings — not re-run in this session (requires review env / modules checkout)
- [x] 10.7 Record passing-after test run output in `openspec/changes/dep-security-cleanup/TDD_EVIDENCE.md` — **2026-04-16** (see “Code-review remediation verification”)
- [ ] 10.8 Commit with message: `feat(deps): remove GPL/wrong packages, add license-gate and security-audit (#<issue>)`

## 11. CI Auto-Publish for Bundled Modules (scope extension)

After this change introduced unsigned-by-default module manifests bumped/signed
by `sign-modules.yml` on push to dev/main, the registry was no longer reached
because `publish-modules.yml` only triggered on tag push or manual dispatch.

- [x] 11.1 Add `workflow_run` trigger to `.github/workflows/publish-modules.yml` after `Module Signature Hardening` completes on dev/main (not blocked by `[skip ci]` on the bot's auto-sign commit)
- [x] 11.2 Add `auto-publish` job that detects modules whose manifest version is strictly greater than the registry's `latest_version` and packages each
- [x] 11.3 Add helper `scripts/_detect_modules_to_publish.py` (compares `module-package.yaml` `version` vs `registry/index.json` `latest_version` per module id, semver-aware via `packaging.version`)
- [x] 11.4 Stage one combined registry PR per workflow run (batched across all bumped modules) instead of one PR per module
- [x] 11.5 Preserve existing single-module flows (tag-push, `workflow_dispatch`) unchanged
