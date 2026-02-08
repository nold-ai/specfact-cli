# Tasks: Enhanced Module Manifest Security and Integrity Validation

## TDD / SDD Order (Enforced)

Per `openspec/config.yaml`, delivery follows strict SDD+TDD order:

1. **Specs first** - Spec deltas define behavior and acceptance scenarios.
2. **Tests second** - Write tests from spec scenarios and run them expecting failure.
3. **Code last** - Implement until tests pass and behavior satisfies specs.

Do not implement production code for changed behavior until corresponding tests exist and have been run expecting failure.

---

## 1. Create git branch from dev

- [ ] 1.1 Ensure `dev` is current and create `feature/arch-06-enhanced-manifest-security`
- [ ] 1.2 Verify current branch is `feature/arch-06-enhanced-manifest-security`

## 2. Tests: manifest security metadata models (TDD)

- [ ] 2.1 Add model tests for `PublisherInfo`, `IntegrityInfo`, and versioned dependency entries
- [ ] 2.2 Add manifest parsing tests for legacy and extended metadata
- [ ] 2.3 Run `pytest tests/unit/specfact_cli/registry/test_module_packages.py -v` and expect failure for new assertions

## 3. Implementation: metadata model extension

- [ ] 3.1 Extend `src/specfact_cli/models/module_package.py` with security metadata models
- [ ] 3.2 Update validation rules for checksum/signature fields and versioned dependencies
- [ ] 3.3 Ensure public APIs use `@icontract` and `@beartype` decorators
- [ ] 3.4 Re-run related model tests and expect pass

## 4. Tests: checksum/signature validation engine (TDD)

- [ ] 4.1 Add `tests/unit/specfact_cli/registry/test_crypto_validator.py`
- [ ] 4.2 Add checksum match/mismatch tests
- [ ] 4.3 Add signature verification success/failure tests (with fixtures/mocks)
- [ ] 4.4 Run `pytest tests/unit/specfact_cli/registry/test_crypto_validator.py -v` and expect failure

## 5. Implementation: crypto validator

- [ ] 5.1 Create `src/specfact_cli/registry/crypto_validator.py`
- [ ] 5.2 Implement checksum verification helper
- [ ] 5.3 Implement signature verification helper and key import flow
- [ ] 5.4 Add robust error handling for missing keys/signatures
- [ ] 5.5 Re-run validator tests and expect pass

## 6. Tests: installer and lifecycle trust enforcement (TDD)

- [ ] 6.1 Add tests for installer rejection on checksum/signature mismatch
- [ ] 6.2 Add tests for unsigned-module opt-in behavior (`--allow-unsigned`)
- [ ] 6.3 Add tests ensuring unaffected modules still register when one fails trust checks
- [ ] 6.4 Run registry/install tests and expect failure

## 7. Implementation: trust enforcement integration

- [ ] 7.1 Update `src/specfact_cli/registry/module_installer.py` to apply verification stages
- [ ] 7.2 Update `src/specfact_cli/registry/module_packages.py` for registration-time trust checks
- [ ] 7.3 Implement explicit allow-unsigned policy path and logging
- [ ] 7.4 Re-run updated lifecycle/installer tests and expect pass

## 8. Tests: signing automation artifacts (TDD)

- [ ] 8.1 Add tests for signing script invocation and artifact expectations
- [ ] 8.2 Add CI workflow lint/validation checks for signing workflow
- [ ] 8.3 Run script/workflow tests and expect failure where new artifacts are missing

## 9. Implementation: signing automation

- [ ] 9.1 Add `scripts/sign-module.sh`
- [ ] 9.2 Add `.github/workflows/sign-modules.yml`
- [ ] 9.3 Ensure signing outputs integrate with manifest integrity fields
- [ ] 9.4 Re-run signing-related tests and expect pass

## 10. Quality gates and validation

- [ ] 10.1 Run `hatch run format`
- [ ] 10.2 Run `hatch run lint`
- [ ] 10.3 Run `hatch run type-check`
- [ ] 10.4 Run `hatch run contract-test`
- [ ] 10.5 Run `hatch run smart-test`
- [ ] 10.6 Run `openspec validate arch-06-enhanced-manifest-security --strict`

## 11. Documentation research and review

- [ ] 11.1 Identify impacted docs: `docs/reference/`, `docs/guides/`, `README.md`, `docs/index.md`
- [ ] 11.2 Add `docs/reference/module-security.md` (trust model, checksum/signature flow)
- [ ] 11.3 Update architecture docs with module trust and integrity lifecycle
- [ ] 11.4 Update `docs/_layouts/default.html` navigation for new docs

## 12. Version and changelog

- [ ] 12.1 Determine semantic version bump for new security capability
- [ ] 12.2 Sync version in `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py`
- [ ] 12.3 Add changelog entry for manifest security, integrity checks, and signing automation

## 13. GitHub issue creation

- [ ] 13.1 Export proposal to GitHub with sanitize enabled:
  - `specfact sync bridge --adapter github --mode export-only --sanitize --repo-owner nold-ai --repo-name specfact-cli --repo /home/dom/git/nold-ai/specfact-cli --change-ids arch-06-enhanced-manifest-security`
- [ ] 13.2 Verify issue created in `nold-ai/specfact-cli` with labels and sanitized body
- [ ] 13.3 Verify `proposal.md` Source Tracking contains issue number and URL

## 14. Create pull request to dev (LAST)

- [ ] 14.1 Commit completed implementation tasks with conventional commit message
- [ ] 14.2 Push `feature/arch-06-enhanced-manifest-security`
- [ ] 14.3 Create PR to `dev` with links to OpenSpec change and issue
