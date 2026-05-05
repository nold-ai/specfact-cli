# Implementation Tasks: marketplace-05-registry-federation

## TDD / SDD Order (Enforced)

Per config.yaml, tests MUST come before implementation for any behavior-changing task. Order:

1. Spec deltas (already created in this change)
2. Tests from spec scenarios (expect failure — no implementation yet)
3. Code implementation (until tests pass and behavior satisfies spec)
4. Evidence recorded in `openspec/changes/marketplace-05-registry-federation/TDD_EVIDENCE.md`

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `gh issue develop 329 --repo nold-ai/specfact-cli --name feature/marketplace-05-registry-federation`
  - [ ] 1.1.3 `git fetch origin && git worktree add ../specfact-cli-worktrees/feature/marketplace-05-registry-federation feature/marketplace-05-registry-federation`
  - [ ] 1.1.4 `cd ../specfact-cli-worktrees/feature/marketplace-05-registry-federation`
  - [ ] 1.1.5 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.6 `git branch --show-current` (verify: `feature/marketplace-05-registry-federation`)

> All subsequent tasks run inside the worktree directory.
> **Hard blocker**: marketplace-03 must be implemented and merged (provides `trust/key_store.py`, `trust/resolver.py`).
> marketplace-04 is recommended but not hard-blocking.

---

## 2. Review spec files (SDD)

- [ ] 2.1 Review specs created in this change
  - [ ] 2.1.1 `openspec/changes/marketplace-05-registry-federation/specs/registry-federation/spec.md`
  - [ ] 2.1.2 `openspec/changes/marketplace-05-registry-federation/specs/registry-certificates/spec.md`
  - [ ] 2.1.3 `openspec/changes/marketplace-05-registry-federation/specs/trust-propagation/spec.md`
  - [ ] 2.1.4 `openspec validate marketplace-05-registry-federation --strict`
  - [ ] 2.1.5 `hatch run yaml-lint`

---

## 3. Create registry certificate data models (TDD)

- [ ] 3.1 Write tests for registry cert models (expect failure)
  - [ ] 3.1.1 Create `tests/unit/trust/test_registry_cert_models.py`
  - [ ] 3.1.2 Test `RegistryCert`: all required fields, URL validated as HTTPS, expires_at > issued_at
  - [ ] 3.1.3 Test `RegistryCert` with non-HTTPS URL → validation error
  - [ ] 3.1.4 Test `RegistryCert` with expires_at before issued_at → validation error
  - [ ] 3.1.5 Test `RegistryStoreEntry`: includes effective_tier, trust_local bool, cert metadata
  - [ ] 3.1.6 Run tests — expect failures
  - [ ] 3.1.7 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 3.2 Implement models in `trust/models.py` (extend)
  - [ ] 3.2.1 Add `RegistryCert`, `RegistryStoreEntry` Pydantic models to `trust/models.py`
  - [ ] 3.2.2 Validators: `url` is HTTPS, `expires_at` > `issued_at`, `tier` in allowed set
  - [ ] 3.2.3 Run tests — expect pass
  - [ ] 3.2.4 Record passing evidence in `TDD_EVIDENCE.md`

---

## 4. Implement trust/registry_cert.py (TDD)

