# Implementation Tasks: marketplace-03-publisher-identity

## TDD / SDD Order (Enforced)

Per config.yaml, tests MUST come before implementation for any behavior-changing task. Order:

1. Spec deltas (already created in this change)
2. Tests from spec scenarios (expect failure — no implementation yet)
3. Code implementation (until tests pass and behavior satisfies spec)
4. Evidence recorded in `openspec/changes/marketplace-03-publisher-identity/TDD_EVIDENCE.md`

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `gh issue develop 327 --repo nold-ai/specfact-cli --name feature/marketplace-03-publisher-identity`
  - [ ] 1.1.3 `git fetch origin && git worktree add ../specfact-cli-worktrees/feature/marketplace-03-publisher-identity feature/marketplace-03-publisher-identity`
  - [ ] 1.1.4 `cd ../specfact-cli-worktrees/feature/marketplace-03-publisher-identity`
  - [ ] 1.1.5 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.6 `git branch --show-current` (verify: `feature/marketplace-03-publisher-identity`)

> All subsequent tasks run inside the worktree directory.
> **Hard blocker**: marketplace-02 (#215) must be implemented and merged before this branch is opened for code work. Branch can be created and spec/test work begun, but code changes to `custom_registries.py` integration points must wait for marketplace-02.

---

## 2. Write spec deltas and review (SDD)

- [ ] 2.1 Review spec files created in this change
  - [ ] 2.1.1 Review `openspec/changes/marketplace-03-publisher-identity/specs/publisher-identity/spec.md`
  - [ ] 2.1.2 Review `openspec/changes/marketplace-03-publisher-identity/specs/module-trust-chain/spec.md`
  - [ ] 2.1.3 Review `openspec/changes/marketplace-03-publisher-identity/specs/trust-resolution/spec.md`
  - [ ] 2.1.4 Review `openspec/changes/marketplace-03-publisher-identity/specs/module-security/spec.md` (delta)
  - [ ] 2.1.5 Run `openspec validate marketplace-03-publisher-identity --strict` and fix any issues
  - [ ] 2.1.6 Run `hatch run yaml-lint` to validate YAML/markdown

---

## 3. Create Pydantic models for trust layer (TDD)

- [ ] 3.1 Write tests for trust layer data models (expect failure)
  - [ ] 3.1.1 Create `tests/unit/trust/test_models.py`
  - [ ] 3.1.2 Test `PublisherRecord` Pydantic model: required fields, validation
  - [ ] 3.1.3 Test `PublisherIndex` model: publishers list, schema_version, nold_ai_signature
  - [ ] 3.1.4 Test `AuditEntry` model: timestamp UTC enforcement, field presence
  - [ ] 3.1.5 Test `InstallFlags` model: trust_community, trust_unregistered booleans
  - [ ] 3.1.6 Run tests — expect failures (models do not exist)
  - [ ] 3.1.7 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 3.2 Implement trust layer models
  - [ ] 3.2.1 Create `src/specfact_cli/trust/__init__.py`
  - [ ] 3.2.2 Create `src/specfact_cli/trust/models.py` with `PublisherRecord`, `PublisherIndex`, `AuditEntry`, `InstallFlags`, `InstallDecision`, `ValidationResult`
  - [ ] 3.2.3 All models use `Pydantic BaseModel` with `Field(...)` and descriptions
  - [ ] 3.2.4 Run tests — expect pass
  - [ ] 3.2.5 Record passing evidence in `TDD_EVIDENCE.md`

---

## 4. Implement key_store.py (TDD)

- [ ] 4.1 Write tests for key_store (expect failure)
  - [ ] 4.1.1 Create `tests/unit/trust/test_key_store.py`
  - [ ] 4.1.2 Test `get_root_public_key()` returns Ed25519PublicKey (use test fixture key)
  - [ ] 4.1.3 Test no network call is made during key load
  - [ ] 4.1.4 Test key is loadable offline (no network mock needed)
  - [ ] 4.1.5 Run tests — expect failures
  - [ ] 4.1.6 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 4.2 Implement key_store.py
  - [ ] 4.2.1 Create `src/specfact_cli/trust/key_store.py`
  - [ ] 4.2.2 Embed NOLD AI test root public key (base64 Ed25519) as module constant for test; production key injected at build time via `hatch build` hook or environment variable
  - [ ] 4.2.3 Implement `get_root_public_key() -> Ed25519PublicKey`
  - [ ] 4.2.4 Add `@beartype` and `@ensure` result is not None
  - [ ] 4.2.5 Run tests — expect pass
  - [ ] 4.2.6 Record passing evidence in `TDD_EVIDENCE.md`

---

## 5. Implement publisher_registry.py (TDD)

- [ ] 5.1 Write tests for publisher_registry (expect failure)
  - [ ] 5.1.1 Create `tests/unit/trust/test_publisher_registry.py`
  - [ ] 5.1.2 Test `fetch_publisher_index()` fetches and verifies signature (mock HTTP + crypto)
  - [ ] 5.1.3 Test cache hit returns cached index without HTTP call
  - [ ] 5.1.4 Test stale cache (>7 days) returns stale with warning when CDN offline
  - [ ] 5.1.5 Test tampered index raises `PublisherIndexTamperError`
  - [ ] 5.1.6 Test `resolve_publisher()` returns `PublisherRecord` when found
  - [ ] 5.1.7 Test `resolve_publisher()` returns `None` when not found (no raise)
  - [ ] 5.1.8 Run tests — expect failures
  - [ ] 5.1.9 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 5.2 Implement publisher_registry.py
  - [ ] 5.2.1 Create `src/specfact_cli/trust/publisher_registry.py`
  - [ ] 5.2.2 Implement `fetch_publisher_index(trust_index_url: str, cache_dir: Path) -> PublisherIndex`
  - [ ] 5.2.3 Cache: write to `~/.specfact/cache/publishers-index.json` with mtime TTL check
  - [ ] 5.2.4 Implement `resolve_publisher(publisher_id: str, index: PublisherIndex) -> PublisherRecord | None`
  - [ ] 5.2.5 Add `@require`, `@ensure`, `@beartype` on all public functions
  - [ ] 5.2.6 Run tests — expect pass
  - [ ] 5.2.7 Record passing evidence in `TDD_EVIDENCE.md`

---

## 6. Implement resolver.py (TDD)

- [ ] 6.1 Write tests for trust resolver (expect failure)
  - [ ] 6.1.1 Create `tests/unit/trust/test_resolver.py`
  - [ ] 6.1.2 Test `resolve_effective_tier()`: official+verified=official, verified+community=community, community+unregistered=unregistered, etc.
  - [ ] 6.1.3 Test `enforce_install_policy()`: official→install, verified→install, community(no flag)→prompt, community(--trust-community)→install, unregistered(no flag)→block, unregistered(--trust-unregistered)→install
  - [ ] 6.1.4 Test `append_audit_log()` appends correct line format to log file
  - [ ] 6.1.5 Run tests — expect failures
  - [ ] 6.1.6 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 6.2 Implement resolver.py
  - [ ] 6.2.1 Create `src/specfact_cli/trust/resolver.py`
  - [ ] 6.2.2 Implement `resolve_effective_tier(publisher_tier: str, registry_tier: str) -> str` (min by rank)
  - [ ] 6.2.3 Implement `enforce_install_policy(module_handle: str, tier: str, flags: InstallFlags) -> InstallDecision`
  - [ ] 6.2.4 Implement `append_audit_log(entry: AuditEntry) -> None` (append-only to `~/.specfact/module-audit.log`)
  - [ ] 6.2.5 Add `@require`, `@ensure`, `@beartype` on all public functions
  - [ ] 6.2.6 Run tests — expect pass
  - [ ] 6.2.7 Record passing evidence in `TDD_EVIDENCE.md`

---

## 7. Extend crypto_validator.py (TDD)

- [ ] 7.1 Write tests for extended crypto_validator (expect failure)
  - [ ] 7.1.1 Create or extend `tests/unit/registry/test_crypto_validator.py`
  - [ ] 7.1.2 Test `validate_module()` official tier path is unchanged (regression test — must keep passing)
  - [ ] 7.1.3 Test `validate_module()` verified tier: valid publisher sig → pass
  - [ ] 7.1.4 Test `validate_module()` verified tier: invalid publisher sig → `PublisherSignatureMismatchError`
  - [ ] 7.1.5 Test `validate_module()` community tier: valid publisher sig → pass (no countersig required)
  - [ ] 7.1.6 Test `validate_registry_endorsement()`: valid NOLD AI countersig → True
  - [ ] 7.1.7 Test `validate_registry_endorsement()`: tampered countersig → `RegistryEndorsementTamperError`
  - [ ] 7.1.8 Test `validate_module()` unknown tier → `UnknownTierError`
  - [ ] 7.1.9 Run tests — expect failures for new tests; official tests must continue to pass
  - [ ] 7.1.10 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 7.2 Extend crypto_validator.py
  - [ ] 7.2.1 Add `validated` and `community` tier branches to `validate_module()` (match/case dispatch)
  - [ ] 7.2.2 Add `validate_publisher_attestation(bundle_sha256: str, publisher_record: PublisherRecord, publisher_signature: str) -> bool`
  - [ ] 7.2.3 Add `validate_registry_endorsement(entry: RegistryEntry, root_key: Ed25519PublicKey) -> bool`
  - [ ] 7.2.4 Add `UnknownTierError`, `PublisherSignatureMismatchError`, `RegistryEndorsementTamperError` exceptions
  - [ ] 7.2.5 Do NOT modify the `official` branch (verified by regression tests)
  - [ ] 7.2.6 Add `@require`, `@ensure`, `@beartype` on new public functions
  - [ ] 7.2.7 Run tests — all must pass including regression tests for official path
  - [ ] 7.2.8 Record passing evidence in `TDD_EVIDENCE.md`

---

## 8. Integrate trust layer into module_registry install/search/info (TDD)

- [ ] 8.1 Write integration tests for module_registry with trust (expect failure)
  - [ ] 8.1.1 Create `tests/integration/test_module_trust_integration.py`
  - [ ] 8.1.2 Test install official module: no prompt, no audit log entry
  - [ ] 8.1.3 Test install verified module: no prompt, no audit log entry
  - [ ] 8.1.4 Test install community module without flag: prompt shown, abort on N
  - [ ] 8.1.5 Test install community module with `--trust-community`: install without prompt, audit log entry created
  - [ ] 8.1.6 Test install unregistered module without flag: blocked with error
  - [ ] 8.1.7 Test install unregistered module with `--trust-unregistered`: installs with warning, audit log entry
  - [ ] 8.1.8 Test `specfact module search` output contains tier badges
  - [ ] 8.1.9 Test `specfact module info` output contains publisher tier detail
  - [ ] 8.1.10 Run tests — expect failures
  - [ ] 8.1.11 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 8.2 Integrate trust layer into module_registry
  - [ ] 8.2.1 Modify `src/specfact_cli/modules/module_registry/src/` install command: call `resolver.enforce_install_policy()` before download
  - [ ] 8.2.2 Add `--trust-community` and `--trust-unregistered` flags to install command
  - [ ] 8.2.3 Modify `specfact module search` output: add tier badge column
  - [ ] 8.2.4 Modify `specfact module info` output: add publisher tier detail block
  - [ ] 8.2.5 Run integration tests — expect pass
  - [ ] 8.2.6 Record passing evidence in `TDD_EVIDENCE.md`

---

## 9. Extend scripts/publish-module.py with registry endorsement signing

- [ ] 9.1 Write tests for publish-module registry endorsement step (expect failure)
  - [ ] 9.1.1 Create or extend `tests/unit/scripts/test_publish_module.py`
  - [ ] 9.1.2 Test that endorsement signing step is called after publisher signing
  - [ ] 9.1.3 Test that `registry_signature` field is added to index entry
  - [ ] 9.1.4 Run tests — expect failures
  - [ ] 9.1.5 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 9.2 Extend scripts/publish-module.py
  - [ ] 9.2.1 Add NOLD AI countersig step after existing publisher signing
  - [ ] 9.2.2 Sign over `name + version + publisher_id + checksum_sha256` (canonical JSON, sorted keys)
  - [ ] 9.2.3 Write `registry_signature` field into the registry index entry
  - [ ] 9.2.4 Add `scripts/sign-publishers.py` (signs `publishers/index.json` with NOLD AI key; run by CI)
  - [ ] 9.2.5 Run tests — expect pass
  - [ ] 9.2.6 Record passing evidence in `TDD_EVIDENCE.md`

---

## 10. Module signing verification quality gate

- [ ] 10.1 `hatch run ./scripts/verify-modules-signature.py --require-signature`
- [ ] 10.2 If verification fails after module changes, re-sign affected manifests:
  - [ ] 10.2.1 `hatch run python scripts/sign-modules.py --key-file <private-key.pem> <module-package.yaml ...>`
  - [ ] 10.2.2 Bump module version before re-signing (patch increment)
  - [ ] 10.2.3 Re-run verification until fully green

---

## 11. Quality gates

- [ ] 11.1 `hatch run format` (ruff format + autofix)
- [ ] 11.2 `hatch run type-check` (basedpyright strict)
- [ ] 11.3 `hatch run lint`
- [ ] 11.4 `hatch run yaml-lint`
- [ ] 11.5 `hatch run contract-test`
- [ ] 11.6 `hatch test --cover -v` (full suite, all trust/ tests must pass)

---

## 12. Documentation research and review

- [ ] 12.1 Identify affected documentation:
  - [ ] 12.1.1 `docs/guides/publisher-trust.md` (new — publisher tiers, install flags, trust index URL override)
  - [ ] 12.1.2 `docs/reference/module-commands.md` (update: --trust-community, --trust-unregistered flags; tier badges in search/info)
  - [ ] 12.1.3 `docs/_layouts/default.html` (add publisher-trust guide to sidebar navigation)
  - [ ] 12.1.4 `README.md` (add brief mention of trust tier system in module ecosystem section)
- [ ] 12.2 Write/update each affected doc
  - [ ] 12.2.1 Create `docs/guides/publisher-trust.md` with Jekyll front-matter (layout, title, permalink, description)
  - [ ] 12.2.2 Update `docs/reference/module-commands.md` — add new flags, trust display examples
  - [ ] 12.2.3 Update `docs/_layouts/default.html` — add publisher-trust to Guides sidebar section
- [ ] 12.3 Verify front-matter is correct on all new/edited pages

---

## 13. Version and changelog

- [ ] 13.1 Determine version bump: this is a feature branch → minor increment
  - [ ] 13.1.1 Check current version in `pyproject.toml`
  - [ ] 13.1.2 Propose increment (e.g. `0.38.2 → 0.39.0`) and confirm with user before applying
- [ ] 13.2 Sync version across `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`
- [ ] 13.3 Add `CHANGELOG.md` entry under new `[X.Y.Z] - YYYY-MM-DD` section:
  - `Added: Publisher identity trust layer (trust/, publisher_registry, resolver, key_store)`
  - `Added: Module trust chain verification (publisher attestation + registry endorsement countersig)`
  - `Added: Trust tier display in module search and info output (--trust-community, --trust-unregistered flags)`

---

## 14. GitHub issue creation

- [x] 14.1 GitHub issue already created: [#327](https://github.com/nold-ai/specfact-cli/issues/327)
- [x] 14.2 Linked to project board
- [x] 14.3 `proposal.md` Source Tracking updated with issue #327
- [x] 14.4 `CHANGE_ORDER.md` updated with marketplace-03 entry and GitHub issue #327

---

## 15. Create PR

- [ ] 15.1 Commit all changes from inside the worktree:
  - [ ] 15.1.1 `git add src/specfact_cli/trust/ src/specfact_cli/registry/crypto_validator.py src/specfact_cli/modules/module_registry/src/ scripts/ docs/ openspec/ pyproject.toml setup.py CHANGELOG.md`
  - [ ] 15.1.2 `git commit -S -m "feat: publisher identity and module trust chain (marketplace-03)"`
  - [ ] 15.1.3 `git push -u origin feature/marketplace-03-publisher-identity`
- [ ] 15.2 Create PR body from `.github/pull_request_template.md`
  - Include: `Fixes nold-ai/specfact-cli#<issue-number>`, OpenSpec change ID: `marketplace-03-publisher-identity`
- [ ] 15.3 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/marketplace-03-publisher-identity --title "feat: publisher identity and module trust chain" --body-file /tmp/pr-marketplace-03.md`
- [ ] 15.4 `gh project item-add 1 --owner nold-ai --url <PR_URL>`
- [ ] 15.5 Verify Development link on issue; set project status to "In Progress"

---

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd /home/dom/git/nold-ai/specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/marketplace-03-publisher-identity`
- [ ] `git branch -d feature/marketplace-03-publisher-identity`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/marketplace-03-publisher-identity`
