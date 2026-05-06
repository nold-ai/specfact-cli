# Tasks: telemetry-01-opentelemetry-default-on

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/telemetry-01-opt-in-scope` from `origin/dev` for the scope rewrite, then use a fresh implementation branch from `origin/dev` after validation (per
  `AGENTS.md`; use `git worktree add` … `origin/dev`, not a stale local `dev` tip).
- [ ] 1.2 Run `hatch env create` in the worktree (Hatch bootstrap) before implementation.
- [ ] 1.3 Pre-flight checks: `hatch run format`/`lint` smoke as applicable, `hatch run smart-test` parity or CI-green base,
  and clean `git status` before merge-related pushes.
- [ ] 1.4 `AGENTS.md` policy self-check (worktree-only; no commits from protected checkouts).
- [ ] 1.5 Revert or supersede any pending implementation branch that shipped community default-on telemetry before continuing implementation.
- [ ] 1.6 Reconfirm scope against plan and proposal.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/telemetry-otel/spec.md` with active opt-in, first-run consent, disclosure, and enterprise-default-off scenarios.
- [ ] 2.2 Write pydantic allowlist model tests that fail first (disallowed field, missing field, wrong enum).
- [ ] 2.3 Write resolution-chain tests (env > CLI > config > init/first-run consent > profile > enterprise default > builtin disabled) that fail first.
- [ ] 2.4 Write first-run consent tests: interactive prompt accepts, interactive prompt declines, non-interactive no-prompt disabled.
- [ ] 2.5 Write telemetry disclosure tests proving tracked fields and rejected categories are rendered before consent and in status output.
- [ ] 2.6 Capture failing-first output in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement `TelemetryEmitter` with pydantic allowlist model in `src/specfact_cli/telemetry/emitter.py`.
- [ ] 3.2 Implement resolution chain in `src/specfact_cli/telemetry/resolution.py` with `@icontract`/`@beartype`.
- [ ] 3.3 Implement `specfact telemetry [enable|disable|status]` command surface.
- [ ] 3.4 Implement `specfact init` and first-interactive-run active opt-in consent recording.
- [ ] 3.5 Implement non-interactive/CI disabled-by-default handling with no prompt.
- [ ] 3.6 Implement telemetry disclosure rendering for consent and status surfaces.
- [ ] 3.7 Implement `.specfact/telemetry/sent.log` append-only writer for transmitted payloads.
- [ ] 3.8 Wire enterprise-default detection (`.specfact/enterprise.yaml` + `SPECFACT_ENTERPRISE` env).
- [ ] 3.9 Wire emitter into CLI entry point so opted-in invocations flow through it.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests until all scenarios pass; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Update `docs/` with telemetry policy, active opt-in instructions, payload schema, and "what is never tracked" disclosure.
- [ ] 4.3 Add payload schema to `docs/agent-rules/` for downstream consumers (finops, enterprise).
- [ ] 4.4 Run `openspec validate telemetry-01-opentelemetry-default-on --strict`.
- [ ] 4.5 Run `hatch run format && hatch run type-check && hatch run contract-test && hatch test --cover -v`.

## 5. Delivery

- [ ] 5.1 Mirror change to `specfact-cli-internal/wiki/sources/telemetry-01-opentelemetry-default-on.md`; run `scripts/wiki_rebuild_graph.py`.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` with this change and its downstream dependents (finops-01, enterprise-02).
- [ ] 5.3 Open PR from the validated telemetry implementation branch to `dev`.
- [ ] 5.4 After merge to `dev`, from repository root run `openspec archive telemetry-01-opentelemetry-default-on` when the
  change is complete (do not manually move change folders).
- [ ] 5.5 Post-merge cleanup: `git worktree remove <path>`, delete the telemetry implementation branch,
  `git worktree prune`, and delete the remote feature branch if your release flow requires (`git push origin --delete
  <branch>`).
