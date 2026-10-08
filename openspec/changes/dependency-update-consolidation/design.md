# Focused baseline repair

Reuse existing #747 and its change identity. This implementation branch covers only the
focused scenarios; do not copy #748's broader inspection-only mapping into a verified claim.

Two early assumptions: patched packages resolve together and analyzer failures indicate a
production regression. The three-package graph fails Semgrep/PyJWT and virtualenv/discovery
constraints. The five-package candidate resolves exactly PyJWT 2.15.1, urllib3 2.8.0,
virtualenv 21.7.13, Semgrep 1.179.0 and python-discovery 1.6.0. Unchanged dev reproduction
shows the analyzer fixture fails by staging .git/config before invoking production code.

Publish spec/tests/agent acceptance first with unchanged locks and the broken fixture;
retain authentic host RED. Never fabricate run IDs, late-RED authority, reviewer identity
or prior receipts. Repair through reviewed lock generation and the narrow staging root.
Preserve trust exceptions, signatures, release versions, gates and exact module fixture.

JWT options must remain caller-owned and expiry must remain enforced on reuse; normal signed
tokens and trailing signature padding must work. Check urllib3 proxy TLS/body boundaries,
virtualenv discovery/seeding and Semgrep invocation separately. Virtualenv 21.7.13 is not a
universal downloaded-wheel integrity guarantee; disclose metadata-unavailable limitations.

Obtain independent patch review and applicable native/quality/security/Python matrix proof.
Integrate through normal review, then update #755 and obtain its new exact-head member grant.
Roll back coherent inputs only to a reviewed safe graph, retaining evidence. Broader #748
scope and all planned workflow runtime tasks remain outside this repair.
