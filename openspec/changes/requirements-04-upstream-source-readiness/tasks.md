## 1. Governance and dependency readiness

- [x] 1.1 Create core issue #648 under Requirements Layer feature #366 with
  `enhancement` and `change-proposal` labels and SpecFact CLI project assignment.
- [x] 1.2 Link the modules companion issue
  `nold-ai/specfact-cli-modules#346` in the paired proposal and issue scope.
- [ ] 1.3 Synchronize #648 and #346 with the released core version and explicit
  cross-repository blocker relation before module implementation begins.
- [ ] 1.4 Recheck issue state, parent, labels, project assignment, blockers,
  and active-work concurrency immediately before implementation.

## 2. Specification and failing evidence

- [x] 2.1 Add a pinned fixture representing the supported official Spec Kit
  scaffold and derive failing tests for placeholder and
  `NEEDS CLARIFICATION` rejection.
- [x] 2.2 Add failing tests for missing substantive Functional Requirements and
  missing meaningful acceptance scenarios while user stories are present.
- [x] 2.3 Add failing tests proving completed Spec Kit sources retain stable IDs,
  SHA-256 revisions, given/when/then rules, idempotency, and read-only sources.
- [x] 2.4 Add failing tests for policy-required OpenSpec validation failure,
  missing required validator, and portable no-validator import.
- [x] 2.5 Record targeted failing-before evidence in `TDD_EVIDENCE.md`.

## 3. Core source-readiness implementation

- [x] 3.1 Define the contract-safe readiness policy and bounded OpenSpec CLI
  invocation without ambient executable probing.
- [x] 3.2 Implement atomic readiness diagnostics in the native import-result
  contract: `incomplete-source-template`, `source-incomplete`,
  `source-invalid`, and `upstream-validator-unavailable`.
- [x] 3.3 Implement narrow, fixture-backed Spec Kit draft-marker and structural
  completeness checks without generic bracket matching or a new authoring
  schema.
- [x] 3.4 Integrate readiness before OpenSpec and Spec Kit normalization, with
  public API contracts (`@beartype`, `@require`, `@ensure`) on any new public
  surfaces.
- [x] 3.5 Run targeted tests and record passing-after evidence in
  `TDD_EVIDENCE.md`.

## 4. Compatibility, documentation, and quality gates

- [x] 4.1 Add regression coverage for existing accepted native imports and
  readiness-versus-downstream-gate separation.
- [x] 4.2 Update core requirements/import documentation with source-readiness
  diagnostics and policy behavior; cross-link the modules command guidance.
- [x] 4.3 Run format, type-check, lint, contract, smart-test, targeted tests,
  and relevant documentation checks.
- [x] 4.4 Run a fresh full SpecFact code review JSON report after the last
  substantive change, resolve every finding, and record the evidence.

## 5. Delivery

- [ ] 5.1 Run `openspec validate requirements-04-upstream-source-readiness --strict`
  and synchronize #648 and the internal wiki source page with final scope,
  version, dependencies, and status.
- [ ] 5.2 Release the core contract, update the modules issue blocker, and open
  the companion modules implementation only after compatibility is published.
- [ ] 5.3 Open the core PR to `dev` with core and modules dependency evidence.
