## Context

specfact-cli is licensed **Apache-2.0**. The attribution audit identified packages in distributed extras that violate this license (GPL-2.0 `pyan3`), packages that are entirely wrong (OpenMined `syft`, SaaS `bearer`), and a low-adoption runtime dep (`json5`) with a straightforward replacement. The codebase uses a strict contract-first architecture (`@beartype` + `@icontract` on all public APIs), so all replacements must preserve decorator surfaces and existing type signatures.

Current affected files:

- `src/specfact_cli/analyzers/graph_analyzer.py` — calls `pyan3` CLI via `subprocess`, parses DOT output
- `src/specfact_cli/utils/optional_deps.py` — availability checks for `pyan3`, `syft`, `bearer`
- `src/specfact_cli/utils/project_artifact_write.py` — uses `json5.loads` / `json5.dumps`
- `pyproject.toml` — all extras and hatch-test env

## Goals / Non-Goals

**Goals:**

- Eliminate all GPL packages from distributed extras (`dev`, `enhanced-analysis`) to preserve Apache-2.0 compatibility and unblock future enterprise/commercial licensing.
- Remove wrong packages (`syft`, `bearer`) that add install weight with no functional benefit.
- Replace `pyan3` with a functionally equivalent, MIT-licensed call-graph tool (`pycg`).
- Replace `json5` runtime dep with `commentjson` + stdlib `json` for JSONC read/write.
- Add `bandit` as the correct Python-native static security analysis tool (was the intended role of `bearer`).
- Document accepted GPL exceptions (`pygments`, `semgrep`) and Phase 2 targets (`pylint`, `gitpython`).

**Non-Goals:**

- `gitpython` → `dulwich` migration (3-file adapter rewrite; Phase 2 change).
- `pylint` → ruff strict replacement (requires ruff rule alignment work; Phase 2 change).
- Removing `semgrep` — required for code analysis in all environments.
- Removing `pygments` — transitive via `rich`; not directly removable.
- Any public CLI surface or API contract changes.

## Decisions

### Decision 1: `pycg` over other call-graph alternatives

**Chosen:** `pycg>=0.0.7` (MIT, actively maintained)

**Alternatives considered:**

- `pyan` (original) — unmaintained since ~2016, worse than `pyan3`.
- `importlab` (Google, Apache-2.0) — analyzes import graphs only, not call graphs.
- Custom AST walker — significant implementation effort for equivalent coverage; YAGNI given `pycg` exists.

**Rationale:** `pycg` is invoked as a CLI subprocess (same pattern as `pyan3`), outputs JSON (`{caller: [callee, ...]}` simple JSON adjacency list, where the value list contains the callees of the key) rather than DOT format, and is MIT-licensed. The call-graph feature in `graph_analyzer.py` is already optional (guarded by `check_cli_tool_available`), so the DOT→JSON parser swap is entirely internal to `extract_call_graph` and `_parse_dot_file`. No public API change.

