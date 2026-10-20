# Design

## Usage and ownership

The eventual consumer keeps ordinary pip extras, frozen uv installation, the
`semgrep` command and `semgrep.console_scripts.pysemgrep` entry module. A new
public distribution identity changes packaging ownership, not scanner code. Its
proposed version is 1.179.0.post1, a legal public postrelease. Local versions and
direct wheel URL dependencies cannot satisfy the future public core release.

One immutable recipe owns the seven exact upstream hashes, complete platform
tags, proposed downstream identity and MCP 1.29.0 to 1.30.0 transformation. One
standard-library producer owns archive validation and payload comparison. The
workflow owns canonical compression runtime, build/test aggregation and CI-only
attestation. Existing dependency gates own eventual consumer adoption. There is
no new self-approved admission service and no protected-policy root change.

## Certificate proof

The fresh Requirements consumer intentionally uses the trusted base verifier
closure. Its installed certifi is not the candidate delivery. The mapped test
therefore identifies the candidate's exact certifi wheel from uv.lock and the
hash-protected export, verifies its SHA256, metadata and RECORD, and parses only
its CA bundle as inert data with trusted SSL. Candidate package imports and
site-packages never enter the verifier. The installed-bundle regression remains
unchanged as separate actual-runtime coverage.

The revised mapping needs independent technical acceptance and a genuine new
native RED/GREEN cycle. Existing certificate RED records remain historical
proof of the earlier correction, not fabricated acceptance of the new mapping.
The new cycle may retain passing certificate coverage while the new scanner
artifact case fails on actual current upstream MCP 1.29.0 metadata.

## Exact wheel transformation

`build --recipe PATH --upstream PATH --output DIR` returns a candidate wheel.
`verify --recipe PATH --upstream PATH --candidate PATH` verifies the exact output.
These are proposed interfaces until implementation. A validated recipe contains
seven `UpstreamWheel(filename, sha256, url, platform_tag)` rows. A built candidate
binds its output digest to the source and recipe digests. None grants publication.

Permit only Name, Version, exact MCP dependency, explicit downstream lineage
notice, identity-derived .dist-info/.data root names and resulting RECORD changes.
Preserve every other payload byte, native/library mode, full WHEEL tag, entrypoint
and license notice. Reject unsafe/duplicate archive paths, invalid RECORD,
unexpected metadata cardinality, changed source hashes and incomplete platforms.
Do not retag manylinux and musllinux as generic Linux. They have different native
payloads and loaders. Use bounded deterministic ZIP_DEFLATED compression; measure
actual sizes and reproducibility against the destination's upload limits.

One canonical CI build produces all seven artifacts. The 21 native cells install
those exact artifacts, rather than rebuilding per Python. Separate cell outputs
converge only in a read-only aggregator that rejects missing/duplicate coverage,
mixed source/recipe identities or installation of different wheel hashes.

## Migration, audit and publication

The fork and upstream distribution own the same installed paths. Prove fresh
installs and an explicit upstream-uninstall/reinstall or fresh-environment
migration. Reject dual ownership. Do not claim a bare pip upgrade removes the old
package or that the fork satisfies another package's upstream-name dependency.
Test the pinned signed module's actual scanner and distribution-owner contracts.

Retain actual downstream advisory queries and every actual transitive package.
Add exact upstream Semgrep code coverage only after proving payload equivalence.
Unknown, missing, skipped or duplicate identities and tool errors fail closed.
Keep actual MCP 1.30.0 and certifi coverage. A new package name is not an audit fix.
Review complete native component licenses/notices and corresponding source.

CI attests exact producer source, recipe, wheel and native evidence hashes.
Candidate jobs receive no publishing credentials. A separate publication job
consumes the tested bytes without rebuilding and uses an operator-controlled
project-specific PyPI Trusted Publisher. First publication, name ownership and
configuration remain unestablished. Plain pip supplies normal PyPI trust, not
custom Sigstore verification. Verify actual published hashes/provenance before
changing all three canonical Semgrep declarations and normally refreshing locks.

## Synthesis and rejected alternatives

Three independent model candidates converged on public registry delivery.
Independent cross-review selected the most complete candidate; retain its upload
size and migration checks, and the second candidate's Python module and additive
audit contracts. Reject the third candidate's local version and custom approval
service. Isolation alone leaves vulnerable MCP. Embedding the scanner changes
base install footprint and platform packaging. Unauthenticated OpenGrep wheels
and incomplete component closure cannot substitute for verified delivery.
PR #779's draft protected-dev selectors are not adopted universal policy.

## Boundaries

Core remains 0.55.11. The parked native replacement scope, module reset sequence,
protected authority and all required gates remain. No locally signed artifact,
audit suppression, core merge/publication or duplicate closure is authorized.
Producer preparation and candidate success are not final consumer remediation.
