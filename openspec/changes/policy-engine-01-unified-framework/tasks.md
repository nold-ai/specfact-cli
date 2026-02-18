# Tasks: Policy Engine — Unified Framework (Δ1)

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply.

1. Spec deltas define behavior in `specs/policy-engine/spec.md`.
2. **Tests second**: Write tests from spec scenarios; run tests and **expect failure**.
3. **Code last**: Implement until tests pass.

---

## 1. Create git worktree branch from dev

- [x] 1.1 Ensure on dev and up to date; create branch `feature/policy-engine-01-unified-framework`; verify.

## 2. Tests first (policy validate, suggest, config)

- [x] 2.1 Write tests from spec: policy validate (deterministic, output format), policy suggest (confidence, no auto-write), config load.
- [x] 2.2 Run tests: `hatch run pytest tests/integration/commands/test_policy_engine_commands.py -v`; **expect failure**.

## 3. Implement Policy Engine

- [x] 3.1 Implement policy config loader (`.specfact/policy.yaml`); schema for DoR/DoD/Flow/PI.
- [x] 3.2 Implement `specfact policy validate` (deterministic, JSON + Markdown output; rule id, severity, evidence, recommended action).
- [x] 3.3 Implement `specfact policy suggest` (AI-assisted, confidence-scored, patch-ready; no write without explicit action).
- [x] 3.4 Run tests; **expect pass**.

## 4. Quality gates and documentation

- [x] 4.1 Run format, type-check, contract-test.
- [x] 4.2 Update docs (agile-scrum-workflows, devops-adapter-integration); CHANGELOG; version sync.

## 5. Create Pull Request to dev

- [x] 5.1 Commit, push, create PR to dev; use repo PR template.

## 6. Scope extension: policy templates and docs hints

- [x] 6.1 Add spec scenarios for `specfact policy init` template scaffolding and validate docs hints.
- [x] 6.2 Add tests for interactive/non-interactive template generation and validate error hint output.
- [x] 6.3 Implement `specfact policy init` with template selection (`--template` + interactive prompt) writing `.specfact/policy.yaml`.
- [x] 6.4 Source built-in policy templates from `resources/templates/policies/` and ensure package inclusion.
- [x] 6.5 Extend `specfact policy validate` errors to include policy format documentation hint.
- [x] 6.6 Capture failing-first and passing evidence for new scope in `TDD_EVIDENCE.md`.

## 7. Scope extension: artifact auto-discovery and format normalization

- [x] 7.1 Add spec scenarios for automatic policy input discovery from `.specfact/backlog-baseline.json` and `.specfact/plans/backlog-*`.
- [x] 7.2 Add tests for validate/suggest without `--snapshot` when standard `.specfact` artifacts exist.
- [x] 7.3 Add tests for payload normalization across `items` list, `items` dict, and `backlog_graph.items`.
- [x] 7.4 Implement policy input resolver to auto-discover existing `.specfact` artifacts when `--snapshot` is omitted.
- [x] 7.5 Implement payload normalization so policy evaluation accepts existing backlog graph and plan shapes.
- [x] 7.6 Update policy command docs to describe auto-discovery behavior and artifact precedence.
- [x] 7.7 Capture failing-first and passing evidence for this scope extension in `TDD_EVIDENCE.md`.

## 8. Scope extension: compatibility mapping for imported fields

- [x] 8.1 Add spec scenarios for resolving policy-required fields from `raw_data` aliases and description sections.
- [x] 8.2 Add tests proving imported baseline artifacts can satisfy policy-required fields without manual reshaping.
- [x] 8.3 Implement compatibility mapping from common provider/raw aliases to canonical policy fields.
- [x] 8.4 Implement lightweight description-section extraction for acceptance criteria / definition of done.
- [x] 8.5 Update docs with compatibility mapping behavior and examples.
- [x] 8.6 Capture failing-first and passing evidence for this extension in `TDD_EVIDENCE.md`.

## 9. Scope extension: result filtering/limiting and grouped output

- [x] 9.1 Add spec scenarios for `--rule` and `--limit` on validate/suggest.
- [x] 9.2 Add spec scenarios for optional `--group-by-item` output.
- [x] 9.3 Add tests covering validate/suggest filtering and limiting behavior.
- [x] 9.4 Add tests covering grouped output structure for validate/suggest.
- [x] 9.5 Implement command options (`--rule`, `--limit`, `--group-by-item`) and output shaping.
- [x] 9.6 Update docs for new options and examples.
- [x] 9.7 Capture failing-first and passing evidence for this extension in `TDD_EVIDENCE.md`.
- [x] 9.8 Adjust grouped-mode `--limit` semantics to cap item groups (not sub-item findings) and suppress duplicate flat payload arrays.
- [x] 9.9 Resolve review findings: repo-relative explicit `--snapshot` resolution and package-relative policy module imports.
