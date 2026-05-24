# Change: Clean code cleanup onboarding docs

## Why

The core README and getting-started docs already mention `ai_bloat`, but they describe the earlier advisory flow: run JSON, inspect findings, then use `/specfact.08-simplify`. The Code Review bundle is now planned to expose cleanup forecasts, an AI-bloat index, preserve signals, and remediation packets that any AI IDE can consume.

Core docs should explain that value without duplicating bundle-deep command reference. The first-contact path should show developers that SpecFact can help fight AI-generated bloat with deterministic review evidence, while the modules docs remain canonical for exact flags and JSON schema details.

## What Changes

- Update core onboarding docs to describe the JSON-first cleanup loop: run review, inspect forecast/index, hand remediation packets to an AI IDE, apply only safe guidance, and re-run for proof.
- Update the Code Review module handoff page so users understand which cleanup details live on `modules.specfact.io`.
- Keep README and quickstart examples aligned with the module capability without hardcoding unstable implementation details before the modules change ships.
- Link this docs change to the modules-side capability change [nold-ai/specfact-cli-modules#297](https://github.com/nold-ai/specfact-cli-modules/issues/297).

## Capabilities

### Modified Capabilities

- `readme-first-contact`: Present clean-code cleanup as a first-contact value path for AI-assisted codebases.
- `docs-aha-moment-entry`: Update the quickstart aha path to include cleanup forecast and AI IDE handoff language.
- `code-review-module`: Keep the core module handoff accurate while delegating command details to the modules docs site.
- `review-report-model`: Document the additive report shape at a high level when mirrored in core docs.

## Impact

- **Affected docs:** `README.md`, `docs/getting-started/quickstart.md`, and `docs/modules/code-review.md`.
- **Affected ownership boundary:** Core docs summarize the value path; modules docs own exact command flags and schema field details.
- **No runtime impact:** This is a docs-only companion to the modules implementation.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue:** [#584](https://github.com/nold-ai/specfact-cli/issues/584)
- **Parent Feature:** [#356](https://github.com/nold-ai/specfact-cli/issues/356)
- **Repository:** nold-ai/specfact-cli
- **Paired Modules Change:** [nold-ai/specfact-cli-modules#297](https://github.com/nold-ai/specfact-cli-modules/issues/297)
- **Last Synced Status:** synced
- **Sanitized:** false