- [ ] 4.1 Write tests for registry_cert module (expect failure)
  - [ ] 4.1.1 Create `tests/unit/trust/test_registry_cert.py`
  - [ ] 4.1.2 Test `fetch_registry_cert()`: valid cert JSON at `/.specfact/registry-cert.json` → returns RegistryCert (mock HTTP)
  - [ ] 4.1.3 Test `fetch_registry_cert()`: 404 → returns None (not raises)
  - [ ] 4.1.4 Test `verify_registry_cert()`: valid sig → True
  - [ ] 4.1.5 Test `verify_registry_cert()`: tampered sig → False (or raises RegistryCertVerificationError)
  - [ ] 4.1.6 Test `verify_registry_cert()`: URL mismatch → raises RegistryCertUrlMismatchError
  - [ ] 4.1.7 Test `store_registry_cert()`: writes to registries.json correctly
  - [ ] 4.1.8 Test `get_effective_registry_tier()`: certified → tier from cert; uncertified → community; local → local
  - [ ] 4.1.9 Test `get_effective_registry_tier()`: expired cert → community with warning
  - [ ] 4.1.10 Run tests — expect failures
  - [ ] 4.1.11 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 4.2 Implement `src/specfact_cli/trust/registry_cert.py`
  - [ ] 4.2.1 `fetch_registry_cert(registry_url: str) -> RegistryCert | None`
  - [ ] 4.2.2 `verify_registry_cert(cert: RegistryCert, root_key: Ed25519PublicKey) -> bool` — URL mismatch raises RegistryCertUrlMismatchError
  - [ ] 4.2.3 `store_registry_cert(cert: RegistryCert, store_path: Path) -> None`
  - [ ] 4.2.4 `load_registry_store(store_path: Path) -> list[RegistryStoreEntry]`
  - [ ] 4.2.5 `get_effective_registry_tier(registry_url: str, store: list[RegistryStoreEntry]) -> str` — handle expiry → community downgrade with warning
  - [ ] 4.2.6 `@require`, `@ensure`, `@beartype` on all public functions
  - [ ] 4.2.7 Run tests — expect pass
  - [ ] 4.2.8 Record passing evidence in `TDD_EVIDENCE.md`

---

## 5. Update trust/resolver.py for registry tier integration (TDD)

- [ ] 5.1 Write tests for updated resolver (expect failure)
  - [ ] 5.1.1 Extend `tests/unit/trust/test_resolver.py`
  - [ ] 5.1.2 Test `resolve_effective_tier()`: all combinations from trust-propagation spec (official+verified=official, verified+community=community, verified+local=local, any+unregistered=unregistered)
  - [ ] 5.1.3 Test tier rank order: official(4)>verified(3)>community(2)>local(1)>unregistered(0)
  - [ ] 5.1.4 Run tests — expect failures for new cases (regression tests from marketplace-03 must still pass)
  - [ ] 5.1.5 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 5.2 Update `trust/resolver.py`
  - [ ] 5.2.1 Add `local` to `TIER_RANK` constant (rank: 1, between community and unregistered)
  - [ ] 5.2.2 Update `resolve_effective_tier()` to use full rank dict
  - [ ] 5.2.3 Verify marketplace-03 regression tests still pass
  - [ ] 5.2.4 Run all tests — expect pass
  - [ ] 5.2.5 Record passing evidence in `TDD_EVIDENCE.md`

---

## 6. Extend custom_registries.py with certificate verification (TDD)

- [ ] 6.1 Write tests for extended add-registry (expect failure)
  - [ ] 6.1.1 Extend `tests/unit/registry/test_custom_registries.py`
  - [ ] 6.1.2 Test `add_registry()` with valid cert: stored with effective_tier from cert
  - [ ] 6.1.3 Test `add_registry()` with 404 cert: stored as community with warning
  - [ ] 6.1.4 Test `add_registry()` with invalid cert sig: raises RegistryCertVerificationError, not stored
  - [ ] 6.1.5 Test `add_registry()` with URL mismatch: raises RegistryCertUrlMismatchError, not stored
  - [ ] 6.1.6 Test `add_registry(--trust-local)`: stored with effective_tier=local, no cert fetch
  - [ ] 6.1.7 Test `list_registries()`: output includes effective_tier badge and cert expiry
  - [ ] 6.1.8 Run tests — expect failures
  - [ ] 6.1.9 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 6.2 Extend `custom_registries.py`
  - [ ] 6.2.1 Modify `add_registry()` to call `trust/registry_cert.py: fetch_registry_cert()` → verify → store
  - [ ] 6.2.2 Add `--trust-local` flag support: skip cert fetch, store as `local` tier
  - [ ] 6.2.3 Update `list_registries()` output: add effective_tier badge column, cert expiry field
  - [ ] 6.2.4 Run tests — expect pass
  - [ ] 6.2.5 Record passing evidence in `TDD_EVIDENCE.md`

