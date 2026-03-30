# Change: First-contact story and onboarding overhaul across repo and docs entry points

## Why

SpecFact looks credible and powerful to first-time visitors, but the current first-contact surfaces
still make users absorb topology, module ownership, and multiple personas before they can answer the
most important go/no-go questions: what SpecFact is, why it exists, why they should care, what they
get, and how to start immediately.

The sharper product truth is that SpecFact is the validation and alignment layer for software
delivery in the age of AI-assisted coding: it reduces drift between backlog intent, specification,
implementation, tests, and policy. That matters in four concrete situations:
- AI-assisted or “vibe-coded” greenfield work needs a validation layer so fast wins do not become
  fragile long-term liabilities.
- Brownfield systems need reverse-engineered understanding and structured handoff into spec-first
  tools such as OpenSpec or Spec-Kit.
- Teams need protection against the “I wanted X but got Y” drift that starts in backlog language and
  grows through specification and implementation.
- Larger organizations need a path from local CLI rigor to centrally managed policy enforcement
  across developers, AI IDEs, and CI/CD.

If the README, GitHub repo metadata, core docs homepage, and modules docs homepage do not tell that
story with a fast path to first value, users may respect the project but still hesitate to try it.
This change sharpens those entry points so the project feels both mature and compelling on first
contact.

## What Changes

- **OVERHAUL** the root `README.md` so it leads with a single product story centered on validation
  and alignment, a clear value proposition, a fast first-run path, and segmented “choose your path”
  guidance for different users.
- **REFRAME** the core docs landing pages (`docs/index.md` and related navigation/landing copy) so
  they behave like onboarding entry points rather than internal documentation indexes, while making
  the “why now” case for AI-assisted and brownfield delivery.
- **ALIGN** the modules docs homepage handoff so it clearly explains what belongs on
  `docs.specfact.io` versus `modules.specfact.io` without forcing newcomers to learn repository
  topology before they understand the product, and so brownfield/spec-first handoff value is
  explicit.
- **IMPROVE** GitHub repository first-contact metadata, including repository description, topics/tags,
  and any repo-facing intro copy that influences the landing impression before README scroll depth.
- **ANSWER** the key first-contact questions consistently across all central entry points:
  - What is SpecFact?
  - Why does it exist?
  - Why should I use it?
  - What do I get from it?
  - How do I get started?
- **DEFINE** a repeatable messaging hierarchy and story framework so future docs/homepage changes do
  not drift back into capability sprawl or topology-first wording.
 - **POSITION** the future enterprise policy-management path clearly enough to strengthen trust and
   seriousness, without making the product sound enterprise-only today.

## Capabilities

### New Capabilities

- `first-contact-story`: defines the canonical product story and messaging hierarchy for the repo
  homepage, docs homepage, and cross-site handoff surfaces, centered on SpecFact as the validation
  and alignment layer for software delivery.
- `entrypoint-onboarding`: defines the required first-run onboarding path and “choose your path”
  navigation across README, core docs, and modules docs entry points for greenfield, brownfield,
  and backlog-to-code workflows.

### Modified Capabilities

- `documentation-alignment`: documentation landing and handoff requirements must align with the new
  first-contact story, repo/docs/modules ownership framing, and cross-site discoverability rules.

## Impact

- **Affected repo entry points**: `README.md`, GitHub repo description/topics guidance, badges, and
  above-the-fold intro copy.
- **Affected core docs**: `docs/index.md`, any shared landing-page copy, and sidebar/top-nav wording
  that shapes the first visit to `https://docs.specfact.io/`.
- **Affected modules docs coordination**: homepage copy and cross-site handoff expectations for
  `https://modules.specfact.io/` (with implementation split across the owning repo where needed).
- **Affected docs policy**: contributor guidance must reflect the canonical message hierarchy and the
  required first-contact questions.
- **User-facing impact**: higher clarity, faster orientation, stronger trial intent, and more
  coherent positioning for both new and returning users, especially around AI-assisted delivery,
  brownfield modernization, and end-to-end alignment value.
