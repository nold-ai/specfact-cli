# Change: Patch certificate trust and prepare an MCP-patched scanner distribution

## Why

The owner requested autonomous fixes through green PR #782, with signing only in
CI/CD, on 2026-10-20 Europe/Berlin. The certifi correction is published at
66ee3d58959e7798a6a7a5a1ed5c41d1db37fbc0. Its package, compatibility and ordinary
quality checks pass. The strict frozen audit still reports MCP 1.29.0 against
CVE-2026-59951. Supported upstream Semgrep releases through 1.182.0 exact-pin it.
Normal dependency resolution cannot select patched MCP 1.30.0 with those wheels.

On 2026-10-21 the architecture review selected a separately named, CI-produced
Semgrep distribution over isolation alone or embedding the scanner into core.
Isolation retains the vulnerable delivered dependency. The new public package
identity preserves optional scanner installation, normal pip/uv resolution and
future core PyPI metadata compatibility. Publication is an explicit operator
boundary, not an outcome already established by this proposal.

## What Changes

- Retain certifi >=2026.10.19 and coherent core patch version 0.55.11.
- Correct Requirements proof to inspect the exact frozen certifi wheel as inert
  certificate data. Its trusted verifier must not import candidate dependencies.
  Keep the existing installed-bundle regression as additional runtime evidence.
- Prepare a bounded producer for proposed `specfact-semgrep==1.179.0.post1`, using
  seven exact upstream Semgrep 1.179.0 wheels and MCP 1.30.0. Preserve full tags,
  Python/native payload bytes, permissions, entrypoints and original notices.
- Build once with deterministic compression, execute the same bytes in all 21
  supported platform/Python cells, and attest source, outputs and evidence in CI.
- Require explicit source/license review, normal installer and migration proof,
  complete actual/upstream advisory coverage and operator-controlled publication.
  Keep canonical scanner dependencies unchanged until actual PyPI publication and
  artifact verification permit normal frozen regeneration.

No audit omission, advisory waiver, resolver override, local signing, core merge
or core publication is included. A candidate producer does not fix the delivered
MCP graph. Final authority and covered-PR closure remain dependent on actual green
consumer adoption. PR #779 remains an unmerged related proposal; its candidate
mechanics and source hashes are design inputs, not adopted admission authority.
The fourteen native replacement scenarios remain parked and unimplemented.

## Capabilities

### New Capabilities

- `isolated-scanner-runtime`: certificate trust safety and an exact packaging-only
  scanner dependency correction, with production adoption separately gated.

### Modified Capabilities

None.

## Impact

Certificate proof, one exact scanner recipe, one bounded producer and its candidate
CI/evidence, focused tests and dependency-only hotfix preparation. Existing scanner
commands and imports remain. A renamed distribution cannot safely coexist with
upstream Semgrep because they own the same files. Existing environments require a
reviewed fresh-environment or explicit uninstall/reinstall migration, proved before
adoption. It does not satisfy third-party `Requires-Dist: semgrep` declarations.

## Source Tracking

- **Source Repository**: nold-ai/specfact-cli
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/780>
- **Last Synced Status**: Todo. The owner's autonomous MCP-fixing request authorizes
  this scoped producer preparation. Modules #523 still gates actual scanner
  removal/replacement; preserving runtime interfaces requires testing the exact
  pinned installed module and any distribution ownership requirements.

## Acceptance Criteria

- The exact frozen certifi artifact and installed runtime exclude compromised DER
  SHA256 `86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b`.
- Actual current upstream metadata first fails the MCP 1.30.0 artifact contract;
  reviewed generated wheels pass it without changing scanner payloads or tags.
- Every native cell installs the same canonical built wheel and proves scanner,
  Python entry module, MCP, dependency integrity, audit and relevant module use.
- Only reviewed CI signs. Public package ownership, publisher configuration and
  first publication require the operator's concrete activation before adoption.
- Actual public-index pip/uv adoption, complete audits, final exact-tree authority
  and all required CI checks precede readiness, duplicate closure or promotion.
