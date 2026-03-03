# Gap Analysis: module-migration-02-bundle-extraction

**Date:** 2026-03-02
**Author:** Review of completed change scope against full migration requirements
**Scope:** Assess whether migration-02 tasks and follow-up changes (migration-03, migration-04) achieve a full, lossless slice-and-dice of the 17 non-core modules out of specfact-cli into specfact-cli-modules, at the same quality standard as the original codebase.

---

## Migration completion state at time of review

| Layer | Status |
|-------|--------|
| Bundle package structure in specfact-cli-modules | ✅ Done |
| Module source moved + re-export shims in place | ✅ Done |
| Registry index.json populated (5 entries, signed) | ✅ Done |
| Official-tier crypto_validator, module_installer | ✅ Done |
| publish-module.py bundle mode | ✅ Done |
| In-repo manifest re-signing | ✅ Done |
| specfact-cli PR #332 CI green | ✅ Done |
| Migration-complete gate (17.8) | ⏳ Pending |
| Import dependency categorization (section 19.1) | ❌ Not started |
| Test migration + quality parity (section 18) | ❌ Not started |
| Dependency decoupling full execution (section 19.2–19.4) | ❌ Not started |
| Docs migration (section 20) | ❌ Not started |
| Build pipeline in specfact-cli-modules (section 21) | ❌ Not started |
| Central config files in specfact-cli-modules (section 22) | ❌ Not started |
| License and contribution artifacts (section 23) | ❌ Not started |

---

## Gap 1 — IMPORT_DEPENDENCY_ANALYSIS.md is uncategorized (CRITICAL)

**Location:** `IMPORT_DEPENDENCY_ANALYSIS.md`, 85 imports listed
**Severity:** Critical — blocks safe migration-03 implementation
**Status:** NOT started

### Finding

`IMPORT_DEPENDENCY_ANALYSIS.md` lists every `from specfact_cli.* import` found in specfact-cli-modules but the Category, Target bundle, and Notes columns are **all blank**. Section 19.1 is the task that fills this in, but it is currently not a prerequisite for gate 17.8.

### Why it blocks migration-03

Migration-03 will delete `src/specfact_cli/modules/{project,plan,backlog,...}/` directories. If any of the 85 uncategorized imports resolve to code that lives in those or adjacent directories (e.g., `specfact_cli.sync.*`, `specfact_cli.analyzers.*`, `specfact_cli.generators.*`, `specfact_cli.backlog.*`), the bundle code in specfact-cli-modules will raise `ImportError` at runtime after migration-03.

The suggested initial categorization table labels these as likely MIGRATE candidates:
- `analyzers.*` → codebase/project
- `sync.*` → codebase/project
- `backlog.*` → backlog
- `generators.*`, `comparators.*`, `enrichers.*` → spec/project
- `importers.*`, `migrations.*`, `parsers.*` → project

If these are MIGRATE but have not yet been moved into specfact-cli-modules when migration-03 deletes in-repo module dirs, the migration is **not lossless** — it silently breaks bundle imports.

### Required action

Section 19.1.1–19.1.4 (full import categorization) **must complete before gate 17.8** is run and accepted. Migration-03 may not begin implementation until all MIGRATE-tier items are either:
- (a) migrated to specfact-cli-modules (preferred), or
- (b) confirmed as CORE with documented rationale (stays in specfact-cli)

**New tasks added:** See tasks.md section 17.8.0.

---

## Gap 2 — Migration-03 deletes Python import shims without declaring it (CRITICAL)

**Location:** migration-03 proposal "What Changes"
**Severity:** Critical — undeclared breaking change in migration-03
**Status:** NOT documented in migration-03

### Finding

Migration-02 places `__getattr__` re-export shims at:
```
src/specfact_cli/modules/<name>/src/<name>/__init__.py
```
These shims delegate `from specfact_cli.modules.validate import X` to `from specfact_codebase.validate import X` and emit a `DeprecationWarning`.

Migration-02's deprecation notice states: "removal in next major version."

Migration-03's "What Changes" says: "DELETE: `src/specfact_cli/modules/{...}/`" — the **entire directory** — which implicitly deletes these shims. However, migration-03's proposal does **not explicitly state** that the `specfact_cli.modules.*` Python import compatibility is being removed. The "Backward compatibility" section in migration-03 only mentions CLI-visible command changes (flat commands), not import path compatibility.

### Why this matters

Any code (third-party integrations, internal tools, documentation examples) that does `from specfact_cli.modules.validate import app` will get `ImportError` after migration-03 without any warning in the migration-03 change notes.

Additionally: migration-02 says "one major version cycle" for shim removal, but going from 0.2x to 0.40 may not satisfy the semantic intent of "one major version." This needs an explicit version-cycle justification.

