# Design

Use the existing Python dependency and frozen-delivery owners. Add a canonical
certifi minimum beside requests and regenerate locks with the checked-in refresh
command. Do not add a second certificate store, environment registry or scanner
runtime implementation.

The regression observes TLS trust material rather than mirroring a version string.
Create an SSL context with only certifi's CA file, obtain its DER certificates and
compare SHA256 fingerprints. The store must be nonempty and must not contain the
compromised emSign ECC Root CA - G3 fingerprint. This test fails with the exact old
frozen bundle and passes with the patched universal bundle.

The source code and Semgrep execution contract remain unchanged. All three frozen
Python audits still run; the known MCP failure remains visible. The prior native
proposal, its fourteen scenarios and migration prerequisites are preserved as
future work under `openspec/parking-lot/replace-vulnerable-scanner-runtime/`.
They require their own acceptance and execution evidence before any implementation.
Do not convert their inspections into runtime proof for this certifi-only unit.

The owner requires signing through CI/CD only. Versioning follows the actual
compatible dependency patch; publication and promotion remain blocked by MCP.
