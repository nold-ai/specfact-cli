# Implementation Tasks: marketplace-04-revocation

## TDD / SDD Order (Enforced)

Per config.yaml, tests MUST come before implementation for any behavior-changing task. Order:

1. Spec deltas (already created in this change)
2. Tests from spec scenarios (expect failure — no implementation yet)
3. Code implementation (until tests pass and behavior satisfies spec)
4. Evidence recorded in `openspec/changes/marketplace-04-revocation/TDD_EVIDENCE.md`

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `gh issue develop 328 --repo nold-ai/specfact-cli --name feature/marketplace-04-revocation`
  - [ ] 1.1.3 `git fetch origin && git worktree add ../specfact-cli-worktrees/feature/marketplace-04-revocation feature/marketplace-04-revocation`
  - [ ] 1.1.4 `cd ../specfact-cli-worktrees/feature/marketplace-04-revocation`
  - [ ] 1.1.5 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.6 `git branch --show-current` (verify: `feature/marketplace-04-revocation`)

> All subsequent tasks run inside the worktree directory.
> **Hard blocker**: marketplace-03 must be implemented and merged before code work begins. Trust layer (`trust/publisher_registry.py`, `trust/resolver.py`) is a required dependency.

---

## 2. Review spec files (SDD)

- [ ] 2.1 Review specs created in this change
  - [ ] 2.1.1 `openspec/changes/marketplace-04-revocation/specs/publisher-revocation/spec.md`
  - [ ] 2.1.2 `openspec/changes/marketplace-04-revocation/specs/module-revocation/spec.md`
  - [ ] 2.1.3 `openspec/changes/marketplace-04-revocation/specs/grace-window-policy/spec.md`
  - [ ] 2.1.4 `openspec/changes/marketplace-04-revocation/specs/automated-scan/spec.md`
  - [ ] 2.1.5 `openspec validate marketplace-04-revocation --strict`
  - [ ] 2.1.6 `hatch run yaml-lint`

---

## 3. Create revocation data models (TDD)

- [ ] 3.1 Write tests for revocation models (expect failure)
  - [ ] 3.1.1 Create `tests/unit/trust/test_revocation_models.py`
  - [ ] 3.1.2 Test `RevocationEntry`: required fields (publisher_id/module_name, reason, revoked_at, grace_window_days)
  - [ ] 3.1.3 Test `PublisherRevocationIndex`: schema_version, nold_ai_signature, revocations list
  - [ ] 3.1.4 Test `ModuleRevocationIndex`: same structure, module-scoped entries
  - [ ] 3.1.5 Test `GraceWindowPolicy`: grace_days, install_action, existing_action
  - [ ] 3.1.6 Test `RevocationStatus`: is_revoked, reason, grace_status, days_remaining
  - [ ] 3.1.7 Run tests — expect failures
  - [ ] 3.1.8 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 3.2 Implement revocation models in `src/specfact_cli/trust/models.py` (extend)
  - [ ] 3.2.1 Add `RevocationEntry`, `PublisherRevocationIndex`, `ModuleRevocationIndex`, `GraceWindowPolicy`, `GraceStatus`, `RevocationStatus`, `RevocationDecision`, `RevocationContext` to `trust/models.py`
  - [ ] 3.2.2 All Pydantic BaseModel with Field(...) and descriptions
  - [ ] 3.2.3 `revoked_at` must be UTC-aware datetime
  - [ ] 3.2.4 Run tests — expect pass
  - [ ] 3.2.5 Record passing evidence in `TDD_EVIDENCE.md`

---

## 4. Implement revocation.py (TDD)

