# Change: readme-star-conversion-01

## Why

The repository README still opens with platform and governance language before showing a runnable
command or a visible proof point. First-time visitors have to scroll past conceptual explanation
before they see what SpecFact actually does on a real repository.

That is a conversion problem for the audience most likely to star or try the project:

- Python developers who want a concrete CLI outcome fast
- solo engineers and vibe coders who evaluate tools by running one command
- OSS visitors who decide in seconds whether a repo looks useful or too enterprise-heavy

The current README already contains the uvx-first review path, but it appears only after multiple
sections of framing. The README also lacks a real terminal output block that proves what the tool
returns. A first-contact surface that does not show input -> output wastes the strongest available
trust signal for an OSS CLI.

This change restructures the README so the first screen answers four questions immediately:

1. What does this do?
2. What does the output look like?
3. How do I try it right now?
4. Why should I care?

## What Changes

- Rewrite the README top section around a proof-first hero:
  - concrete one-line value proposition for developers
  - badges directly below the title
  - uvx quickstart within the first screen
  - real sample output block directly after the quickstart
  - visible CTA to star the repo if the output is useful
- Add a reproducible capture script and checked-in evidence bundle for the README sample output
- Reorder README sections so developer-first outcomes appear above enterprise and module-system
  detail
- Add a short "How SpecFact is built" section that turns the repo's OpenSpec + TDD workflow into a
  trust signal
- Add copy-pasteable pre-commit and GitHub Actions snippets near the top-half of the README
- Keep team / enterprise content, module system detail, and documentation topology, but move them
  below the proof-first onboarding flow

## Capabilities
### New Capabilities

- `readme-first-contact`: The repository README acts as a proof-first OSS landing page that leads
  with a concrete CLI outcome, a runnable command, and a visible output example
- `readme-output-evidence`: The README sample output is backed by a reproducible capture script and
  stored evidence files, not hand-written terminal copy

### Modified Capabilities

- `first-contact-story`: README messaging shifts from platform-internal framing toward developer
  outcomes while preserving truthful claims and deeper product context below the fold
- `entrypoint-onboarding`: The README must surface the runnable uvx entry path before architecture,
  backlog, governance, or module-system sections

## Impact

**Files expected to change**

- `README.md`
- `docs/index.md` if needed to preserve first-contact parity with the README
- `tests/unit/docs/test_wow_entrypoint_contract.py`
- `tests/unit/docs/test_first_contact_story.py`
- `docs/_support/readme-first-contact/capture-readme-output.sh`
- `docs/_support/readme-first-contact/sample-output/`
- `openspec/CHANGE_ORDER.md`

**Behavior / documentation impact**

- The repo's first screen becomes developer-first and proof-first
- Enterprise and governance content is preserved but moved below the fold
- The README gains a reproducible evidence path for the sample output block
- Docs parity is maintained so README and docs landing do not drift on the first-contact story

**Rollback**

- Restore the previous README structure and delete the evidence bundle references if the new layout
  proves less clear or creates maintenance burden


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #481
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/481>
- **Last Synced Status**: proposed
- **Sanitized**: false