---

## 7. Update module_registry search output for effective tier (TDD)

- [ ] 7.1 Write tests for effective-tier badges in search output (expect failure)
  - [ ] 7.1.1 Extend `tests/integration/test_module_trust_integration.py`
  - [ ] 7.1.2 Test search result for verified-publisher + community-registry: badge = `[community]`
  - [ ] 7.1.3 Test search result for any-publisher + local-registry: badge = `[local]`
  - [ ] 7.1.4 Test install policy uses effective tier (verified+community → prompt if no --trust-community)
  - [ ] 7.1.5 Run tests — expect failures
  - [ ] 7.1.6 Record failing evidence in `TDD_EVIDENCE.md`

- [ ] 7.2 Update module_registry search/install
  - [ ] 7.2.1 Modify search output to use effective_tier (publisher_tier ∩ registry_tier) for badge
  - [ ] 7.2.2 Modify install pre-flight to use effective_tier for policy resolution
  - [ ] 7.2.3 Update `specfact module info` to show both publisher tier and registry tier separately
  - [ ] 7.2.4 Run tests — expect pass
  - [ ] 7.2.5 Record passing evidence in `TDD_EVIDENCE.md`

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
  - [ ] 10.1.1 Update `docs/guides/custom-registries.md` (from marketplace-02): add certificate requirements, --trust-local, tier propagation examples, cert expiry handling
  - [ ] 10.1.2 Update `docs/guides/publisher-trust.md` (from marketplace-03): add registry federation section explaining how registry tier caps publisher tier
  - [ ] 10.1.3 Update `docs/reference/module-commands.md`: document --trust-local flag, list-registries cert expiry column
  - [ ] 10.1.4 Update `docs/_layouts/default.html` if new pages added

---

## 11. Version and changelog

- [ ] 11.1 Determine version bump: feature branch → minor increment (confirm with user)
- [ ] 11.2 Sync version across `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`
- [ ] 11.3 `CHANGELOG.md` entry:
  - `Added: Registry federation with NOLD AI certificate verification (trust/registry_cert.py)`
  - `Added: --trust-local flag for air-gapped enterprise registries`
  - `Added: Trust score propagation — effective tier = min(publisher_tier, registry_tier)`
  - `Added: [local], [community], [verified], [official] tier badges propagated through registry federation`

---

## 12. GitHub issue creation

- [x] 12.1 GitHub issue already created: [#329](https://github.com/nold-ai/specfact-cli/issues/329)
- [x] 12.2 Linked to project board
- [x] 12.3 `proposal.md` Source Tracking updated with issue #329
- [x] 12.4 `CHANGE_ORDER.md` updated with marketplace-05 entry and GitHub issue #329

---

## 13. Create PR

- [ ] 13.1 Commit from inside the worktree
  - [ ] 13.1.1 `git add src/specfact_cli/trust/ src/specfact_cli/registry/custom_registries.py src/specfact_cli/modules/module_registry/ docs/ openspec/ pyproject.toml setup.py CHANGELOG.md`
  - [ ] 13.1.2 `git commit -S -m "feat: registry federation and trust certificate verification (marketplace-05)"`
  - [ ] 13.1.3 `git push -u origin feature/marketplace-05-registry-federation`
- [ ] 13.2 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/marketplace-05-registry-federation --title "feat: registry federation and trust certificate verification" --body-file /tmp/pr-marketplace-05.md`
- [ ] 13.3 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

---

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd /home/dom/git/nold-ai/specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/marketplace-05-registry-federation`
- [ ] `git branch -d feature/marketplace-05-registry-federation`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/marketplace-05-registry-federation`