### Required action

Migration-03's proposal must be updated to:
1. Explicitly state that the `specfact_cli.modules.*` Python import shims are removed as part of this change
2. Add a "Migration path for import consumers" section to its documentation update
3. Justify what "one major version cycle" means in this context (version series reference)

**New task added:** See tasks.md section 17.9 — task 17.9.2.

---

## Gap 3 — Flat-shim removal claimed by both migration-03 and migration-04 (CRITICAL)

**Location:** CHANGE_ORDER.md wave table; migration-03 proposal; migration-04 proposal
**Severity:** Critical — overlapping scope, risk of double-delete or conflicting implementations
**Status:** NOT reconciled

### Finding

| Change | Wave | Claims to remove |
|--------|------|-----------------|
| migration-04 | Wave 3 (parallel with 02) | `FLAT_TO_GROUP` + `_make_shim_loader()` in `module_packages.py` |
| migration-03 | Wave 4 (after 02) | "Backward-compat flat command shims registered by `bootstrap.py` in module-migration-01" |

Both changes claim to remove the flat command shim layer. CHANGE_ORDER.md places migration-04 **before** migration-03 in the wave order. If migration-04 is implemented first and removes `FLAT_TO_GROUP` and `_make_shim_loader()` from `module_packages.py`, migration-03's flat shim removal claim will either:
- Fail (already deleted)
- Silently do nothing (if the code is gone)
- Create confusion about what migration-03 is actually removing from `bootstrap.py`

The distinction between `module_packages.py` (migration-04 target) and `bootstrap.py` (migration-03 target) may be intentional but is not documented. Neither proposal has a "depends on / assumes" note about the other.

### Required action

