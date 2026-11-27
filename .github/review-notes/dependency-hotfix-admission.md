# Scoped dependency hotfix admission follow-up

This follow-up implements the Requirements admission requested after
[nold-ai/specfact-cli#782](https://github.com/nold-ai/specfact-cli/pull/782)
merged into dev. Its merge commit is
`3cf72e848a2b5a233d3f599898d6983319d375de`. The original three Requirements
checks remain failed. Security Audit passed with the exact temporary MCP
advisory exception. A merge does not convert the failed provenance into proof.

The companion protected-policy proposal is
[nold-ai/.github#4](https://github.com/nold-ai/.github/pull/4).
The implementation evaluates a separately approved HumanApprovedLateCycle
state at all three core CI boundaries. The original native report remains
failed and unchanged. Every boundary independently checks the exact source,
head/tree, policy revision, evidence, live human permission and expiry.
A previous decision sidecar grants no authority to another run.

The original eleven dependency cases remain required. Three new workflow
control cases cover native report preservation, enforced policy failures,
scoped routing and an isolated CI-only native evidence attester. Their real
pre-code workflow refusal is retained in the change's TDD evidence. The
admission implementation has independent technical review and local verification.
Protected deployment and live CI attestation verification remain pending.

This follow-up changes CI controls and their specification and tests. It does
not change application runtime, dependency pins, core version or signed module
assets. It does not supply historical native RED, suppress other findings or
authorize a protected deployment or merge. Signing is CI/CD-only. The owner
will review the exact deployment and grant payloads after implementation.

A later dependency-only package hotfix still starts from published v0.55.4
commit `d579970565530c3fd7b98bad4de90cf874c2a99d`, with a release payload check
that excludes unrelated unreleased dev runtime changes. This CI follow-up is
not a package release or a promotion of all dev commits.