- [ ] 4.1 Write tests for revocation checker (expect failure)
  - [ ] 4.1.1 Create `tests/unit/trust/test_revocation.py`
  - [ ] 4.1.2 Test `fetch_revocation_indexes()`: fetch + sig verify + cache (mock HTTP)
  - [ ] 4.1.3 Test cache hit within 1h TTL — no HTTP call
  - [ ] 4.1.4 Test stale cache when offline — serve with warning
  - [ ] 4.1.5 Test `check_publisher_revocation()`: not-revoked → RevocationStatus(is_revoked=False)
  - [ ] 4.1.6 Test `check_publisher_revocation()`: revoked, security_incident → RevocationStatus(is_revoked=True, grace_days=0)
  - [ ] 4.1.7 Test `check_publisher_revocation()`: revoked, policy_violation, within 30d → grace status
  - [ ] 4.1.8 Test `check_publisher_revocation()`: revoked, policy_violation, past 30d → expired
  - [ ] 4.1.9 Test `check_module_revocation()`: same grace window logic for module entries
  - [ ] 4.1.10 Test `compute_grace_status()`: all four reason codes + unknown reason → most restrictive
  - [ ] 4.1.11 Test `enforce_revocation_policy()`: security_incident → hard_block; policy_violation in window → warn; etc.
  - [ ] 4.1.12 Run tests — expect failures
  - [ ] 4.1.13 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 4.2 Implement `src/specfact_cli/trust/revocation.py`
  - [ ] 4.2.1 `GRACE_WINDOWS` constant (dict of reason → GraceWindowPolicy)
  - [ ] 4.2.2 `fetch_revocation_indexes(trust_index_url, cache_dir) -> tuple[PublisherRevocationIndex, ModuleRevocationIndex]`
  - [ ] 4.2.3 Cache in `~/.specfact/cache/publishers-revoked.json` and `registry-modules-revoked.json` (1h TTL)
  - [ ] 4.2.4 `check_publisher_revocation(publisher_id, index) -> RevocationStatus`
  - [ ] 4.2.5 `check_module_revocation(module_name, version, index) -> RevocationStatus`
  - [ ] 4.2.6 `compute_grace_status(revoked_at, reason) -> GraceStatus`
  - [ ] 4.2.7 `enforce_revocation_policy(status, context) -> RevocationDecision`
  - [ ] 4.2.8 `@require`, `@ensure`, `@beartype` on all public functions
  - [ ] 4.2.9 Run tests — expect pass
  - [ ] 4.2.10 Record passing evidence in `TDD_EVIDENCE.md`

---

## 5. Integrate revocation into module_registry install/invocation (TDD)

- [ ] 5.1 Write integration tests (expect failure)
  - [ ] 5.1.1 Create `tests/integration/test_revocation_integration.py`
  - [ ] 5.1.2 Test install of security_incident-revoked publisher: hard block, no flag override
  - [ ] 5.1.3 Test install of policy_violation-revoked publisher, in window: warn + prompt
  - [ ] 5.1.4 Test install of policy_violation-revoked publisher, past window: hard block
  - [ ] 5.1.5 Test install of publisher_request-revoked, in window: warn + prompt, succeeds
  - [ ] 5.1.6 Test install of api_incompatibility-revoked module: warn, suggest newer, not blocked in window
  - [ ] 5.1.7 Test invocation warning for installed security_incident-revoked module
  - [ ] 5.1.8 Test weekly re-check triggered when last check > 7 days ago
  - [ ] 5.1.9 Run tests — expect failures
  - [ ] 5.1.10 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 5.2 Integrate revocation into module_registry
  - [ ] 5.2.1 Add revocation pre-flight to install command (after trust tier resolution, before download)
  - [ ] 5.2.2 Add revocation warning check on module load (for already-installed modules)
  - [ ] 5.2.3 Add `revocation_check_interval` config key (default: `7d`) to `~/.specfact/config.yaml`
  - [ ] 5.2.4 Implement periodic re-check: track last check timestamp in `~/.specfact/cache/revocation-last-check`
  - [ ] 5.2.5 Run tests — expect pass
  - [ ] 5.2.6 Record passing evidence in `TDD_EVIDENCE.md`

---

## 6. Implement AST scan (TDD)

- [ ] 6.1 Write tests for bundle scanner (expect failure)
  - [ ] 6.1.1 Create `tests/unit/scripts/test_bundle_scan.py`
  - [ ] 6.1.2 Test `scan_bundle()` on clean bundle — empty findings
  - [ ] 6.1.3 Test detection of `exec(base64.b64decode(...))` pattern
  - [ ] 6.1.4 Test detection of `subprocess.run(shell=True)` + HTTP URL in same file
  - [ ] 6.1.5 Test detection of network call at module top level
  - [ ] 6.1.6 Test detection of `eval(<network-response-variable>)` pattern
  - [ ] 6.1.7 Test `ScanReport.has_blocking_findings()` — True when block-severity finding present
  - [ ] 6.1.8 Run tests — expect failures
  - [ ] 6.1.9 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 6.2 Implement AST scan
  - [ ] 6.2.1 Create `src/specfact_cli/trust/bundle_scanner.py` with `scan_bundle(bundle_path) -> ScanReport`
  - [ ] 6.2.2 Implement all four check patterns using stdlib `ast` module only
  - [ ] 6.2.3 Integrate scan call into `scripts/publish-module.py` before publication step
  - [ ] 6.2.4 Create `.github/workflows/scan-bundles.yml` (triggers on push/PR to specfact-cli-modules, *.py changes)
  - [ ] 6.2.5 Add `@require`, `@ensure`, `@beartype` to `scan_bundle()`
  - [ ] 6.2.6 Run tests — expect pass
  - [ ] 6.2.7 Record passing evidence in `TDD_EVIDENCE.md`

