## Context

SpecFact already has multiple credible first-contact surfaces: the GitHub repository landing,
`README.md`, `docs.specfact.io`, and `modules.specfact.io`. The current problem is not lack of
information. It is narrative fragmentation. The product story shifts too quickly from value to
topology, modules, migration notes, and audience variants before a newcomer can decide whether
SpecFact is relevant.

The sharper product thesis coming out of the discovery work is:
- SpecFact is the validation and alignment layer for software delivery.
- In greenfield and AI-assisted work, it adds the missing rigor layer that keeps fast generation
  from becoming unstable delivery.
- In brownfield work, it reverse-engineers trustworthy understanding and feeds structured insight
  into spec-first workflows instead of competing with them.
- Across backlog, specs, and implementation, it reduces the “I wanted X but got Y” failure mode.
- At enterprise scale, it creates a path from local CLI review to centrally managed policy
  enforcement across developers, AI IDEs, and CI/CD.

The current docs architecture is also cross-repository: `specfact-cli` owns the core runtime and
canonical top-level docs, while `specfact-cli-modules` owns module-deep workflow docs. That split is
correct, but the handoff currently feels like internal structure rather than intentional onboarding.

Stakeholders are:
- first-time visitors deciding whether to try SpecFact
- returning users who need a fast path to the right docs surface
- maintainers who need a stable messaging hierarchy that does not drift

## Goals / Non-Goals

**Goals:**
- establish one canonical product story for all first-contact surfaces
- make the validation-and-alignment USP explicit instead of implied
- answer the core user questions consistently:
  - what is SpecFact?
  - why does it exist?
  - why should I use it?
  - what do I get?
  - how do I start?
- define a single fast-start path before branching into persona- or workflow-specific guidance
- differentiate greenfield validation value from brownfield reverse-engineering value without
  diluting the core identity
- clarify the core-docs versus modules-docs handoff without requiring topology knowledge first
- include GitHub repo metadata expectations so the product story starts before README scroll depth

**Non-Goals:**
- redesign the entire information architecture of all docs
- rewrite all deep reference pages or module-specific guides
- change CLI runtime behavior or command ownership
- introduce new hosting infrastructure or search systems

## Decisions

### Decision: Treat first-contact as a single product surface

The repository landing, root README, `docs/index.md`, and modules homepage will be treated as one
coordinated onboarding surface rather than independent copy islands.

Why:
- users evaluate the product across those touchpoints, not file-by-file
- a split message creates hesitation even when each page is individually “good”

Alternative considered:
- improve each page independently without a shared message hierarchy
  - rejected because it tends to recreate drift and different answers to “what is SpecFact?”

### Decision: Lead with one primary identity sentence and one fast-start path

Each first-contact surface will lead with:
- one identity statement
- one primary value proposition
- one short “start here now” path

Why:
- visitors need a fast go/no-go decision before they want product topology
- a single path reduces overwhelm and increases trial intent

Alternative considered:
- preserve multiple equal onboarding paths near the top
  - rejected because the current problem is over-choice and diluted focus

### Decision: Define the product as a validation-and-alignment layer, not a feature bucket

The canonical story will define SpecFact first as the validation and alignment layer for software
delivery, with “keep backlog, specs, tests, and code in sync” presented as the observable outcome.

Why:
- “keep in sync” is true but too generic on its own
- validation plus alignment explains the value for AI-assisted coding, brownfield analysis, and
  enterprise governance in one frame

Alternative considered:
- define the product primarily by the Swiss-knife metaphor or by enumerating command families
  - rejected because metaphor alone is not enough and capability lists obscure the USP

### Decision: Separate headline from proof points

The top-level story will answer “what is SpecFact?” in plain language. Supporting details such as
greenfield/brownfield support, SDD/TDD/contracts, AI-copilot compatibility, reverse-engineering
handoff into spec-first tools, and module extensibility will remain as proof points rather than
headline overload.

Why:
- those details are strengths, but they are secondary to basic product comprehension

Alternative considered:
- keep the current capability-dense hero
  - rejected because it communicates breadth before clarity

### Decision: Make cross-site ownership explicit but delayed

Core docs will explain that `docs.specfact.io` is the default starting point and
`modules.specfact.io` is the deeper workflow/bundle layer. The modules site will explicitly route
newcomers back to core docs if they are not yet oriented.

Why:
- the repo split is an implementation detail until the user is ready for deeper workflows

Alternative considered:
- merge all explanations into the README hero
  - rejected because it front-loads topology before value

### Decision: Define a reusable question-answer framework

The change will encode the required first-contact questions and expected answers so future updates
can be reviewed against a concrete standard.

Why:
- without a framework, copy regresses toward “everything SpecFact can do”
- this creates an auditable quality bar for README/docs/repo metadata changes

## Risks / Trade-offs

- [Risk] Stronger positioning may deprioritize some secondary capabilities above the fold.
  → Mitigation: keep those capabilities in proof sections and “choose your path” cards lower on the page.

- [Risk] The enterprise policy-management direction could overshadow current solo/team usefulness.
  → Mitigation: position enterprise policy as the scale-up path, not the prerequisite reason to adopt.

- [Risk] Cross-repo docs handoff changes may need mirrored implementation in `specfact-cli-modules`.
  → Mitigation: define the contract here and call out the modules-side follow-up explicitly in tasks.

- [Risk] Maintainers may disagree on the strongest primary message.
  → Mitigation: make the first-contact questions explicit and use them as review criteria rather than taste alone.

- [Risk] GitHub repo metadata changes are partly outside code review flow.
  → Mitigation: document the target description/topics/tagline in the change so maintainers can apply them consistently.

## Migration Plan

1. Define the first-contact story and onboarding requirements in OpenSpec.
2. Rewrite README hero and first-run sections around the validation-and-alignment hierarchy.
3. Update `docs/index.md` and adjacent landing copy to mirror the same hierarchy.
4. Define the required modules-docs handoff copy and implementation note for the modules repo,
   especially around brownfield reverse-engineering and bundle-deep workflow ownership.
5. Update contributor/docs guidance so future edits preserve the same structure.
6. Capture before/after evidence from the affected pages and verify markdown/docs gates.

Rollback is straightforward: revert the docs and metadata copy changes if the new positioning proves
confusing or materially worsens navigation metrics/feedback.

## Open Questions

- Should the canonical identity sentence explicitly include “Swiss-knife CLI” in every surface, or
  should that phrase remain the README/repo-facing metaphor while docs use a plainer version?
- Which GitHub topics/tags best reinforce discoverability without overfitting to internal jargon?
- How much modules-site wording can be changed in this repo versus requiring a paired change in
  `specfact-cli-modules`?
