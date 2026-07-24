# Tasks: audit-01-reproducible-delivery

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, implement in this order: specs, failing tests, production/configuration changes, passing evidence. Do not change CI or package configuration until the corresponding policy tests fail.

---

## 1. Create git worktree for this change

- [x] 1.1 Create `feature/audit-01-reproducible-delivery` from refreshed `origin/dev` in `../specfact-cli-worktrees/feature/audit-01-reproducible-delivery`.
- [x] 1.2 Bootstrap the project environment and record smart-test and contract-test pre-flight status.

## 2. Spec-first preparation

- [x] 2.1 Add reproducible-delivery and basedpyright spec deltas.
- [x] 2.2 Add design decisions, rollback paths, source tracking, and public CI/documentation impact.
- [ ] 2.3 Update the matching internal wiki source and rebuild the graph from the internal repository root.

## 3. Test-first evidence

- [x] 3.1 Add failing workflow-policy tests for frozen installs, no dependency resolution after wheel build, explicit type project selection, JSON artifact upload, and Python 3.11–3.13 wheel smoke.
- [x] 3.2 Add failing tests for a commit-SHA-only modules fixture lock and rejection of branch refs in blocking workflows.
- [x] 3.3 Add failing unit tests for lock/export freshness and normalized reproducibility evidence.
- [x] 3.4 Run the focused tests and record failing-before output in `TDD_EVIDENCE.md`.

## 4. Implementation

- [x] 4.1 Declare the required CI tools in project metadata, generate `uv.lock` and the hash-verified CI export, and add deterministic refresh/check scripts.
- [x] 4.2 Add the reviewed modules fixture lock and make blocking runtime jobs checkout and verify that SHA.
- [x] 4.3 Convert blocking CI/release jobs to frozen environments; build once and install the wheel with `--no-deps`.
- [x] 4.4 Remove `pyrightconfig.json`; update Hatch/CI commands to pass `--project pyproject.toml` and emit JSON output.
- [x] 4.5 Add the blocking Python 3.11–3.13 wheel-smoke matrix and the scheduled/manual advisory lower-bound compatibility lane.
- [x] 4.5.1 Keep the pipx wheel-smoke invocation compatible with uv-backed pipx by
  avoiding a duplicate `--no-deps` flag while retaining the frozen dependency install.
- [x] 4.6 Update dependency-hygiene and quality-gate governance plus contributor documentation.
- [x] 4.7 Remove the unreviewed third-party SBOM generator; render and compare SPDX
  evidence from `pip inspect` using repository-owned standard-library code.

## 5. Passing evidence and quality gates

- [x] 5.1 Re-run focused tests and capture passing evidence in `TDD_EVIDENCE.md`.
- [x] 5.2 Run `openspec validate audit-01-reproducible-delivery --strict`.
- [x] 5.3 Run formatting, type-check, workflow lint, lock verification, license/security gates, contract tests, smart tests, and the SpecFact code-review gate.
- [x] 5.4 Validate a clean locked build twice and retain normalized dependency/SBOM digests as CI artifacts.

## 6. Documentation and delivery

- [x] 6.1 Update README/contributor and CI documentation for lock refresh, fixture pin updates, advisory compatibility evidence, and type-check authority.
- [x] 6.2 Apply the required version/changelog update after the final scope is known (Unreleased; no module asset change requires a module version bump).
- [x] 6.2.1 Add type-runner and dependency-trust spec deltas; update the internal wiki mirror before implementation.
- [x] 6.2.2 Add failing workflow, dependency-policy, and license-classification tests; record failing evidence.
- [x] 6.2.3 Replace the PyPI BasedPyright/Node runtime path with the committed npm type-tool lock and SHA-pinned Node setup.
- [x] 6.2.4 Remove Pylint/Dill from frozen CI and Hatch lint; prove the Ruff replacement remains blocking.
- [x] 6.2.5 Add the expiring Pycparser review record and evidence-based mixed-license classifier; repair the failing CI checks.
- [x] 6.2.6 Update contributor/security documentation, refresh frozen Python inputs, and run the complete dependency and CI policy gates.
- [x] 6.2.7 Replace the Socket-alerted Pycparser 3.0 release, add immutable-artifact provenance binding, and enforce native dependency-trust gates in pre-commit and CI.
- [ ] 6.3 Commit, push, create a PR to `dev`, link it to issue #651 and project #1, and update issue status to In Progress.

## Post-merge cleanup

- [ ] Archive with `openspec archive audit-01-reproducible-delivery`, refresh internal wiki status from its repository root, and remove the worktree after merge.
