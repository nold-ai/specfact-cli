## Planning validation

Date: 2026-09-20 Europe/Berlin. Scope: proposal/specification and dependency alignment only; runtime implementation is unstarted.

Owner approval covers paired workflow proposals and amendments to the existing R09 planning PRs. This record is not implementation readiness: refresh GitHub metadata and current source/producer interfaces before behavior work. Implementation tasks remain unchecked.

OpenSpec 1.13.0: strict validation PASS for this change and the amended R09 change. Scoped Markdown (core repository configuration used for paired public planning files) and `git diff --check`: PASS. New capabilities have no existing canonical-name collision; R09 deltas retain their existing capability ownership. Existing PR Requirements/authority failures remain separately disclosed; no fabricated sidecar, analyzer PASS or unconditional-success gate is introduced.

Ownership review: workflow local state is separate from governance envelopes, Requirements v3, Code Review 1.6/1.7 and optional seal/conformance contracts. Dependency direction is modules #481 -> workflow modules -> core runtime adoption; projection can ship independently. Related roadmap work is not a blanket blocker. Native edges and metadata must be read back after issue creation.

GitHub metadata readback confirmed User Story type, djm81 assignment, enhancement/openspec/change-proposal labels, SpecFact CLI project 1 / Todo, native core #742 parent #372 and modules #483 parent #163. Native blocked-by and blocking readback confirms modules #481 -> modules #483 -> core #742; no reverse dependency or added optional-roadmap blocker. Readback is a planning snapshot, not future implementation readiness.

Normal pre-commit was exercised on this planning amendment. The Requirements stage rejected both R09 and workflow proposals with `unsupported-sidecar-schema` (two sources, zero passing); downstream Block2 checks therefore did not run. Other applicable commit hooks passed. Retain the existing owner-authorized planning-only `SKIP=cli-block2` exception for this commit; no runtime/remote gate change or passing Requirements/CI claim. Core used its exact pinned modules fixture for the diagnostic.

All 13 active changes represented in this PR diff passed strict OpenSpec validation after alignment. This is structural planning validation, not runtime acceptance.
