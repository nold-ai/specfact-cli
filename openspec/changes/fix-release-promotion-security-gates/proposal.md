# Change: Fix release promotion security gates

## Why

The frozen development graph on `dev` still resolves `mcp==1.23.3` through
Semgrep 1.171.0, leaving three published MCP advisories in both authoritative
lock representations. GitHub CodeQL also reports one shared cache-persistence
sink as 24 duplicate workflow dataflows. The currently proposed PR #698 grew a
PR-controlled amendment/provenance subsystem with two unresolved P1 findings;
that subsystem is unnecessary now that an organization-required workflow
authenticates an unedited member capability against the exact repository, pull
request, branch, commit, and tree.

## What Changes

- Disable persistent `uv` and post-fixture npm caches and retain the
  compatibility lane only on the protected scheduled trigger.
- Verify the immutable module fixture commit and tree before exporting its path.
- Upgrade only the optional development/scanning tool edge to Semgrep 1.175.0
  and its compatible fixed `mcp==1.29.0`; remove the obsolete MCP waiver.
- Bind Code Review lock inputs and license exceptions to their exact isolated
  environment.
- Fail closed when Git cannot prove a native OpenSpec archive, and preserve
  ordinary active-change deletes and renames.
- Resolve installed pytest before adding the repository root, classify malformed
  bootstrap authority as metadata failure, and protect `rg` path arguments.
- Archive completed change #689 and release the next patch version, 0.55.4.
- Do not replay PR #698's amendment cycles, final-producer authority, expanded
  AST provenance framework, or systemd executor.

## Capabilities

### Modified Capabilities

- `trustworthy-green-checks`: remove persistent privileged caches and dynamic
  manual fixture execution while preserving required checks.
- `dep-license-gate`: select a compatible fixed Semgrep/MCP graph and scope
  license exceptions to the exact reviewed interpreter.
- `requirements-runtime-proof-delivery`: authenticate archive selection and
  prevent repository-root pytest shadowing without a new proof framework.

## Impact

- **Affected code:** CI setup/orchestration, frozen dependency policy, license
  and archive checks, two small Requirements helpers, release metadata, and
  focused tests.
- **Security:** clears six duplicate MCP alert manifestations without an
  exception and removes the shared CodeQL cache sink. The CodeQL exploit path is
  unproven on the current immutable fixture, so the cache change is classified
  as fail-closed hardening rather than a confirmed compromise.
- **Compatibility:** no core runtime dependency or public CLI/API changes.
  Twine 7.0.0, Hatchling 1.32.0, Setuptools `<85`, pip 26.2.1, and Ruby JSON
  2.21.2 are already present and unchanged on `dev`.
- **Documentation:** update the dependency trust record and changelog; README,
  public guides, landing page, and navigation are unaffected.
- **Rollback:** revert the security PR. After publication, correct through a
  forward patch; yank only an unsafe PyPI artifact and never rewrite a tag.

## Source Tracking

- **GitHub Issue**: #692
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/692>2>2>2>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open; in progress; assigned; labels bug/openspec/QA/security