---

## 7. Create revocation signing scripts

- [ ] 7.1 Create `scripts/revoke-publisher.py`
  - [ ] 7.1.1 Signs revocation entry in `publishers/revoked.json` with NOLD AI key
  - [ ] 7.1.2 Accepts: publisher_id, handle, reason (enum: security_incident/policy_violation/publisher_request/api_incompatibility), grace_window_days
  - [ ] 7.1.3 Appends to `publishers/revoked.json` and re-signs the full index
- [ ] 7.2 Create `scripts/revoke-module.py`
  - [ ] 7.2.1 Signs per-module revocation entry in `registry/modules/revoked.json`
  - [ ] 7.2.2 Accepts: module_name, version, reason, grace_window_days
  - [ ] 7.2.3 Appends and re-signs

---

## 8. Module signing verification quality gate

- [ ] 8.1 `hatch run ./scripts/verify-modules-signature.py --require-signature`
- [ ] 8.2 Re-sign and bump version if any module changed

---

## 9. Quality gates

- [ ] 9.1 `hatch run format`
- [ ] 9.2 `hatch run type-check`
- [ ] 9.3 `hatch run lint`
- [ ] 9.4 `hatch run yaml-lint`
- [ ] 9.5 `hatch run contract-test`
- [ ] 9.6 `hatch test --cover -v`

---

## 10. Documentation research and review

- [ ] 10.1 Identify and update affected documentation:
  - [ ] 10.1.1 Create `docs/trust/grace-window-policy.md` (Jekyll front-matter required; ToS-linkable)
  - [ ] 10.1.2 Update `docs/reference/module-commands.md`: revocation warning messages, `revocation_check_interval` config
  - [ ] 10.1.3 Update `docs/_layouts/default.html`: add `Trust` section to sidebar with grace-window-policy link
  - [ ] 10.1.4 Update `docs/guides/publisher-trust.md` (from marketplace-03): add note on revocation and grace windows

---

## 11. Version and changelog

- [ ] 11.1 Determine version bump: feature branch → minor increment (confirm with user)
- [ ] 11.2 Sync version across `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`
- [ ] 11.3 `CHANGELOG.md` entry:
  - `Added: Publisher and module revocation infrastructure (trust/revocation.py)`
  - `Added: Grace window policy enforcement by reason type (security_incident/policy_violation/publisher_request/api_incompatibility)`
  - `Added: CI AST scan for bundle publication (.github/workflows/scan-bundles.yml)`
  - `Added: docs/trust/grace-window-policy.md`

---

## 12. GitHub issue creation

- [x] 12.1 GitHub issue already created: [#328](https://github.com/nold-ai/specfact-cli/issues/328)
- [x] 12.2 Linked to project board
- [x] 12.3 `proposal.md` Source Tracking updated with issue #328
- [x] 12.4 `CHANGE_ORDER.md` updated with marketplace-04 entry and GitHub issue #328

---

## 13. Create PR

- [ ] 13.1 Commit from inside the worktree
  - [ ] 13.1.1 `git add src/specfact_cli/trust/ src/specfact_cli/modules/module_registry/ scripts/ .github/workflows/ docs/ openspec/ pyproject.toml setup.py CHANGELOG.md`
  - [ ] 13.1.2 `git commit -S -m "feat: publisher and module revocation infrastructure (marketplace-04)"`
  - [ ] 13.1.3 `git push -u origin feature/marketplace-04-revocation`
- [ ] 13.2 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/marketplace-04-revocation --title "feat: publisher and module revocation infrastructure" --body-file /tmp/pr-marketplace-04.md`
- [ ] 13.3 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

---

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd /home/dom/git/nold-ai/specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/marketplace-04-revocation`
- [ ] `git branch -d feature/marketplace-04-revocation`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/marketplace-04-revocation`