**Adapter change:** `_parse_dot_file(dot_path: Path) → dict[str, list[str]]` is renamed to `_parse_pycg_json(json_path: Path) → dict[str, list[str]]`. The method body changes from DOT regex parsing to `json.loads`. Edge direction is preserved as caller → callees (matching `extract_call_graph`'s public contract). The return type and the public `extract_call_graph` signature are unchanged.

### Decision 2: `commentjson` + stdlib `json` over other JSONC alternatives

**Chosen:** `commentjson>=0.9.0` (MIT) for reads; `json.dumps` for writes.

**Alternatives considered:**

- `pyjson5` — different API; less actively maintained than `commentjson`.
- `json_with_comments` — very low adoption.
- Custom comment-stripper (regex) — fragile; edge cases around comments inside strings.
- Keep `json5` — low-adoption, unclear maintenance trajectory; not worth the supply-chain risk for a simple JSONC read.

**Rationale:** The read path (`json5.loads`) only needs to strip `//` and `/* */` comments and trailing commas from VS Code `settings.json` — exactly what `commentjson` does via stdlib `json` under the hood. The write path (`json5.dumps(..., quote_keys=True, trailing_commas=False)`) produces standard JSON: stdlib `json.dumps(indent=4)` is identical output (keys are always quoted, no trailing commas). Drop-in replacement with two import changes and three call-site edits.

### Decision 3: `bandit` as the security analysis replacement for `bearer`

**Chosen:** `bandit>=1.7.0` (MIT, Apache Software Foundation, widely adopted).

**Rationale:** The `bearer` PyPI package was intended to provide security data-flow scanning. The actual bearer security scanner is a Ruby/Go binary, not a pip package. `bandit` is the de-facto Python-native static security analysis tool: it scans for common security issues (hardcoded passwords, dangerous `subprocess` usage, SQL injection patterns, etc.), is MIT-licensed, integrates with pre-commit and CI, and is broadly adopted in the Python ecosystem.

### Decision 4: Wrong-PyPI `syft` / `bearer` removal; enhanced-analysis stack is Python-native

**Rationale:** The PyPI packages named `syft` and `bearer` were the wrong artifacts (not Anchore Syft / Bearer security scanner). Both were removed from `pyproject.toml`. Optional enhanced analysis is checked via `check_enhanced_analysis_dependencies()` in `optional_deps.py`, which reports `pycg`, `bandit`, and `graphviz` using `check_cli_tool_available("pycg")`, `check_cli_tool_available("bandit")`, and `check_python_package_available("graphviz")` (tuple shape `(available, error_message | None)` per tool). There is **no** `check_cli_tool_available("syft")` probe in this codebase: Anchore Syft remains an out-of-band install if SBOM generation is needed later.

### Decision 5: GPL exception documentation strategy

Rather than silently accepting GPL packages, each retained GPL/LGPL package gets an inline `pyproject.toml` comment documenting:

- The license
- Why it is accepted (subprocess isolation, transitive-only, LGPL not GPL)
- Its Phase 2 status if it is a removal target

This makes the exception policy auditable and keeps future maintainers from accidentally normalising new GPL additions without review.

### Decision 6: License gate implementation using pip-licenses + pip-audit

**Chosen:** `pip-licenses>=4.0.0` (MIT) for license enumeration; `pip-audit>=2.0.0` (MIT, PyPA) for CVE scanning; custom `scripts/check_license_compliance.py` with `scripts/license_allowlist.yaml`.

**Alternatives considered:**

- `liccheck` — configuration-based license checker, but allowlist management is less transparent.
- `fossa` / `snyk` — cloud-based SCA tools; violate the offline-first constraint and introduce vendor lock-in.
- socket.dev CLI — not pip-installable; requires cloud connectivity; suitable for CI but not local development.
- Manual review — what we just did; scales poorly and missed the wrong packages for months.

**Rationale:** `pip-licenses` reads the installed environment (from `dist-info` metadata) and returns SPDX expressions — no network required. `pip-audit` queries the OSV database (can run offline against a local snapshot). Both are MIT-licensed and widely adopted. The allowlist YAML keeps exceptions auditable and diff-visible in PRs; any new exception requires a documented reason, making GPL creep immediately visible in code review.

**Gate design:**

- `hatch run license-check` → `python scripts/check_license_compliance.py`
- `hatch run security-audit` → `python scripts/security_audit_gate.py` (CVSS-threshold wrapper over `pip-audit` JSON)
- `hatch run bandit-scan` → `bandit -r src/ -ll`
- CI: both gates run on every PR; `license-check` specifically triggered on `pyproject.toml` changes.

**Allowlist initial entries (at change time):**

```yaml
- package: pylint
  license: GPL-2.0-or-later
  reason: "Dev-only tool, invoked as subprocess. Phase 2 removal target (replace with ruff strict)."
- package: pygments
  license: GPL-2.0-or-later
  reason: "Transitive dep of rich (runtime). Cannot remove without removing rich. Monitored."
- package: semgrep
  license: LGPL-2.1
  reason: "Required for code analysis in all envs. LGPL not GPL/AGPL; invoked as subprocess."
```

**Agent-rules integration:** A new section added to `docs/agent-rules/` (`55-dependency-hygiene.md`) that specifies the (A)GPL prohibition, allowlist process, and required gates. Indexed in `docs/agent-rules/INDEX.md`.

## Risks / Trade-offs

**`pycg` output format differs from `pyan3`** → The internal call-graph representation changes from DOT adjacency to JSON. Risk: edge cases in `_parse_pycg_json` miss call edges that `_parse_dot_file` captured (or vice versa). Mitigation: add unit tests with known Python files asserting specific call edges in the JSON output. The feature is optional and gated; a regression degrades gracefully (empty graph, no crash).

**`commentjson` trailing-comma handling** → `commentjson` strips trailing commas before parsing. Risk: malformed JSONC files that `json5` accepted but `commentjson` rejects (edge: deeply nested trailing commas). Mitigation: test with real VS Code `settings.json` fixtures; `commentjson` 0.9.0+ handles all JSONC patterns used by VS Code.

**`pycg` version stability** → `pycg` is `0.0.x`, pre-release versioning. Risk: API instability. Mitigation: pin `>=0.0.7` (known stable), test in CI. The feature is optional; a future pycg breakage degrades gracefully via `check_cli_tool_available` returning `False`.

**`bandit` not yet wired into CI** → Adding `bandit` to `dev` without a full CI gate means findings accumulate silently. Mitigation: add a `bandit-scan` hatch script as part of this change so it is runnable; full CI gate is Phase 2.

**`pylint` (GPL-2.0) stays in Phase 1** → `pylint` remains in `dev` and `hatch-test`. Risk: enterprise licensing review flags it. Mitigation: `dev` extra is not installed by end-users in normal usage; pylint is a developer tool. Phase 2 change will replace it with `ruff --select ALL`.

## Migration Plan

1. **Branch**: `feature/dep-security-cleanup` (worktree at `specfact-cli-worktrees/feature/dep-security-cleanup`).
2. **pyproject.toml**: Remove `syft`, `bearer`, `pyan3`; add `pycg`, `bandit`, `commentjson`; swap `json5` → `commentjson` in runtime deps; add GPL exception comments.
3. **optional\_deps.py**: Remove `syft`/`bearer` checks; add `bandit`; rename `pyan3` → `pycg`.
4. **graph\_analyzer.py**: Swap `pyan3` subprocess + DOT parser → `pycg` subprocess + JSON parser.
5. **project\_artifact\_write.py**: Swap `json5` → `commentjson` + stdlib `json`.
6. **Tests**: Add/update unit tests covering new paths; run full test suite.
7. **TDD\_EVIDENCE.md**: Record failing-before / passing-after runs per SDD+TDD discipline.
8. **Docs review**: Check `docs/` and README for any references to `pyan3`, `json5`, `bearer`, `syft`; update install instructions and dependency documentation.

**Rollback**: The worktree branch can be abandoned with `git worktree remove`. No database or schema migrations involved; pyproject.toml changes are fully reversible.

### Decision 7: Auto-publish bundled modules from CI after sign-modules

**Chosen:** Add a `workflow_run` trigger to `.github/workflows/publish-modules.yml` that fires after `sign-modules.yml` (Module Signature Hardening) completes successfully on dev/main, plus a new `auto-publish` job that compares each bundled `module-package.yaml` `version` against the in-repo snapshot `resources/bundled-module-registry/index.json` and packages every module whose version is strictly greater, then opens a PR **in specfact-cli** updating that snapshot (marketplace `registry/index.json` in `specfact-cli-modules` is out of scope for bundled modules).

**Why this scope extension is in this change:** the dependency cleanup removed local-sign requirements and pushed signing into CI (sign-modules.yml). That left no automated follow-up for bundled packaging on dev pushes because `publish-modules.yml` only triggered on tag-push / `workflow_dispatch`, and the bot's auto-sign commit carries `[skip ci]` (which suppresses `push` events but **not** `workflow_run`). Without the trigger added here, every dev merge could leave the bundled snapshot stale relative to bumped in-repo modules.

**Alternatives considered:**

- Drop `[skip ci]` from the auto-sign commit and add a `push` trigger — risks an infinite loop with sign-modules.yml itself; `[skip ci]` is load-bearing for that.
- Detect changed modules via `git diff HEAD HEAD~1` — misses cases where the user pre-bumped the version in the merged PR (the auto-sign commit then only changes signature fields, not version).
- One PR per module — noisier history; rejected in favor of one combined PR per CI run.

**Rationale:** Comparing manifest version vs the bundled snapshot `latest_version` is robust to all version-bump origins (user bump, sign-modules auto-bump, multiple sequential merges). The check is implemented in `scripts/_detect_modules_to_publish.py` using `packaging.version.Version` for semver-correct comparison. The existing tag-push and `workflow_dispatch` flows are preserved for bundled packaging; PRs target this repository.

## Open Questions

- **`pycg` vs `staticfg`**: Is there appetite to evaluate `staticfg` (static flow graphs, MIT) as a future enhancement on top of `pycg`? Not blocking; track in backlog.
- **`bandit` CI gate scope**: Should `bandit` run on `src/` only, or also `tools/`? Decide at implementation time; default to `src/` to avoid tool-directory noise.
- **`pygments` long-term**: If `rich` ever drops the `pygments` dependency (possible in a future major), we should remove the accepted-exception comment. Worth watching rich's changelog.
