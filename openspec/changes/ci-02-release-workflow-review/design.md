# Design

Execute a small isolated Python block in each source-consuming workflow. Load only the canonical verifier and public
key from the separate base checkout. For this release, the minimum required bundle set is backlog, codebase,
code-review, govern, project, requirements and spec (each with the `specfact-` prefix). This seven-bundle minimum is a
release invariant, not a permanent aggregate manifest or an upper bound. Authenticate the signed per-module manifest
and filesystem payload for every `packages/*/src` import root, including any additional exported roots, before exports.
Changing the required minimum requires an explicit reviewed update. Do not execute the PR-owned wrapper. Current main
lacks that wrapper, so changing only its path would break bootstrap. The canonical verifier CLI scans another layout;
use its existing API.

This removes the wrapper dependency. It does not establish protected authority around PR-controlled workflow YAML.
The existing base-SHA checkout, identity checks, least-privilege permissions and export ordering remain unchanged.
Tests execute the actual workflow shell with real ephemeral signing fixtures and a hostile local wrapper. These test
keys are generated per fixture and are unrelated to publisher signing credentials.

Keep original docs16 and trigger-parity proof immutable. New scenario mapping selects prospective authentication and
Node regressions using exact parameter selectors. Complete push preservation is already implemented; its passing
controls remain separate mandatory regression evidence and are not included in an all-failing prospective RED plan.
Changing the old mapping would invalidate its retained proof; the review disposition must state this constraint.

Use the existing pinned setup-node action and Node24.16.0 used elsewhere in this repository. Set it before Python
validation in tests, compat-py311 and scheduled dependency-compatibility; preserve promotion skip conditions.
