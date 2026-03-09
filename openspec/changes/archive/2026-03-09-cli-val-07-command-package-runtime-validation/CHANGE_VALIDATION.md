# Change Validation: cli-val-07-command-package-runtime-validation

- **Validated on (UTC):** 2026-03-06T08:06:49Z
- **Workflow:** /wf-validate-change (proposal-stage dry-run validation)
- **Strict command:** `openspec validate cli-val-07-command-package-runtime-validation --strict`
- **Result:** PASS

## Implementation Finalization Update

- **Updated on (UTC):** 2026-03-09T21:23:21Z
- **Implementation status:** Implemented, archive pending
- **Finalized scope additions during implementation:**
  - `backlog map-fields` now ignores non-mappable built-in required ADO hierarchy identifiers (`System.IterationId`, `System.AreaId`)
  - `backlog map-fields` now emits incremental `N/M` metadata-fetch progress after work item type selection
  - shared bridge logger diagnostics are hidden from normal console output unless `--debug` is enabled
  - `specfact module upgrade` now reports each upgraded module on its own line with `old -> new` versions
- **Evidence updated:** `TDD_EVIDENCE.md` contains failing/passing runs for backlog mapping, bundled-upgrade warning severity, logger-output leakage, and module-upgrade output formatting
- **Docs updated:** `docs/technical/testing.md` and `docs/reference/debug-logging.md`
- **Version release target:** `0.40.3`

## Final Validation Evidence

- Focused regressions passed:
  - `python -m pytest tests/unit/test_runtime.py -q -k bridge_logger_stays_off_console_when_debug_disabled`
  - `python -m pytest tests/unit/registry/test_module_installer.py -q -k satisfied_dependencies_without_warning`
  - `python -m pytest tests/unit/modules/module_registry/test_commands.py -q -k "upgrade_command or upgrade_without_module_name_upgrades_all_marketplace or one_line_per_module_with_versions"`
  - `cd /home/dom/git/nold-ai/specfact-cli-modules && HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/specfact_backlog/test_map_fields_command.py -q -k "reports_progress_for_selected_work_item_type_metadata or interactive_ignores_builtin_required_hierarchy_ids"`
- Local quality gates passed during implementation:
  - `hatch run format`
  - `hatch run type-check`
  - `hatch run lint`
  - `hatch run yaml-lint`
  - `hatch run contract-test`
  - `hatch run smart-test`

## Final Assessment

- Runtime-validation scope is now implemented and evidenced.
- Normal non-debug output is cleaner and user-directed, while actionable warnings remain visible through explicit formatting paths.
- The change is ready for commit/PR/archive workflow steps.

## Scope Summary

- **New capabilities:** `command-package-runtime-validation`
- **Modified capabilities:** `user-module-root`, `debug-logging`
- **Declared dependencies:** marketplace-02 archived baseline, backlog-core-05 archived user-root bootstrap baseline, module-migration-08 archived release-stabilization baseline
- **Proposed affected code paths:**
  - `src/specfact_cli/registry/module_packages.py`
  - `src/specfact_cli/registry/module_discovery.py`
  - CLI validation / acceptance test surfaces in this repository
  - command-package manifests and Typer apps in `../specfact-cli-modules/packages/`

## Format Validation

- **proposal.md Format:** PASS
  - Required sections present: Why, What Changes, Capabilities, Impact
  - Capability contract is explicit: one new capability plus two modified capabilities
  - Scope is specific to command-package runtime validation and startup-output behavior
- **design.md Format:** PASS
  - Context, Goals / Non-Goals, Decisions, Risks / Trade-offs, Migration Plan, and Open Questions are present
  - Design decisions explain inventory source, validation order, and warning-vs-debug behavior
- **specs Format:** PASS
  - `specs/command-package-runtime-validation/spec.md` defines inventory, execution order, invocation coverage, output leakage detection, and actionable reporting
  - `specs/user-module-root/spec.md` adds canonical-user-root silent-startup requirements
  - `specs/debug-logging/spec.md` adds debug-gated discovery-diagnostic requirements
- **tasks.md Format:** PASS
  - Hierarchical numbered sections and checkbox tasks are present
  - TDD / SDD ordering is called out explicitly
  - Tasks enumerate command-family coverage in logical order across core and official bundles

## Dependency and Integration Review

- **CHANGE_ORDER.md consistency:** PASS
  - New pending row added under CLI end-user validation as `cli-val-07-command-package-runtime-validation`
  - Baseline dependencies point to already-implemented archived work for marketplace install, user-root bootstrap, and release stabilization
- **Cross-repo integration:** PASS
  - Change explicitly depends on both this repo and the sibling `specfact-cli-modules` repo being analyzed together
  - Inventory source is aligned with bundle manifests plus Typer app trees, which reduces drift between docs and shipped command surface
- **Release-validation fit:** PASS
  - Change is a validation/fix planning track, not a bundle taxonomy redesign
  - Scope directly addresses the reported `0.40.1` startup-noise regression and extends coverage to every shipped command family

## Breaking-Change Analysis

- **Breaking changes detected:** 0 at proposal stage
- **Behavioral tightening proposed:** yes
  - canonical `~/.specfact/modules` startup must stop emitting non-actionable duplicate/shadow output
  - internal discovery/protocol diagnostics must move behind debug-mode channels
- **Risk assessment:** low to medium
  - functional risk is low because command availability is preserved
  - regression risk exists if warning suppression hides legitimate conflicts, but the specs explicitly preserve actionable security and scope-precedence warnings

## Impact Assessment

- **Impact Level:** Medium
- **Code Impact:** registry/discovery logging and validation harness coverage
- **Test Impact:** new or extended command inventory, black-box/runtime validation, and startup-noise regression tests
- **Documentation Impact:** contributor/release validation workflow docs need updates
- **Release Impact:** patch-level bugfix plus stronger release-validation coverage

## Validation Outcome

- Required artifacts are present and complete: `proposal.md`, `design.md`, `specs/`, `tasks.md`
- `openspec validate ... --strict` passes
- The change is ready for implementation-phase intake
- The plan is sufficiently scoped to audit:
  - core commands (`specfact`, `init`, `module`, `upgrade`)
  - all five official bundles (`project`, `spec`, `code`, `backlog`, `govern`)
  - nested command families and leaf commands via inventory expansion from Typer apps
