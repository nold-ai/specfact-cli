# Implementation tasks

Planning only; all implementation tasks remain unchecked. Each numbered task is a bounded work slice, split further if it exceeds two hours. Development follows spec -> relevant failing test/reproduction -> code -> passing verification, with concise notes and CI artifacts rather than immutable hosted RED history.

## 1. Establish implementation scope

- [ ] 1.1 Fetch current refs and create a fresh issue-linked worktree from origin/dev; retain the primary checkout and verify branch/worktree ownership.
- [ ] 1.2 Refresh public hierarchy and read back #740/#481, dependencies, project state, and the dependency review; resolve concurrent In Progress ownership before implementation.
- [ ] 1.3 Revalidate these spec deltas against current runtime and the selected signed module release; reconcile superseded R07 without applying its historical task list.
- [ ] 1.4 Prepare the exact coordinated repository/organization policy migration and rollback, including required checks, trusted workflow source, and absence of per-PR authority bypasses.
- [ ] 1.5 Before behavior tests or implementation, update and review agent rules, `openspec/config.yaml`, OpenSpec templates and pre-commit guidance using the configured-gate mapping in design.md for the owner-authorized MEB migration. Remove mandatory authored run transcripts, hosted RED and proof receipts from normal work while retaining useful regression order and independent checks. Runtime enforcement changes remain in phase 4.

- [ ] 1.6 Open linked implementation PRs as bounded governance, signed-contract adoption and orchestration slices become reviewable. Integrate prerequisite slices through the reviewed migration policy before trusted pilot or enforcement; do not defer the first PR until after cutover.

## 2. Specify and demonstrate regression boundaries

- [ ] 2.1 Add focused cases for missing/empty/malformed/wrong-revision JUnit, exact selected outcomes, and no promotion of local/self-declared metadata to CI authority; observe meaningful failures before code changes.
- [ ] 2.2 Add ordinary PR, documentation, dependency, fork and dev-to-main cases that need no retained RED, frozen mapping or authority comment; retain the real #737/#738 acceptance and authentication controls.
- [ ] 2.3 Add independent-verdict and module report compatibility cases; use current fixture data without copying historical logs into Git.

## 3. Implement lean delivery

- [ ] 3.1 Adopt the signed #481 contract after verifying its manifest/payload and supported core compatibility.
- [ ] 3.2 Consume existing required suite outputs once per candidate/environment and emit compact current-run results plus always-published diagnostics.
- [ ] 3.3 Replace the default multi-stage historical proof path and promotion reuse with current-candidate validation; retain explicit legacy behavior only where supported.
- [ ] 3.4 Update contributor/Requirements/CI documentation and verify public command examples. Keep optional assurance instructions out of default generated guidance.

## 4. Verify and activate

- [ ] 4.1 Run focused/full affected tests and applicable format/type/lint/contracts, independent security, code review, OpenSpec, frozen delivery, and signature checks. Keep a fresh `.specfact/code-review.json` for the reviewed candidate and disposition every finding by fix, reasoned rejection, or individually authorized documented exception before completion; do not restart historical proof ceremonies.
- [ ] 4.2 Pilot representative PR paths from the reviewed, integrated trusted source in non-blocking mode and verify evidence identity, job conclusion propagation, artifact retention and required-check emission.
- [ ] 4.3 Apply the reviewed coordinated repository and organization enforcement cutover, verify readback on dev/main, and remove obsolete default-path proof helpers/tests that only implement retired policy.
- [ ] 4.4 Review ten representative PRs using existing CI data; record concise overhead/regression observations and resolve cutover defects. Do not add a metrics gate.

## 5. Finalize

- [ ] 5.1 Reconcile #662 and merged-awaiting-archive records without rewriting historical evidence; update CHANGE_ORDER and internal mirrors.
- [ ] 5.2 Finalize the implementation PRs opened in 1.6 with short validation/rollback notes and #740/#481 links; complete remaining reviewed integration and confirm all migration slices are accounted for.

After protected integration, archive completed changes using `openspec archive`; never manually move superseded or unimplemented deltas into canonical specs. Remove the implementation worktree only after merge.
