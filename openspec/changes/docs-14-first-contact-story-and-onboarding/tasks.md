# Tasks: docs-14-first-contact-story-and-onboarding

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, specs come first, tests/evidence come second, and implementation comes
last. Messaging and docs changes still require explicit before/after validation and captured
evidence in `TDD_EVIDENCE.md`.

---

## 1. Create git worktree for this change

- [x] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
- [x] 1.2 Change into the worktree and run `hatch env create`.
- [x] 1.3 Verify the branch name and working directory match `docs-14-first-contact-story-and-onboarding`.
- [x] 1.4 Run `hatch run smart-test-status` from inside the worktree.
- [x] 1.5 Run `hatch run contract-test-status` from inside the worktree.

## 2. Research and message contract

- [x] 2.1 Review the current first-contact surfaces: GitHub repo landing, `README.md`, `docs/index.md`,
  and the current modules-site homepage/handoff copy.
- [x] 2.2 Capture the current answers to:
  - [x] 2.2.1 What is SpecFact?
  - [x] 2.2.2 Why does it exist?
  - [x] 2.2.3 Why should I use it?
  - [x] 2.2.4 What do I get from it?
  - [x] 2.2.5 How do I get started?
- [x] 2.3 Define the canonical story hierarchy and the one recommended fast-start path before editing
  implementation files.
- [x] 2.4 Lock the sharper USP in writing:
  - [x] 2.4.1 SpecFact as the validation and alignment layer for software delivery
  - [x] 2.4.2 AI-assisted greenfield validation as one entry value path
  - [x] 2.4.3 Brownfield reverse-engineering into spec-first workflows as another value path
  - [x] 2.4.4 backlog-to-code drift reduction as the end-to-end business value
  - [x] 2.4.5 enterprise policy management as the scale-up story, not the only audience

## 3. Test-first / evidence-first preparation

- [x] 3.1 Add or update docs validation checks, snapshot-style assertions, or reviewable evidence that
  prove the new messaging hierarchy and first-run path are present.
- [x] 3.2 Record the pre-implementation state in `TDD_EVIDENCE.md`, including the current README/docs
  wording and any failing or missing validation checks.

## 4. Implementation: GitHub and README entry point

- [x] 4.1 Rewrite the top of `README.md` around the canonical identity statement, value proposition,
  and one fast-start path.
- [x] 4.2 Add explicit “choose your path” guidance after the primary getting-started flow.
- [x] 4.3 Document the intended GitHub repository description/topics/tagline updates in the repo-owned
  source so maintainers can apply the same story above the fold.
- [x] 4.4 Ensure the README answers the five first-contact questions explicitly and in order.

## 5. Implementation: Core docs and modules handoff

- [x] 5.1 Update `docs/index.md` and any adjacent landing/navigation copy so `docs.specfact.io`
  mirrors the same story and onboarding order as the README.
- [x] 5.2 Add or update the core-docs handoff to `modules.specfact.io` so it explains why and when a
  user should move to module-deep docs.
- [x] 5.3 Define the required modules-homepage wording/contract for the paired `specfact-cli-modules`
  implementation so the modules site routes un-oriented users back to core docs.
- [x] 5.4 Make the brownfield/spec-first handoff explicit in core and modules onboarding copy.

## 6. Implementation: Alignment and contributor guidance

- [x] 6.1 Update contributor-facing guidance so future entry-point edits preserve the same messaging
  hierarchy.
- [x] 6.2 Ensure cross-site ownership wording remains consistent with the current core-versus-modules
  documentation contract.

## 7. Validation and quality gates

- [x] 7.1 `hatch run format`
- [x] 7.2 `hatch run type-check`
- [ ] 7.3 `hatch run lint`
- [ ] 7.4 `hatch run contract-test`
- [ ] 7.5 `hatch test --cover -v`
- [x] 7.6 `hatch run yaml-lint`
- [x] 7.7 Run the targeted docs/tests/review checks added for this change.
- [x] 7.8 Update `TDD_EVIDENCE.md` with post-implementation passing evidence and before/after entry-point comparisons.
- [x] 7.9 Run `openspec validate docs-14-first-contact-story-and-onboarding --strict`.

## 8. Delivery

- [x] 8.1 Update `openspec/CHANGE_ORDER.md` with implementation status when work begins/lands.
- [x] 8.2 Stage and commit with a Conventional Commit message.
- [x] 8.3 Push the feature branch and open a PR to `dev`.
- [ ] 8.4 After merge to `dev`, remove the worktree and delete the feature branch locally/remotely.