1. Determine whether migration-04's `module_packages.py` removal and migration-03's `bootstrap.py` removal are genuinely distinct (different code locations, different responsibilities)
2. If distinct: update both proposals to cross-reference each other and document which code each change removes
3. If overlapping: update migration-03 to mark flat shim removal as "done by migration-04 (prerequisite)" and remove the duplicate claim
4. Update CHANGE_ORDER.md to reflect the clarified dependency (migration-03 should likely block-after migration-04, or migration-04's description should exclude the bootstrap.py part)

**New task added:** See tasks.md section 17.9 — task 17.9.1.

---

## Gap 4 — Sections 18–23 scope ambiguity: no explicit follow-up change ownership (IMPORTANT)

**Location:** tasks.md sections 18–23; "Handoff" section
**Severity:** Important — creates permanent open state for migration-02 or loses work
**Status:** Sections are pending with no blocking relationship defined

### Finding

Migration-02's "Handoff to migration-03 and migration-04" section defines migration-02 as complete when:
1. specfact-cli PR merged to dev
2. specfact-cli-modules five bundles merged
3. Migration-complete gate passes (17.8)

But tasks.md sections 18–23 (≈50 sub-tasks) remain `[ ]` pending and live inside migration-02's task file. This creates two bad outcomes:
- **Option A**: Migration-02 stays open indefinitely while sections 18–23 are worked through → blocks the "non-reversible gate" from being accepted → blocks migration-03
- **Option B**: Migration-02 is closed at 17.8 with 18–23 silently abandoned → specfact-cli-modules permanently lacks quality parity

### Required action

Create a dedicated follow-up change `module-migration-05-modules-repo-quality` that owns sections 18–23. Mark sections 18–23 in migration-02's tasks.md as "DEFERRED → module-migration-05" with a cross-reference. Update CHANGE_ORDER.md with the new entry blocked by migration-02.

**New files created:** `openspec/changes/module-migration-05-modules-repo-quality/proposal.md` and `tasks.md` (stubs with full scope from migration-02 sections 18–23).

---

## Gap 5 — No quality guardrails in specfact-cli-modules before it becomes canonical source (IMPORTANT)

**Location:** specfact-cli-modules repo quality tooling
**Severity:** Important — quality regression as soon as migration-03 closes
**Status:** Partially addressed by migration-05, but timing is not enforced

### Finding

After migration-03 closes, specfact-cli-modules is the canonical home for 17 modules. A developer fixing a bug in `specfact_backlog` after migration-03 will find:
- No `hatch run contract-test` (`@icontract` / CrossHair validation)
- No coverage threshold enforcement
- No `hatch run smart-test` (incremental test runner)
- No pre-commit hooks
- No basedpyright strict configuration
- No PR orchestrator or branch protection

This is a direct regression against the project's quality standard ("continued work on bundles in specfact-cli-modules has the same quality standards and test scripts as in specfact-cli").

### Required action

Module-migration-05 sections 18.2 (quality tooling), 21 (build pipeline), and 22 (central config) **must land before or simultaneously with migration-03**. The CHANGE_ORDER.md dependency must reflect this: migration-03 should be blocked-by or co-released-with the quality tooling sections of migration-05.

At minimum, sections 21 (PR orchestrator workflow) and 22 (root config files — pyproject, ruff, basedpyright, pylint) must be done before migration-03 closes. Tests (section 18.3) and dependency decoupling (section 19) can follow.

**Action captured in CHANGE_ORDER.md and migration-05 proposal.**

---

## Gap 6 — Migration gate is presence-only; no behavioral parity smoke test (MINOR)

**Location:** tasks.md 17.8; MIGRATION_GATE.md
**Severity:** Minor — gate is necessary but not sufficient for lossless claim
**Status:** Gate script checks presence (74/74 ✅) but not behavior

### Finding

`validate-modules-repo-sync.py --gate` verifies:
- All 74 files present in specfact-cli-modules: ✅
- Content differences accepted with `SPECFACT_MIGRATION_CONTENT_VERIFIED=1`: ✅

There is no automated step that exercises bundle code through the **installed bundle path** (not shims) to confirm behavioral parity. A logic divergence introduced between extraction and gate would pass.

### Required action

Add to gate checklist (task 17.8) a behavioral smoke test step:
```bash
hatch test -- tests/unit/bundles/ tests/integration/test_bundle_install.py -v
```
This verifies the bundle lifecycle (install, official-tier verify, dep resolution) and bundle layout, which exercises the canonical bundle paths rather than shims.

**Updated in tasks.md section 17.8.**

---

## Gap 7 — Post-extraction cleanup ownership clarified (MINOR)

**Location:** design.md Q1; migration-03/05 handoff
**Severity:** Minor — deferred scope boundary
**Status:** ownership now assigned to migration-06 (repurposed)

### Finding

After bundle extraction and core slimming, residual non-core coupling may remain in specfact-cli core (for example models/utilities/helpers still only needed by extracted bundles). This cleanup scope was not explicitly owned in migration-03/05 task boundaries.

### Required action

Assign residual decoupling cleanup to a dedicated change: `module-migration-06-core-decoupling-cleanup`, sequenced after migration-03 with migration-05 quality baseline complete.

**Captured in CHANGE_ORDER.md as migration-06 repurposed scope.**

---

## Gap 8 — No bundle version divergence policy (MINOR)

**Location:** Absent from all change artifacts
**Severity:** Minor — operational gap post-migration
**Status:** Not addressed in any pending change

### Finding

All five bundles are currently version-locked to core's minor version (e.g., 0.29.0). After migration-03 enables independent development in specfact-cli-modules, bundles and core will have independent release cycles. No policy exists for:
- Minimum/maximum acceptable divergence between a bundle version and core's `core_compatibility` range
- What constitutes a patch vs minor vs major bump for a bundle (e.g., "adding a command = minor, fixing a bug = patch, changing a public API = major")
- How a bundle consumer pins versions against `core_compatibility`

### Required action

Add a "Bundle versioning policy" section to specfact-cli-modules `AGENTS.md` or a spec delta during migration-05 section 18.5.3. Include: semver semantics for bundles, `core_compatibility` field maintenance rules, and release process.

**Captured as a task in migration-05 tasks.md.**

---

## Remediation ownership summary

| Gap | Severity | Owned by | Actions taken |
|-----|----------|----------|---------------|
| 1. Import categorization not done before gate | Critical | migration-02 (17.8.0) | Added pre-gate section 17.8.0 to tasks.md |
| 2. Migration-03 undeclared Python import shim removal | Critical | migration-02 (17.9.2) + migration-03 proposal | Added task 17.9.2 to update migration-03 |
| 3. Flat-shim overlap migration-03 vs migration-04 | Critical | migration-02 (17.9.1) + both proposals | Added task 17.9.1 to reconcile; CHANGE_ORDER.md updated |
| 4. Sections 18–23 scope ambiguity | Important | New: module-migration-05 | Created migration-05 stub; marked 18–23 deferred in tasks.md |
| 5. No quality baseline before migration-03 | Important | module-migration-05 + CHANGE_ORDER | Added migration-05 as prerequisite for migration-03 in CHANGE_ORDER.md |
| 6. Gate lacks behavioral smoke test | Minor | migration-02 (17.8) | Added smoke test step to 17.8 checklist |
| 7. Residual core decoupling cleanup unassigned | Minor | Assigned in CHANGE_ORDER.md | Repurposed migration-06 to core decoupling cleanup |
| 8. No bundle version divergence policy | Minor | module-migration-05 (section 18.5.3) | Added task to migration-05 tasks.md |
