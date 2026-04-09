## Context

Core init/setup flows currently decide write behavior locally inside command helpers such as `ide_setup.py` and `modules/init/src/commands.py`. That makes file mutation semantics inconsistent: some paths skip existing files, some overwrite, and some merge only part of the payload without an explicit ownership model. Issue `#487` exposed the most visible failure mode: `.vscode/settings.json` is a user-owned config file that SpecFact touches for one narrow purpose, but the current workflow can still wipe unrelated settings if the write path degrades from merge to replacement.

This is a cross-cutting change because the same trust boundary exists for any local artifact under a user repository. The design therefore needs a reusable policy, not a one-off patch in `create_vscode_settings()`.

## Goals / Non-Goals

**Goals:**
- Define a single core contract for user-project artifact writes.
- Separate artifact ownership from mutation mechanics so commands can declare what they own.
- Preserve unrelated user configuration by default for mergeable structured files.
- Make destructive replacement explicit, recoverable, and auditable.
- Add CI/static enforcement so future init/setup work cannot reintroduce raw overwrite behavior.

**Non-Goals:**
- Rebuild every existing local-write path in one change across both repos.
- Introduce interactive patch review for every init command in this first slice.
- Support arbitrary semantic merges for all file formats; unsupported formats can fail-safe or use create-only/explicit-replace behavior.

## Decisions

### 1. Introduce a core `safe_project_write` layer with declared write modes

Core will add a shared helper that accepts:
- target path
- artifact owner id
- write mode (`create_only`, `merge_structured`, `append_managed_block`, `explicit_replace`)
- managed keys or managed block selectors
- backup/recovery policy

Rationale:
- Command code should describe intent, not implement bespoke overwrite logic.
- A central helper is the only realistic way to enforce policy in CI.

Alternatives considered:
- Fix only `.vscode/settings.json` merge logic. Rejected because the same failure pattern would persist elsewhere.
- Rely on `--force` flags alone. Rejected because the unsafe default remains.

### 2. Treat project artifacts as partially owned unless SpecFact is authoritative for the full file

The helper will require ownership classification:
- full-file ownership: SpecFact may replace with backup/explicit confirmation semantics
- partial ownership: SpecFact may modify only declared keys/sections/blocks
- unowned: command must fail unless it is create-only

For `.vscode/settings.json`, SpecFact owns only its prompt recommendation entries, not the document.

Rationale:
- Ownership is the boundary between safe reconciliation and unacceptable overwrite.
- This generalizes to YAML/JSON/TOML configs and managed markdown blocks.

Alternatives considered:
- Infer ownership heuristically from file path. Rejected because path-based assumptions are fragile and opaque.

### 3. Structured-file reconciliation will preserve unrelated user data and only rewrite managed sections

For JSON settings files, the merge logic will:
- parse existing content
- preserve all non-managed keys
- remove/refresh only prior SpecFact-managed entries
- write back normalized JSON

If parsing fails, the default behavior will be fail-safe with guidance, not empty-file replacement. Explicit replace may still exist behind force-style intent plus backup.

Rationale:
- The bug exists because full-document replacement was allowed for a partial-ownership file.

Alternatives considered:
- Best-effort fallback to `{}` on parse error. Rejected because that recreates silent data loss.

### 4. Backups and recovery metadata are mandatory for lossy operations

Any `explicit_replace` or fallback-recovery path will create a timestamped backup under a SpecFact-managed recovery location and emit actionable output naming:
- original path
- backup path
- reason replacement was required

Rationale:
- Even explicit destructive actions need a reversible path.

### 5. Add a CI gate for unsafe user-project writes

The repo will add a gate with two signals:
- static scan/rule: block direct writes to likely user-project artifacts from init/setup flows unless routed through the safe-write helper
- regression tests: fixture repositories with existing user config verifying no unrelated keys are lost

Rationale:
- Policy without enforcement will drift.
- Fixture tests catch behavior regressions the static rule cannot prove.

Alternatives considered:
- Tests only. Rejected because new raw-write code paths could land without touching existing fixtures.
- Static rule only. Rejected because safe helper misuse still needs behavioral coverage.

## Risks / Trade-offs

- `[Risk]` Initial scope may not cover every write path in one pass. → Mitigation: enforce the policy first for core init/setup and pair it with a modules-runtime adoption change.
- `[Risk]` Structured merge rules may become format-specific and verbose. → Mitigation: support only a narrow set of sanctioned merge strategies and fail-safe otherwise.
- `[Risk]` Static detection may produce false positives on safe writes outside init/setup. → Mitigation: scope the first gate to user-project artifact paths and allow helper-based exemptions only.
- `[Risk]` Backup files can clutter repos if stored locally. → Mitigation: store recovery artifacts in a dedicated SpecFact-managed location outside normal source files and document cleanup.

## Migration Plan

1. Add the core safe-write abstraction and ownership model.
2. Move `init ide` settings mutation onto the helper and cover the `#487` regression with fixtures.
3. Route other core init/setup artifact writes through the helper where applicable.
4. Add the CI/static gate and regression fixtures.
5. Land the paired modules-runtime adoption change so bundle commands use the same contract.

Rollback strategy:
- If helper rollout causes unexpected breakage, commands can temporarily fail-safe (skip with warning) rather than performing legacy overwrite behavior.

## Open Questions

- Which existing user-project artifact paths should be in the first “protected path” CI rule set beyond `.vscode/settings.json`?
- Should explicit destructive replacement remain non-interactive in CI only via `--force`, or require an additional machine-readable confirmation flag?
